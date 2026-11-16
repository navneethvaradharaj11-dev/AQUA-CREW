"""
SQLAlchemy Models for Unified Operational Intelligence & Decision Support Platform (Task 12)
Persists operational assessments, explainable recommendations, human-in-the-loop decisions,
priorities, impact assessments, evidence references, execution records, and performance snapshots.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey
from datetime import datetime, timezone
import uuid

from app.database.session import Base


class OperationalAssessmentModel(Base):
    __tablename__ = "operational_assessments"

    id = Column(String(64), primary_key=True, index=True)
    assessment_name = Column(String(256), nullable=False)
    total_recommendations = Column(Integer, default=0)
    immediate_action_count = Column(Integer, default=0)
    urgent_leak_count = Column(Integer, default=0)
    preventive_count = Column(Integer, default=0)
    critical_segments_analyzed = Column(Integer, default=0)
    overall_network_urgency = Column(String(32), default="ROUTINE", index=True)  # STABLE, ROUTINE, ELEVATED, CRITICAL
    
    summary_json = Column(Text, default="{}", nullable=False)
    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class OperationalRecommendationModel(Base):
    __tablename__ = "operational_recommendations"

    id = Column(String(64), primary_key=True, index=True)
    assessment_id = Column(String(64), nullable=True, index=True)
    category = Column(String(64), nullable=False, index=True)
    # Categories: IMMEDIATE_INSPECTION, URGENT_LEAK_INVESTIGATION, PREVENTIVE_MAINTENANCE,
    #             HYDRAULIC_INVESTIGATION, PIPELINE_HEALTH_REVIEW, ROVER_DISPATCH_RECOMMENDED,
    #             CONTINUOUS_MONITORING, HUMAN_ENGINEERING_REVIEW

    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    segment_name = Column(String(256), nullable=False)
    associated_incident_id = Column(String(64), nullable=True, index=True)
    associated_cluster_id = Column(String(64), nullable=True, index=True)

    risk_severity = Column(String(32), nullable=False, index=True)  # CRITICAL, HIGH, MODERATE, LOW
    priority_score = Column(Float, nullable=False, index=True)       # 0.0 to 100.0
    priority_tier = Column(String(32), nullable=False, index=True)   # CRITICAL_IMMEDIATE, URGENT, HIGH_PRIORITY, ROUTINE, DEFERRED

    recommended_action = Column(String(256), nullable=False)
    action_details = Column(Text, nullable=True)
    why_explanation = Column(Text, nullable=False)
    what_missing = Column(Text, default="None. All primary telemetric indicators available.")
    expected_impact = Column(Text, nullable=False)

    contributing_factors_json = Column(Text, default="{}", nullable=False)
    evidence_sources_json = Column(Text, default="[]", nullable=False)
    resource_requirements_json = Column(Text, default="{}", nullable=False)

    confidence = Column(Float, default=0.85)             # 0.0 to 1.0
    data_completeness_pct = Column(Float, default=90.0)  # 0.0 to 100.0
    uncertainty_margin = Column(Float, default=5.0)      # +/- score points

    status = Column(String(32), default="GENERATED", index=True)
    # Lifecycle: GENERATED -> PENDING_REVIEW -> APPROVED / REJECTED -> EXECUTION_PENDING -> IN_PROGRESS -> COMPLETED / FAILED / CANCELLED
    approval_status = Column(String(32), default="PENDING", index=True)  # PENDING, APPROVED, REJECTED

    assigned_rover_id = Column(String(64), nullable=True, index=True)
    dispatched_mission_id = Column(String(64), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)

    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class OperationalDecisionModel(Base):
    __tablename__ = "operational_decisions"

    id = Column(String(64), primary_key=True, index=True)
    recommendation_id = Column(String(64), nullable=False, index=True)
    decision_type = Column(String(32), nullable=False, index=True)  # APPROVED, REJECTED, OVERRIDDEN, REASSESSED
    decision_reason = Column(Text, nullable=False)

    operator_id = Column(String(128), default="OPERATOR-SUPERVISOR-01")
    operator_name = Column(String(128), default="Lead Operations Engineer")

    override_priority = Column(Float, nullable=True)
    allocated_resource_id = Column(String(64), nullable=True)
    resulting_mission_id = Column(String(64), nullable=True, index=True)

    decision_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    ip_address = Column(String(64), default="127.0.0.1")
    audit_hash = Column(String(128), nullable=True)

    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class OperationalPriorityModel(Base):
    __tablename__ = "operational_priorities"

    id = Column(String(64), primary_key=True, index=True)
    recommendation_id = Column(String(64), unique=True, nullable=False, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)

    rank_position = Column(Integer, default=1, index=True)
    composite_priority_score = Column(Float, nullable=False, index=True)  # 0.0 to 100.0

    # Explicit separated components (no blind summation)
    incident_severity_component = Column(Float, default=0.0)      # 0.0 to 100.0
    vulnerability_component = Column(Float, default=0.0)          # 0.0 to 100.0
    asset_health_component = Column(Float, default=0.0)           # 0.0 to 100.0
    hydraulic_impact_component = Column(Float, default=0.0)       # 0.0 to 100.0
    service_criticality_component = Column(Float, default=0.0)    # 0.0 to 100.0
    recurrence_component = Column(Float, default=0.0)             # 0.0 to 100.0
    confidence_weight = Column(Float, default=1.0)                # 0.0 to 1.0

    weights_version = Column(String(64), default="v1.0.0-multi-criteria-pareto", nullable=False)
    weights_applied_json = Column(Text, default="{}", nullable=False)
    reassessment_counter = Column(Integer, default=0)
    last_ranked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class OperationalImpactAssessmentModel(Base):
    __tablename__ = "operational_impact_assessments"

    id = Column(String(64), primary_key=True, index=True)
    recommendation_id = Column(String(64), nullable=False, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    scenario_id = Column(String(64), nullable=True)

    estimated_water_loss_m3_day = Column(Float, default=0.0)
    is_water_loss_measured = Column(Boolean, default=False)
    service_disruption_risk = Column(String(32), default="LOW")  # NONE, LOW, MODERATE, SEVERE, EXTREME
    affected_nodes_count = Column(Integer, default=0)
    affected_population_estimate = Column(Integer, default=0)

    hydraulic_headloss_delta_m = Column(Float, default=0.0)
    min_pressure_drop_bar = Column(Float, default=0.0)

    estimated_inspection_distance_m = Column(Float, default=0.0)
    estimated_mission_energy_pct = Column(Float, default=0.0)
    estimated_inspection_duration_min = Column(Float, default=0.0)

    cost_impact_display = Column(String(64), default="NOT AVAILABLE", nullable=False)
    data_quality_rating = Column(String(32), default="ESTIMATED_SIMULATED")
    assumptions_json = Column(Text, default="{}", nullable=False)
    uncertainty_margin_pct = Column(Float, default=15.0)

    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class OperationalEvidenceReferenceModel(Base):
    __tablename__ = "operational_evidence_references"

    id = Column(String(64), primary_key=True, index=True)
    recommendation_id = Column(String(64), nullable=False, index=True)
    evidence_type = Column(String(64), nullable=False, index=True)
    # ACOUSTIC_ANOMALY, PRESSURE_DROP, FLOW_IMBALANCE, MOISTURE_READING,
    # VULNERABILITY_PROFILE, CLUSTER_PROXIMITY, HISTORICAL_TREND, HYDRAULIC_DEFICIT, ROVER_TELEMETRY

    source_module = Column(String(64), nullable=False)
    # TASK_07_AI, TASK_09_PREDICTIVE, TASK_10_DIGITAL_TWIN, TASK_11_GEOSPATIAL, TASK_05_ROVER
    source_table = Column(String(64), nullable=False)
    source_record_id = Column(String(64), nullable=False, index=True)

    metric_name = Column(String(64), nullable=False)
    metric_value = Column(Float, nullable=True)
    metric_unit = Column(String(32), default="")
    confidence_score = Column(Float, default=0.85)
    evidence_summary = Column(String(256), nullable=False)
    payload_json = Column(Text, nullable=True)

    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class OperationalExecutionRecordModel(Base):
    __tablename__ = "operational_execution_records"

    id = Column(String(64), primary_key=True, index=True)
    recommendation_id = Column(String(64), nullable=False, index=True)
    decision_id = Column(String(64), nullable=True)
    mission_id = Column(String(64), nullable=True, index=True)
    assigned_rover_id = Column(String(64), nullable=True, index=True)

    execution_stage = Column(String(32), default="DISPATCH_PREPARED", index=True)
    # DISPATCH_PREPARED, TRANSIT_TO_TARGET, INSPECTING, MISSION_COMPLETED, MISSION_ABORTED, ACTION_FAILED

    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    distance_inspected_m = Column(Float, default=0.0)
    energy_consumed_pct = Column(Float, default=0.0)
    findings_summary = Column(Text, nullable=True)
    leak_confirmed = Column(Boolean, nullable=True)
    telemetry_log_id = Column(String(64), nullable=True)

    last_updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class OperationalPerformanceSnapshotModel(Base):
    __tablename__ = "operational_performance_snapshots"

    id = Column(String(64), primary_key=True, index=True)
    snapshot_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    active_recommendations_count = Column(Integer, default=0)
    approved_pending_execution_count = Column(Integer, default=0)
    in_progress_missions_count = Column(Integer, default=0)
    completed_inspections_count = Column(Integer, default=0)
    rejected_recommendations_count = Column(Integer, default=0)

    average_decision_latency_seconds = Column(Float, default=0.0)
    network_average_vulnerability = Column(Float, default=0.0)
    active_hotspots_count = Column(Integer, default=0)
    available_rovers_count = Column(Integer, default=0)
    fleet_readiness_pct = Column(Float, default=0.0)

    metrics_bundle_json = Column(Text, default="{}", nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)

