"""
AQUA CREW — Repair Management Repository Layer (Task 16)
Provides thread-safe transactional persistence, state transition enforcement,
virtual crew seeding, audit logging, and cryptographic verification for repair entities.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import json
import uuid
import hashlib

from app.models.repair_management import (
    RepairAssessmentModel,
    RepairRecommendationModel,
    RepairPlanModel,
    RepairResourceModel,
    RepairCostEstimateModel,
    RepairCrewModel,
    RepairScheduleModel,
    RepairWorkflowEventModel,
    RepairVerificationModel,
)
from app.schemas.repair_management import (
    DamageAssessmentSchema,
    SupportingEvidenceItem,
    RepairRecommendationSchema,
    RepairPlanSchema,
    RepairCostEstimateSchema,
    RepairScheduleItemSchema,
    RepairVerificationSchema,
    RepairWorkflowStatus,
)
from app.core.exceptions import AquaCrewException


DEFAULT_CREWS = [
    {
        "id": "CREW-MECH-01",
        "crew_name": "Metro Rapid Mechanical Repair Crew",
        "specialization": "PIPELINE_MECHANICAL",
        "skills": ["split_sleeve_clamping", "joint_resealing", "emergency_isolation", "hot_tapping"],
        "members": [
            {"member_id": "M-01", "name": "Marcus Vance", "role": "Lead Foreman", "certification": "AWWA Certified Class IV", "hourly_rate_usd": 85.0},
            {"member_id": "M-02", "name": "Elena Rostova", "role": "Pipefitter", "certification": "Pressure Piping Journeyman", "hourly_rate_usd": 65.0},
            {"member_id": "M-03", "name": "Tariq Al-Mansoor", "role": "Safety Specialist", "certification": "OSHA Confined Space Supervisor", "hourly_rate_usd": 60.0},
        ],
        "is_available": True,
        "base_location_lat": 40.7128,
        "base_location_lng": -74.0060,
    },
    {
        "id": "CREW-HEAVY-02",
        "crew_name": "Trunk Line Replacement Squad",
        "specialization": "HEAVY_EXCAVATION",
        "skills": ["trench_shoring", "heavy_crane_handling", "large_diameter_jointing", "thrust_blocking"],
        "members": [
            {"member_id": "M-04", "name": "David Chen", "role": "Excavation Superintendent", "certification": "Heavy Civil Master", "hourly_rate_usd": 90.0},
            {"member_id": "M-05", "name": "Brian O'Connor", "role": "Heavy Equipment Operator", "certification": "Crane & Excavator Class A", "hourly_rate_usd": 75.0},
            {"member_id": "M-06", "name": "Samuel Jackson", "role": "Welder / Joint Specialist", "certification": "AWS D1.1 Structural", "hourly_rate_usd": 70.0},
            {"member_id": "M-07", "name": "Amina Diallo", "role": "Traffic Controller", "certification": "DOT Traffic Safety", "hourly_rate_usd": 45.0},
        ],
        "is_available": True,
        "base_location_lat": 40.7180,
        "base_location_lng": -74.0120,
    },
    {
        "id": "CREW-LINING-03",
        "crew_name": "Trenchless CIPP Rehabilitation Unit",
        "specialization": "TRENCHLESS_REHABILITATION",
        "skills": ["cipp_inversion", "uv_curing", "robotic_lateral_reinstatement", "internal_epoxy_spray"],
        "members": [
            {"member_id": "M-08", "name": "Sarah Lindqvist", "role": "Trenchless Systems Engineer", "certification": "NASSCO PACP/LACP Master", "hourly_rate_usd": 95.0},
            {"member_id": "M-09", "name": "Carlos Gomez", "role": "Curing Process Technician", "certification": "Thermoset UV Specialist", "hourly_rate_usd": 70.0},
        ],
        "is_available": True,
        "base_location_lat": 40.7050,
        "base_location_lng": -74.0010,
    },
    {
        "id": "CREW-VALVE-04",
        "crew_name": "Valves & Hydraulic Controls Team",
        "specialization": "VALVE_AND_PRESSURE",
        "skills": ["prv_calibration", "gate_valve_overhaul", "actuator_servicing", "pressure_relief_testing"],
        "members": [
            {"member_id": "M-10", "name": "Rajiv Patel", "role": "Lead Instrumentation Engineer", "certification": "Control Systems PE", "hourly_rate_usd": 105.0},
            {"member_id": "M-11", "name": "Kevin Meyer", "role": "Mechanical Tech", "certification": "Hydraulic Valve Specialist", "hourly_rate_usd": 68.0},
        ],
        "is_available": True,
        "base_location_lat": 40.7220,
        "base_location_lng": -74.0040,
    },
]


class RepairRepository:
    # -------------------------------------------------------------------------
    # Allowed Finite State Transitions
    # -------------------------------------------------------------------------
    VALID_TRANSITIONS: Dict[str, List[str]] = {
        "INSPECTION_COMPLETED": ["DAMAGE_ASSESSED", "ON_HOLD", "REJECTED"],
        "DAMAGE_ASSESSED": ["REPAIR_RECOMMENDED", "REQUIRES_REINSPECTION", "ON_HOLD", "REJECTED"],
        "REPAIR_RECOMMENDED": ["ENGINEERING_REVIEW_PENDING", "ON_HOLD", "REJECTED"],
        "ENGINEERING_REVIEW_PENDING": ["APPROVED", "REJECTED", "REQUIRES_REINSPECTION", "ON_HOLD"],
        "APPROVED": ["RESOURCE_PLANNED", "ON_HOLD", "REJECTED"],
        "RESOURCE_PLANNED": ["SCHEDULED", "ON_HOLD", "REJECTED"],
        "SCHEDULED": ["REPAIR_IN_PROGRESS", "ON_HOLD", "REJECTED"],
        "REPAIR_IN_PROGRESS": ["REPAIR_COMPLETED", "FAILED", "ON_HOLD"],
        "REPAIR_COMPLETED": ["VERIFICATION_PENDING", "REQUIRES_REINSPECTION"],
        "VERIFICATION_PENDING": ["VERIFIED", "REQUIRES_REINSPECTION", "FAILED"],
        "VERIFIED": ["CLOSED"],
        "CLOSED": [],
        "REJECTED": ["DAMAGE_ASSESSED", "ENGINEERING_REVIEW_PENDING"],
        "ON_HOLD": [
            "DAMAGE_ASSESSED", "REPAIR_RECOMMENDED", "ENGINEERING_REVIEW_PENDING",
            "APPROVED", "RESOURCE_PLANNED", "SCHEDULED", "REPAIR_IN_PROGRESS", "REJECTED"
        ],
        "FAILED": ["REQUIRES_REINSPECTION", "ENGINEERING_REVIEW_PENDING"],
        "REQUIRES_REINSPECTION": ["INSPECTION_COMPLETED", "DAMAGE_ASSESSED"],
    }

    # -------------------------------------------------------------------------
    # Damage Assessments
    # -------------------------------------------------------------------------
    @staticmethod
    def save_assessment(db: Session, schema: DamageAssessmentSchema) -> RepairAssessmentModel:
        model = db.query(RepairAssessmentModel).filter(RepairAssessmentModel.id == schema.id).first()
        evidence_dicts = [e.model_dump() for e in schema.supporting_evidence]
        
        if not model:
            model = RepairAssessmentModel(
                id=schema.id,
                pipeline_segment_id=schema.pipeline_segment_id,
                segment_name=schema.segment_name,
                source_inspection_report_id=schema.source_inspection_report_id,
                damage_category=schema.damage_category,
                severity=schema.severity,
                pipe_material=schema.pipe_material,
                pipe_diameter_mm=schema.pipe_diameter_mm,
                pipe_age_years=schema.pipe_age_years,
                nominal_pressure_psi=schema.nominal_pressure_psi,
                estimated_water_loss_lph=schema.estimated_water_loss_lph,
                structural_vulnerability_score=schema.structural_vulnerability_score,
                previous_repair_count=schema.previous_repair_count,
                inspection_confidence=schema.inspection_confidence,
                evidence_completeness_pct=schema.evidence_completeness_pct,
                missing_information_json=json.dumps(schema.missing_information),
                engineering_review_required=schema.engineering_review_required,
                supporting_evidence_json=json.dumps(evidence_dicts),
                assessment_notes=schema.assessment_notes,
                assessed_by=schema.assessed_by,
                assessed_at=datetime.fromisoformat(schema.assessed_at.replace("Z", "+00:00")),
                is_simulated=schema.is_simulated,
            )
            db.add(model)
        else:
            model.damage_category = schema.damage_category
            model.severity = schema.severity
            model.estimated_water_loss_lph = schema.estimated_water_loss_lph
            model.structural_vulnerability_score = schema.structural_vulnerability_score
            model.inspection_confidence = schema.inspection_confidence
            model.evidence_completeness_pct = schema.evidence_completeness_pct
            model.missing_information_json = json.dumps(schema.missing_information)
            model.supporting_evidence_json = json.dumps(evidence_dicts)
            model.assessment_notes = schema.assessment_notes

        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_assessment(db: Session, assessment_id: str) -> Optional[RepairAssessmentModel]:
        return db.query(RepairAssessmentModel).filter(RepairAssessmentModel.id == assessment_id).first()

    @staticmethod
    def get_assessment_by_segment(db: Session, segment_id: str) -> Optional[RepairAssessmentModel]:
        return db.query(RepairAssessmentModel).filter(
            RepairAssessmentModel.pipeline_segment_id == segment_id
        ).order_by(RepairAssessmentModel.assessed_at.desc()).first()

    @staticmethod
    def list_assessments(db: Session, limit: int = 100) -> List[RepairAssessmentModel]:
        return db.query(RepairAssessmentModel).order_by(RepairAssessmentModel.assessed_at.desc()).limit(limit).all()

    @staticmethod
    def model_to_assessment_schema(model: RepairAssessmentModel) -> DamageAssessmentSchema:
        missing_info = []
        if model.missing_information_json:
            try:
                missing_info = json.loads(model.missing_information_json)
            except Exception:
                pass
        evidence_items = []
        if model.supporting_evidence_json:
            try:
                raw_items = json.loads(model.supporting_evidence_json)
                for it in raw_items:
                    evidence_items.append(SupportingEvidenceItem(**it))
            except Exception:
                pass

        return DamageAssessmentSchema(
            id=model.id,
            pipeline_segment_id=model.pipeline_segment_id,
            segment_name=model.segment_name or "",
            source_inspection_report_id=model.source_inspection_report_id,
            damage_category=model.damage_category,
            severity=model.severity,
            pipe_material=model.pipe_material or "Ductile Iron",
            pipe_diameter_mm=model.pipe_diameter_mm or 300.0,
            pipe_age_years=model.pipe_age_years,
            nominal_pressure_psi=model.nominal_pressure_psi or 65.0,
            estimated_water_loss_lph=model.estimated_water_loss_lph or 0.0,
            structural_vulnerability_score=model.structural_vulnerability_score or 50.0,
            previous_repair_count=model.previous_repair_count or 0,
            inspection_confidence=model.inspection_confidence or 0.85,
            evidence_completeness_pct=model.evidence_completeness_pct or 80.0,
            missing_information=missing_info,
            engineering_review_required=model.engineering_review_required,
            supporting_evidence=evidence_items,
            assessment_notes=model.assessment_notes or "",
            assessed_by=model.assessed_by or "SYSTEM_REPAIR_ENGINE",
            assessed_at=model.assessed_at.isoformat() if model.assessed_at else datetime.now(timezone.utc).isoformat(),
            is_simulated=model.is_simulated,
        )

    # -------------------------------------------------------------------------
    # Repair Recommendations
    # -------------------------------------------------------------------------
    @staticmethod
    def save_recommendation(db: Session, schema: RepairRecommendationSchema) -> RepairRecommendationModel:
        model = db.query(RepairRecommendationModel).filter(RepairRecommendationModel.id == schema.id).first()
        opts_dicts = [o.model_dump() for o in schema.all_evaluated_options]

        if not model:
            model = RepairRecommendationModel(
                id=schema.id,
                damage_assessment_id=schema.damage_assessment_id,
                pipeline_segment_id=schema.pipeline_segment_id,
                primary_recommended_method=schema.primary_recommended_method,
                secondary_alternative_method=schema.secondary_alternative_method,
                all_evaluated_options_json=json.dumps(opts_dicts),
                engineering_rationale=schema.engineering_rationale,
                urgency_tier=schema.urgency_tier,
                requires_isolation=schema.requires_isolation,
                bypass_pumping_needed=schema.bypass_pumping_needed,
                traffic_disruption_level=schema.traffic_disruption_level,
                status=schema.status,
                created_at=datetime.fromisoformat(schema.created_at.replace("Z", "+00:00")),
                is_simulated=schema.is_simulated,
            )
            db.add(model)
        else:
            model.primary_recommended_method = schema.primary_recommended_method
            model.secondary_alternative_method = schema.secondary_alternative_method
            model.all_evaluated_options_json = json.dumps(opts_dicts)
            model.engineering_rationale = schema.engineering_rationale
            model.urgency_tier = schema.urgency_tier
            model.status = schema.status

        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_recommendation(db: Session, rec_id: str) -> Optional[RepairRecommendationModel]:
        return db.query(RepairRecommendationModel).filter(RepairRecommendationModel.id == rec_id).first()

    @staticmethod
    def get_recommendation_by_assessment(db: Session, assessment_id: str) -> Optional[RepairRecommendationModel]:
        return db.query(RepairRecommendationModel).filter(
            RepairRecommendationModel.damage_assessment_id == assessment_id
        ).first()

    # -------------------------------------------------------------------------
    # Repair Plans & Workflow State Transitions
    # -------------------------------------------------------------------------
    @staticmethod
    def save_plan(db: Session, schema: RepairPlanSchema) -> RepairPlanModel:
        model = db.query(RepairPlanModel).filter(RepairPlanModel.id == schema.id).first()
        factors_json = json.dumps(schema.priority.contributing_factors) if schema.priority else "{}"

        if not model:
            model = RepairPlanModel(
                id=schema.id,
                plan_name=schema.plan_name,
                pipeline_segment_id=schema.pipeline_segment_id,
                segment_name=schema.segment_name,
                damage_assessment_id=schema.damage_assessment_id,
                repair_recommendation_id=schema.repair_recommendation_id,
                selected_method=schema.selected_method,
                workflow_status=schema.workflow_status,
                repair_priority_score=schema.priority.repair_priority_score if schema.priority else 50.0,
                priority_category=schema.priority.priority_category if schema.priority else "MEDIUM",
                priority_factors_json=factors_json,
                approved_by=schema.approved_by,
                approved_at=datetime.fromisoformat(schema.approved_at.replace("Z", "+00:00")) if schema.approved_at else None,
                rejection_reason=schema.rejection_reason,
                operator_notes=schema.operator_notes,
                digital_twin_scenario_id=schema.digital_twin_scenario_id,
                created_by=schema.created_by,
                created_at=datetime.fromisoformat(schema.created_at.replace("Z", "+00:00")),
                is_simulated=schema.is_simulated,
            )
            db.add(model)
        else:
            model.selected_method = schema.selected_method
            model.workflow_status = schema.workflow_status
            if schema.priority:
                model.repair_priority_score = schema.priority.repair_priority_score
                model.priority_category = schema.priority.priority_category
                model.priority_factors_json = factors_json
            model.digital_twin_scenario_id = schema.digital_twin_scenario_id
            model.operator_notes = schema.operator_notes

        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_plan(db: Session, plan_id: str) -> Optional[RepairPlanModel]:
        return db.query(RepairPlanModel).filter(RepairPlanModel.id == plan_id).first()

    @staticmethod
    def get_plan_by_segment(db: Session, segment_id: str) -> Optional[RepairPlanModel]:
        # Return latest active/open plan for segment
        return db.query(RepairPlanModel).filter(
            RepairPlanModel.pipeline_segment_id == segment_id,
            RepairPlanModel.workflow_status.notin_(["CLOSED", "REJECTED"])
        ).order_by(RepairPlanModel.created_at.desc()).first()

    @staticmethod
    def list_plans(db: Session, status: Optional[str] = None, limit: int = 100) -> List[RepairPlanModel]:
        q = db.query(RepairPlanModel)
        if status:
            q = q.filter(RepairPlanModel.workflow_status == status)
        return q.order_by(RepairPlanModel.repair_priority_score.desc(), RepairPlanModel.created_at.desc()).limit(limit).all()

    @classmethod
    def transition_plan_status(
        cls,
        db: Session,
        plan_id: str,
        target_status: RepairWorkflowStatus,
        user_id: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> RepairPlanModel:
        """
        Atomically validates and transitions repair plan workflow state.
        Logs an immutable audit event in RepairWorkflowEventModel.
        """
        plan = cls.get_plan(db, plan_id)
        if not plan:
            raise AquaCrewException(status_code=404, code="PLAN_NOT_FOUND", message=f"Repair plan '{plan_id}' not found.")

        current = plan.workflow_status
        allowed = cls.VALID_TRANSITIONS.get(current, [])

        if target_status not in allowed:
            raise AquaCrewException(
                status_code=400,
                code="INVALID_STATE_TRANSITION",
                message=f"Cannot transition repair plan from '{current}' to '{target_status}'. Allowed transitions: {allowed}",
            )

        # Apply state updates
        plan.workflow_status = target_status
        if target_status == "APPROVED":
            plan.approved_by = user_id
            plan.approved_at = datetime.now(timezone.utc)
        elif target_status == "REJECTED":
            plan.rejection_reason = reason

        # Audit event record
        event = RepairWorkflowEventModel(
            id=f"EVT-WF-{uuid.uuid4().hex[:8].upper()}",
            repair_plan_id=plan_id,
            from_status=current,
            to_status=target_status,
            changed_by=user_id,
            reason=reason,
            details_json=json.dumps(details or {}),
            timestamp=datetime.now(timezone.utc),
        )
        db.add(event)

        db.commit()
        db.refresh(plan)
        return plan

    # -------------------------------------------------------------------------
    # Resources & Cost Estimates
    # -------------------------------------------------------------------------
    @staticmethod
    def save_cost_estimate(db: Session, schema: RepairCostEstimateSchema) -> RepairCostEstimateModel:
        model = db.query(RepairCostEstimateModel).filter(RepairCostEstimateModel.id == schema.id).first()
        comp_dicts = [c.model_dump() for c in schema.components]

        if not model:
            model = RepairCostEstimateModel(
                id=schema.id,
                repair_plan_id=schema.damage_assessment_id,
                damage_assessment_id=schema.damage_assessment_id,
                pipeline_segment_id=schema.pipeline_segment_id,
                components_json=json.dumps(comp_dicts),
                total_material_cost_usd=schema.total_material_cost_usd,
                total_equipment_cost_usd=schema.total_equipment_cost_usd,
                total_labour_cost_usd=schema.total_labour_cost_usd,
                inspection_cost_usd=schema.inspection_cost_usd,
                estimated_water_loss_cost_usd=schema.estimated_water_loss_cost_usd,
                restoration_cost_usd=schema.restoration_cost_usd,
                contingency_cost_usd=schema.contingency_cost_usd,
                total_estimated_cost_usd=schema.total_estimated_cost_usd,
                estimated_downtime_hours=schema.estimated_downtime_hours,
                cost_uncertainty_lower_bound_usd=schema.cost_uncertainty_lower_bound_usd,
                cost_uncertainty_upper_bound_usd=schema.cost_uncertainty_upper_bound_usd,
                created_at=datetime.fromisoformat(schema.created_at.replace("Z", "+00:00")),
                is_simulated=schema.is_simulated,
            )
            db.add(model)
        else:
            model.components_json = json.dumps(comp_dicts)
            model.total_material_cost_usd = schema.total_material_cost_usd
            model.total_equipment_cost_usd = schema.total_equipment_cost_usd
            model.total_labour_cost_usd = schema.total_labour_cost_usd
            model.total_estimated_cost_usd = schema.total_estimated_cost_usd

        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_cost_estimate(db: Session, estimate_id: str) -> Optional[RepairCostEstimateModel]:
        return db.query(RepairCostEstimateModel).filter(RepairCostEstimateModel.id == estimate_id).first()

    @staticmethod
    def get_cost_estimate_by_assessment(db: Session, assessment_id: str) -> Optional[RepairCostEstimateModel]:
        return db.query(RepairCostEstimateModel).filter(
            RepairCostEstimateModel.damage_assessment_id == assessment_id
        ).first()

    # -------------------------------------------------------------------------
    # Virtual Crews & Schedules
    # -------------------------------------------------------------------------
    @staticmethod
    def seed_default_crews(db: Session) -> None:
        """Seeds standard virtual repair crews if database table is empty."""
        for c in DEFAULT_CREWS:
            existing = db.query(RepairCrewModel).filter(RepairCrewModel.id == c["id"]).first()
            if not existing:
                model = RepairCrewModel(
                    id=c["id"],
                    crew_name=c["crew_name"],
                    specialization=c["specialization"],
                    skills_json=json.dumps(c["skills"]),
                    members_json=json.dumps(c["members"]),
                    is_available=c["is_available"],
                    base_location_lat=c["base_location_lat"],
                    base_location_lng=c["base_location_lng"],
                    created_at=datetime.now(timezone.utc),
                )
                db.add(model)
        db.commit()

    @staticmethod
    def list_crews(db: Session, available_only: bool = False) -> List[RepairCrewModel]:
        q = db.query(RepairCrewModel)
        if available_only:
            q = q.filter(RepairCrewModel.is_available.is_(True))
        return q.all()

    @staticmethod
    def get_crew(db: Session, crew_id: str) -> Optional[RepairCrewModel]:
        return db.query(RepairCrewModel).filter(RepairCrewModel.id == crew_id).first()

    @staticmethod
    def save_schedule(db: Session, schema: RepairScheduleItemSchema) -> RepairScheduleModel:
        model = db.query(RepairScheduleModel).filter(RepairScheduleModel.id == schema.schedule_id).first()
        start_dt = datetime.fromisoformat(schema.scheduled_start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(schema.scheduled_end.replace("Z", "+00:00"))

        if not model:
            model = RepairScheduleModel(
                id=schema.schedule_id,
                repair_plan_id=schema.repair_plan_id,
                crew_id=schema.crew_id,
                crew_name=schema.crew_name,
                scheduled_start=start_dt,
                scheduled_end=end_dt,
                estimated_duration_hours=schema.estimated_duration_hours,
                travel_distance_km=schema.travel_distance_km,
                travel_time_hours=schema.travel_time_hours,
                has_schedule_conflicts=schema.has_schedule_conflicts,
                schedule_conflict_details=schema.schedule_conflict_details,
                scheduling_notes=schema.scheduling_notes,
                created_at=datetime.now(timezone.utc),
            )
            db.add(model)
        else:
            model.scheduled_start = start_dt
            model.scheduled_end = end_dt
            model.estimated_duration_hours = schema.estimated_duration_hours
            model.has_schedule_conflicts = schema.has_schedule_conflicts
            model.schedule_conflict_details = schema.schedule_conflict_details

        # Update crew current assignment
        crew = db.query(RepairCrewModel).filter(RepairCrewModel.id == schema.crew_id).first()
        if crew:
            crew.is_available = False
            crew.current_assigned_job_id = schema.repair_plan_id

        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_schedule_by_plan(db: Session, plan_id: str) -> Optional[RepairScheduleModel]:
        return db.query(RepairScheduleModel).filter(RepairScheduleModel.repair_plan_id == plan_id).first()

    # -------------------------------------------------------------------------
    # Post-Repair Verifications & SHA-256 Digest
    # -------------------------------------------------------------------------
    @classmethod
    def calculate_verification_hash(cls, schema: RepairVerificationSchema) -> str:
        payload = {
            "id": schema.id,
            "repair_plan_id": schema.repair_plan_id,
            "pipeline_segment_id": schema.pipeline_segment_id,
            "verification_outcome": schema.verification_outcome,
            "leakage_reduction_pct": schema.leakage_reduction_pct,
            "acoustic_anomaly_cleared": schema.acoustic_anomaly_cleared,
            "pressure_gradient_restored": schema.pressure_gradient_restored,
            "verified_by": schema.verified_by,
            "verified_at": schema.verified_at,
        }
        canonical = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def save_verification(cls, db: Session, schema: RepairVerificationSchema) -> RepairVerificationModel:
        if not schema.tamper_proof_hash:
            schema.tamper_proof_hash = cls.calculate_verification_hash(schema)

        model = db.query(RepairVerificationModel).filter(RepairVerificationModel.id == schema.id).first()
        evidence_dicts = [e.model_dump() for e in schema.supporting_evidence]

        if not model:
            model = RepairVerificationModel(
                id=schema.id,
                repair_plan_id=schema.repair_plan_id,
                pipeline_segment_id=schema.pipeline_segment_id,
                verification_outcome=schema.verification_outcome,
                pre_repair_leakage_lph=schema.pre_repair_leakage_lph,
                post_repair_leakage_lph=schema.post_repair_leakage_lph,
                leakage_reduction_pct=schema.leakage_reduction_pct,
                acoustic_anomaly_cleared=schema.acoustic_anomaly_cleared,
                pressure_gradient_restored=schema.pressure_gradient_restored,
                remaining_uncertainty_pct=schema.remaining_uncertainty_pct,
                supporting_evidence_json=json.dumps(evidence_dicts),
                verified_by=schema.verified_by,
                verified_at=datetime.fromisoformat(schema.verified_at.replace("Z", "+00:00")),
                tamper_proof_hash=schema.tamper_proof_hash,
                is_simulated=schema.is_simulated,
            )
            db.add(model)
        else:
            model.verification_outcome = schema.verification_outcome
            model.post_repair_leakage_lph = schema.post_repair_leakage_lph
            model.leakage_reduction_pct = schema.leakage_reduction_pct
            model.acoustic_anomaly_cleared = schema.acoustic_anomaly_cleared
            model.pressure_gradient_restored = schema.pressure_gradient_restored
            model.tamper_proof_hash = schema.tamper_proof_hash

        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_verification(db: Session, verification_id: str) -> Optional[RepairVerificationModel]:
        return db.query(RepairVerificationModel).filter(RepairVerificationModel.id == verification_id).first()

    @staticmethod
    def get_verification_by_plan(db: Session, plan_id: str) -> Optional[RepairVerificationModel]:
        return db.query(RepairVerificationModel).filter(RepairVerificationModel.repair_plan_id == plan_id).first()

    @classmethod
    def verify_report_integrity(cls, db: Session, verification_id: str) -> bool:
        model = cls.get_verification(db, verification_id)
        if not model or not model.tamper_proof_hash:
            return False

        payload = {
            "id": model.id,
            "repair_plan_id": model.repair_plan_id,
            "pipeline_segment_id": model.pipeline_segment_id,
            "verification_outcome": model.verification_outcome,
            "leakage_reduction_pct": model.leakage_reduction_pct,
            "acoustic_anomaly_cleared": model.acoustic_anomaly_cleared,
            "pressure_gradient_restored": model.pressure_gradient_restored,
            "verified_by": model.verified_by,
            "verified_at": model.verified_at.isoformat() if model.verified_at else "",
        }
        canonical = json.dumps(payload, sort_keys=True)
        computed_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return computed_hash == model.tamper_proof_hash

    # -------------------------------------------------------------------------
    # Workflow Audit Events
    # -------------------------------------------------------------------------
    @staticmethod
    def list_workflow_events(db: Session, plan_id: Optional[str] = None, limit: int = 100) -> List[RepairWorkflowEventModel]:
        q = db.query(RepairWorkflowEventModel)
        if plan_id:
            q = q.filter(RepairWorkflowEventModel.repair_plan_id == plan_id)
        return q.order_by(RepairWorkflowEventModel.timestamp.desc()).limit(limit).all()
