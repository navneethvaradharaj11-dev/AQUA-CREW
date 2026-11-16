"""
AQUA CREW — Infrastructure Risk Prediction Service (Task 11 / 11.5)
Forecasts future pipeline vulnerability scores across 24-hour, 7-day, and 30-day horizons
with non-linear saturation clamping, expanding uncertainty intervals, key risk drivers,
mitigation urgency ratings, and explicit model versioning.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import math

from app.models.pipeline_segment import PipelineSegmentModel
from app.services.infrastructure_intelligence.vulnerability_scoring_service import VulnerabilityScoringService


class InfrastructurePredictionService:
    PREDICTION_MODEL_VERSION = "v1.2.0-hybrid-physics-geodesic"

    @classmethod
    def forecast_risk(
        cls,
        segment: PipelineSegmentModel,
        current_vulnerability: float,
        trend_info: Dict[str, Any],
        contributing_factors: Optional[Dict[str, Any]] = None,
        cluster_proximity_m: float = 9999.0,
    ) -> Dict[str, Any]:
        """
        Projects future vulnerability scores for 24h, 7d, and 30d horizons.
        Uses deterministic degradation velocity with expanding confidence intervals.
        """
        v0 = max(0.0, min(100.0, current_vulnerability))
        d24 = trend_info.get("trend_24h_delta", 0.0)
        d7 = trend_info.get("trend_7d_delta", 0.0)
        d30 = trend_info.get("trend_30d_delta", 0.0)

        # Strictly clamp projected scores to [0.0, 100.0]
        p24 = round(max(0.0, min(100.0, v0 + d24)), 1)
        p7 = round(max(0.0, min(100.0, v0 + d7)), 1)
        p30 = round(max(0.0, min(100.0, v0 + d30)), 1)

        # Confidence intervals with expanding uncertainty (24h < 7d < 30d)
        base_unc = 3.0
        ci_24h = {
            "lower_bound": round(max(0.0, p24 - (base_unc + 1.0)), 1),
            "upper_bound": round(min(100.0, p24 + (base_unc + 1.0)), 1),
        }
        ci_7d = {
            "lower_bound": round(max(0.0, p7 - (base_unc + 3.5)), 1),
            "upper_bound": round(min(100.0, p7 + (base_unc + 3.5)), 1),
        }
        ci_30d = {
            "lower_bound": round(max(0.0, p30 - (base_unc + 7.5)), 1),
            "upper_bound": round(min(100.0, p30 + (base_unc + 7.5)), 1),
        }

        # Determine projected risk levels using strict boundaries
        lvl_24h = VulnerabilityScoringService.get_vulnerability_level(p24)
        lvl_7d = VulnerabilityScoringService.get_vulnerability_level(p7)
        lvl_30d = VulnerabilityScoringService.get_vulnerability_level(p30)

        # Synthesize primary risk drivers from factors
        drivers = []
        if contributing_factors:
            for cat, data in contributing_factors.items():
                if isinstance(data, dict):
                    if data.get("score", 0.0) >= 60.0:
                        for r in data.get("reasons", []):
                            if r not in drivers:
                                drivers.append(r)
        if not drivers:
            drivers.append(f"Gradual operational hydraulic aging on {segment.material} conduit")

        # Mitigation urgency
        if p24 >= 80.0 or p7 >= 85.0 or trend_info.get("rapid_degradation"):
            urgency = "IMMEDIATE"
        elif p7 >= 60.0 or p30 >= 70.0:
            urgency = "SHORT_TERM"
        elif p30 >= 45.0:
            urgency = "PLANNED"
        else:
            urgency = "ROUTINE"

        return {
            "pipeline_segment_id": segment.id,
            "current_vulnerability_score": v0,
            "projected_risk_24h": p24,
            "projected_level_24h": lvl_24h,
            "confidence_interval_24h": ci_24h,
            "projected_risk_7d": p7,
            "projected_level_7d": lvl_7d,
            "confidence_interval_7d": ci_7d,
            "projected_risk_30d": p30,
            "projected_level_30d": lvl_30d,
            "confidence_interval_30d": ci_30d,
            "primary_risk_drivers": drivers[:4],
            "mitigation_urgency": urgency,
            "cluster_proximity_m": cluster_proximity_m,
            "model_version": cls.PREDICTION_MODEL_VERSION,
            "is_simulated": True,
            "source": "VIRTUAL_SIMULATION_ENGINE",
        }
