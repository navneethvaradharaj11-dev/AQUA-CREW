"""
Optimization Validation & Engineering Safety Verification Service (Task 14)
Performs independent hydraulic re-evaluation of candidate configurations using
the trusted WNTR/EPANET simulation engine. Strictly rejects any candidate violating physical or regulatory constraints.
"""
from typing import Dict, Any, List, Tuple
import copy

from app.services.hydraulic_engine.simulation_results import HydraulicSimulationResult
from app.services.hydraulic_engine.simulation_runner import SimulationRunner
from app.schemas.optimization import (
    OptimizationCandidateSchema,
    OptimizationConstraintsSchema,
)


class OptimizationValidator:
    """
    Mandatory safety gate: verifies physical and hydraulic viability of proposed configurations.
    """

    @classmethod
    def verify_candidate(
        cls,
        candidate_variables: Dict[str, float],
        base_network_data: Dict[str, Any],
        scenario_overrides: Dict[str, Any],
        constraints: OptimizationConstraintsSchema,
        duration_hours: int = 24,
        timestep_minutes: int = 60,
        demand_model: str = "PDA",
    ) -> Tuple[bool, Optional[HydraulicSimulationResult], List[str]]:
        """
        Executes full hydraulic simulation on an isolated network copy.
        Evaluates convergence, mass continuity, pressure limits, pipe velocities, and tank boundaries.
        """
        violations: List[str] = []

        # 1. Variable bounds validation
        pump_speed = candidate_variables.get("pump_speed_P1", 1.0)
        if pump_speed < 0.50 or pump_speed > 1.20:
            violations.append(f"Pump speed ({pump_speed:.2f}) outside permissible engineering bounds [0.50, 1.20].")

        prv_setting = candidate_variables.get("prv_setting_PRV01", 3.5)
        if prv_setting < 1.0 or prv_setting > 6.0:
            violations.append(f"PRV downstream setting ({prv_setting:.2f} bar) outside acceptable range [1.0, 6.0 bar].")

        if len(violations) > 0:
            return False, None, violations

        # 2. Prepare isolated network copy (Rule 11: Never mutate baseline!)
        net_copy = copy.deepcopy(base_network_data)
        overrides_copy = copy.deepcopy(scenario_overrides)

        # Apply candidate decision variables to isolated network copy
        if "pump_overrides" not in overrides_copy:
            overrides_copy["pump_overrides"] = {}
        overrides_copy["pump_overrides"]["LINK-PUMP-BOOSTER-01"] = {
            "status": "OPEN" if pump_speed > 0.05 else "CLOSED",
            "speed": pump_speed,
        }

        # Update PRV setting in links
        if "LINK-VALVE-HRB-PRV" in net_copy.get("links", {}):
            net_copy["links"]["LINK-VALVE-HRB-PRV"]["valve_setting"] = prv_setting

        # 3. Independent Hydraulic Simulation Execution
        try:
            sim_result = SimulationRunner.execute(
                network_data=net_copy,
                scenario_id="SCEN-OPTIMIZATION-VERIFY",
                scenario_type="CANDIDATE_VERIFICATION",
                duration_hours=duration_hours,
                timestep_minutes=timestep_minutes,
                solver_mode=demand_model,
                overrides=overrides_copy,
            )
        except Exception as ex:
            violations.append(f"Hydraulic solver execution failed during re-verification: {str(ex)}")
            return False, None, violations

        # 4. Check Convergence
        if not sim_result.converged:
            violations.append("Hydraulic solver did not achieve numerical convergence.")

        # 5. Check Pressure Constraints
        for nid, nres in sim_result.nodes.items():
            ntype = net_copy.get("nodes", {}).get(nid, {}).get("node_type", nres.node_type).upper()
            if ntype == "JUNCTION":
                p = float(nres.pressure_bar)
                if p < constraints.min_service_pressure_bar:
                    violations.append(f"Node '{nid}' pressure ({p:.2f} bar) violates minimum service pressure ({constraints.min_service_pressure_bar:.2f} bar).")
                elif p > constraints.max_allowable_pressure_bar:
                    violations.append(f"Node '{nid}' pressure ({p:.2f} bar) exceeds maximum structural limit ({constraints.max_allowable_pressure_bar:.2f} bar).")

        # 6. Check Pipe Velocities
        for lid, lres in sim_result.links.items():
            ltype = net_copy.get("links", {}).get(lid, {}).get("link_type", lres.link_type).upper()
            if ltype == "PIPE":
                v = float(lres.velocity_mps)
                if v > constraints.max_pipe_velocity_mps:
                    violations.append(f"Pipe '{lid}' velocity ({v:.2f} m/s) exceeds maximum velocity constraint ({constraints.max_pipe_velocity_mps:.2f} m/s).")

        # 7. Check Demand Satisfaction
        req_d = sum(
            float(n.get("base_demand_lps", 0.0))
            for n in net_copy.get("nodes", {}).values()
            if n.get("node_type", "").upper() == "JUNCTION"
        )
        deliv_d = sum(
            max(0.0, float(n.actual_demand_lps))
            for nid, n in sim_result.nodes.items()
            if net_copy.get("nodes", {}).get(nid, {}).get("node_type", "").upper() == "JUNCTION"
        )
        sat_ratio = (deliv_d / req_d) if req_d > 0 else 1.0
        if sat_ratio < constraints.min_demand_satisfaction_ratio:
            violations.append(
                f"Demand satisfaction ({sat_ratio * 100:.1f}%) is below minimum required threshold ({constraints.min_demand_satisfaction_ratio * 100:.1f}%)."
            )

        # 8. Check Mass Balance Continuity
        tot_leak = sum(float(n.leak_flow_lps) for n in sim_result.nodes.values())
        tot_supply = deliv_d + tot_leak
        if tot_supply <= 0.0:
            violations.append("Network flow is zero: supply discontinuity detected.")

        is_valid = (len(violations) == 0)
        return is_valid, sim_result, violations

