"""
Simulation Runner for Hydraulic Engine (Task 10)
Coordinates solver selection, scenario setup, parameter perturbation, and output packaging.
"""
from typing import Dict, Any, Optional
import json

from app.services.hydraulic_engine.base_engine import HydraulicEngineBase
from app.services.hydraulic_engine.wntr_engine import WNTREngine, HAS_WNTR
from app.services.hydraulic_engine.todini_solver import TodiniGlobalGradientSolver
from app.services.hydraulic_engine.simulation_results import HydraulicSimulationResult


class SimulationRunner:
    """
    Executes steady-state and extended-period hydraulic simulations under baseline
    or perturbed what-if operational scenarios.
    """

    @classmethod
    def execute(
        cls,
        network_data: Dict[str, Any],
        scenario_id: str = "SCEN-DEFAULT",
        scenario_type: str = "BASELINE",
        duration_hours: int = 24,
        timestep_minutes: int = 60,
        solver_mode: str = "PDA",
        overrides: Optional[Dict[str, Any]] = None,
    ) -> HydraulicSimulationResult:
        """
        Runs the hydraulic simulation and returns standardized results.
        """
        network_data["scenario_id"] = scenario_id
        merged_overrides = overrides or {}

        # If scenario specifies overrides in JSON
        if isinstance(merged_overrides, str):
            try:
                merged_overrides = json.loads(merged_overrides)
            except Exception:
                merged_overrides = {}

        # Select Engine: WNTR Engine if installed and requested, else Todini solver
        if HAS_WNTR and solver_mode.upper() != "PURE_TODINI":
            engine: HydraulicEngineBase = WNTREngine(network_data)
            engine.apply_overrides(merged_overrides)
            return engine.run_simulation(
                duration_hours=duration_hours,
                timestep_minutes=timestep_minutes,
                demand_model=solver_mode,
            )
        else:
            solver = TodiniGlobalGradientSolver(network_data)
            return solver.solve(
                duration_hours=duration_hours,
                timestep_minutes=timestep_minutes,
                demand_multiplier=float(merged_overrides.get("demand_multiplier", 1.0)),
                leak_overrides=merged_overrides.get("leaks", []),
                pipe_overrides=merged_overrides.get("pipe_overrides", {}),
                pump_overrides=merged_overrides.get("pump_overrides", {}),
            )

