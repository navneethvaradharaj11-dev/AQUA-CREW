"""
SQLAlchemy Models for Autonomous Inspection Intelligence & Multi-Rover Orchestration (Task 15)
Provides relational persistence for inspection recommendations, multi-rover plans,
simulated execution progress, adaptive rerouting logs, and evidence-grounded reports.
"""
from sqlalchemy import Column, String, Float, Integer, Text, Boolean, DateTime
from datetime import datetime, timezone
import json

from app.database.session import Base


class InspectionRecommendationModel(Base):
    __tablename__ = "inspection_recommendations_t15"

    id = Column(String(64), primary_key=True, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    segment_name = Column(String(128), default="")
    priority_score = Column(Float, nullable=False, default=50.0)
    priority_category = Column(String(32), default="MEDIUM", index=True)
    urgency_factors_json = Column(Text, nullable=True) # JSON dict of sub-scores
    supporting_evidence_json = Column(Text, nullable=True) # JSON list of SupportingEvidenceItem
    primary_classification = Column(String(32), default="DERIVED")
    confidence = Column(Float, default=0.85)
    uncertainty_radius_m = Column(Float, default=20.0)
    recommended_method = Column(String(64), default="ACOUSTIC_CORRELATION")
    estimated_duration_minutes = Column(Integer, default=30)
    required_rover_capabilities_json = Column(Text, nullable=True) # JSON list of string capabilities
    recommended_action = Column(Text, default="")
    human_approval_status = Column(String(32), default="PENDING_APPROVAL", index=True)
    rejection_reason = Column(String(256), nullable=True)
    approved_by = Column(String(128), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)


class InspectionPlanModel(Base):
    __tablename__ = "inspection_plans"

    id = Column(String(64), primary_key=True, index=True)
    plan_name = Column(String(128), nullable=False)
    allocations_json = Column(Text, nullable=False) # Serialized list of MultiRoverAllocationItemSchema
    unreachable_targets_json = Column(Text, nullable=True)
    conflict_checks_passed = Column(Boolean, default=True)
    total_rovers_assigned = Column(Integer, default=0)
    total_targets_covered = Column(Integer, default=0)
    human_approval_status = Column(String(32), default="PENDING_APPROVAL", index=True)
    rejection_reason = Column(String(256), nullable=True)
    approved_by = Column(String(128), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)


class InspectionExecutionModel(Base):
    __tablename__ = "inspection_executions"

    id = Column(String(64), primary_key=True, index=True)
    plan_id = Column(String(64), nullable=False, index=True)
    mission_id = Column(String(64), nullable=False, index=True)
    rover_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), default="SCHEDULED", index=True)
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer, default=10)
    progress_percentage = Column(Float, default=0.0)
    current_lat = Column(Float, nullable=False)
    current_lng = Column(Float, nullable=False)
    distance_traversed_m = Column(Float, default=0.0)
    remaining_distance_m = Column(Float, default=0.0)
    battery_percentage = Column(Float, default=100.0)
    motor_temp_c = Column(Float, default=25.0)
    active_anomalies_count = Column(Integer, default=0)
    route_adapted = Column(Boolean, default=False)
    adaptation_history_json = Column(Text, nullable=True)
    recent_observations_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)


class InspectionReportModel(Base):
    __tablename__ = "inspection_reports_t15"

    id = Column(String(64), primary_key=True, index=True)
    plan_id = Column(String(64), nullable=False, index=True)
    mission_id = Column(String(64), nullable=False, index=True)
    rover_id = Column(String(64), nullable=False, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    segment_name = Column(String(128), default="")
    inspection_method = Column(String(64), default="ACOUSTIC_CORRELATION")
    start_time = Column(String(64), default="")
    completion_time = Column(String(64), default="")
    route_distance_m = Column(Float, default=0.0)
    inspected_distance_m = Column(Float, default=0.0)
    sensor_observations_count = Column(Integer, default=0)
    detected_anomalies_json = Column(Text, nullable=True)
    evidence_provenance = Column(String(32), default="SIMULATED")
    ai_classification_json = Column(Text, nullable=True)
    updated_infrastructure_risk = Column(Float, default=50.0)
    inspection_outcome = Column(String(32), default="SUCCESS")
    unresolved_uncertainties_json = Column(Text, nullable=True)
    recommended_next_action = Column(Text, default="")
    operator_review_status = Column(String(32), default="PENDING_REVIEW", index=True)
    reviewed_by = Column(String(128), nullable=True)
    operator_notes = Column(Text, nullable=True)
    payload_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)


class InspectionEventModel(Base):
    __tablename__ = "inspection_events"

    id = Column(String(64), primary_key=True, index=True)
    plan_id = Column(String(64), nullable=True, index=True)
    mission_id = Column(String(64), nullable=True, index=True)
    rover_id = Column(String(64), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    details_json = Column(Text, nullable=True)
    user_id = Column(String(128), default="SYSTEM")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

