"""
Operational Impact Assessment Service (Task 12 - Phase 9)
Provides multidimensional impact estimations covering water loss, pipeline consequence,
service disruption, inspection traversal metrics, and maintenance urgency.
Strict Governance Rule: Financial savings or currency metrics are NOT fabricated;
cost display is explicitly marked "NOT AVAILABLE".
Distinguishes simulated hydraulic loss from measured physical meter loss.
"""
from typing import Dict, Any, Optional
import uuid
from datetime import datetime, timezone

from app.services.operational_intelligence.operational_hydraulic_impact_service import OperationalHydraulicImpactService


class OperationalImpactService:
    @classmethod
    def assess_recommendation_impact(
        cls,
        recommendation_id: str,
        pipeline_segment_id: str,
        diameter_mm: int = 300,
        risk_severity: str = "HIGH",
        nominal_pressure_bar: float = 4.2,
        segment_length_m: float = 500.0,
    ) -> Dict[str, Any]:
        """
        Calculates impact metrics for an operational recommendation.
        """
        # Determine equivalent orifice diameter based on risk severity
        if risk_severity == "CRITICAL":
            orifice_mm = 25.0
            urgency = "IMMEDIATE"
        elif risk_severity == "HIGH":
            orifice_mm = 15.0
            urgency = "HIGH"
        elif risk_severity == "MODERATE":
            orifice_mm = 8.0
            urgency = "MEDIUM"
        else:
            orifice_mm = 3.0
            urgency = "ROUTINE"

        hydraulic_eval = OperationalHydraulicImpactService.evaluate_leak_impact(
            db=None,
            pipeline_segment_id=pipeline_segment_id,
            leak_orifice_diameter_mm=orifice_mm,
            nominal_pressure_bar=nominal_pressure_bar,
        )

        est_inspection_dist = round(segment_length_m, 1)
        est_inspection_dur = round(est_inspection_dist / 0.5 / 60.0, 1)  # 0.5 m/s crawl speed in minutes
        est_energy = round(est_inspection_dist * 0.008, 1)              # 0.8% per 100m

        return {
            "id": f"IMP-{uuid.uuid4().hex[:8]}",
            "recommendation_id": recommendation_id,
            "pipeline_segment_id": pipeline_segment_id,
            "scenario_id": hydraulic_eval["scenario_id"],
            "estimated_water_loss_m3_day": hydraulic_eval["estimated_water_loss_m3_day"],
            "is_water_loss_measured": False,
            "service_disruption_risk": hydraulic_eval["service_disruption_risk"],
            "affected_nodes_count": hydraulic_eval["affected_nodes_count"],
            "affected_population_estimate": hydraulic_eval["affected_population_estimate"],
            "hydraulic_headloss_delta_m": hydraulic_eval["hydraulic_headloss_delta_m"],
            "min_pressure_drop_bar": hydraulic_eval["min_pressure_drop_bar"],
            "estimated_inspection_distance_m": est_inspection_dist,
            "estimated_mission_energy_pct": est_energy,
            "estimated_inspection_duration_min": est_inspection_dur,
            "estimated_maintenance_urgency": urgency,
            "cost_impact_display": "NOT AVAILABLE",
            "data_quality_rating": "ESTIMATED_SIMULATED",
            "assumptions": {
                "calculation_method": "Torricelli Aperture Discharge & Equivalent Zone Demand Differential",
                "units": {
                    "water_loss": "m3/day",
                    "inspection_distance": "m",
                    "inspection_duration": "minutes",
                    "mission_energy": "% battery reserve",
                    "pressure_drop": "bar",
                },
                "uncertainty_basis": "Empirical orifice discharge uncertainty +/- 15%",
                "economic_valuation_status": "Omitted per governance rule (no fabricated currency)",
            },
            "uncertainty_margin_pct": 15.0,
            "assessed_at": datetime.now(timezone.utc).isoformat(),
            "is_simulated": True,
            "source": "VIRTUAL_SIMULATION_ENGINE",
        }

