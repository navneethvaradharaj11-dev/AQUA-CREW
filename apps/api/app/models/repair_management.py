"""
SQLAlchemy Persistent Models for Repair Planning & Management System (Task 16)
Stores damage assessments, engineering repair recommendations, resource allocations,
cost estimates, virtual crew schedules, workflow audit events, and post-repair verification records.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey
from datetime import datetime, timezone
import uuid

from app.database.session import Base


class RepairAssessmentModel(Base):
    __tablename__ = "repair_assessments"

    id = Column(String(64), primary_key=True, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    segment_name = Column(String(128), default="")
    source_inspection_report_id = Column(String(64), nullable=True, index=True)
    damage_category = Column(String(64), nullable=False, index=True)
    severity = Column(String(32), nullable=False, index=True)
    pipe_material = Column(String(64), default="Ductile Iron")
    pipe_diameter_mm = Column(Float, default=300.0)
    pipe_age_years = Column(Float, nullable=True)
    nominal_pressure_psi = Column(Float, default=65.0)
    estimated_water_loss_lph = Column(Float, default=0.0)
    structural_vulnerability_score = Column(Float, default=50.0)
    previous_repair_count = Column(Integer, default=0)
    inspection_confidence = Column(Float, default=0.85)
    evidence_completeness_pct = Column(Float, default=80.0)
    missing_information_json = Column(Text, nullable=True)
    engineering_review_required = Column(Boolean, default=True)
    supporting_evidence_json = Column(Text, nullable=True)
    assessment_notes = Column(Text, default="")
    assessed_by = Column(String(128), default="SYSTEM_REPAIR_ENGINE")
    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)


class RepairRecommendationModel(Base):
    __tablename__ = "repair_recommendations"

    id = Column(String(64), primary_key=True, index=True)
    damage_assessment_id = Column(String(64), nullable=False, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    primary_recommended_method = Column(String(64), nullable=False, index=True)
    secondary_alternative_method = Column(String(64), nullable=True)
    all_evaluated_options_json = Column(Text, nullable=True)
    engineering_rationale = Column(Text, default="")
    urgency_tier = Column(String(32), default="PLANNED", index=True)
    requires_isolation = Column(Boolean, default=True)
    bypass_pumping_needed = Column(Boolean, default=False)
    traffic_disruption_level = Column(String(32), default="LOW")
    status = Column(String(32), default="PROPOSED", index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)


class RepairPlanModel(Base):
    __tablename__ = "repair_plans"

    id = Column(String(64), primary_key=True, index=True)
    plan_name = Column(String(128), nullable=False)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    segment_name = Column(String(128), default="")
    damage_assessment_id = Column(String(64), nullable=False, index=True)
    repair_recommendation_id = Column(String(64), nullable=False, index=True)
    selected_method = Column(String(64), nullable=False, index=True)
    workflow_status = Column(String(64), default="DAMAGE_ASSESSED", index=True)
    repair_priority_score = Column(Float, default=50.0, index=True)
    priority_category = Column(String(32), default="MEDIUM", index=True)
    priority_factors_json = Column(Text, nullable=True)
    approved_by = Column(String(128), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    operator_notes = Column(Text, nullable=True)
    digital_twin_scenario_id = Column(String(64), nullable=True)
    created_by = Column(String(128), default="ENGINEER_SYSTEM")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)


class RepairResourceModel(Base):
    __tablename__ = "repair_resources"

    id = Column(String(64), primary_key=True, index=True)
    repair_plan_id = Column(String(64), nullable=False, index=True)
    resource_id = Column(String(64), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False, index=True)
    unit = Column(String(32), default="PIECE")
    estimated_quantity = Column(Float, default=1.0)
    compatibility_requirements = Column(Text, default="")
    availability_status = Column(String(32), default="IN_STOCK", index=True)
    estimated_unit_cost_usd = Column(Float, default=0.0)
    total_cost_usd = Column(Float, default=0.0)
    supplier_info = Column(String(128), default="MUNICIPAL_DEPOT")
    cost_data_source = Column(String(32), default="DERIVED")
    cost_data_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RepairCostEstimateModel(Base):
    __tablename__ = "repair_cost_estimates"

    id = Column(String(64), primary_key=True, index=True)
    repair_plan_id = Column(String(64), nullable=True, index=True)
    damage_assessment_id = Column(String(64), nullable=False, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    components_json = Column(Text, nullable=True)
    total_material_cost_usd = Column(Float, default=0.0)
    total_equipment_cost_usd = Column(Float, default=0.0)
    total_labour_cost_usd = Column(Float, default=0.0)
    inspection_cost_usd = Column(Float, default=0.0)
    estimated_water_loss_cost_usd = Column(Float, default=0.0)
    restoration_cost_usd = Column(Float, default=0.0)
    contingency_cost_usd = Column(Float, default=0.0)
    total_estimated_cost_usd = Column(Float, default=0.0)
    estimated_downtime_hours = Column(Float, default=4.0)
    cost_uncertainty_lower_bound_usd = Column(Float, default=0.0)
    cost_uncertainty_upper_bound_usd = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)


class RepairCrewModel(Base):
    __tablename__ = "repair_crews"

    id = Column(String(64), primary_key=True, index=True)
    crew_name = Column(String(128), nullable=False)
    specialization = Column(String(64), default="PIPELINE_MECHANICAL")
    skills_json = Column(Text, nullable=True)
    members_json = Column(Text, nullable=True)
    is_available = Column(Boolean, default=True, index=True)
    base_location_lat = Column(Float, default=40.7128)
    base_location_lng = Column(Float, default=-74.0060)
    current_assigned_job_id = Column(String(64), nullable=True)
    max_daily_hours = Column(Float, default=8.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RepairScheduleModel(Base):
    __tablename__ = "repair_schedules"

    id = Column(String(64), primary_key=True, index=True)
    repair_plan_id = Column(String(64), nullable=False, index=True)
    crew_id = Column(String(64), nullable=False, index=True)
    crew_name = Column(String(128), default="")
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    estimated_duration_hours = Column(Float, default=4.0)
    travel_distance_km = Column(Float, default=0.0)
    travel_time_hours = Column(Float, default=0.5)
    has_schedule_conflicts = Column(Boolean, default=False)
    schedule_conflict_details = Column(Text, nullable=True)
    scheduling_notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RepairWorkflowEventModel(Base):
    __tablename__ = "repair_workflow_events"

    id = Column(String(64), primary_key=True, index=True)
    repair_plan_id = Column(String(64), nullable=False, index=True)
    from_status = Column(String(64), nullable=False)
    to_status = Column(String(64), nullable=False, index=True)
    changed_by = Column(String(128), default="SYSTEM")
    reason = Column(Text, nullable=False)
    details_json = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class RepairVerificationModel(Base):
    __tablename__ = "repair_verifications"

    id = Column(String(64), primary_key=True, index=True)
    repair_plan_id = Column(String(64), nullable=False, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    verification_outcome = Column(String(64), nullable=False, index=True)
    pre_repair_leakage_lph = Column(Float, default=0.0)
    post_repair_leakage_lph = Column(Float, default=0.0)
    leakage_reduction_pct = Column(Float, default=100.0)
    acoustic_anomaly_cleared = Column(Boolean, default=True)
    pressure_gradient_restored = Column(Boolean, default=True)
    remaining_uncertainty_pct = Column(Float, default=5.0)
    supporting_evidence_json = Column(Text, nullable=True)
    verified_by = Column(String(128), default="LEAD_ENGINEER")
    verified_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    tamper_proof_hash = Column(String(64), nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)

