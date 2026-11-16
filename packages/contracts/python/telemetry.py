"""
Rover & Sensor Telemetry Schemas
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class GeoCoordinates(BaseModel):
    latitude: float
    longitude: float
    elevation_m: Optional[float] = None
    pipe_segment_id: Optional[str] = None
    pipe_distance_m: Optional[float] = None


class RoverKinematics(BaseModel):
    velocity_mps: float
    heading_deg: float
    pitch_deg: Optional[float] = None
    roll_deg: Optional[float] = None


class RoverDiagnostics(BaseModel):
    battery_soc_pct: float = Field(ge=0.0, le=100.0)
    internal_temp_c: float
    motor_current_amps: float
    signal_rssi_dbm: float


class RoverSensorPayload(BaseModel):
    acoustic_spl_db: float
    acoustic_dominant_freq_hz: float
    ground_moisture_pct: Optional[float] = None
    ambient_temperature_c: Optional[float] = None


class RoverTelemetryPacket(BaseModel):
    device_id: str
    device_type: Literal["autonomous_ground_rover", "in_pipe_crawler", "aerial_survey_drone"]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["idle", "surveying", "returning", "maintenance", "error"]
    location: GeoCoordinates
    kinematics: RoverKinematics
    diagnostics: RoverDiagnostics
    payload_sensors: RoverSensorPayload


class StationarySensorReading(BaseModel):
    sensor_id: str
    pipe_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pressure_psi: float
    flow_rate_lpm: float
    acoustic_noise_level_db: float
    battery_voltage_v: float


class LeakDetectionAlert(BaseModel):
    alert_id: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pipe_segment_id: str
    latitude: float
    longitude: float
    severity: Literal["low", "medium", "high", "critical"]
    confidence_score: float = Field(ge=0.0, le=1.0)
    estimated_loss_rate_lpm: float
    acoustic_signature_peak_hz: float
    status: Literal["suspected", "investigating", "confirmed", "repaired"]

