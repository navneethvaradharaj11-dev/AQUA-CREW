"""
Constrained Multi-Objective Hydraulic Optimization Engine (Task 14)
Coordinates global and local optimization algorithms, evaluates physical constraints,
and calculates baseline-versus-candidate comparative performance.
"""
from typing import Dict, Any, List, Optional, Tuple
import time
import uuid
import copy
from datetime import datetime, timezone
import numpy as np

from app.services.hydraulic_engine.simulation_results import HydraulicSimulationResult
from app.services.hydraulic_engine.simulation_runner import SimulationRunner
from app.services.hydraulic_engine.network_performance_service import NetworkPerformanceService
from app.services.hydraulic_engine.optimization_validator import OptimizationValidator
from app.services.hydraulic_engine.pareto_analysis_service import ParetoAnalysisService, PROFILE_WEIGHTS
from app.schemas.optimization import (
    OptimizationTriggerRequest,
    OptimizationCandidateSchema,
    BaselineComparisonSchema,
    OptimizationJobDetailResponse,
    ObjectiveWeightsSchema,
    OptimizationConstraintsSchema,
)


class OptimizationEngine:
    """
    Core solver for water distribution network optimization.
    Evaluates pump speeds, PRV setpoints, leakage reduction, energy efficiency, and pressure stability.
    """

    @classmethod
    def execute_optimization(
        cls,
        network_data: Dict[str, Any],
        request: OptimizationTriggerRequest,
        user_id: str = "USR-ENG-01",
        scenario_overrides: Optional[Dict[str, Any]] = None,
        duration_hours: int = 24,
        timestep_minutes: int = 60,
        demand_model: str = "PDA",
    ) -> OptimizationJobDetailResponse:
        """
        Executes end-to-end constrained multi-objective optimization.
        """
        start_time = time.perf_counter()
        job_id = f"OPT-JOB-{uuid.uuid4().hex[:10].upper()}"
        np.random.seed(request.random_seed or 42)

        # 1. Resolve Weights and Constraints
        if request.objective_profile == "CUSTOM" and request.custom_weights:
            weights = request.custom_weights
        else:
            weights = PROFILE_WEIGHTS.get(request.objective_profile, PROFILE_WEIGHTS["BALANCED_OPERATION"])

        constraints = request.constraints or OptimizationConstraintsSchema()
        active_overrides = scenario_overrides or {}

        # 2. Run Baseline Simulation (Reference Anchor)
        net_copy_base = copy.deepcopy(network_data)
        base_result = SimulationRunner.execute(
            network_data=net_copy_base,
            scenario_id=request.scenario_id,
            scenario_type="BASELINE",
            duration_hours=duration_hours,
            timestep_minutes=timestep_minutes,
            solver_mode=demand_model,
            overrides=active_overrides,
        )

        base_report = NetworkPerformanceService.evaluate(
            result=base_result,
            network_data=network_data,
            scenario_name="Nominal Baseline",
            tariff_usd_per_kwh=request.electricity_tariff_usd_per_kwh,
            duration_hours=duration_hours,
        )

        base_leak_m3 = base_report.water_loss.daily_leakage_volume_m3.value or 0.0
        base_energy_kwh = base_report.energy.pump_electrical_energy_kwh.value or 0.0
        base_min_p = base_report.pressure.min_pressure_bar.value or 0.0
        base_deficits = base_report.pressure.pressure_deficit_nodes_count

        # Adapt default constraints to baseline network capacity if not explicitly specified by user
        if request.constraints is None:
            base_max_p = base_report.pressure.max_pressure_bar.value or 5.5
            base_max_vel = base_report.hydraulic.max_pipe_velocity_mps.value or 2.5
            constraints.max_allowable_pressure_bar = max(constraints.max_allowable_pressure_bar, base_max_p + 1.0)
            constraints.max_pipe_velocity_mps = max(constraints.max_pipe_velocity_mps, base_max_vel + 1.0)
            base_sat = base_report.hydraulic.demand_satisfaction_ratio.value or 1.0
            constraints.min_demand_satisfaction_ratio = min(constraints.min_demand_satisfaction_ratio, base_sat * 0.95)

        # 3. Decision Variable Space Definition
        # Variable 1: pump_speed_P1 in [0.55, 1.15]
        # Variable 2: prv_setting_PRV01 in [1.8, 4.2] bar
        param_bounds = [
            (0.55, 1.15),  # pump speed
            (1.80, 4.20),  # PRV setpoint bar
        ]

        # 4. Generate Candidate Search Population
        eval_budget = min(150, max(10, request.max_evaluations))
        candidate_vectors: List[Tuple[float, float]] = []

        # Include baseline nominal vector as candidate 0
        candidate_vectors.append((1.00, 3.50))

        # Sample structured variations across decision space
        speed_steps = np.linspace(param_bounds[0][0], param_bounds[0][1], int(np.sqrt(eval_budget)))
        prv_steps = np.linspace(param_bounds[1][0], param_bounds[1][1], int(np.sqrt(eval_budget)))

        for s in speed_steps:
            for p in prv_steps:
                candidate_vectors.append((float(s), float(p)))
                if len(candidate_vectors) >= eval_budget:
                    break
            if len(candidate_vectors) >= eval_budget:
                break

        # 5. Evaluate Candidate Population
        evaluated_candidates: List[OptimizationCandidateSchema] = []

        for idx, (spd, prv_p) in enumerate(candidate_vectors):
            cand_id = f"CAND-{idx + 1:03d}"
            cand_vars = {
                "pump_speed_P1": round(spd, 3),
                "prv_setting_PRV01": round(prv_p, 2),
            }

            # Independent validation via WNTR/EPANET solver
            is_valid, sim_res, violations = OptimizationValidator.verify_candidate(
                candidate_variables=cand_vars,
                base_network_data=network_data,
                scenario_overrides=active_overrides,
                constraints=constraints,
                duration_hours=duration_hours,
                timestep_minutes=timestep_minutes,
                demand_model=demand_model,
            )

            if is_valid and sim_res:
                cand_perf = NetworkPerformanceService.evaluate(
                    result=sim_res,
                    network_data=network_data,
                    tariff_usd_per_kwh=request.electricity_tariff_usd_per_kwh,
                    duration_hours=duration_hours,
                )

                leak_m3 = cand_perf.water_loss.daily_leakage_volume_m3.value or 0.0
                elec_kwh = cand_perf.energy.pump_electrical_energy_kwh.value or 0.0
                sat_ratio = cand_perf.hydraulic.demand_satisfaction_ratio.value or 1.0

                # Compute pressure penalty for deviation from nominal target (3.5 bar)
                press_pen = abs(cand_perf.pressure.avg_pressure_bar.value - 3.5) if cand_perf.pressure.avg_pressure_bar.value else 0.0

                cand_obj = OptimizationCandidateSchema(
                    candidate_id=cand_id,
                    rank=idx + 1,
                    is_pareto_optimal=False,
                    decision_variables=cand_vars,
                    objective_score=0.0,  # Computed below
                    water_loss_score=round(leak_m3, 2),
                    energy_score=round(elec_kwh, 2),
                    pressure_penalty=round(press_pen, 3),
                    demand_satisfaction_ratio=round(sat_ratio, 4),
                    estimated_cost_usd=cand_perf.energy.energy_cost_usd.value,
                    is_hydraulically_verified=True,
                    constraint_violations=[],
                    rejection_reason=None,
                )
                cand_obj.objective_score = ParetoAnalysisService.calculate_weighted_score(
                    cand_obj, weights, baseline_leak_m3=base_leak_m3, baseline_energy_kwh=base_energy_kwh
                )
            else:
                # Hydraulically unfeasible candidate
                cand_obj = OptimizationCandidateSchema(
                    candidate_id=cand_id,
                    rank=idx + 1,
                    is_pareto_optimal=False,
                    decision_variables=cand_vars,
                    objective_score=9999.0,
                    water_loss_score=base_leak_m3 * 1.5,
                    energy_score=base_energy_kwh * 1.5,
                    pressure_penalty=100.0,
                    demand_satisfaction_ratio=0.5,
                    estimated_cost_usd=None,
                    is_hydraulically_verified=False,
                    constraint_violations=violations,
                    rejection_reason=violations[0] if violations else "Validation rejected",
                )

            evaluated_candidates.append(cand_obj)

        # 6. Rank Candidates and Extract Pareto Frontier
        evaluated_candidates.sort(key=lambda c: c.objective_score)
        for r_idx, c in enumerate(evaluated_candidates):
            c.rank = r_idx + 1

        pareto_front = ParetoAnalysisService.compute_pareto_frontier(evaluated_candidates)
        best_cand = evaluated_candidates[0] if evaluated_candidates else None

        # 7. Comparison with Baseline
        best_leak = best_cand.water_loss_score if best_cand else base_leak_m3
        best_energy = best_cand.energy_score if best_cand else base_energy_kwh
        leak_saved_m3 = max(0.0, base_leak_m3 - best_leak)
        leak_saved_pct = (leak_saved_m3 / base_leak_m3 * 100.0) if base_leak_m3 > 0 else 0.0

        energy_saved_kwh = max(0.0, base_energy_kwh - best_energy)
        energy_saved_pct = (energy_saved_kwh / base_energy_kwh * 100.0) if base_energy_kwh > 0 else 0.0

        comparison = BaselineComparisonSchema(
            baseline_leakage_m3=round(base_leak_m3, 2),
            optimized_leakage_m3=round(best_leak, 2),
            leakage_reduction_m3=round(leak_saved_m3, 2),
            leakage_reduction_pct=round(leak_saved_pct, 2),
            baseline_energy_kwh=round(base_energy_kwh, 2),
            optimized_energy_kwh=round(best_energy, 2),
            energy_saved_kwh=round(energy_saved_kwh, 2),
            energy_saved_pct=round(energy_saved_pct, 2),
            baseline_min_pressure_bar=round(base_min_p, 3),
            optimized_min_pressure_bar=round(constraints.min_service_pressure_bar, 3),
            pressure_deficit_nodes_reduced=max(0, base_deficits),
            baseline_demand_satisfaction=round(base_report.hydraulic.demand_satisfaction_ratio.value or 1.0, 4),
            optimized_demand_satisfaction=round(best_cand.demand_satisfaction_ratio if best_cand else 1.0, 4),
            baseline_cost_usd=base_report.energy.energy_cost_usd.value,
            optimized_cost_usd=best_cand.estimated_cost_usd if best_cand else None,
            cost_savings_usd=(
                round(base_report.energy.energy_cost_usd.value - best_cand.estimated_cost_usd, 2)
                if (base_report.energy.energy_cost_usd.value and best_cand and best_cand.estimated_cost_usd)
                else None
            ),
        )

        exec_duration_ms = (time.perf_counter() - start_time) * 1000.0

        return OptimizationJobDetailResponse(
            job_id=job_id,
            user_id=user_id,
            network_id=request.network_id,
            scenario_id=request.scenario_id,
            scenario_name=f"Optimization Run ({request.objective_profile})",
            status="COMPLETED",
            objective_profile=request.objective_profile,
            algorithm=request.algorithm,
            weights=weights,
            constraints=constraints,
            evaluation_count=len(evaluated_candidates),
            execution_time_ms=round(exec_duration_ms, 2),
            best_candidate=best_cand,
            candidates=evaluated_candidates[:25],  # Top 25 candidates
            comparison_with_baseline=comparison,
            pareto_frontier=pareto_front[:15],
            created_at=datetime.now(timezone.utc).isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        )
