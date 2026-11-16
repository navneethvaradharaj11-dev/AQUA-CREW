"""
AQUA CREW — Sensor Calibration Management Service (Task 18)
Enforces metrological calibration standards, tracks recalibration schedules,
and flags uncalibrated or overdue telemetry with data-quality warnings.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.iot import (
    SensorCalibrationModel,
    SensorModel,
    IoTDeviceModel,
    DeviceAuditLogModel,
)


class CalibrationService:
    @staticmethod
    def calculate_calibration_status(
        calibration_result: str,
        next_due_date: datetime,
        current_time: Optional[datetime] = None,
    ) -> str:
        """Determines calibration state based on outcome and due date."""
        now = current_time or datetime.now(timezone.utc)
        norm_result = (calibration_result or "").upper().strip()

        if norm_result in ["FAIL", "OUT_OF_TOLERANCE"]:
            return "FAILED"

        # Ensure timezone-aware comparison
        if next_due_date.tzinfo is None:
            next_due_date = next_due_date.replace(tzinfo=timezone.utc)

        if next_due_date < now:
            return "OVERDUE"
        elif now <= next_due_date <= (now + timedelta(days=14)):
            return "DUE"
        else:
            return "CALIBRATED"

    @classmethod
    def register_calibration(
        cls,
        db: Session,
        sensor_id: str,
        device_id: str,
        calibration_method: str,
        calibration_reference: str,
        calibration_result: str,
        accuracy_tolerance: float,
        technician: str,
        certificate_reference: str,
        next_due_date: datetime,
        calibration_date: Optional[datetime] = None,
        notes: str = "",
        actor: str = "system",
    ) -> SensorCalibrationModel:
        """
        Registers a new metrological calibration record.
        Updates sensor and parent device calibration statuses accordingly.
        """
        now = datetime.now(timezone.utc)
        calib_date = calibration_date or now

        # Compute status
        status = cls.calculate_calibration_status(
            calibration_result=calibration_result,
            next_due_date=next_due_date,
            current_time=now,
        )

        calib_id = f"CALIB-{uuid.uuid4().hex[:8].upper()}"
        calib = SensorCalibrationModel(
            id=calib_id,
            sensor_id=sensor_id,
            device_id=device_id,
            calibration_date=calib_date,
            last_calibration_date=calib_date,
            next_due_date=next_due_date,
            calibration_method=calibration_method,
            calibration_reference=calibration_reference,
            calibration_result=calibration_result.upper(),
            accuracy_tolerance=accuracy_tolerance,
            technician=technician,
            certificate_reference=certificate_reference,
            calibration_status=status,
            notes=notes,
            created_at=now,
        )
        db.add(calib)

        # Update parent device calibration status
        device = db.query(IoTDeviceModel).filter(IoTDeviceModel.id == device_id).first()
        if device:
            device.calibration_status = status
            device.updated_at = now

        # Audit event
        audit = DeviceAuditLogModel(
            id=f"AUD-{uuid.uuid4().hex[:10].upper()}",
            device_id=device_id,
            action="CALIBRATION_RECORDED",
            actor=actor,
            status="SUCCESS",
            ip_address="127.0.0.1",
            details={
                "calibration_id": calib_id,
                "sensor_id": sensor_id,
                "result": calibration_result,
                "status": status,
                "certificate_reference": certificate_reference,
            },
            timestamp=now,
        )
        db.add(audit)

        db.commit()
        db.refresh(calib)
        return calib

    @staticmethod
    def get_calibration_records(
        db: Session,
        device_id: Optional[str] = None,
        sensor_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[SensorCalibrationModel], int]:
        """Retrieves historical calibration records with optional filtering."""
        query = db.query(SensorCalibrationModel)
        if device_id:
            query = query.filter(SensorCalibrationModel.device_id == device_id)
        if sensor_id:
            query = query.filter(SensorCalibrationModel.sensor_id == sensor_id)

        total = query.count()
        records = query.order_by(desc(SensorCalibrationModel.calibration_date)).offset(skip).limit(limit).all()
        return records, total

    @staticmethod
    def evaluate_sensor_calibration_quality(
        db: Session,
        device_id: str,
        sensor_id: str,
    ) -> Tuple[str, Optional[str]]:
        """
        Assesses calibration impact on telemetry quality.
        Returns: (quality_flag, reason_or_warning)
          - ("VALID", None)
          - ("UNCALIBRATED", "Sensor has no calibration record")
          - ("SUSPECT", "Sensor calibration is overdue")
          - ("INVALID", "Sensor calibration marked FAILED")
        """
        now = datetime.now(timezone.utc)
        latest_calib = (
            db.query(SensorCalibrationModel)
            .filter(
                SensorCalibrationModel.device_id == device_id,
                SensorCalibrationModel.sensor_id == sensor_id,
            )
            .order_by(desc(SensorCalibrationModel.calibration_date))
            .first()
        )

        if not latest_calib:
            return "UNCALIBRATED", "Sensor has no record of certified calibration."

        if latest_calib.calibration_status == "FAILED" or latest_calib.calibration_result in ["FAIL", "OUT_OF_TOLERANCE"]:
            return "INVALID", f"Sensor failed calibration certificate {latest_calib.certificate_reference}."

        due_date = latest_calib.next_due_date
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)

        if due_date < now:
            days_overdue = (now - due_date).days
            return "SUSPECT", f"Sensor calibration expired {days_overdue} days ago ({latest_calib.certificate_reference})."

        return "VALID", None

    @staticmethod
    def audit_and_update_overdue_calibrations(db: Session) -> int:
        """Scheduled audit routine: marks overdue calibrations."""
        now = datetime.now(timezone.utc)
        overdue_calibs = (
            db.query(SensorCalibrationModel)
            .filter(
                SensorCalibrationModel.calibration_status != "OVERDUE",
                SensorCalibrationModel.calibration_status != "FAILED",
                SensorCalibrationModel.next_due_date < now,
            )
            .all()
        )

        count = 0
        for c in overdue_calibs:
            c.calibration_status = "OVERDUE"
            # Update device as well
            dev = db.query(IoTDeviceModel).filter(IoTDeviceModel.id == c.device_id).first()
            if dev:
                dev.calibration_status = "OVERDUE"
                dev.status = "DEGRADED"
            count += 1

        if count > 0:
            db.commit()
        return count

