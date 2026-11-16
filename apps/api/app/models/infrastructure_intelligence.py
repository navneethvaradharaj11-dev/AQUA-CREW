"""
SQLAlchemy Models for Infrastructure Intelligence & Geospatial Risk Prediction (Task 11)
Persists pipeline vulnerability profiles, spatial incident clusters, geographic risk zones,
temporal deterioration trends, predictive risk forecasts, and prioritized inspection queues.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text
from datetime import datetime, timezone
import uuid

from app.database.session import Base


class PipelineVulnerabilityProfileModel(Base):
    __tablename__ = "pipeline_vulnerability_profiles"

    id = Column(String(64), primary_key=True, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, unique=True, index=True)
    segment_name = Column(String(256), nullable=False)
    material = Column(String(128), default="")
    diameter_mm = Column(Integer, default=300)
    length_m = Column(Float, default=1000.0)
    pressure_zone_id = Column(String(64), default="PZ-01", index=True)
    category = Column(String(64), default="TRANSMISSION_MAIN")

    # Overall Vulnerability (0.0 to 100.0)
    vulnerability_score = Column(Float, nullable=False, index=True)
    vulnerability_level = Column(String(32), nullable=False, index=True)  # VERY_LOW, LOW, MODERATE, HIGH, CRITICAL

    # Explainable Component Scores (0.0 to 100.0 each)
    hydraulic_score = Column(Float, default=0.0)      # 30% weight
    structural_score = Column(Float, default=0.0)     # 25% weight
    incident_score = Column(Float, default=0.0)       # 25% weight
    environmental_score = Column(Float, default=0.0)  # 20% weight

    # Contributing factors breakdown and metrics
    contributing_factors = Column(Text, nullable=True)  # JSON-encoded dictionary of factors and weights
    confidence = Column(Float, default=0.85)            # 0.0 to 1.0
    data_completeness_pct = Column(Float, default=90.0) # 0.0 to 100.0
    uncertainty_margin = Column(Float, default=5.0)     # score points +/-

    # Temporal & Deterioration
    deterioration_rate_per_day = Column(Float, default=0.0)
    trend_direction = Column(String(32), default="STABLE", index=True)  # DETERIORATING, STABLE, IMPROVING
    active_incident_count = Column(Integer, default=0)
    last_inspection_date = Column(DateTime(timezone=True), nullable=True)

    # Coordinates cache for geospatial operations (midpoint lat, lng)
    midpoint_lat = Column(Float, nullable=True)
    midpoint_lng = Column(Float, nullable=True)

    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class InfrastructureRiskAssessmentModel(Base):
    __tablename__ = "infrastructure_risk_assessments"

    id = Column(String(64), primary_key=True, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    vulnerability_score = Column(Float, nullable=False)
    risk_level = Column(String(32), nullable=False, index=True)
    risk_category = Column(String(64), default="STRUCTURAL_FATIGUE")

    # Multi-horizon risk projections (score 0.0 to 100.0)
    projected_risk_24h = Column(Float, default=0.0)
    projected_risk_7d = Column(Float, default=0.0)
    projected_risk_30d = Column(Float, default=0.0)

    # Temporal deltas
    trend_24h_delta = Column(Float, default=0.0)
    trend_7d_delta = Column(Float, default=0.0)
    trend_30d_delta = Column(Float, default=0.0)

    risk_drivers = Column(Text, nullable=True)  # JSON-encoded list of primary drivers
    mitigation_urgency = Column(String(32), default="PLANNED", index=True)  # IMMEDIATE, SHORT_TERM, PLANNED, ROUTINE
    hydraulic_deficit_flag = Column(Boolean, default=False)
    cluster_proximity_m = Column(Float, default=9999.0)

    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class SpatialIncidentClusterModel(Base):
    __tablename__ = "spatial_incident_clusters"

    id = Column(String(64), primary_key=True, index=True)
    cluster_name = Column(String(128), nullable=False)
    zone_id = Column(String(64), default="ZONE-CENTRAL", index=True)
    centroid_lat = Column(Float, nullable=False)
    centroid_lng = Column(Float, nullable=False)
    radius_m = Column(Float, default=250.0)
    incident_count = Column(Integer, default=1)
    dominant_material = Column(String(128), default="Cast Iron")
    average_severity = Column(Float, default=0.5)
    cluster_risk_level = Column(String(32), default="HIGH", index=True)  # LOW, MODERATE, HIGH, CRITICAL

    affected_segment_ids = Column(Text, nullable=False)  # JSON-encoded list of segment IDs
    hotspot_intensity = Column(Float, default=0.5)       # 0.0 to 1.0 (density / severity factor)
    is_active = Column(Boolean, default=True, index=True)
    identified_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class GeographicRiskZoneModel(Base):
    __tablename__ = "geographic_risk_zones"

    id = Column(String(64), primary_key=True, index=True)
    zone_code = Column(String(32), nullable=False, unique=True, index=True)
    zone_name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)

    total_segments = Column(Integer, default=0)
    total_length_km = Column(Float, default=0.0)
    avg_vulnerability_score = Column(Float, default=0.0)
    dominant_risk_level = Column(String(32), default="MODERATE", index=True)
    critical_segment_count = Column(Integer, default=0)
    active_clusters_count = Column(Integer, default=0)
    avg_pressure_psi = Column(Float, default=60.0)

    bounds_json = Column(Text, nullable=True)  # GeoJSON bounding polygon or bbox
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class InspectionPriorityRecordModel(Base):
    __tablename__ = "inspection_priority_records"

    id = Column(String(64), primary_key=True, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    segment_name = Column(String(256), nullable=False)

    priority_score = Column(Float, nullable=False, index=True)  # 0.0 to 100.0
    priority_level = Column(String(32), nullable=False, index=True)  # CRITICAL_IMMEDIATE, HIGH_PRIORITY, ROUTINE_SCHEDULED, MONITORING_ONLY
    status = Column(String(32), default="PENDING", index=True)       # PENDING, ACKNOWLEDGED, DISPATCHED, DISMISSED

    target_latitude = Column(Float, nullable=False)
    target_longitude = Column(Float, nullable=False)
    reasons = Column(Text, nullable=True)            # JSON list of justification strings
    suggested_action = Column(String(256), default="Acoustic and pressure inspection with crawler rover")

    assigned_rover_id = Column(String(64), nullable=True, index=True)
    mission_recommendation_id = Column(String(64), nullable=True, index=True)
    reviewed_by = Column(String(128), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    operator_notes = Column(Text, nullable=True)
    dismissal_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)


class InfrastructureIntelligenceSnapshotModel(Base):
    __tablename__ = "infrastructure_intelligence_snapshots"

    id = Column(String(64), primary_key=True, index=True)
    total_segments_analyzed = Column(Integer, default=0)
    critical_segments_count = Column(Integer, default=0)
    high_risk_segments_count = Column(Integer, default=0)
    moderate_risk_segments_count = Column(Integer, default=0)
    low_risk_segments_count = Column(Integer, default=0)
    average_network_vulnerability = Column(Float, default=0.0)
    active_clusters_count = Column(Integer, default=0)
    pending_inspections_count = Column(Integer, default=0)
    network_deterioration_rate = Column(Float, default=0.0)

    summary_json = Column(Text, nullable=True)  # JSON-encoded metrics snapshot
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)

