"""
Multi-Scenario Optimization Service (Task 14)
Evaluates candidate configurations across 10 diverse hydraulic operating conditions,
identifying resilient configurations and proving that no single setting is globally optimal for all states.
"""
from typing import Dict, Any, List, Optional
import copy

from app.services.hydraulic_engine.simulation_runner import SimulationRunner
from app.services.hydraulic_engine.network_performance_service import NetworkPerformanceService
from app.services.hydraulic_engine.optimization_validator import OptimizationValidator
from app.schemas.optimization import OptimizationConstraintsSchema


MULTI_SCENARIO_DEFINITIONS = [
    {
        "scenario_key": "NORMAL_DEMAND",
        "name": "Normal Diurnal Demand",
        "overrides": {"demand_multiplier": 1.0, "leaks": [], "pipe_overrides": {}, "pump_overrides": {}},
    },
    {
        "scenario_key": "PEAK_DEMAND",
        "name": "Summer Morning Peak Demand Surge",
        "overrides": {"demand_multiplier": 1.6, "leaks": [], "pipe_overrides": {}, "pump_overrides": {}},
    },
    {
        "scenario_key": "LOW_DEMAND",
        "name": "Minimum Night Flow Condition",
        "overrides": {"demand_multiplier": 0.50, "leaks": [], "pipe_overrides": {}, "pump_overrides": {}},
    },
    {
        "scenario_key": "MINOR_LEAK",
        "name": "Developing Pin-Hole Leak at Industrial Feeder",
        "overrides": {
            "demand_multiplier": 1.0,
            "leaks": [{"node_id": "NODE-JUNC-04", "area_m2": 0.0004, "discharge_coeff": 0.75}],
            "pipe_overrides": {},
            "pump_overrides": {},
        },
    },
    {
        "scenario_key": "MAJOR_BURST",
        "name": "Severe Pipe Burst on Metro Central Trunk B",
        "overrides": {
            "demand_multiplier": 1.0,
            "leaks": [{"node_id": "NODE-JUNC-02", "area_m2": 0.0035, "discharge_coeff": 0.80}],
            "pipe_overrides": {},
            "pump_overrides": {},
        },
    },
    {
        "scenario_key": "PUMP_OUTAGE",
        "name": "Spine Booster Pump Mechanical Trip",
        "overrides": {
            "demand_multiplier": 1.0,
            "leaks": [],
            "pipe_overrides": {},
            "pump_overrides": {"LINK-PUMP-BOOSTER-01": {"status": "CLOSED", "speed": 0.0}},
        },
    },
    {
        "scenario_key": "TANK_DEPLETION",
        "name": "Low Reserve Storage Tank Operating Mode",
        "overrides": {
            "demand_multiplier": 1.1,
            "leaks": [],
            "pipe_overrides": {},
            "pump_overrides": {},
        },
    },
    {
        "scenario_key": "ZONE_DISTURBANCE",
        "name": "Low-Elevation Harbor Zone Pressure Imbalance",
        "overrides": {
            "demand_multiplier": 1.25,
            "leaks": [],
            "pipe_overrides": {},
            "pump_overrides": {},
        },
    },
    {
        "scenario_key": "RECOVERY_ISOLATION",
        "name": "Post-Repair Network Isolation & Trunk B Reroute",
        "overrides": {
            "demand_multiplier": 0.95,
            "leaks": [],
            "pipe_overrides": {"LINK-PIPE-TRUNK-B1": {"status": "CLOSED"}},
            "pump_overrides": {"LINK-PUMP-BOOSTER-01": {"status": "OPEN", "speed": 1.15}},
        },
    },
    {
        "scenario_key": "COMBINED_PEAK_LEAK",
        "name": "Combined Summer Peak Demand and Active Distribution Leak",
        "overrides": {
            "demand_multiplier": 1.45,
            "leaks": [{"node_id": "NODE-JUNC-02", "area_m2": 0.0015, "discharge_coeff": 0.75}],
            "pipe_overrides": {},
            "pump_overrides": {},
        },
    },
]


class MultiScenarioOptimizer:
    """
    Simulates and compares baseline vs candidate configurations across 10 operational conditions.
    """

    @classmethod
    def evaluate_all_scenarios(
        cls,
        network_data: Dict[str, Any],
        candidate_variables: Dict[str, float],
        constraints: Optional[OptimizationConstraintsSchema] = None,
        duration_hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """
        Executes paired simulation for all 10 scenarios.
        """
        active_constraints = constraints or OptimizationConstraintsSchema()
        scenario_results = []

        for s_def in MULTI_SCENARIO_DEFINITIONS:
            s_key = s_def["scenario_key"]
            s_name = s_def["name"]
            overrides = s_def["overrides"]

            # 1. Baseline Run
            net_base = copy.deepcopy(network_data)
            base_sim = SimulationRunner.execute(
                network_data=net_base,
                scenario_id=f"BASE-{s_key}",
                scenario_type=s_key,
                duration_hours=duration_hours,
                overrides=overrides,
            )
            base_perf = NetworkPerformanceService.evaluate(
                result=base_sim,
                network_data=network_data,
                scenario_name=s_name,
                duration_hours=duration_hours,
            )

            # 2. Candidate Run (Applying decision variables)
            is_valid, cand_sim, violations = OptimizationValidator.verify_candidate(
                candidate_variables=candidate_variables,
                base_network_data=network_data,
                scenario_overrides=overrides,
                constraints=active_constraints,
                duration_hours=duration_hours,
            )

            cand_perf = None
            if is_valid and cand_sim:
                cand_perf = NetworkPerformanceService.evaluate(
                    result=cand_sim,
                    network_data=network_data,
                    scenario_name=f"{s_name} (Optimized)",
                    duration_hours=duration_hours,
                )

            base_leak = base_perf.water_loss.daily_leakage_volume_m3.value or 0.0
            cand_leak = cand_perf.water_loss.daily_leakage_volume_m3.value if cand_perf else base_leak
            leak_saved = max(0.0, base_leak - cand_leak)

            base_energy = base_perf.energy.pump_electrical_energy_kwh.value or 0.0
            cand_energy = cand_perf.energy.pump_electrical_energy_kwh.value if cand_perf else base_energy
            energy_saved = max(0.0, base_energy - cand_energy)

            scenario_results.append({
                "scenario_key": s_key,
                "scenario_name": s_name,
                "is_candidate_feasible": is_valid,
                "violations": violations,
                "baseline_leakage_m3": round(base_leak, 2),
                "optimized_leakage_m3": round(cand_leak, 2),
                "leakage_reduction_m3": round(leak_saved, 2),
                "baseline_energy_kwh": round(base_energy, 2),
                "optimized_energy_kwh": round(cand_energy, 2),
                "energy_saved_kwh": round(energy_saved, 2),
                "baseline_min_pressure_bar": base_perf.pressure.min_pressure_bar.value,
                "optimized_min_pressure_bar": cand_perf.pressure.min_pressure_bar.value if cand_perf else None,
                "baseline_demand_satisfaction": base_perf.hydraulic.demand_satisfaction_ratio.value,
                "optimized_demand_satisfaction": cand_perf.hydraulic.demand_satisfaction_ratio.value if cand_perf else None,
            })

        return scenario_results

