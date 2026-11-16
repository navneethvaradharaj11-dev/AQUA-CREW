"""
AQUA CREW — Pydantic Schemas for IoT Device Ecosystem & Hardware Gateway (Task 18)
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ---------------------------------------------------------
# Device Schemas
# ---------------------------------------------------------
class SensorSchema(BaseModel):
    id: str
    sensor_type: str
    measurement_unit: str
    min_range: float = 0.0
    max_range: float = 100.0
    accuracy_tolerance: float = 0.05
    sampling_rate_hz: float = 1.0
    is_active: bool = True
    latest_reading_value: Optional[float] = None
    latest_reading_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class SensorCalibrationSchema(BaseModel):
    id: str
    sensor_id: str
    calibration_date: Optional[datetime] = None
    next_due_date: datetime
    calibration_method: str
    calibration_reference: str
    calibration_result: str
    accuracy_tolerance: float
    technician: str
    certificate_reference: str
    calibration_status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class DeviceCreateRequest(BaseModel):
    id: str = Field(..., description="Unique Device ID (e.g. DEV-ACOUSTIC-10)")
    name: str = Field(..., description="Human-readable device name")
    device_type: str = Field(..., description="Device category (e.g. ACOUSTIC_LEAK_SENSOR, PRESSURE_SENSOR)")
    manufacturer: str = Field(default="AQUA CREW Lab")
    hardware_model: str = Field(default="ESP32-S3-WROOM")
    firmware_version: str = Field(default="v1.4.0-sim")
    hardware_revision: str = Field(default="revB.0")
    installation_location: str = Field(default="")
    pipeline_segment_id: Optional[str] = Field(default=None)
    dma_zone: str = Field(default="DMA-METRO-CENTRAL")
    latitude: float = Field(default=40.7128)
    longitude: float = Field(default=-74.0060)
    elevation_m: float = Field(default=12.0)
    supported_sensor_types: List[str] = Field(default_factory=list)
    communication_protocol: str = Field(default="MQTT")
    is_simulated: bool = Field(default=True)


class DeviceUpdateRequest(BaseModel):
    name: Optional[str] = None
    installation_location: Optional[str] = None
    pipeline_segment_id: Optional[str] = None
    dma_zone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_m: Optional[float] = None
    firmware_version: Optional[str] = None
    status: Optional[str] = None


class DeviceResponse(BaseModel):
    id: str
    name: str
    device_type: str
    manufacturer: str
    hardware_model: str
    firmware_version: str
    hardware_revision: str
    installation_location: str
    pipeline_segment_id: Optional[str] = None
    dma_zone: str
    latitude: float
    longitude: float
    elevation_m: float
    supported_sensor_types: List[str] = Field(default_factory=list)
    communication_protocol: str
    status: str
    last_communication_at: Optional[datetime] = None
    calibration_status: str
    auth_status: str
    is_simulated: bool
    owner_id: Optional[str] = None
    created_at: Optional[datetime] = None
    sensors: List[SensorSchema] = Field(default_factory=list)
    calibrations: List[SensorCalibrationSchema] = Field(default_factory=list)

    class Config:
        from_attributes = True


class DeviceRegistrationResponse(BaseModel):
    success: bool = True
    device: DeviceResponse
    api_key: str
    message: str = "Device registered successfully. Store API key safely; it cannot be retrieved again."


class DeviceListResponse(BaseModel):
    success: bool = True
    total: int
    devices: List[DeviceResponse]


# ---------------------------------------------------------
# Telemetry Schemas
# ---------------------------------------------------------
class TelemetryIngestPayload(BaseModel):
    device_id: str
    sensor_id: Optional[str] = None
    sensor_type: str
    value: float
    unit: str
    timestamp: Optional[str] = None
    sequence_number: Optional[int] = 1
    provenance: Optional[str] = "MEASURED"
    firmware_version: Optional[str] = None
    calibration_reference: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BatchTelemetryIngestRequest(BaseModel):
    batch_id: Optional[str] = None
    readings: List[TelemetryIngestPayload]


class DeviceTelemetryResponse(BaseModel):
    id: str
    device_id: str
    sensor_id: str
    sensor_type: str
    measurement_value: float
    unit: str
    sequence_number: int
    timestamp: datetime
    ingested_at: Optional[datetime] = None
    data_quality: str
    provenance: str
    pipeline_segment_id: Optional[str] = None
    is_simulated: bool

    class Config:
        from_attributes = True


class TelemetryListResponse(BaseModel):
    success: bool = True
    total: int
    telemetries: List[DeviceTelemetryResponse]


# ---------------------------------------------------------
# Calibration Schemas
# ---------------------------------------------------------
class RegisterCalibrationRequest(BaseModel):
    sensor_id: str
    device_id: str
    calibration_method: str = "HYDRAULIC_REFERENCE_COMPARISON"
    calibration_reference: str = "STD-REF-FLOW-A109"
    calibration_result: str = "PASS"
    accuracy_tolerance: float = 0.05
    technician: str = "Certified Calibration Metrologist"
    certificate_reference: str = "ISO-17025-CERT"
    next_due_date: datetime
    calibration_date: Optional[datetime] = None
    notes: Optional[str] = ""


class CalibrationListResponse(BaseModel):
    success: bool = True
    total: int
    records: List[SensorCalibrationSchema]


# ---------------------------------------------------------
# Device Command & Actuation Safety Schemas
# ---------------------------------------------------------
class DeviceCommandRequest(BaseModel):
    command: str = Field(..., description="Allowlisted command: READ_STATUS, REQUEST_TELEMETRY, RUN_DEVICE_DIAGNOSTICS, etc.")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DeviceCommandResponse(BaseModel):
    success: bool
    device_id: str
    command: str
    status: str
    result: Dict[str, Any]
    safety_state: str = "HARDWARE_ACTUATION_DISABLED"


# ---------------------------------------------------------
# Status & Overview Schemas
# ---------------------------------------------------------
class IoTStatusOverviewResponse(BaseModel):
    success: bool = True
    metrics: Dict[str, Any]
    mqtt_status: Dict[str, Any]
    hardware_safety: str = "SIMULATION_FIRST_MODE_ACTIVE"
    timestamp: str

