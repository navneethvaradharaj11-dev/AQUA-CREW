"""
AQUA CREW — Repair Prioritization Engine (Task 16)
Calculates objective, evidence-based repair priority scores, SLAs, and escalation triggers.
Strictly separates repair priority from inspection urgency.
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.pipeline_segment import PipelineSegmentModel
from app.models.infrastructure_intelligence import SpatialIncidentClusterModel
from app.repositories.pipeline_repository import PipelineRepository
from app.schemas.repair_management import (
    DamageAssessmentSchema,
    RepairPrioritySchema,
)


class RepairPrioritizationEngine:
    PRIORITY_WEIGHTS = {
        "damage_severity": 0.30,
        "water_loss_volume": 0.25,
        "conduit_criticality": 0.20,
        "structural_vulnerability": 0.15,
        "spatial_hotspot_risk": 0.10,
    }

    @classmethod
    def calculate_priority(
        cls,
        db: Session,
        assessment: DamageAssessmentSchema,
    ) -> RepairPrioritySchema:
        """
        Calculates multi-factor repair priority score (0-100), response SLA, and escalations.
        """
        factors: Dict[str, float] = {}

        # 1. Damage Severity (30%)
        sev_map = {
            "CRITICAL": 100.0,
            "HIGH": 75.0,
            "MODERATE": 50.0,
            "LOW": 25.0,
            "UNDETERMINED": 20.0,
        }
        factors["damage_severity"] = sev_map.get(assessment.severity, 30.0)

        # 2. Water Loss Magnitude (25%)
        # 500 L/h or greater yields 100 score
        loss_score = min(100.0, (assessment.estimated_water_loss_lph / 500.0) * 100.0)
        factors["water_loss_volume"] = round(loss_score, 1)

        # 3. Conduit Criticality / Diameter (20%)
        # Arterial 600mm main yields 100 score
        crit_score = min(100.0, (assessment.pipe_diameter_mm / 600.0) * 100.0)
        factors["conduit_criticality"] = round(crit_score, 1)

        # 4. Structural Vulnerability (15%)
        factors["structural_vulnerability"] = round(assessment.structural_vulnerability_score, 1)

        # 5. Spatial Hotspot Risk (10%)
        clusters = db.query(SpatialIncidentClusterModel).all()
        in_hotspot = len(clusters) > 0
        factors["spatial_hotspot_risk"] = 85.0 if in_hotspot else 20.0

        # Weighted Composite Score
        composite = sum(factors[k] * cls.PRIORITY_WEIGHTS[k] for k in cls.PRIORITY_WEIGHTS)
        composite = round(max(0.0, min(100.0, composite)), 1)

        # Priority Category & Recommended SLA
        escalations: List[str] = []
        if composite >= 75.0 or assessment.severity == "CRITICAL" or assessment.estimated_water_loss_lph >= 5000.0:
            category = "CRITICAL"
            sla_hours = 24
            escalations.extend([
                "MANDATORY_BOIL_WATER_ADVISORY_CHECK",
                "EMERGENCY_ROADWAY_DETOUR_PERMIT",
                "PUBLIC_UTILITIES_COMMISSION_NOTIFICATION",
            ])
        elif composite >= 55.0 or assessment.severity == "HIGH":
            category = "HIGH"
            sla_hours = 72
            escalations.append("MUNICIPAL_TRAFFIC_DIVERT_PERMIT")
        elif composite >= 35.0:
            category = "MEDIUM"
            sla_hours = 336  # 14 days
        else:
            category = "LOW"
            sla_hours = 720  # 30 days

        return RepairPrioritySchema(
            pipeline_segment_id=assessment.pipeline_segment_id,
            repair_priority_score=composite,
            priority_category=category,
            contributing_factors=factors,
            uncertainty_margin=5.0 if assessment.evidence_completeness_pct >= 80.0 else 12.0,
            recommended_response_time_hours=sla_hours,
            escalation_requirements=escalations,
            calculated_at=datetime.now(timezone.utc).isoformat(),
        )
