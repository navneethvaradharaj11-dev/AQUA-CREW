"""
SQLAlchemy Mission Recommendation Persistent Model
Represents explainable rover dispatch recommendations pending human operator approval.
"""
from sqlalchemy import Column, String, Float, Integer, Text, Boolean, DateTime
from datetime import datetime, timezone

from app.database.session import Base


class MissionRecommendationModel(Base):
    __tablename__ = "mission_recommendations"

    id = Column(String(64), primary_key=True, index=True)
    detection_id = Column(String(64), nullable=False, index=True)
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    recommended_rover_id = Column(String(64), nullable=False, index=True)
    recommended_rover_name = Column(String(128), default="")
    priority_score = Column(Float, default=50.0)
    priority_category = Column(String(32), default="MEDIUM", index=True)
    status = Column(String(32), default="PENDING_APPROVAL", index=True)
    rejection_reason = Column(String(256), nullable=True)

    # Route & Trajectory
    route_distance_m = Column(Float, default=0.0)
    estimated_duration_s = Column(Float, default=0.0)
    estimated_energy_pct = Column(Float, default=0.0)
    battery_reserve_after_pct = Column(Float, default=0.0)
    destination_lat = Column(Float, nullable=True)
    destination_lng = Column(Float, nullable=True)
    localization_uncertainty_m = Column(Float, nullable=True)

    # Serialized JSON structures
    route_waypoints_json = Column(Text, nullable=False)
    route_segments_json = Column(Text, nullable=True)
    contributing_factors = Column(Text, nullable=True)
    explanation = Column(Text, default="")

    # Assignment Tracking
    assigned_mission_id = Column(String(64), nullable=True, index=True)
    operator_notes = Column(Text, nullable=True)
    approved_by = Column(String(128), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(128), default="VIRTUAL_SIMULATION_ENGINE")

