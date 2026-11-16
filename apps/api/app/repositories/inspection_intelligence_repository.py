"""
AQUA CREW — Inspection Intelligence Repository (Task 15)
Manages persistence for recommendations, plans, executions, reports, and audit events.
Enforces atomic status transitions and SHA-256 cryptographic payload integrity.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import hashlib
import uuid
from sqlalchemy.orm import Session

from app.models.inspection_intelligence import (
    InspectionRecommendationModel,
    InspectionPlanModel,
    InspectionExecutionModel,
    InspectionReportModel,
    InspectionEventModel,
)
from app.schemas.inspection_intelligence import (
    InspectionRecommendationSchema,
    InspectionPlanSchema,
    InspectionExecutionProgressSchema,
    InspectionReportSchema,
    SupportingEvidenceItem,
)
from app.core.exceptions import AquaCrewException


class InspectionIntelligenceRepository:
    @staticmethod
    def _compute_hash(payload: Any) -> str:
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    # -------------------------------------------------------------------------
    # Recommendations
    # -------------------------------------------------------------------------
    @classmethod
    def save_recommendation(
        cls,
        db: Session,
        rec: InspectionRecommendationSchema,
    ) -> InspectionRecommendationModel:
        model = db.query(InspectionRecommendationModel).filter(InspectionRecommendationModel.id == rec.id).first()
        if not model:
            model = InspectionRecommendationModel(id=rec.id)
            db.add(model)

        model.pipeline_segment_id = rec.pipeline_segment_id
        model.segment_name = rec.segment_name
        model.priority_score = rec.priority_score
        model.priority_category = rec.priority_category
        model.urgency_factors_json = json.dumps(rec.urgency_factors)
        model.supporting_evidence_json = json.dumps([e.model_dump() for e in rec.supporting_evidence])
        model.primary_classification = rec.primary_classification
        model.confidence = rec.confidence
        model.uncertainty_radius_m = rec.uncertainty_radius_m
        model.recommended_method = rec.recommended_method
        model.estimated_duration_minutes = rec.estimated_duration_minutes
        model.required_rover_capabilities_json = json.dumps(rec.required_rover_capabilities)
        model.recommended_action = rec.recommended_action
        model.human_approval_status = rec.human_approval_status
        model.rejection_reason = rec.rejection_reason
        model.approved_by = rec.approved_by
        model.is_simulated = rec.is_simulated

        db.commit()
        db.refresh(model)
        return model

    @classmethod
    def get_recommendation(cls, db: Session, rec_id: str) -> Optional[InspectionRecommendationModel]:
        return db.query(InspectionRecommendationModel).filter(InspectionRecommendationModel.id == rec_id).first()

    @classmethod
    def list_recommendations(
        cls,
        db: Session,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50,
    ) -> List[InspectionRecommendationModel]:
        query = db.query(InspectionRecommendationModel)
        if status:
            query = query.filter(InspectionRecommendationModel.human_approval_status == status.upper())
        if priority:
            query = query.filter(InspectionRecommendationModel.priority_category == priority.upper())
        return query.order_by(InspectionRecommendationModel.priority_score.desc()).limit(limit).all()

    # -------------------------------------------------------------------------
    # Inspection Plans
    # -------------------------------------------------------------------------
    @classmethod
    def save_plan(cls, db: Session, plan: InspectionPlanSchema) -> InspectionPlanModel:
        model = db.query(InspectionPlanModel).filter(InspectionPlanModel.id == plan.id).first()
        if not model:
            model = InspectionPlanModel(id=plan.id)
            db.add(model)

        model.plan_name = plan.plan_name
        model.allocations_json = json.dumps([a.model_dump() for a in plan.allocations])
        model.unreachable_targets_json = json.dumps(plan.unreachable_targets)
        model.conflict_checks_passed = plan.conflict_checks_passed
        model.total_rovers_assigned = plan.total_rovers_assigned
        model.total_targets_covered = plan.total_targets_covered
        model.human_approval_status = plan.human_approval_status
        model.rejection_reason = plan.rejection_reason
        model.approved_by = plan.approved_by
        model.is_simulated = plan.is_simulated

        db.commit()
        db.refresh(model)
        return model

    @classmethod
    def get_plan(cls, db: Session, plan_id: str) -> Optional[InspectionPlanModel]:
        return db.query(InspectionPlanModel).filter(InspectionPlanModel.id == plan_id).first()

    @classmethod
    def list_plans(cls, db: Session, limit: int = 30) -> List[InspectionPlanModel]:
        return db.query(InspectionPlanModel).order_by(InspectionPlanModel.created_at.desc()).limit(limit).all()

    @classmethod
    def atomically_approve_plan(
        cls,
        db: Session,
        plan_id: str,
        operator_id: str,
        notes: Optional[str] = None,
    ) -> InspectionPlanModel:
        # Atomic test-and-set to prevent race conditions
        rows = db.query(InspectionPlanModel).filter(
            InspectionPlanModel.id == plan_id,
            InspectionPlanModel.human_approval_status == "PENDING_APPROVAL"
        ).update({
            "human_approval_status": "APPROVED",
            "approved_by": operator_id,
            "approved_at": datetime.now(timezone.utc),
        })
        db.flush()

        if rows == 0:
            existing = cls.get_plan(db, plan_id)
            if not existing:
                raise AquaCrewException(status_code=404, code="PLAN_NOT_FOUND", message=f"Plan '{plan_id}' not found.")
            raise AquaCrewException(
                status_code=400,
                code="INVALID_PLAN_STATE",
                message=f"Plan '{plan_id}' is in status '{existing.human_approval_status}' (must be PENDING_APPROVAL).",
            )

        db.commit()
        model = cls.get_plan(db, plan_id)

        cls.log_event(
            db,
            event_type="INSPECTION_PLAN_APPROVED",
            plan_id=plan_id,
            user_id=operator_id,
            details={"operator_notes": notes, "plan_name": model.plan_name},
        )
        return model

    @classmethod
    def atomically_reject_plan(
        cls,
        db: Session,
        plan_id: str,
        operator_id: str,
        reason: str,
    ) -> InspectionPlanModel:
        rows = db.query(InspectionPlanModel).filter(
            InspectionPlanModel.id == plan_id,
            InspectionPlanModel.human_approval_status == "PENDING_APPROVAL"
        ).update({
            "human_approval_status": "REJECTED",
            "rejection_reason": reason,
        })
        db.flush()

        if rows == 0:
            existing = cls.get_plan(db, plan_id)
            if not existing:
                raise AquaCrewException(status_code=404, code="PLAN_NOT_FOUND", message=f"Plan '{plan_id}' not found.")
            raise AquaCrewException(
                status_code=400,
                code="INVALID_PLAN_STATE",
                message=f"Plan '{plan_id}' is in status '{existing.human_approval_status}' (must be PENDING_APPROVAL).",
            )

        db.commit()
        model = cls.get_plan(db, plan_id)

        cls.log_event(
            db,
            event_type="INSPECTION_PLAN_REJECTED",
            plan_id=plan_id,
            user_id=operator_id,
            details={"rejection_reason": reason},
        )
        return model

    # -------------------------------------------------------------------------
    # Executions
    # -------------------------------------------------------------------------
    @classmethod
    def save_execution(cls, db: Session, exec_data: InspectionExecutionProgressSchema) -> InspectionExecutionModel:
        model = db.query(InspectionExecutionModel).filter(InspectionExecutionModel.mission_id == exec_data.mission_id).first()
        if not model:
            model = InspectionExecutionModel(
                id=f"EXEC-{uuid.uuid4().hex[:10].upper()}",
                mission_id=exec_data.mission_id,
            )
            db.add(model)

        model.plan_id = exec_data.plan_id
        model.rover_id = exec_data.rover_id
        model.status = exec_data.status
        model.current_step = exec_data.current_step
        model.total_steps = exec_data.total_steps
        model.progress_percentage = exec_data.progress_percentage
        model.current_lng = exec_data.current_coordinates[0]
        model.current_lat = exec_data.current_coordinates[1]
        model.distance_traversed_m = exec_data.distance_traversed_m
        model.remaining_distance_m = exec_data.remaining_distance_m
        model.battery_percentage = exec_data.battery_percentage
        model.motor_temp_c = exec_data.motor_temp_c
        model.active_anomalies_count = exec_data.active_anomalies_detected
        model.route_adapted = exec_data.route_adapted
        model.adaptation_history_json = json.dumps(exec_data.adaptation_history)
        model.recent_observations_json = json.dumps([o.model_dump() for o in exec_data.recent_observations])
        model.is_simulated = exec_data.is_simulated

        db.commit()
        db.refresh(model)
        return model

    @classmethod
    def get_execution_by_mission(cls, db: Session, mission_id: str) -> Optional[InspectionExecutionModel]:
        return db.query(InspectionExecutionModel).filter(InspectionExecutionModel.mission_id == mission_id).first()

    # -------------------------------------------------------------------------
    # Reports
    # -------------------------------------------------------------------------
    @classmethod
    def save_report(cls, db: Session, rep: InspectionReportSchema) -> InspectionReportModel:
        model = db.query(InspectionReportModel).filter(InspectionReportModel.id == rep.id).first()
        if not model:
            model = InspectionReportModel(id=rep.id)
            db.add(model)

        model.plan_id = rep.plan_id
        model.mission_id = rep.mission_id
        model.rover_id = rep.rover_id
        model.pipeline_segment_id = rep.pipeline_segment_id
        model.segment_name = rep.segment_name
        model.inspection_method = rep.inspection_method
        model.start_time = rep.start_time
        model.completion_time = rep.completion_time
        model.route_distance_m = rep.route_distance_m
        model.inspected_distance_m = rep.inspected_distance_m
        model.sensor_observations_count = rep.sensor_observations_count
        model.detected_anomalies_json = json.dumps(rep.detected_anomalies)
        model.evidence_provenance = rep.evidence_provenance
        model.ai_classification_json = json.dumps(rep.ai_classification) if rep.ai_classification else None
        model.updated_infrastructure_risk = rep.updated_infrastructure_risk
        model.inspection_outcome = rep.inspection_outcome
        model.unresolved_uncertainties_json = json.dumps(rep.unresolved_uncertainties)
        model.recommended_next_action = rep.recommended_next_action
        model.operator_review_status = rep.operator_review_status
        model.reviewed_by = rep.reviewed_by
        model.operator_notes = rep.operator_notes
        model.payload_hash = cls._compute_hash(rep.model_dump())
        model.is_simulated = rep.is_simulated

        db.commit()
        db.refresh(model)
        return model

    @classmethod
    def get_report(cls, db: Session, report_id: str) -> Optional[InspectionReportModel]:
        return db.query(InspectionReportModel).filter(InspectionReportModel.id == report_id).first()

    @classmethod
    def list_reports(cls, db: Session, limit: int = 50) -> List[InspectionReportModel]:
        return db.query(InspectionReportModel).order_by(InspectionReportModel.created_at.desc()).limit(limit).all()

    # -------------------------------------------------------------------------
    # Events & Audit Logging
    # -------------------------------------------------------------------------
    @classmethod
    def log_event(
        cls,
        db: Session,
        event_type: str,
        user_id: str = "SYSTEM",
        plan_id: Optional[str] = None,
        mission_id: Optional[str] = None,
        rover_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> InspectionEventModel:
        evt = InspectionEventModel(
            id=f"INSP-EVT-{uuid.uuid4().hex[:10].upper()}",
            plan_id=plan_id,
            mission_id=mission_id,
            rover_id=rover_id,
            event_type=event_type,
            details_json=json.dumps(details or {}),
            user_id=user_id,
        )
        db.add(evt)
        db.commit()
        db.refresh(evt)
        return evt

    @classmethod
    def list_events(cls, db: Session, limit: int = 100) -> List[InspectionEventModel]:
        return db.query(InspectionEventModel).order_by(InspectionEventModel.created_at.desc()).limit(limit).all()

