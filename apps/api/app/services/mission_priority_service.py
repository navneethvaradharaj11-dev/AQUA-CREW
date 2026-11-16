"""
AQUA CREW — Mission Priority Engine
Evaluates AI leak detection telemetry, pressure transients, pipeline criticality,
and localization uncertainty to compute explainable dispatch priority scores (0–100).
"""
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone

from app.models.ai_detection import AiDetectionModel
from app.schemas.dispatch import MissionPriorityAssessment


class MissionPriorityService:
    # Priority Thresholds
    THRESHOLDS = {
        "CRITICAL": 90.0,
        "HIGH": 70.0,
        "MEDIUM": 40.0,
        "LOW": 0.0,
    }

    @classmethod
    def calculate_priority(
        cls,
        detection: AiDetectionModel,
        pipe_meta: Optional[Dict[str, Any]] = None,
    ) -> MissionPriorityAssessment:
        factors: Dict[str, float] = {}
        total_score = 0.0

        # 1. Risk Level Scoring (Max 35 pts)
        risk = (detection.risk_level or "MODERATE").upper()
        if risk == "CRITICAL":
            factors["risk_severity"] = 35.0
        elif risk == "HIGH":
            factors["risk_severity"] = 25.0
        elif risk == "MODERATE":
            factors["risk_severity"] = 15.0
        elif risk == "LOW":
            factors["risk_severity"] = 5.0
        else:
            factors["risk_severity"] = 0.0
        total_score += factors["risk_severity"]

        # 2. Leak Classification Likelihood (Max 25 pts)
        classification = (detection.classification or "MEDIUM_LEAK_PROBABILITY").upper()
        if classification == "HIGH_LEAK_PROBABILITY":
            factors["classification_likelihood"] = 25.0
        elif classification == "MEDIUM_LEAK_PROBABILITY":
            factors["classification_likelihood"] = 18.0
        elif classification == "LOW_LEAK_PROBABILITY":
            factors["classification_likelihood"] = 8.0
        else:
            factors["classification_likelihood"] = 0.0
        total_score += factors["classification_likelihood"]

        # 3. Estimated Water Loss (Max 20 pts)
        loss = detection.estimated_loss_lph or 0.0
        if loss >= 2000.0:
            factors["water_loss_volume"] = 20.0
        elif loss >= 1000.0:
            factors["water_loss_volume"] = 15.0
        elif loss >= 500.0:
            factors["water_loss_volume"] = 10.0
        elif loss > 50.0:
            factors["water_loss_volume"] = 5.0
        else:
            factors["water_loss_volume"] = 0.0
        total_score += factors["water_loss_volume"]

        # 4. Pipeline Infrastructure Criticality (Max 12 pts)
        pipe_category = (pipe_meta.get("category") if pipe_meta else "secondary") or "secondary"
        if pipe_category.lower() == "primary":
            factors["infrastructure_criticality"] = 12.0
        elif pipe_category.lower() == "secondary":
            factors["infrastructure_criticality"] = 8.0
        else:
            factors["infrastructure_criticality"] = 4.0
        total_score += factors["infrastructure_criticality"]

        # 5. Pressure Transient Drop (Max 8 pts)
        pressure_dev = -1.2  # default nominal delta
        if detection.contributing_features:
            try:
                import json
                feats = json.loads(detection.contributing_features)
                if "pressure_deviation" in feats:
                    pressure_dev = -float(feats["pressure_deviation"])
            except Exception:
                pass

        if pressure_dev <= -1.0:
            factors["pressure_drop_severity"] = 8.0
        elif pressure_dev <= -0.5:
            factors["pressure_drop_severity"] = 5.0
        else:
            factors["pressure_drop_severity"] = 2.0
        total_score += factors["pressure_drop_severity"]

        # 6. Localization Uncertainty Evaluation
        uncertainty = detection.localization_uncertainty_m
        uncertainty_warning: Optional[str] = None

        if uncertainty is not None and uncertainty > 30.0:
            uncertainty_warning = (
                f"Elevated spatial uncertainty (±{uncertainty:.1f}m). "
                "Recommend wide acoustic search pattern along segment."
            )
        elif uncertainty is not None and uncertainty <= 15.0 and (detection.confidence or 0.0) >= 0.85:
            # High precision boost (+5 pts up to max 100)
            factors["localization_precision_bonus"] = 5.0
            total_score += 5.0

        # Clamp score to [0, 100]
        final_score = min(100.0, max(0.0, round(total_score, 1)))

        # Determine Category
        if final_score >= cls.THRESHOLDS["CRITICAL"]:
            category = "CRITICAL"
            recommended_response = "Immediate autonomous rover dispatch required. Alert sector operations supervisor."
        elif final_score >= cls.THRESHOLDS["HIGH"]:
            category = "HIGH"
            recommended_response = "High-priority rover inspection recommended within 2 hours."
        elif final_score >= cls.THRESHOLDS["MEDIUM"]:
            category = "MEDIUM"
            recommended_response = "Scheduled inspection patrol during current operational shift."
        else:
            category = "LOW"
            recommended_response = "Routine stationary sensor monitoring. Defer rover mobilization."

        # Generate Explainable Narrative
        explanation = (
            f"Priority score {final_score}/100 ({category}) derived from: "
            f"Risk Level {risk} ({factors.get('risk_severity', 0)} pts), "
            f"Likelihood {classification} ({factors.get('classification_likelihood', 0)} pts), "
            f"Est. Loss {loss:.0f} L/h ({factors.get('water_loss_volume', 0)} pts), and "
            f"{pipe_category.capitalize()} Pipeline Tier ({factors.get('infrastructure_criticality', 0)} pts)."
        )

        return MissionPriorityAssessment(
            priority_score=final_score,
            priority_category=category,
            contributing_factors=factors,
            explanation=explanation,
            recommended_response=recommended_response,
            uncertainty_warning=uncertainty_warning,
            timestamp=datetime.now(timezone.utc),
            source_detection_id=detection.id,
        )

