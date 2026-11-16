"""
AQUA CREW — Intelligent Inspection Prioritization Service (Task 11)
Ranks municipal pipeline inspection targets based on vulnerability, deterioration velocity,
cluster proximity, and asset consequence, coordinating rover dispatch workflows.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import uuid
from sqlalchemy.orm import Session

from app.models.pipeline_segment import PipelineSegmentModel
from app.models.infrastructure_intelligence import InspectionPriorityRecordModel
from app.models.ai_detection import AiDetectionModel
from app.models.rover import RoverModel
from app.models.mission_recommendation import MissionRecommendationModel
from app.services.mission_planning_service import MissionPlanningService
from app.core.exceptions import AquaCrewException


class InspectionPriorityService:
    @classmethod
    def calculate_priority_score(
        cls,
        vulnerability_score: float,
        deterioration_rate_per_day: float,
        cluster_distance_m: float,
        segment: PipelineSegmentModel,
    ) -> Tuple[float, str, List[str], str]:
        """
        Calculates composite priority score (0-100) and returns (score, level, reasons, suggested_action).
        """
        reasons = []

        # 1. Vulnerability contribution (40%)
        vuln_contrib = 0.40 * vulnerability_score
        if vulnerability_score >= 80.0:
            reasons.append(f"Critical vulnerability index ({vulnerability_score:.1f}/100)")
        elif vulnerability_score >= 60.0:
            reasons.append(f"Elevated vulnerability index ({vulnerability_score:.1f}/100)")

        # 2. Deterioration velocity contribution (25%)
        if deterioration_rate_per_day >= 0.25:
            det_score = 92.0
            reasons.append(f"Rapid degradation rate (+{deterioration_rate_per_day:.2f} pts/day)")
        elif deterioration_rate_per_day >= 0.12:
            det_score = 65.0
            reasons.append(f"Progressive structural wear (+{deterioration_rate_per_day:.2f} pts/day)")
        else:
            det_score = 30.0
        det_contrib = 0.25 * det_score

        # 3. Cluster proximity contribution (20%)
        if cluster_distance_m <= 150.0:
            prox_score = 95.0
            reasons.append(f"Located directly within active incident hotspot ({cluster_distance_m:.0f}m)")
        elif cluster_distance_m <= 400.0:
            prox_score = 72.0
            reasons.append(f"Hotspot proximity zone ({cluster_distance_m:.0f}m)")
        elif cluster_distance_m <= 800.0:
            prox_score = 45.0
        else:
            prox_score = 20.0
        prox_contrib = 0.20 * prox_score

        # 4. Asset consequence / criticality (15%)
        cat = (segment.category or "").lower()
        dia = segment.diameter_mm or 300
        if "primary" in cat or "trunk" in cat or dia >= 600:
            crit_score = 90.0
            reasons.append(f"Arterial trunk conduit (dia: {dia}mm) carries high systemic failure consequence")
        elif "secondary" in cat or dia >= 350:
            crit_score = 60.0
        else:
            crit_score = 40.0
        crit_contrib = 0.15 * crit_score

        total_score = round(max(0.0, min(100.0, vuln_contrib + det_contrib + prox_contrib + crit_contrib)), 1)

        # Categorize level
        if total_score >= 80.0:
            priority_level = "CRITICAL_IMMEDIATE"
            suggested_action = "Immediate acoustic crawling patrol and acoustic leak pinpointing"
        elif total_score >= 60.0:
            priority_level = "HIGH_PRIORITY"
            suggested_action = "Scheduled autonomous rover sonar & visual inspection within 48h"
        elif total_score >= 40.0:
            priority_level = "ROUTINE_SCHEDULED"
            suggested_action = "Routine preventive rover patrol and pressure sensor validation"
        else:
            priority_level = "MONITORING_ONLY"
            suggested_action = "Continuous virtual telemetry monitoring; no physical dispatch required"

        if not reasons:
            reasons.append("Standard periodic inspection recommendation based on service age")

        return total_score, priority_level, reasons, suggested_action

    @classmethod
    def sync_inspection_queue(
        cls,
        db: Session,
        segments: List[PipelineSegmentModel],
        vulnerability_profiles: Dict[str, Dict[str, Any]],
        trend_records: Dict[str, Dict[str, Any]],
        cluster_distances: Dict[str, float],
    ) -> List[InspectionPriorityRecordModel]:
        """
        Synchronizes the inspection queue for all segments, updating existing pending records
        or creating new ones when priority is significant.
        """
        existing_records = {
            r.pipeline_segment_id: r
            for r in db.query(InspectionPriorityRecordModel).all()
        }

        updated_or_created = []

        for seg in segments:
            profile = vulnerability_profiles.get(seg.id, {})
            v_score = profile.get("vulnerability_score", 30.0)
            trend = trend_records.get(seg.id, {})
            det_rate = trend.get("deterioration_rate_per_day", 0.05)
            dist_c = cluster_distances.get(seg.id, 9999.0)

            # Determine coordinates midpoint
            mid_lat = profile.get("midpoint_lat") or 40.7128
            mid_lng = profile.get("midpoint_lng") or -74.0060

            p_score, p_level, reasons, suggested_action = cls.calculate_priority_score(
                v_score, det_rate, dist_c, seg
            )

            existing = existing_records.get(seg.id)
            if existing:
                # Update priority score and reasons if still pending or acknowledged
                if existing.status in ["PENDING", "ACKNOWLEDGED"]:
                    existing.priority_score = p_score
                    existing.priority_level = p_level
                    existing.reasons = json.dumps(reasons)
                    existing.suggested_action = suggested_action
                    existing.target_latitude = mid_lat
                    existing.target_longitude = mid_lng
                    existing.updated_at = datetime.now(timezone.utc)
                updated_or_created.append(existing)
            else:
                # Create record
                rec_id = f"INSP-{uuid.uuid4().hex[:6].upper()}"
                rec = InspectionPriorityRecordModel(
                    id=rec_id,
                    pipeline_segment_id=seg.id,
                    segment_name=seg.name,
                    priority_score=p_score,
                    priority_level=p_level,
                    status="PENDING",
                    target_latitude=mid_lat,
                    target_longitude=mid_lng,
                    reasons=json.dumps(reasons),
                    suggested_action=suggested_action,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    is_simulated=True,
                    source="VIRTUAL_SIMULATION_ENGINE",
                )
                db.add(rec)
                updated_or_created.append(rec)

        db.commit()
        return updated_or_created

    @classmethod
    def acknowledge_priority(
        cls,
        db: Session,
        priority_id: str,
        operator_name: str = "OPERATOR_CHIEF",
        notes: Optional[str] = None,
    ) -> InspectionPriorityRecordModel:
        """
        Marks an inspection queue record as acknowledged by the operator.
        """
        record = db.query(InspectionPriorityRecordModel).filter(
            InspectionPriorityRecordModel.id == priority_id
        ).first()

        if not record:
            raise AquaCrewException(
                status_code=404,
                code="PRIORITY_RECORD_NOT_FOUND",
                message=f"Inspection priority record '{priority_id}' not found.",
            )

        record.status = "ACKNOWLEDGED"
        record.reviewed_by = operator_name
        record.reviewed_at = datetime.now(timezone.utc)
        if notes:
            record.operator_notes = notes
        record.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def dismiss_priority(
        cls,
        db: Session,
        priority_id: str,
        operator_name: str = "OPERATOR_CHIEF",
        reason: Optional[str] = None,
    ) -> InspectionPriorityRecordModel:
        """
        Dismisses an inspection priority target with justification.
        """
        record = db.query(InspectionPriorityRecordModel).filter(
            InspectionPriorityRecordModel.id == priority_id
        ).first()

        if not record:
            raise AquaCrewException(
                status_code=404,
                code="PRIORITY_RECORD_NOT_FOUND",
                message=f"Inspection priority record '{priority_id}' not found.",
            )

        record.status = "DISMISSED"
        record.reviewed_by = operator_name
        record.reviewed_at = datetime.now(timezone.utc)
        record.dismissal_reason = reason or "Operator dismissed: verified false positive or scheduled in overhaul."
        record.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def request_inspection(
        cls,
        db: Session,
        priority_id: str,
        operator_name: str = "OPERATOR_CHIEF",
        preferred_rover_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches an inspection request:
        1. Ensures an AI detection exists for the pipeline segment (or synthesizes an inspection trigger).
        2. Calls MissionPlanningService.plan_mission_for_detection(...) to create a formal rover recommendation.
        3. Updates the inspection record to DISPATCHED and attaches rover and recommendation IDs.
        4. Preserves human operator approval gate (operator_approval_required: true).
        """
        record = db.query(InspectionPriorityRecordModel).filter(
            InspectionPriorityRecordModel.id == priority_id
        ).first()

        if not record:
            raise AquaCrewException(
                status_code=404,
                code="PRIORITY_RECORD_NOT_FOUND",
                message=f"Inspection priority record '{priority_id}' not found.",
            )

        # Duplicate protection check
        if record.status == "DISPATCHED" and record.mission_recommendation_id:
            existing_rec = db.query(MissionRecommendationModel).filter(
                MissionRecommendationModel.id == record.mission_recommendation_id,
                MissionRecommendationModel.status.in_(["PENDING_APPROVAL", "APPROVED"])
            ).first()
            if existing_rec:
                raise AquaCrewException(
                    status_code=409,
                    code="DUPLICATE_DISPATCH_REJECTED",
                    message=f"Active inspection mission recommendation already exists ({existing_rec.id}). Redundant dispatch rejected.",
                )

        # Check preferred rover battery and availability if explicitly requested
        if preferred_rover_id:
            rover = db.query(RoverModel).filter(RoverModel.id == preferred_rover_id).first()
            if not rover:
                raise AquaCrewException(
                    status_code=404,
                    code="ROVER_NOT_FOUND",
                    message=f"Preferred rover '{preferred_rover_id}' not found in fleet database."
                )
            if rover.battery_percentage is not None and rover.battery_percentage < 20.0:
                raise AquaCrewException(
                    status_code=400,
                    code="ROVER_BATTERY_INSUFFICIENT",
                    message=f"Rover '{rover.name}' ({rover.id}) has insufficient battery reserve ({rover.battery_percentage:.1f}% < 20.0%). Select an alternate rover.",
                )

        # 1. Look for existing detection or create an inspection diagnostic trigger
        detection = db.query(AiDetectionModel).filter(
            AiDetectionModel.pipeline_segment_id == record.pipeline_segment_id
        ).order_by(AiDetectionModel.created_at.desc()).first()

        if not detection:
            det_id = f"DET-INSP-{uuid.uuid4().hex[:6].upper()}"
            detection = AiDetectionModel(
                id=det_id,
                pipeline_segment_id=record.pipeline_segment_id,
                anomaly_score=round(record.priority_score / 100.0, 2),
                classification="MEDIUM_LEAK_PROBABILITY" if record.priority_score < 75.0 else "HIGH_LEAK_PROBABILITY",
                confidence=0.88,
                risk_level="HIGH" if record.priority_score >= 60.0 else "MODERATE",
                estimated_loss_lph=180.0,
                estimated_latitude=record.target_latitude,
                estimated_longitude=record.target_longitude,
                localization_uncertainty_m=25.0,
                localization_quality="MODERATE",
                status="PENDING_REVIEW",
                risk_explanation=f"Autonomous inspection requested from Infrastructure Intelligence Queue ({record.priority_level}).",
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            )
            db.add(detection)
            db.commit()
            db.refresh(detection)

        # 2. Plan rover mission recommendation
        priority_category = "CRITICAL" if record.priority_score >= 80.0 else "HIGH" if record.priority_score >= 60.0 else "MEDIUM"
        recommendation = MissionPlanningService.plan_mission_for_detection(
            db=db,
            detection_id=detection.id,
            preferred_rover_id=preferred_rover_id,
            priority_override=priority_category,
        )

        # 3. Update priority record
        record.status = "DISPATCHED"
        record.assigned_rover_id = recommendation.recommended_rover_id
        record.mission_recommendation_id = recommendation.id
        record.reviewed_by = operator_name
        record.reviewed_at = datetime.now(timezone.utc)
        if notes:
            record.operator_notes = notes
        record.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(record)

        return {
            "status": "DISPATCHED",
            "priority_record_id": record.id,
            "pipeline_segment_id": record.pipeline_segment_id,
            "mission_recommendation_id": recommendation.id,
            "assigned_rover_id": recommendation.recommended_rover_id,
            "assigned_rover_name": recommendation.recommended_rover_name,
            "planned_route_distance_m": recommendation.route_distance_m,
            "operator_approval_required": True,
            "recommendation_status": recommendation.status,
            "message": f"Inspection mission recommendation generated for rover {recommendation.recommended_rover_name}. Operator approval required to launch.",
        }

