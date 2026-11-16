"""
SQLAlchemy Telemetry Record Historical Model
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from datetime import datetime, timezone

from app.database.session import Base


class TelemetryRecordModel(Base):
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rover_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    velocity_mps = Column(Float, default=0.0)
    heading_deg = Column(Float, default=0.0)
    battery_pct = Column(Float, default=100.0)
    motor_temp_c = Column(Float, default=25.0)
    internal_temp_c = Column(Float, default=25.0)
    motor_current_amps = Column(Float, default=0.0)
    signal_rssi_dbm = Column(Float, default=-65.0)
    acoustic_spl_db = Column(Float, default=40.0)
    dominant_freq_hz = Column(Float, default=500.0)
    ground_moisture_pct = Column(Float, default=15.0)
    operating_state = Column(String(32), default="IDLE")
    pipe_segment_id = Column(String(64), default="")

    is_simulated = Column(Boolean, default=True, nullable=False)

