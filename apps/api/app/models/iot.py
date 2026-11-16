"""
AQUA CREW — Persistent IoT & Hardware Device Ecosystem Models (Task 18)
Defines schema for:
  - IoTDeviceModel
  - DeviceCredentialMetadataModel
  - SensorModel
  - SensorCalibrationModel
  - DeviceTelemetryModel
  - DeviceEventModel
  - DeviceConnectionModel
  - DeviceAuditLogModel
  - TelemetryProcessingResultModel
"""
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database.session import Base


class IoTDeviceModel(Base):
    __tablename__ = "iot_devices"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    device_type = Column(String(64), nullable=False, index=True)
    # ACOUSTIC_LEAK_SENSOR, PRESSURE_SENSOR, FLOW_METER, MOISTURE_SENSOR,
    # TEMPERATURE_SENSOR, OPTICAL_INSPECTION_SENSOR, ENVIRONMENTAL_MONITOR, VIRTUAL_SIMULATION_DEVICE

    manufacturer = Column(String(128), default="AQUA CREW Lab / Nordic")
    hardware_model = Column(String(64), default="ESP32-S3-WROOM")
    firmware_version = Column(String(32), default="v1.4.0-sim")
    hardware_revision = Column(String(32), default="revB.2")

    installation_location = Column(String(255), default="")
    pipeline_segment_id = Column(String(64), nullable=True, index=True)
    dma_zone = Column(String(64), default="DMA-METRO-CENTRAL", index=True)

    latitude = Column(Float, nullable=False, default=40.7128)
    longitude = Column(Float, nullable=False, default=-74.0060)
    elevation_m = Column(Float, default=12.5)

    supported_sensor_types = Column(JSON, default=list)  # ["acoustic", "temperature"]
    communication_protocol = Column(String(32), default="MQTT")  # MQTT, HTTP_REST, MODBUS_SIM, SIMULATED

    # Lifecycle state: REGISTERED, PROVISIONING, ACTIVE, DEGRADED, OFFLINE, MAINTENANCE, REVOKED, QUARANTINED
    status = Column(String(32), default="REGISTERED", index=True)
    last_communication_at = Column(DateTime(timezone=True), nullable=True)

    # Calibration: CALIBRATED, DUE, OVERDUE, UNCALIBRATED, FAILED
    calibration_status = Column(String(32), default="CALIBRATED", index=True)
    calibration_metadata = Column(JSON, default=dict)

    maintenance_history = Column(JSON, default=list)

    # Auth: AUTHENTICATED, UNAUTHENTICATED, REVOKED, QUARANTINED
    auth_status = Column(String(32), default="AUTHENTICATED", index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)
    owner_id = Column(String(64), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    credentials = relationship("DeviceCredentialMetadataModel", back_populates="device", cascade="all, delete-orphan")
    sensors = relationship("SensorModel", back_populates="device", cascade="all, delete-orphan")
    calibrations = relationship("SensorCalibrationModel", back_populates="device", cascade="all, delete-orphan")
    telemetries = relationship("DeviceTelemetryModel", back_populates="device", cascade="all, delete-orphan")
    events = relationship("DeviceEventModel", back_populates="device", cascade="all, delete-orphan")
    connections = relationship("DeviceConnectionModel", back_populates="device", cascade="all, delete-orphan")


class DeviceCredentialMetadataModel(Base):
    __tablename__ = "device_credentials"

    id = Column(String(64), primary_key=True, index=True)
    device_id = Column(String(64), ForeignKey("iot_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    credential_type = Column(String(32), default="API_KEY")  # API_KEY, TOKEN_HMAC, MTLS_CERT_FINGERPRINT
    key_prefix = Column(String(32), nullable=False)
    hashed_secret = Column(String(255), nullable=False)
    allowed_topics = Column(JSON, default=list)

    revoked = Column(Boolean, default=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(String(255), nullable=True)

    last_rotated_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    device = relationship("IoTDeviceModel", back_populates="credentials")


class SensorModel(Base):
    __tablename__ = "sensors"

    id = Column(String(64), primary_key=True, index=True)
    device_id = Column(String(64), ForeignKey("iot_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    sensor_type = Column(String(32), nullable=False, index=True)  # acoustic, pressure, flow, moisture, temperature, optical
    measurement_unit = Column(String(16), nullable=False)  # dB, bar, L/s, %, °C, metadata
    min_range = Column(Float, default=0.0)
    max_range = Column(Float, default=100.0)
    accuracy_tolerance = Column(Float, default=0.05)
    sampling_rate_hz = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True, index=True)

    latest_reading_value = Column(Float, nullable=True)
    latest_reading_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    device = relationship("IoTDeviceModel", back_populates="sensors")


class SensorCalibrationModel(Base):
    __tablename__ = "sensor_calibrations"

    id = Column(String(64), primary_key=True, index=True)
    sensor_id = Column(String(64), nullable=False, index=True)
    device_id = Column(String(64), ForeignKey("iot_devices.id", ondelete="CASCADE"), nullable=False, index=True)

    calibration_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_calibration_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    next_due_date = Column(DateTime(timezone=True), nullable=False, index=True)

    calibration_method = Column(String(64), default="HYDRAULIC_REFERENCE_COMPARISON")
    calibration_reference = Column(String(128), default="STD-REF-FLOW-A109")
    calibration_result = Column(String(32), default="PASS")  # PASS, ADJUSTED_PASS, FAIL, OUT_OF_TOLERANCE
    accuracy_tolerance = Column(Float, default=0.05)
    technician = Column(String(128), default="Chief Hydraulic Calibration Technician")
    certificate_reference = Column(String(128), default="ISO-17025-AQUA-8819")

    # CALIBRATED, DUE, OVERDUE, UNCALIBRATED, FAILED
    calibration_status = Column(String(32), default="CALIBRATED", index=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    device = relationship("IoTDeviceModel", back_populates="calibrations")


class DeviceTelemetryModel(Base):
    __tablename__ = "device_telemetries"

    id = Column(String(64), primary_key=True, index=True)
    device_id = Column(String(64), ForeignKey("iot_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    sensor_id = Column(String(64), nullable=False, index=True)
    sensor_type = Column(String(32), nullable=False, index=True)

    measurement_value = Column(Float, nullable=False)
    unit = Column(String(16), nullable=False)
    raw_payload = Column(JSON, nullable=True)

    sequence_number = Column(Integer, default=1, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    ingested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    # VALID, SUSPECT, STALE, INVALID, DUPLICATE, MISSING, UNCALIBRATED
    data_quality = Column(String(32), default="VALID", index=True)
    # MEASURED, SIMULATED, DERIVED, PREDICTED, OPERATOR_ENTERED, UNKNOWN
    provenance = Column(String(32), default="MEASURED", index=True)

    firmware_version = Column(String(32), default="")
    calibration_reference = Column(String(128), default="")
    pipeline_segment_id = Column(String(64), default="", index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)

    device = relationship("IoTDeviceModel", back_populates="telemetries")


class DeviceEventModel(Base):
    __tablename__ = "device_events"

    id = Column(String(64), primary_key=True, index=True)
    device_id = Column(String(64), ForeignKey("iot_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    # STATUS_CHANGE, THRESHOLD_ALERT, DISCONNECTION, RECONNECTION, BATTERY_LOW, FIRMWARE_UPDATE, TAMPER_DETECT
    severity = Column(String(16), default="INFO")  # INFO, WARNING, CRITICAL
    description = Column(String(255), nullable=False)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    device = relationship("IoTDeviceModel", back_populates="events")


class DeviceConnectionModel(Base):
    __tablename__ = "device_connections"

    id = Column(String(64), primary_key=True, index=True)
    device_id = Column(String(64), ForeignKey("iot_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    protocol = Column(String(32), default="MQTT")
    ip_address = Column(String(45), default="127.0.0.1")
    connected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    disconnected_at = Column(DateTime(timezone=True), nullable=True)
    messages_received = Column(Integer, default=0)
    messages_sent = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)
    status = Column(String(32), default="CONNECTED", index=True)  # CONNECTED, DISCONNECTED, DROPPED
    disconnect_reason = Column(String(255), nullable=True)

    device = relationship("IoTDeviceModel", back_populates="connections")


class DeviceAuditLogModel(Base):
    __tablename__ = "device_audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    device_id = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)
    # REGISTRATION, AUTHENTICATION, FAILED_AUTHENTICATION, CREDENTIAL_ROTATION,
    # CREDENTIAL_REVOCATION, QUARANTINE, CONFIGURATION_CHANGE, ACTUATION_COMMAND_REJECTED
    actor = Column(String(128), default="system")
    status = Column(String(32), default="SUCCESS")  # SUCCESS, DENIED, FAILURE
    ip_address = Column(String(45), default="127.0.0.1")
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class TelemetryProcessingResultModel(Base):
    __tablename__ = "telemetry_processing_results"

    id = Column(String(64), primary_key=True, index=True)
    batch_id = Column(String(64), default="")
    device_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), default="ACCEPTED", index=True)  # ACCEPTED, REJECTED, FLAGGED
    rejection_reason = Column(String(255), nullable=True)
    processing_latency_ms = Column(Float, default=0.0)
    routed_to_ai_leak = Column(Boolean, default=False)
    routed_to_digital_twin = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

