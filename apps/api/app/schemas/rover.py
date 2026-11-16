"""
Pydantic Schemas for Rover Fleet & Commands
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone


class RoverLocation(BaseModel):
    station_name: str = Field(alias="stationName", default="")
    pipe_segment_id: str = Field(alias="pipeSegmentId", default="")
    latitude: float
    longitude: float
    route_progress_pct: Optional[int] = Field(alias="routeProgressPct", default=0)

    model_config = {"populate_by_name": True}


class RoverKinematics(BaseModel):
    velocity_mps: float = Field(alias="velocityMps", default=0.0)
    heading_deg: float = Field(alias="headingDeg", default=0.0)
    target_speed_mps: Optional[float] = Field(alias="targetSpeedMps", default=0.0)

    model_config = {"populate_by_name": True}


class RoverDiagnostics(BaseModel):
    internal_temp_c: float = Field(alias="internalTempC", default=25.0)
    motor_temp_c: float = Field(alias="motorTempC", default=25.0)
    motor_current_amps: float = Field(alias="motorCurrentAmps", default=0.0)
    signal_rssi_dbm: float = Field(alias="signalRssiDbm", default=-65.0)

    model_config = {"populate_by_name": True}


class RoverPayloadSensors(BaseModel):
    acoustic_spl_db: float = Field(alias="acousticSplDb", default=40.0)
    dominant_freq_hz: float = Field(alias="dominantFreqHz", default=500.0)
    ground_moisture_pct: float = Field(alias="groundMoisturePct", default=15.0)

    model_config = {"populate_by_name": True}


class RoverResponse(BaseModel):
    is_simulated: bool = Field(alias="isSimulated", default=True)
    source: str = "VIRTUAL_SIMULATION_ENGINE"
    simulated_at: datetime = Field(alias="simulatedAt")
    id: str
    name: str
    model: str
    status: str
    operating_state: str = Field(alias="operatingState")
    connection_status: str = Field(alias="connectionStatus")
    battery_percentage: float = Field(alias="batteryPercentage")
    distance_travelled_km: float = Field(alias="distanceTravelledKm")
    current_mission: str = Field(alias="currentMission")
    assigned_mission_id: Optional[str] = Field(alias="assignedMissionId", default=None)
    current_location: RoverLocation = Field(alias="currentLocation")
    last_communication: str = Field(alias="lastCommunication", default="1s ago")
    last_heartbeat_timestamp: datetime = Field(alias="lastHeartbeatTimestamp")
    kinematics: RoverKinematics
    diagnostics: RoverDiagnostics
    payload_sensors: RoverPayloadSensors = Field(alias="payloadSensors")

    model_config = {"populate_by_name": True}


class RoverListResponse(BaseModel):
    success: bool = True
    total: int
    rovers: List[RoverResponse]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RoverCommandRequest(BaseModel):
    command: str = Field(..., description="Command action: PAUSE, RESUME, RETURN_BASE, EMERGENCY_STOP, RESET_ESTOP, SET_STATE")
    target_state: Optional[str] = Field(None, description="Target state if command is SET_STATE")
    reason: str = Field(default="Operator command dispatched via REST API")
    triggered_by: str = Field(default="OPERATOR")


class RoverCommandResponse(BaseModel):
    success: bool
    rover_id: str
    previous_state: str
    new_state: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
