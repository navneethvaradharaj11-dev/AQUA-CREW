"""
Pydantic Schemas for Telemetry Streaming and Historical Records
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class TelemetryHistoryItem(BaseModel):
    id: int
    rover_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    velocity_mps: float
    heading_deg: float
    battery_pct: float
    motor_temp_c: float
    internal_temp_c: float
    signal_rssi_dbm: float
    acoustic_spl_db: float
    operating_state: str
    pipe_segment_id: str
    is_simulated: bool = True


class TelemetryHistoryResponse(BaseModel):
    success: bool = True
    rover_id: Optional[str] = None
    count: int
    page: int
    page_size: int
    records: List[TelemetryHistoryItem]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TelemetryHealthSummary(BaseModel):
    active_rovers: int
    total_rovers: int
    average_battery_pct: float
    signal_health_pct: float
    temperature_alerts: int
    is_simulated: bool = True
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
