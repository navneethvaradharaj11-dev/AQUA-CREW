"""
AQUA CREW — Telemetry Ingestion Engine & Quality Assessment (Task 18)
Validates, normalizes, detects anomalies, checks calibration, enforces 6-tier provenance,
preserves raw evidence, and routes telemetry to AI and hydraulic digital twin pipelines.
"""
import uuid
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.iot import (
    IoTDeviceModel,
    SensorModel,
    DeviceTelemetryModel,
    TelemetryProcessingResultModel,
)
from app.repositories.iot_repository import IotRepository
from app.services.iot.adapters.adapter_factory import SensorAdapterFactory
from app.services.iot.calibration_service import CalibrationService
from app.core.exceptions import AquaCrewException

logger = logging.getLogger("aqua_crew.iot.ingest")

VALID_SENSOR_TYPES = {"acoustic", "pressure", "flow", "moisture", "temperature", "optical"}
VALID_UNITS = {"dB", "bar", "psi", "kpa", "L/s", "lps", "m3/h", "%", "°C", "°F", "C", "F", "metadata"}


class TelemetryIngestException(AquaCrewException):
    def __init__(self, message: str, code: str = "TELEMETRY_INGESTION_ERROR", status_code: int = 400):
        super().__init__(status_code=status_code, code=code, message=message)


class TelemetryIngestionService:
    @classmethod
    def ingest_single_reading(
        cls,
        db: Session,
        raw_payload: Dict[str, Any],
        auth_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingests, validates, and normalizes a single sensor telemetry packet.
        Returns detailed processing outcome and created telemetry record.
        """
        start_time = time.perf_counter()
        now = datetime.now(timezone.utc)

        # 1. Device identification
        device_id = raw_payload.get("device_id")
        if not device_id:
            raise TelemetryIngestException("Missing required 'device_id' in telemetry payload.", code="MISSING_DEVICE_ID")

        device = IotRepository.get_by_id_simple(db, device_id)
        if not device:
            raise TelemetryIngestException(
                f"Device '{device_id}' is not registered in system device catalog.",
                code="UNKNOWN_DEVICE_REJECTED",
                status_code=404,
            )

        # 2. Lifecycle & quarantine check
        if device.status == "REVOKED":
            raise TelemetryIngestException(
                f"Device '{device_id}' has been permanently revoked. Telemetry rejected.",
                code="DEVICE_REVOKED",
                status_code=403,
            )
        if device.status == "QUARANTINED":
            raise TelemetryIngestException(
                f"Device '{device_id}' is in security quarantine. Telemetry rejected.",
                code="DEVICE_QUARANTINED",
                status_code=403,
            )

        # 3. Authenticated ingestion check (if secret provided)
        if auth_secret:
            is_valid_auth = IotRepository.verify_device_credential(db, device_id, auth_secret)
            if not is_valid_auth:
                IotRepository.log_audit_event(
                    db,
                    device_id=device_id,
                    action="FAILED_AUTHENTICATION",
                    actor=device_id,
                    status="DENIED",
                    details={"reason": "Invalid device API key"},
                )
                raise TelemetryIngestException(
                    "Invalid device authentication secret.",
                    code="DEVICE_AUTH_FAILED",
                    status_code=401,
                )

        # 4. Sensor type and unit validation
        sensor_type = str(raw_payload.get("sensor_type", "")).lower().strip()
        if not sensor_type:
            # Fallback to device type
            if "ACOUSTIC" in device.device_type:
                sensor_type = "acoustic"
            elif "PRESSURE" in device.device_type:
                sensor_type = "pressure"
            elif "FLOW" in device.device_type:
                sensor_type = "flow"
            elif "MOISTURE" in device.device_type:
                sensor_type = "moisture"
            elif "TEMPERATURE" in device.device_type:
                sensor_type = "temperature"
            elif "OPTICAL" in device.device_type:
                sensor_type = "optical"
            else:
                sensor_type = "pressure"

        unit = str(raw_payload.get("unit", "")).strip()
        if unit and unit not in VALID_UNITS:
            raise TelemetryIngestException(
                f"Invalid or unsupported measurement unit '{unit}'. Supported: {sorted(list(VALID_UNITS))}",
                code="INVALID_MEASUREMENT_UNIT",
            )

        # 5. Normalization via Sensor Adapter
        adapter = SensorAdapterFactory.get_adapter(sensor_type, device.device_type)
        normalized = adapter.normalize(raw_payload)

        # 6. Timestamp validation
        reading_ts = normalized.timestamp
        if reading_ts.tzinfo is None:
            reading_ts = reading_ts.replace(tzinfo=timezone.utc)

        # Check future timestamp (> 5 minutes)
        if reading_ts > now + timedelta(minutes=5):
            normalized.data_quality = "SUSPECT"
            normalized.metadata["timestamp_warning"] = "Future timestamp detected (>5m)"

        # Check stale reading (> 24 hours old)
        if reading_ts < now - timedelta(hours=24):
            normalized.data_quality = "STALE"
            normalized.metadata["timestamp_warning"] = "Stale telemetry (>24h old)"

        # 7. Sequence number & duplicate detection
        latest_telemetry = (
            db.query(DeviceTelemetryModel)
            .filter(
                DeviceTelemetryModel.device_id == device_id,
                DeviceTelemetryModel.sensor_id == normalized.sensor_id,
            )
            .order_by(desc(DeviceTelemetryModel.timestamp))
            .first()
        )

        if latest_telemetry:
            if normalized.sequence_number == latest_telemetry.sequence_number and normalized.measurement_value == latest_telemetry.measurement_value:
                normalized.data_quality = "DUPLICATE"
                normalized.metadata["duplicate_detected"] = True
            elif normalized.sequence_number < latest_telemetry.sequence_number:
                if normalized.data_quality == "VALID":
                    normalized.data_quality = "SUSPECT"
                normalized.metadata["out_of_order_seq"] = True

        # 8. Calibration quality check
        calib_quality, calib_warning = CalibrationService.evaluate_sensor_calibration_quality(
            db, device_id, normalized.sensor_id
        )
        if calib_quality != "VALID":
            normalized.data_quality = calib_quality
            if calib_warning:
                normalized.metadata["calibration_warning"] = calib_warning

        # 9. Strict Evidence Provenance Enforcement
        # Rule: If device is virtual/simulated, NEVER claim MEASURED evidence!
        if device.is_simulated or device.device_type == "VIRTUAL_SIMULATION_DEVICE":
            normalized.provenance = "SIMULATED"
        elif normalized.provenance not in ["MEASURED", "SIMULATED", "DERIVED", "PREDICTED", "OPERATOR_ENTERED", "UNKNOWN"]:
            normalized.provenance = "UNKNOWN"

        # 10. Persistence
        telemetry_id = f"TEL-{uuid.uuid4().hex[:12].upper()}"
        telemetry_rec = DeviceTelemetryModel(
            id=telemetry_id,
            device_id=device.id,
            sensor_id=normalized.sensor_id,
            sensor_type=normalized.sensor_type,
            measurement_value=normalized.measurement_value,
            unit=normalized.unit,
            raw_payload=raw_payload,
            sequence_number=normalized.sequence_number,
            timestamp=reading_ts,
            ingested_at=now,
            data_quality=normalized.data_quality,
            provenance=normalized.provenance,
            firmware_version=normalized.firmware_version,
            calibration_reference=normalized.calibration_reference,
            pipeline_segment_id=device.pipeline_segment_id or "",
            is_simulated=(normalized.provenance == "SIMULATED"),
        )
        db.add(telemetry_rec)

        # Update device heartbeat & sensor reading
        device.last_communication_at = now
        device.updated_at = now

        sensor = db.query(SensorModel).filter(SensorModel.id == normalized.sensor_id).first()
        if sensor:
            sensor.latest_reading_value = normalized.measurement_value
            sensor.latest_reading_time = reading_ts

        # 11. Cross-Module Routing Evaluation
        routed_ai = False
        routed_twin = False

        if normalized.data_quality in ["VALID", "SUSPECT"]:
            if normalized.sensor_type in ["acoustic", "pressure"]:
                routed_ai = True
            if normalized.sensor_type in ["pressure", "flow"]:
                routed_twin = True

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        proc_result = TelemetryProcessingResultModel(
            id=f"PROC-{uuid.uuid4().hex[:10].upper()}",
            batch_id=str(raw_payload.get("batch_id", "")),
            device_id=device_id,
            status="ACCEPTED",
            processing_latency_ms=round(latency_ms, 3),
            routed_to_ai_leak=routed_ai,
            routed_to_digital_twin=routed_twin,
            timestamp=now,
        )
        db.add(proc_result)

        db.commit()
        db.refresh(telemetry_rec)

        return {
            "success": True,
            "telemetry_id": telemetry_rec.id,
            "device_id": device.id,
            "sensor_id": normalized.sensor_id,
            "sensor_type": normalized.sensor_type,
            "measurement_value": normalized.measurement_value,
            "unit": normalized.unit,
            "timestamp": telemetry_rec.timestamp.isoformat(),
            "data_quality": telemetry_rec.data_quality,
            "provenance": telemetry_rec.provenance,
            "processing_latency_ms": round(latency_ms, 3),
            "routed_to_ai_leak": routed_ai,
            "routed_to_digital_twin": routed_twin,
            "metadata": normalized.metadata,
        }

    @classmethod
    def ingest_batch(
        cls,
        db: Session,
        readings: List[Dict[str, Any]],
        auth_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ingests a batch of readings, recording accepted and rejected counts."""
        accepted = []
        errors = []

        for idx, r in enumerate(readings):
            try:
                res = cls.ingest_single_reading(db, r, auth_secret)
                accepted.append(res)
            except Exception as e:
                errors.append({"index": idx, "error": str(e)})

        return {
            "success": len(errors) == 0,
            "total_processed": len(readings),
            "accepted_count": len(accepted),
            "error_count": len(errors),
            "results": accepted,
            "errors": errors,
        }

    @staticmethod
    def get_latest_telemetries(
        db: Session,
        device_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        quality: Optional[str] = None,
        limit: int = 50,
    ) -> List[DeviceTelemetryModel]:
        """Retrieves recent telemetries with optional filters."""
        query = db.query(DeviceTelemetryModel)
        if device_id:
            query = query.filter(DeviceTelemetryModel.device_id == device_id)
        if sensor_type:
            query = query.filter(DeviceTelemetryModel.sensor_type == sensor_type.lower())
        if quality:
            query = query.filter(DeviceTelemetryModel.data_quality == quality.upper())

        return query.order_by(desc(DeviceTelemetryModel.timestamp)).limit(limit).all()

    @staticmethod
    def get_data_quality_summary(db: Session) -> Dict[str, Any]:
        """Computes summary breakdown across data quality flags and provenance."""
        telemetries = db.query(DeviceTelemetryModel).all()
        quality_counts = {
            "VALID": 0,
            "SUSPECT": 0,
            "STALE": 0,
            "INVALID": 0,
            "DUPLICATE": 0,
            "MISSING": 0,
            "UNCALIBRATED": 0,
        }
        provenance_counts = {
            "MEASURED": 0,
            "SIMULATED": 0,
            "DERIVED": 0,
            "PREDICTED": 0,
            "OPERATOR_ENTERED": 0,
            "UNKNOWN": 0,
        }

        for t in telemetries:
            q = t.data_quality or "VALID"
            p = t.provenance or "MEASURED"
            if q in quality_counts:
                quality_counts[q] += 1
            if p in provenance_counts:
                provenance_counts[p] += 1

        total = len(telemetries)
        valid_ratio = round(quality_counts["VALID"] / max(total, 1), 4)

        return {
            "total_telemetry_records": total,
            "valid_telemetry_ratio": valid_ratio,
            "quality_breakdown": quality_counts,
            "provenance_breakdown": provenance_counts,
        }

