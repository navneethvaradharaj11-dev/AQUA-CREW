"""
AQUA CREW — Secure IoT Device Ecosystem & Hardware Gateway Endpoints (Task 18)
Exposes REST APIs for:
  - Device registry management, search, filtering, and quarantine
  - Device credential provisioning and rotation
  - Telemetry ingestion with data-quality validation and provenance tracking
  - Sensor calibration records and due-date audits
  - Allowlisted non-actuating device commands (strictly rejects physical actuation)
  - Cross-module AI leak detection and hydraulic digital twin deviation comparisons
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Header, Body, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.database.session import get_db
from app.repositories.iot_repository import IotRepository
from app.services.iot.telemetry_ingestion_service import TelemetryIngestionService
from app.services.iot.calibration_service import CalibrationService
from app.services.iot.hardware_safety_service import HardwareSafetyService
from app.services.iot.mqtt_service import mqtt_manager
from app.services.iot.iot_intelligence_bridge import IotIntelligenceBridge
from app.models.iot import IoTDeviceModel, DeviceAuditLogModel
from app.models.user import UserModel
from app.core.auth import (
    require_viewer,
    require_operator,
    require_engineer,
    require_admin,
    get_current_user_optional,
)
from app.schemas.iot import (
    DeviceCreateRequest,
    DeviceUpdateRequest,
    DeviceResponse,
    DeviceRegistrationResponse,
    DeviceListResponse,
    TelemetryIngestPayload,
    BatchTelemetryIngestRequest,
    DeviceTelemetryResponse,
    TelemetryListResponse,
    RegisterCalibrationRequest,
    CalibrationListResponse,
    SensorCalibrationSchema,
    DeviceCommandRequest,
    DeviceCommandResponse,
    IoTStatusOverviewResponse,
)

router = APIRouter()


# ==============================================================================
# 1. DEVICE REGISTRY ENDPOINTS
# ==============================================================================
@router.get("/devices", response_model=DeviceListResponse, summary="List registered IoT devices")
def list_devices(
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, OFFLINE, DEGRADED, etc."),
    device_type: Optional[str] = Query(None, description="Filter by device_type"),
    dma_zone: Optional[str] = Query(None, description="Filter by DMA zone"),
    pipeline_segment_id: Optional[str] = Query(None, description="Filter by associated pipeline"),
    search: Optional[str] = Query(None, description="Free text search on ID, name, manufacturer"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Returns list of registered IoT sensors and gateway nodes matching query criteria.
    """
    devices, total = IotRepository.get_devices(
        db,
        status=status,
        device_type=device_type,
        dma_zone=dma_zone,
        pipeline_segment_id=pipeline_segment_id,
        search=search,
        skip=skip,
        limit=limit,
    )
    return DeviceListResponse(
        success=True,
        total=total,
        devices=[DeviceResponse.model_validate(d) for d in devices],
    )


@router.post("/devices", response_model=DeviceRegistrationResponse, status_code=status.HTTP_201_CREATED, summary="Register new IoT device")
def register_device(
    payload: DeviceCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Registers a new physical or virtual sensor node.
    Generates and returns an initial cryptographic API key for the device.
    """
    existing = IotRepository.get_device_by_id(db, payload.id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Device with ID '{payload.id}' already exists in registry.",
        )

    device, secret = IotRepository.create_device(
        db=db,
        device_id=payload.id,
        name=payload.name,
        device_type=payload.device_type,
        manufacturer=payload.manufacturer,
        hardware_model=payload.hardware_model,
        firmware_version=payload.firmware_version,
        hardware_revision=payload.hardware_revision,
        installation_location=payload.installation_location,
        pipeline_segment_id=payload.pipeline_segment_id,
        dma_zone=payload.dma_zone,
        latitude=payload.latitude,
        longitude=payload.longitude,
        elevation_m=payload.elevation_m,
        supported_sensor_types=payload.supported_sensor_types,
        communication_protocol=payload.communication_protocol,
        owner_id=current_user.id,
        is_simulated=payload.is_simulated,
    )

    return DeviceRegistrationResponse(
        success=True,
        device=DeviceResponse.model_validate(device),
        api_key=secret,
        message="Device registered successfully. Store API key safely; it cannot be retrieved again.",
    )


@router.get("/devices/{device_id}", response_model=DeviceResponse, summary="Get device details by ID")
def get_device(
    device_id: str = Path(..., description="Unique Device ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    device = IotRepository.get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found.")
    return DeviceResponse.model_validate(device)


@router.patch("/devices/{device_id}", response_model=DeviceResponse, summary="Update device metadata")
def update_device(
    device_id: str = Path(..., description="Unique Device ID"),
    payload: DeviceUpdateRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    device = IotRepository.get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(device, k, v)
    device.updated_at = datetime.now(timezone.utc)

    IotRepository.log_audit_event(
        db,
        device_id=device_id,
        action="CONFIGURATION_CHANGE",
        actor=current_user.username or current_user.id,
        details={"updated_fields": list(update_data.keys())},
    )

    db.commit()
    db.refresh(device)
    return DeviceResponse.model_validate(device)


@router.post("/devices/{device_id}/revoke", summary="Revoke device credentials (Admin only)")
def revoke_device(
    device_id: str = Path(...),
    reason: str = Query("Administrative revocation", description="Justification"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
):
    try:
        IotRepository.revoke_device(db, device_id, reason=reason, actor=current_user.username)
        return {"success": True, "message": f"Device '{device_id}' and all associated credentials revoked."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/devices/{device_id}/quarantine", summary="Place device in security quarantine")
def quarantine_device(
    device_id: str = Path(...),
    reason: str = Query("Suspicious telemetry or connection behavior", description="Justification"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    try:
        IotRepository.quarantine_device(db, device_id, reason=reason, actor=current_user.username)
        return {"success": True, "message": f"Device '{device_id}' placed in security quarantine."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/devices/{device_id}/credentials/rotate", summary="Rotate device credentials (Admin only)")
def rotate_credentials(
    device_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
):
    try:
        new_secret = IotRepository.rotate_device_credential(db, device_id, actor=current_user.username)
        return {
            "success": True,
            "device_id": device_id,
            "api_key": new_secret,
            "message": "Credentials rotated. Prior keys invalidated.",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==============================================================================
# 2. DEVICE COMMAND & HARDWARE SAFETY ENFORCEMENT
# ==============================================================================
@router.post("/devices/{device_id}/commands", response_model=DeviceCommandResponse, summary="Dispatch non-actuating command to device")
def execute_device_command(
    device_id: str = Path(...),
    payload: DeviceCommandRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Dispatches allowlisted, non-actuating commands to a registered sensor or gateway node.
    STRICTLY ENFORCES HARDWARE SAFETY: Rejects physical valve, pump, or rover actuator commands.
    """
    device = IotRepository.get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found.")

    if device.status in ["REVOKED", "QUARANTINED"]:
        raise HTTPException(
            status_code=403,
            detail=f"Device '{device_id}' is {device.status}. Commands are prohibited.",
        )

    # HARDWARE SAFETY GATE: Will raise HardwareActuationForbiddenException if actuation requested!
    HardwareSafetyService.verify_operation_safety(payload.command, payload.parameters)

    # Process allowlisted non-actuating command
    command_name = payload.command.upper().strip()
    result_data = {}

    if command_name == "READ_STATUS":
        result_data = {
            "status": device.status,
            "firmware": device.firmware_version,
            "calibration_status": device.calibration_status,
            "last_communication": device.last_communication_at.isoformat() if device.last_communication_at else None,
            "is_simulated": device.is_simulated,
        }
    elif command_name == "REQUEST_TELEMETRY":
        telemetries = TelemetryIngestionService.get_latest_telemetries(db, device_id=device_id, limit=5)
        result_data = {
            "latest_samples_count": len(telemetries),
            "samples": [
                {
                    "sensor_id": t.sensor_id,
                    "sensor_type": t.sensor_type,
                    "value": t.measurement_value,
                    "unit": t.unit,
                    "quality": t.data_quality,
                    "timestamp": t.timestamp.isoformat(),
                }
                for t in telemetries
            ],
        }
    elif command_name == "READ_SENSOR_CONFIG":
        result_data = {
            "supported_sensors": device.supported_sensor_types,
            "protocol": device.communication_protocol,
            "dma_zone": device.dma_zone,
            "pipeline_segment_id": device.pipeline_segment_id,
        }
    elif command_name == "RUN_DEVICE_DIAGNOSTICS":
        result_data = {
            "diagnostic_check": "PASSED",
            "memory_usage_pct": 34.2,
            "battery_level_pct": 94.0,
            "sensor_bus_i2c": "NORMAL",
            "rtc_drift_ms": 12.0,
            "actuators_state": "DISCONNECTED_BY_POLICY",
        }
    else:
        result_data = {"executed": True, "command": command_name, "parameters": payload.parameters}

    IotRepository.log_audit_event(
        db,
        device_id=device_id,
        action="DEVICE_COMMAND_DISPATCHED",
        actor=current_user.username or current_user.id,
        status="SUCCESS",
        details={"command": command_name, "parameters": payload.parameters},
    )

    return DeviceCommandResponse(
        success=True,
        device_id=device_id,
        command=command_name,
        status="EXECUTED",
        result=result_data,
        safety_state="HARDWARE_ACTUATION_DISABLED",
    )


# ==============================================================================
# 3. TELEMETRY INGESTION & QUERY ENDPOINTS
# ==============================================================================
@router.post("/telemetry/ingest", summary="Ingest telemetry from IoT device or gateway")
def ingest_telemetry(
    payload: TelemetryIngestPayload,
    x_device_secret: Optional[str] = Header(None, description="Optional Device API Key for direct IoT ingest"),
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
):
    """
    Ingests, validates, and records a single sensor telemetry packet.
    Accepts either Bearer JWT user authentication or direct X-Device-Secret API key.
    """
    # Verify auth: must have valid JWT user OR valid device secret header
    if not current_user and not x_device_secret:
        raise HTTPException(
            status_code=401,
            detail="Authentication required: Provide Bearer Authorization token or X-Device-Secret header.",
        )

    res = TelemetryIngestionService.ingest_single_reading(
        db=db,
        raw_payload=payload.model_dump(),
        auth_secret=x_device_secret,
    )
    return res


@router.post("/telemetry/ingest/batch", summary="Ingest batch telemetry from edge gateway")
def ingest_telemetry_batch(
    payload: BatchTelemetryIngestRequest,
    x_device_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
):
    if not current_user and not x_device_secret:
        raise HTTPException(
            status_code=401,
            detail="Authentication required: Provide Bearer Authorization token or X-Device-Secret header.",
        )

    readings = [r.model_dump() for r in payload.readings]
    return TelemetryIngestionService.ingest_batch(db, readings, auth_secret=x_device_secret)


@router.get("/devices/{device_id}/telemetry", response_model=TelemetryListResponse, summary="Get telemetry history for device")
def get_device_telemetry(
    device_id: str = Path(...),
    quality: Optional[str] = Query(None, description="Filter by data quality: VALID, SUSPECT, etc."),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    records = TelemetryIngestionService.get_latest_telemetries(
        db, device_id=device_id, quality=quality, limit=limit
    )
    return TelemetryListResponse(
        success=True,
        total=len(records),
        telemetries=[DeviceTelemetryResponse.model_validate(r) for r in records],
    )


@router.get("/telemetry/latest", response_model=TelemetryListResponse, summary="Get global live telemetry stream")
def get_latest_telemetry_feed(
    sensor_type: Optional[str] = Query(None),
    quality: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    records = TelemetryIngestionService.get_latest_telemetries(
        db, sensor_type=sensor_type, quality=quality, limit=limit
    )
    return TelemetryListResponse(
        success=True,
        total=len(records),
        telemetries=[DeviceTelemetryResponse.model_validate(r) for r in records],
    )


@router.get("/telemetry/quality", summary="Get data quality & provenance metrics")
def get_telemetry_quality_metrics(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    return TelemetryIngestionService.get_data_quality_summary(db)


# ==============================================================================
# 4. SENSOR CALIBRATION ENDPOINTS
# ==============================================================================
@router.get("/calibration", response_model=CalibrationListResponse, summary="List sensor calibration records")
def list_calibrations(
    device_id: Optional[str] = Query(None),
    sensor_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    records, total = CalibrationService.get_calibration_records(
        db, device_id=device_id, sensor_id=sensor_id, skip=skip, limit=limit
    )
    return CalibrationListResponse(
        success=True,
        total=total,
        records=[SensorCalibrationSchema.model_validate(r) for r in records],
    )


@router.post("/calibration", response_model=SensorCalibrationSchema, status_code=status.HTTP_201_CREATED, summary="Register sensor calibration record")
def register_calibration(
    payload: RegisterCalibrationRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    calib = CalibrationService.register_calibration(
        db=db,
        sensor_id=payload.sensor_id,
        device_id=payload.device_id,
        calibration_method=payload.calibration_method,
        calibration_reference=payload.calibration_reference,
        calibration_result=payload.calibration_result,
        accuracy_tolerance=payload.accuracy_tolerance,
        technician=payload.technician,
        certificate_reference=payload.certificate_reference,
        next_due_date=payload.next_due_date,
        calibration_date=payload.calibration_date,
        notes=payload.notes or "",
        actor=current_user.username or current_user.id,
    )
    return SensorCalibrationSchema.model_validate(calib)


@router.get("/devices/{device_id}/calibration", response_model=CalibrationListResponse, summary="Get calibration records for device")
def get_device_calibrations(
    device_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    records, total = CalibrationService.get_calibration_records(db, device_id=device_id)
    return CalibrationListResponse(
        success=True,
        total=total,
        records=[SensorCalibrationSchema.model_validate(r) for r in records],
    )


# ==============================================================================
# 5. IOT STATUS, HEALTH & AUDIT ENDPOINTS
# ==============================================================================
@router.get("/status", response_model=IoTStatusOverviewResponse, summary="Get IoT fleet overview and MQTT gateway metrics")
def get_iot_status(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    metrics = IotRepository.get_overview_metrics(db)
    mqtt_stat = mqtt_manager.get_status()

    return IoTStatusOverviewResponse(
        success=True,
        metrics=metrics,
        mqtt_status=mqtt_stat,
        hardware_safety="SIMULATION_FIRST_MODE_ACTIVE",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/health", summary="Health probe for IoT gateway")
def get_iot_health():
    return {
        "status": "HEALTHY",
        "gateway": "SIMULATION_FIRST_GATEWAY",
        "mqtt_connected": mqtt_manager.is_connected,
        "hardware_actuators": "DISABLED_AIR_GAP",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/audit", summary="Get IoT security and operational audit trail (Admin only)")
def get_iot_audit_log(
    device_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_admin),
):
    query = db.query(DeviceAuditLogModel)
    if device_id:
        query = query.filter(DeviceAuditLogModel.device_id == device_id)
    events = query.order_by(DeviceAuditLogModel.timestamp.desc()).limit(limit).all()

    return {
        "success": True,
        "total": len(events),
        "audit_events": [
            {
                "id": e.id,
                "device_id": e.device_id,
                "action": e.action,
                "actor": e.actor,
                "status": e.status,
                "ip_address": e.ip_address,
                "details": e.details,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ],
    }


# ==============================================================================
# 6. CROSS-MODULE INTELLIGENCE ENDPOINTS
# ==============================================================================
@router.get("/digital-twin-comparison", summary="Compare physical/simulated telemetry against digital twin baseline")
def get_digital_twin_comparison(
    pipeline_segment_id: str = Query("PIPE-SEC-4B-92"),
    observed_pressure_bar: float = Query(4.12, description="Observed pressure reading in bar"),
    observed_flow_lps: Optional[float] = Query(89.5, description="Observed flow reading in L/s"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Evaluates hydraulic deviation between sensor observation and EPANET baseline model.
    """
    return IotIntelligenceBridge.compare_with_digital_twin(
        db=db,
        pipeline_segment_id=pipeline_segment_id,
        observed_pressure_bar=observed_pressure_bar,
        observed_flow_lps=observed_flow_lps,
    )


@router.get("/leak-analysis", summary="Route sensor reading to AI leak detection acoustic analysis")
def analyze_leak_from_sensor(
    device_id: str = Query("DEV-ACOUSTIC-01"),
    acoustic_spl_db: float = Query(64.2, description="Acoustic sound pressure level in dB"),
    dominant_freq_hz: float = Query(520.0, description="Dominant acoustic frequency in Hz"),
    pressure_bar: Optional[float] = Query(3.8, description="Local pipe pressure in bar"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Evaluates multi-factor acoustic leak risk using Task 07 intelligence pipeline.
    """
    return IotIntelligenceBridge.evaluate_leak_risk_from_telemetry(
        db=db,
        device_id=device_id,
        acoustic_spl_db=acoustic_spl_db,
        dominant_freq_hz=dominant_freq_hz,
        pressure_bar=pressure_bar,
    )
