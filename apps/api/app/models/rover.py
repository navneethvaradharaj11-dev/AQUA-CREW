"""
SQLAlchemy Rover Persistent Model
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from datetime import datetime, timezone

from app.database.session import Base


class RoverModel(Base):
    __tablename__ = "rovers"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    model = Column(String(128), nullable=False)
    status = Column(String(32), default="ONLINE", index=True)
    operating_state = Column(String(32), default="IDLE", index=True)
    connection_status = Column(String(32), default="ONLINE")
    battery_percentage = Column(Float, default=100.0)
    distance_travelled_km = Column(Float, default=0.0)
    current_mission = Column(String(256), default="")
    assigned_mission_id = Column(String(64), nullable=True, index=True)

    # Location & Kinematics
    station_name = Column(String(256), default="")
    pipe_segment_id = Column(String(64), default="", index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    velocity_mps = Column(Float, default=0.0)
    heading_deg = Column(Float, default=0.0)
    target_speed_mps = Column(Float, default=0.0)
    route_progress_pct = Column(Integer, default=0)

    # Diagnostics
    internal_temp_c = Column(Float, default=25.0)
    motor_temp_c = Column(Float, default=25.0)
    motor_current_amps = Column(Float, default=0.0)
    signal_rssi_dbm = Column(Float, default=-65.0)

    # Payload Sensors
    acoustic_spl_db = Column(Float, default=40.0)
    dominant_freq_hz = Column(Float, default=500.0)
    ground_moisture_pct = Column(Float, default=15.0)

    last_heartbeat = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)

