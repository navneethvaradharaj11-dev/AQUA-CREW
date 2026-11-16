"""
SQLAlchemy Sensor Reading Persistent Model
Records multi-modal readings across pipeline networks and mobile rovers.
"""
from sqlalchemy import Column, String, Float, Boolean, DateTime
from datetime import datetime, timezone

from app.database.session import Base


class SensorReadingModel(Base):
    __tablename__ = "sensor_readings"

    id = Column(String(64), primary_key=True, index=True)
    sensor_id = Column(String(64), nullable=False, index=True)
    sensor_type = Column(String(32), nullable=False, index=True)  # acoustic, pressure, flow, ground_moisture, temperature, rover_acoustic
    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    
    measurement_value = Column(Float, nullable=False)
    measurement_unit = Column(String(16), nullable=False)
    sampling_rate_hz = Column(Float, nullable=True, default=1.0)
    quality_indicator = Column(String(32), default="EXCELLENT", nullable=False)  # EXCELLENT, GOOD, DEGRADED, FAULT
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    source = Column(String(64), default="VIRTUAL_SIMULATION_ENGINE", nullable=False)
