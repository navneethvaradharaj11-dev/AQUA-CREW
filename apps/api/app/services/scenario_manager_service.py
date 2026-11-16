"""
Hydraulic Simulation Scenario Manager & What-If Engine (Task 10)
Manages baseline and what-if simulation scenarios, executes runs,
computes differential comparisons, and integrates with AI leak detection and rover dispatch.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import uuid
import copy
from datetime import datetime, timezone

from app.models.digital_twin import (
    SimulationScenarioModel,
    SimulationRunModel,
    ScenarioComparisonModel,
    HydraulicNetworkModel,
)
from app.services.hydraulic_network_service import HydraulicNetworkService, DEFAULT_NETWORK_ID
from app.services.hydraulic_engine.network_adapter import NetworkAdapter
from app.services.hydraulic_engine.simulation_runner import SimulationRunner
from app.services.hydraulic_engine.simulation_results import HydraulicSimulationResult


DEFAULT_SCENARIOS = [
    {
        "id": "SCEN-BASELINE-01",
        "name": "Baseline Municipal Operating Conditions",
        "scenario_type": "BASELINE",
        "description": "Nominal 24-hour diurnal water distribution across Metro Central with balanced pressure gradients and zero active leaks.",
        "is_baseline": True,
        "duration_hours": 24,
        "time_step_minutes": 60,
        "solver_mode": "PDA",
        "parameters_override": {
            "demand_multiplier": 1.0,
            "leaks": [],
            "pipe_overrides": {},
            "pump_overrides": {},
        },
    },
    {
        "id": "SCEN-PEAK-DEMAND-01",
        "name": "Summer Morning Peak Demand Surge",
        "scenario_type": "HIGH_DEMAND",
        "description": "Simulates 1.6x municipal demand surge during hot summer morning hours, testing peripheral node pressure resilience.",
        "is_baseline": False,
        "duration_hours": 24,
        "time_step_minutes": 60,
        "solver_mode": "PDA",
        "parameters_override": {
            "demand_multiplier": 1.60,
            "leaks": [],
            "pipe_overrides": {},
            "pump_overrides": {},
        },
    },
    {
        "id": "SCEN-BURST-PIPE-02",
        "name": "Severe Pipe Burst on Metro Central Trunk B",
        "scenario_type": "PIPE_BURST",
        "description": "Catastrophic structural pipe rupture on PIPE-SEC-4B-92 near J2. Emitter orifice area 35 cm2 discharging over 40 L/s, inducing major pressure deficit.",
        "is_baseline": False,
        "duration_hours": 24,
        "time_step_minutes": 60,
        "solver_mode": "PDA",
        "parameters_override": {
            "demand_multiplier": 1.0,
            "leaks": [
                {
                    "node_id": "NODE-JUNC-02",
                    "area_m2": 0.0035,
                    "discharge_coeff": 0.80,
                    "pipeline_segment_id": "PIPE-SEC-4B-92",
                    "severity": "CRITICAL_BURST",
                }
            ],
            "pipe_overrides": {},
            "pump_overrides": {},
        },
    },
    {
        "id": "SCEN-MINOR-LEAK-03",
        "name": "Developing Pin-Hole Leak at Industrial Feeder 1",
        "scenario_type": "MINOR_LEAK",
        "description": "Simulates an incipient sub-surface pipe leak on PIPE-IND-1A-04 near J4, correlated with Task 07 acoustic anomalies. Emitter area 4 cm2.",
        "is_baseline": False,
        "duration_hours": 24,
        "time_step_minutes": 60,
        "solver_mode": "PDA",
        "parameters_override": {
            "demand_multiplier": 1.0,
            "leaks": [
                {
                    "node_id": "NODE-JUNC-04",
                    "area_m2": 0.0004,
                    "discharge_coeff": 0.75,
                    "pipeline_segment_id": "PIPE-IND-1A-04",
                    "severity": "MODERATE_LEAK",
                }
            ],
            "pipe_overrides": {},
            "pump_overrides": {},
        },
    },
    {
        "id": "SCEN-PUMP-TRIP-04",
        "name": "Grand Avenue Spine Booster Pump Trip",
        "scenario_type": "PUMP_TRIP",
        "description": "Simulates unannounced mechanical shutdown / power trip of Booster Pump Station P1, testing gravity supply headloss across central network.",
        "is_baseline": False,
        "duration_hours": 24,
        "time_step_minutes": 60,
        "solver_mode": "PDA",
        "parameters_override": {
            "demand_multiplier": 1.0,
            "leaks": [],
            "pipe_overrides": {},
            "pump_overrides": {
                "LINK-PUMP-BOOSTER-01": {"status": "CLOSED", "speed": 0.0}
            },
        },
    },
    {
        "id": "SCEN-RECOVERY-05",
        "name": "Post-Repair Network Isolation & Controlled Recovery",
        "scenario_type": "RECOVERY",
        "description": "Simulates network re-pressurization following emergency valve isolation on Trunk B, routing compensatory flow from Industrial Storage Tank T1.",
        "is_baseline": False,
        "duration_hours": 24,
        "time_step_minutes": 60,
        "solver_mode": "PDA",
        "parameters_override": {
            "demand_multiplier": 0.95,
            "leaks": [],
            "pipe_overrides": {
                "LINK-PIPE-TRUNK-B1": {"status": "CLOSED"}
            },
            "pump_overrides": {
                "LINK-PUMP-BOOSTER-01": {"status": "OPEN", "speed": 1.15}
            },
        },
    },
]


class ScenarioManagerService:
    @staticmethod
    def seed_default_scenarios(db: Session, network_id: str = DEFAULT_NETWORK_ID) -> None:
        HydraulicNetworkService.get_or_create_default_network(db)
        existing_count = db.query(SimulationScenarioModel).filter(SimulationScenarioModel.network_id == network_id).count()
        if existing_count == 0:
            for s in DEFAULT_SCENARIOS:
                scen = SimulationScenarioModel(
                    id=s["id"],
                    network_id=network_id,
                    name=s["name"],
                    scenario_type=s["scenario_type"],
                    description=s["description"],
                    is_baseline=s["is_baseline"],
                    duration_hours=s["duration_hours"],
                    time_step_minutes=s["time_step_minutes"],
                    solver_mode=s["solver_mode"],
                    parameters_override_json=json.dumps(s["parameters_override"]),
                    status="COMPLETED",
                    is_simulated=True,
                )
                db.add(scen)
            db.commit()

            # Pre-run baseline scenario so initial data is immediately available
            baseline = db.query(SimulationScenarioModel).filter(SimulationScenarioModel.id == "SCEN-BASELINE-01").first()
            if baseline:
                ScenarioManagerService.execute_scenario_run(db, baseline.id)

    @staticmethod
    def list_scenarios(db: Session, network_id: str = DEFAULT_NETWORK_ID) -> List[SimulationScenarioModel]:
        ScenarioManagerService.seed_default_scenarios(db, network_id)
        return db.query(SimulationScenarioModel).filter(SimulationScenarioModel.network_id == network_id).all()

    @staticmethod
    def get_scenario(db: Session, scenario_id: str) -> Optional[SimulationScenarioModel]:
        return db.query(SimulationScenarioModel).filter(SimulationScenarioModel.id == scenario_id).first()

    @staticmethod
    def create_scenario(
        db: Session,
        network_id: str,
        name: str,
        scenario_type: str,
        description: str,
        parameters_override: Dict[str, Any],
        duration_hours: int = 24,
        time_step_minutes: int = 60,
        solver_mode: str = "PDA",
        is_baseline: bool = False,
    ) -> SimulationScenarioModel:
        if is_baseline:
            existing_baseline = (
                db.query(SimulationScenarioModel)
                .filter(SimulationScenarioModel.network_id == network_id, SimulationScenarioModel.is_baseline == True)
                .first()
            )
            if existing_baseline:
                raise ValueError("Baseline scenario is immutable and already exists for this network. Overwriting baseline is forbidden.")

        scenario_id = f"SCEN-{uuid.uuid4().hex[:8].upper()}"
        scen = SimulationScenarioModel(
            id=scenario_id,
            network_id=network_id,
            name=name,
            scenario_type=scenario_type,
            description=description,
            is_baseline=is_baseline,
            duration_hours=duration_hours,
            time_step_minutes=time_step_minutes,
            solver_mode=solver_mode,
            parameters_override_json=json.dumps(parameters_override),
            status="PENDING",
            is_simulated=True,
        )
        db.add(scen)
        db.commit()
        db.refresh(scen)
        return scen

    @staticmethod
    def execute_scenario_run(
        db: Session,
        scenario_id: str,
        temporary_overrides: Optional[Dict[str, Any]] = None
    ) -> SimulationRunModel:
        scen = ScenarioManagerService.get_scenario(db, scenario_id)
        if not scen:
            raise ValueError(f"Simulation scenario {scenario_id} not found.")

        # Get network and topology with strict scenario isolation (deep copy)
        topo = HydraulicNetworkService.get_network_topology(db, scen.network_id)
        solver_data = copy.deepcopy(topo["solver_data"])

        # Parse stored parameters override
        try:
            stored_overrides = json.loads(scen.parameters_override_json)
        except Exception:
            stored_overrides = {}

        # Merge with temporary overrides if provided
        if temporary_overrides:
            stored_overrides = copy.deepcopy(stored_overrides)
            stored_overrides.update(temporary_overrides)

        # Execute physical hydraulic simulation
        res: HydraulicSimulationResult = SimulationRunner.execute(
            network_data=solver_data,
            scenario_id=scen.id,
            scenario_type=scen.scenario_type,
            duration_hours=scen.duration_hours,
            timestep_minutes=scen.time_step_minutes,
            solver_mode=scen.solver_mode,
            overrides=stored_overrides,
        )

        # Calculate mass continuity residual for provenance
        mass_residual = abs(res.total_supply_lps - (res.total_demand_lps + res.total_leakage_lps))

        # Store run
        run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
        res_dict = res.to_dict()

        run = SimulationRunModel(
            id=run_id,
            scenario_id=scen.id,
            network_id=scen.network_id,
            execution_timestamp=datetime.now(timezone.utc),
            execution_duration_ms=res.execution_duration_ms,
            converged=res.converged,
            iterations=res.iterations,
            total_demand_m3=round(res.total_demand_lps * 3.6, 2),  # L/s to m3/hr approx
            total_leakage_m3=round(res.total_leakage_lps * 3.6, 2),
            water_loss_percentage=res.water_loss_percentage,
            min_pressure_bar=res.min_pressure_bar,
            max_pressure_bar=res.max_pressure_bar,
            pressure_deficit_nodes_count=res.pressure_deficit_count,
            summary_json=json.dumps({
                "solver_name": res.solver_name,
                "total_supply_lps": res.total_supply_lps,
                "total_demand_lps": res.total_demand_lps,
                "total_leakage_lps": res.total_leakage_lps,
                "mass_continuity_residual_lps": round(mass_residual, 6),
                "mass_conserved": mass_residual < 0.1,  # within 0.1 L/s numerical tolerance
                "avg_pressure_bar": res.avg_pressure_bar,
                "network_version": "1.0.0",
                "is_simulated": True,
                "source": "VIRTUAL_SIMULATION_ENGINE",
            }),
            node_results_json=json.dumps(res_dict["nodes"]),
            link_results_json=json.dumps(res_dict["links"]),
            time_series_json=json.dumps(res_dict["timesteps"]),
            is_simulated=True,
        )
        db.add(run)

        # Mark scenario completed
        scen.status = "COMPLETED"
        scen.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def get_scenario_runs(db: Session, scenario_id: str) -> List[SimulationRunModel]:
        return (
            db.query(SimulationRunModel)
            .filter(SimulationRunModel.scenario_id == scenario_id)
            .order_by(SimulationRunModel.execution_timestamp.desc())
            .all()
        )

    @staticmethod
    def get_run(db: Session, run_id: str) -> Optional[SimulationRunModel]:
        return db.query(SimulationRunModel).filter(SimulationRunModel.id == run_id).first()

    @staticmethod
    def compare_scenarios(
        db: Session,
        baseline_scenario_id: str,
        comparison_scenario_id: str,
    ) -> Dict[str, Any]:
        """
        Calculates hydraulic deltas between a baseline scenario and a what-if perturbation.
        Computes nodal pressure drops, velocity surges, headloss increases, and unserved demand.
        """
        # Ensure latest runs exist for both
        b_runs = ScenarioManagerService.get_scenario_runs(db, baseline_scenario_id)
        if not b_runs:
            b_run = ScenarioManagerService.execute_scenario_run(db, baseline_scenario_id)
        else:
            b_run = b_runs[0]

        c_runs = ScenarioManagerService.get_scenario_runs(db, comparison_scenario_id)
        if not c_runs:
            c_run = ScenarioManagerService.execute_scenario_run(db, comparison_scenario_id)
        else:
            c_run = c_runs[0]

        b_nodes = json.loads(b_run.node_results_json)
        c_nodes = json.loads(c_run.node_results_json)

        b_links = json.loads(b_run.link_results_json)
        c_links = json.loads(c_run.link_results_json)

        # Calculate Node Deltas
        node_deltas = {}
        affected_nodes_count = 0
        for nid, b_n in b_nodes.items():
            c_n = c_nodes.get(nid, {})
            b_p = b_n.get("pressure_bar", 0.0)
            c_p = c_n.get("pressure_bar", 0.0)
            delta_p = round(c_p - b_p, 3)

            b_leak = b_n.get("leak_flow_lps", 0.0)
            c_leak = c_n.get("leak_flow_lps", 0.0)
            delta_leak = round(c_leak - b_leak, 3)

            is_affected = abs(delta_p) > 0.20 or delta_leak > 0.1
            if is_affected:
                affected_nodes_count += 1

            node_deltas[nid] = {
                "node_id": nid,
                "name": b_n.get("name", nid),
                "baseline_pressure_bar": b_p,
                "comparison_pressure_bar": c_p,
                "delta_pressure_bar": delta_p,
                "pressure_drop_pct": round(((b_p - c_p) / b_p * 100.0) if b_p > 0 else 0.0, 1),
                "baseline_leak_lps": b_leak,
                "comparison_leak_lps": c_leak,
                "delta_leak_lps": delta_leak,
                "deficit_introduced": c_n.get("pressure_deficit", False) and not b_n.get("pressure_deficit", False),
            }

        # Calculate Link Deltas
        link_deltas = {}
        high_risk_links_count = 0
        for lid, b_l in b_links.items():
            c_l = c_links.get(lid, {})
            b_f = b_l.get("flow_lps", 0.0)
            c_f = c_l.get("flow_lps", 0.0)
            delta_flow = round(c_f - b_f, 3)

            b_v = b_l.get("velocity_mps", 0.0)
            c_v = c_l.get("velocity_mps", 0.0)
            delta_vel = round(c_v - b_v, 3)

            is_high_risk = c_v > 2.0 or abs(delta_flow) > 15.0
            if is_high_risk:
                high_risk_links_count += 1

            link_deltas[lid] = {
                "link_id": lid,
                "name": b_l.get("name", lid),
                "baseline_flow_lps": b_f,
                "comparison_flow_lps": c_f,
                "delta_flow_lps": delta_flow,
                "baseline_velocity_mps": b_v,
                "comparison_velocity_mps": c_v,
                "delta_velocity_mps": delta_vel,
                "is_high_risk": is_high_risk,
            }

        delta_leakage_m3 = round(c_run.total_leakage_m3 - b_run.total_leakage_m3, 2)
        delta_water_loss_pct = round(c_run.water_loss_percentage - b_run.water_loss_percentage, 2)
        delta_min_p = round(c_run.min_pressure_bar - b_run.min_pressure_bar, 3)

        # Persist comparison record
        cmp_id = f"CMP-{uuid.uuid4().hex[:8].upper()}"
        cmp_model = ScenarioComparisonModel(
            id=cmp_id,
            baseline_scenario_id=baseline_scenario_id,
            comparison_scenario_id=comparison_scenario_id,
            delta_total_leakage_m3=delta_leakage_m3,
            delta_water_loss_pct=delta_water_loss_pct,
            delta_min_pressure_bar=delta_min_p,
            affected_nodes_count=affected_nodes_count,
            high_risk_links_count=high_risk_links_count,
            comparison_matrix_json=json.dumps({
                "nodes": node_deltas,
                "links": link_deltas,
            }),
            is_simulated=True,
        )
        db.add(cmp_model)
        db.commit()

        return {
            "comparison_id": cmp_id,
            "baseline_scenario_id": baseline_scenario_id,
            "comparison_scenario_id": comparison_scenario_id,
            "baseline_run_id": b_run.id,
            "comparison_run_id": c_run.id,
            "delta_total_leakage_m3": delta_leakage_m3,
            "delta_water_loss_pct": delta_water_loss_pct,
            "delta_min_pressure_bar": delta_min_p,
            "affected_nodes_count": affected_nodes_count,
            "high_risk_links_count": high_risk_links_count,
            "nodes": node_deltas,
            "links": link_deltas,
            "is_simulated": True,
            "source": "VIRTUAL_SIMULATION_ENGINE",
        }

    @staticmethod
    def simulate_leak_injection(
        db: Session,
        network_id: str,
        target_node_id: str,
        leak_area_cm2: float = 5.0,
        discharge_coeff: float = 0.75,
        name: str = "Instantaneous What-If Leak Injection"
    ) -> Dict[str, Any]:
        """
        Creates a custom what-if scenario with immediate Torricelli leak injection,
        solves hydraulic convergence, and computes delta against baseline.
        """
        area_m2 = leak_area_cm2 / 10000.0  # cm2 to m2
        scenario = ScenarioManagerService.create_scenario(
            db=db,
            network_id=network_id,
            name=f"What-If Leak @ {target_node_id} ({leak_area_cm2:.1f} cm²)",
            scenario_type="WHAT_IF_LEAK",
            description=f"Operator simulated orifice leak of {leak_area_cm2:.1f} cm2 with Cd={discharge_coeff:.2f} at node {target_node_id}.",
            parameters_override={
                "demand_multiplier": 1.0,
                "leaks": [
                    {
                        "node_id": target_node_id,
                        "area_m2": area_m2,
                        "discharge_coeff": discharge_coeff,
                        "severity": "CRITICAL" if leak_area_cm2 > 10 else "MODERATE",
                    }
                ],
                "pipe_overrides": {},
                "pump_overrides": {},
            },
            duration_hours=24,
            time_step_minutes=60,
            solver_mode="PDA",
        )

        run = ScenarioManagerService.execute_scenario_run(db, scenario.id)

        # Compare with baseline
        cmp_result = ScenarioManagerService.compare_scenarios(
            db=db,
            baseline_scenario_id="SCEN-BASELINE-01",
            comparison_scenario_id=scenario.id,
        )

        return {
            "scenario": {
                "id": scenario.id,
                "name": scenario.name,
                "type": scenario.scenario_type,
            },
            "run": {
                "id": run.id,
                "converged": run.converged,
                "total_leakage_m3": run.total_leakage_m3,
                "water_loss_percentage": run.water_loss_percentage,
                "min_pressure_bar": run.min_pressure_bar,
                "pressure_deficit_nodes_count": run.pressure_deficit_nodes_count,
            },
            "comparison": cmp_result,
        }

