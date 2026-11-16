"""
Pareto Frontier & Multi-Objective Trade-Off Analysis Service (Task 14)
Performs non-dominated sorting and trade-off analysis across competing objectives
(water loss vs pump energy vs pressure quality vs demand satisfaction).
"""
from typing import Dict, Any, List, Optional, Tuple

from app.schemas.optimization import (
    OptimizationCandidateSchema,
    ObjectiveWeightsSchema,
)


PROFILE_WEIGHTS: Dict[str, ObjectiveWeightsSchema] = {
    "BALANCED_OPERATION": ObjectiveWeightsSchema(
        water_loss_weight=0.25,
        energy_weight=0.25,
        pressure_quality_weight=0.25,
        demand_satisfaction_weight=0.25,
        cost_weight=0.0,
    ),
    "ENERGY_EFFICIENCY": ObjectiveWeightsSchema(
        water_loss_weight=0.15,
        energy_weight=0.50,
        pressure_quality_weight=0.20,
        demand_satisfaction_weight=0.15,
        cost_weight=0.0,
    ),
    "LEAKAGE_REDUCTION": ObjectiveWeightsSchema(
        water_loss_weight=0.50,
        energy_weight=0.15,
        pressure_quality_weight=0.20,
        demand_satisfaction_weight=0.15,
        cost_weight=0.0,
    ),
    "PRESSURE_STABILITY": ObjectiveWeightsSchema(
        water_loss_weight=0.15,
        energy_weight=0.15,
        pressure_quality_weight=0.50,
        demand_satisfaction_weight=0.20,
        cost_weight=0.0,
    ),
}


class ParetoAnalysisService:
    """
    Computes non-dominated Pareto frontiers and evaluates multi-objective trade-offs.
    """

    @classmethod
    def dominates(cls, a: OptimizationCandidateSchema, b: OptimizationCandidateSchema) -> bool:
        """
        Returns True if candidate 'a' dominates candidate 'b'.
        For minimization objectives (water_loss, energy, pressure_penalty): a <= b
        For maximization objective (demand_satisfaction): a >= b
        Strictly better in at least one objective.
        """
        # Exclude candidates that failed hydraulic verification
        if not a.is_hydraulically_verified and b.is_hydraulically_verified:
            return False
        if a.is_hydraulically_verified and not b.is_hydraulically_verified:
            return True

        no_worse = (
            a.water_loss_score <= b.water_loss_score and
            a.energy_score <= b.energy_score and
            a.pressure_penalty <= b.pressure_penalty and
            a.demand_satisfaction_ratio >= b.demand_satisfaction_ratio
        )
        strictly_better = (
            a.water_loss_score < b.water_loss_score or
            a.energy_score < b.energy_score or
            a.pressure_penalty < b.pressure_penalty or
            a.demand_satisfaction_ratio > b.demand_satisfaction_ratio
        )
        return no_worse and strictly_better

    @classmethod
    def compute_pareto_frontier(
        cls,
        candidates: List[OptimizationCandidateSchema],
    ) -> List[OptimizationCandidateSchema]:
        """
        Extracts non-dominated (Pareto-optimal) candidate configurations.
        """
        verified_candidates = [c for c in candidates if c.is_hydraulically_verified]
        if not verified_candidates:
            return []

        frontier: List[OptimizationCandidateSchema] = []
        for c in verified_candidates:
            is_dominated = False
            for other in verified_candidates:
                if other.candidate_id != c.candidate_id and cls.dominates(other, c):
                    is_dominated = True
                    break
            if not is_dominated:
                c.is_pareto_optimal = True
                frontier.append(c)
            else:
                c.is_pareto_optimal = False

        # Sort frontier by energy ascending
        frontier.sort(key=lambda x: x.energy_score)
        return frontier

    @classmethod
    def calculate_weighted_score(
        cls,
        candidate: OptimizationCandidateSchema,
        weights: ObjectiveWeightsSchema,
        baseline_leak_m3: float = 100.0,
        baseline_energy_kwh: float = 1000.0,
    ) -> float:
        """
        Computes normalized weighted objective score (lower is better).
        Normalizes leakage and energy by baseline reference values.
        """
        norm_leak = candidate.water_loss_score / max(1.0, baseline_leak_m3)
        norm_energy = candidate.energy_score / max(1.0, baseline_energy_kwh)
        norm_pressure = candidate.pressure_penalty / 10.0
        # Demand penalty: (1.0 - satisfaction) * 10.0
        norm_demand = max(0.0, 1.0 - candidate.demand_satisfaction_ratio) * 10.0

        score = (
            weights.water_loss_weight * norm_leak +
            weights.energy_weight * norm_energy +
            weights.pressure_quality_weight * norm_pressure +
            weights.demand_satisfaction_weight * norm_demand
        )

        # Severe penalty for constraint violations
        if len(candidate.constraint_violations) > 0 or not candidate.is_hydraulically_verified:
            score += 100.0 * max(1, len(candidate.constraint_violations))

        return round(float(score), 4)

    @classmethod
    def explain_tradeoff(
        cls,
        candidate_a: OptimizationCandidateSchema,
        candidate_b: OptimizationCandidateSchema,
    ) -> str:
        """
        Generates engineering explanation of the trade-off between two candidate configurations.
        """
        delta_leak = candidate_a.water_loss_score - candidate_b.water_loss_score
        delta_energy = candidate_a.energy_score - candidate_b.energy_score

        if delta_energy < 0 and delta_leak > 0:
            return (
                f"Candidate {candidate_a.candidate_id} consumes {abs(delta_energy):.1f} kWh less energy "
                f"than Candidate {candidate_b.candidate_id}, but allows {abs(delta_leak):.1f} m³ more water loss "
                f"due to reduced booster pump throttling."
            )
        elif delta_energy > 0 and delta_leak < 0:
            return (
                f"Candidate {candidate_a.candidate_id} reduces water loss by {abs(delta_leak):.1f} m³ "
                f"relative to Candidate {candidate_b.candidate_id}, but requires {abs(delta_energy):.1f} kWh "
                f"more pumping energy to sustain downstream service pressures."
            )
        else:
            return (
                f"Candidate {candidate_a.candidate_id} vs {candidate_b.candidate_id}: "
                f"Delta energy = {delta_energy:+.1f} kWh, Delta leakage = {delta_leak:+.1f} m³."
            )
