"""
SQLAlchemy Mission Persistent Model
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, Text
from datetime import datetime, timezone

from app.database.session import Base


class MissionModel(Base):
    __tablename__ = "missions"

    id = Column(String(64), primary_key=True, index=True)
    assigned_rover_id = Column(String(64), nullable=True, index=True)
    assigned_rover_name = Column(String(128), default="")
    mission_type = Column(String(128), nullable=False)
    progress_percentage = Column(Integer, default=0)
    status = Column(String(32), default="Scheduled", index=True)
    start_time = Column(String(128), default="")
    estimated_completion_time = Column(String(128), default="")
    target_segment_id = Column(String(64), nullable=False, index=True)
    waypoint_count = Column(Integer, default=10)
    completed_waypoints = Column(Integer, default=0)

    # Task 08 Autonomous Dispatch Extensions
    recommendation_id = Column(String(64), nullable=True, index=True)
    source_detection_id = Column(String(64), nullable=True, index=True)
    priority_category = Column(String(32), default="MEDIUM")
    route_distance_m = Column(Float, default=1000.0)
    inspected_distance_m = Column(Float, default=0.0)
    route_waypoints_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)

