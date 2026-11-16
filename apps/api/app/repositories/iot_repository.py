"""
AQUA CREW — IoT Device Ecosystem & Hardware Gateway Repository (Task 18)
Manages persistence, lifecycle states, credentials, calibrations, and audit ledgers.
"""
import uuid
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.models.iot import (
    IoTDeviceModel,
    DeviceCredentialMetadataModel,
    SensorModel,
    SensorCalibrationModel,
    DeviceTelemetryModel,
    DeviceEventModel,
    DeviceConnectionModel,
    DeviceAuditLogModel,
    TelemetryProcessingResultModel,
)

DEFAULT_IOT_DEVICES = [
    {
        "id": "DEV-ACOUSTIC-01",
        "name": "Metro Trunk Acoustic Hydrophone Node A1",
        "device_type": "ACOUSTIC_LEAK_SENSOR",
        "manufacturer": "AquaSense Nordic",
        "hardware_model": "HYD-ESP32-S3",
        "firmware_version": "v1.4.2",
        "hardware_revision": "revB.1",
        "installation_location": "Chamber CB-104, Metro Central Trunk B",
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "dma_zone": "DMA-METRO-CENTRAL",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "elevation_m": 12.5,
        "supported_sensor_types": ["acoustic", "temperature"],
        "communication_protocol": "MQTT",
        "status": "ACTIVE",
        "calibration_status": "CALIBRATED",
        "auth_status": "AUTHENTICATED",
        "is_simulated": True,
        "sensors": [
            {
                "id": "SNS-AC-01-A",
                "sensor_type": "acoustic",
                "measurement_unit": "dB",
                "min_range": 0.0,
                "max_range": 120.0,
                "accuracy_tolerance": 0.02,
                "sampling_rate_hz": 2000.0,
                "latest_reading_value": 48.5,
            },
            {
                "id": "SNS-TEMP-01-B",
                "sensor_type": "temperature",
                "measurement_unit": "°C",
                "min_range": -10.0,
                "max_range": 60.0,
                "accuracy_tolerance": 0.01,
                "sampling_rate_hz": 0.1,
                "latest_reading_value": 16.4,
            },
        ],
        "calibration": {
            "id": "CALIB-AC-01",
            "calibration_method": "ACOUSTIC_CHAMBER_CALIBRATION",
            "calibration_reference": "REF-HYDRO-ISO-9001",
            "calibration_result": "PASS",
            "accuracy_tolerance": 0.02,
            "technician": "Lead Acoustic Metrologist",
            "certificate_reference": "CERT-2026-AQ-441",
            "calibration_status": "CALIBRATED",
            "next_due_days": 180,
        },
    },
    {
        "id": "DEV-PRESSURE-02",
        "name": "High-Pressure Spine Piezoresistive Transducer",
        "device_type": "PRESSURE_SENSOR",
        "manufacturer": "AquaSense Nordic",
        "hardware_model": "P-TRANSDUCER-420",
        "firmware_version": "v2.1.0",
        "hardware_revision": "revC.0",
        "installation_location": "Vault V-12, Grand Avenue Spine Line A",
        "pipeline_segment_id": "PIPE-SEC-4A-10",
        "dma_zone": "DMA-METRO-CENTRAL",
        "latitude": 40.7100,
        "longitude": -74.0080,
        "elevation_m": 14.2,
        "supported_sensor_types": ["pressure"],
        "communication_protocol": "MQTT",
        "status": "ACTIVE",
        "calibration_status": "CALIBRATED",
        "auth_status": "AUTHENTICATED",
        "is_simulated": True,
        "sensors": [
            {
                "id": "SNS-PR-02-A",
                "sensor_type": "pressure",
                "measurement_unit": "bar",
                "min_range": 0.0,
                "max_range": 16.0,
                "accuracy_tolerance": 0.01,
                "sampling_rate_hz": 10.0,
                "latest_reading_value": 4.62,
            }
        ],
        "calibration": {
            "id": "CALIB-PR-02",
            "calibration_method": "DEADWEIGHT_TESTER_CALIBRATION",
            "calibration_reference": "DWT-STANDARD-REF-09",
            "calibration_result": "PASS",
            "accuracy_tolerance": 0.01,
            "technician": "Hydraulic Senior Inspector",
            "certificate_reference": "CERT-2026-PR-902",
            "calibration_status": "CALIBRATED",
            "next_due_days": 90,
        },
    },
    {
        "id": "DEV-FLOW-03",
        "name": "Metro District Electromagnetic Flow Meter",
        "device_type": "FLOW_METER",
        "manufacturer": "Endress+Flow Corp",
        "hardware_model": "MAG-FLOW-800",
        "firmware_version": "v3.0.4",
        "hardware_revision": "revA.4",
        "installation_location": "Inlet Station IS-01, Metro Central Trunk B",
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "dma_zone": "DMA-METRO-CENTRAL",
        "latitude": 40.7145,
        "longitude": -74.0040,
        "elevation_m": 11.8,
        "supported_sensor_types": ["flow", "temperature"],
        "communication_protocol": "MQTT",
        "status": "ACTIVE",
        "calibration_status": "CALIBRATED",
        "auth_status": "AUTHENTICATED",
        "is_simulated": True,
        "sensors": [
            {
                "id": "SNS-FL-03-A",
                "sensor_type": "flow",
                "measurement_unit": "L/s",
                "min_range": 0.0,
                "max_range": 500.0,
                "accuracy_tolerance": 0.015,
                "sampling_rate_hz": 1.0,
                "latest_reading_value": 82.4,
            }
        ],
        "calibration": {
            "id": "CALIB-FL-03",
            "calibration_method": "HYDRAULIC_REFERENCE_COMPARISON",
            "calibration_reference": "ISO-4185-GRAVIMETRIC",
            "calibration_result": "PASS",
            "accuracy_tolerance": 0.015,
            "technician": "Hydraulic Measurement Officer",
            "certificate_reference": "CERT-2026-FL-103",
            "calibration_status": "CALIBRATED",
            "next_due_days": 120,
        },
    },
    {
        "id": "DEV-MOIST-04",
        "name": "Sub-surface Soil Moisture Time-Domain Reflector",
        "device_type": "MOISTURE_SENSOR",
        "manufacturer": "GeoHydrology Labs",
        "hardware_model": "TDR-MOIST-100",
        "firmware_version": "v1.1.0",
        "hardware_revision": "revB.0",
        "installation_location": "Trench Monitoring Node TM-04, Sector 7",
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "dma_zone": "DMA-METRO-CENTRAL",
        "latitude": 40.7132,
        "longitude": -74.0055,
        "elevation_m": 12.0,
        "supported_sensor_types": ["moisture"],
        "communication_protocol": "MQTT",
        "status": "DEGRADED",
        "calibration_status": "OVERDUE",
        "auth_status": "AUTHENTICATED",
        "is_simulated": True,
        "sensors": [
            {
                "id": "SNS-MOIST-04-A",
                "sensor_type": "moisture",
                "measurement_unit": "%",
                "min_range": 0.0,
                "max_range": 100.0,
                "accuracy_tolerance": 0.05,
                "sampling_rate_hz": 0.05,
                "latest_reading_value": 38.2,
            }
        ],
        "calibration": {
            "id": "CALIB-MOIST-04",
            "calibration_method": "SOIL_CORE_GRAVIMETRIC",
            "calibration_reference": "ASTM-D2216",
            "calibration_result": "ADJUSTED_PASS",
            "accuracy_tolerance": 0.05,
            "technician": "Field Environmental Tech",
            "certificate_reference": "CERT-2025-MS-771",
            "calibration_status": "OVERDUE",
            "next_due_days": -15,  # Overdue by 15 days
        },
    },
    {
        "id": "DEV-OPTICAL-05",
        "name": "Pipe Internal Boroscope Optical Rig",
        "device_type": "OPTICAL_INSPECTION_SENSOR",
        "manufacturer": "AquaVision Labs",
        "hardware_model": "BORO-OPT-4K",
        "firmware_version": "v2.0.1",
        "hardware_revision": "revA.2",
        "installation_location": "Inspection Port IP-09, Trunk B",
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "dma_zone": "DMA-METRO-CENTRAL",
        "latitude": 40.7115,
        "longitude": -74.0070,
        "elevation_m": 13.0,
        "supported_sensor_types": ["optical"],
        "communication_protocol": "HTTP_REST",
        "status": "MAINTENANCE",
        "calibration_status": "UNCALIBRATED",
        "auth_status": "AUTHENTICATED",
        "is_simulated": True,
        "sensors": [
            {
                "id": "SNS-OPT-05-A",
                "sensor_type": "optical",
                "measurement_unit": "metadata",
                "min_range": 0.0,
                "max_range": 100.0,
                "accuracy_tolerance": 0.1,
                "sampling_rate_hz": 30.0,
                "latest_reading_value": 92.0,
            }
        ],
        "calibration": {
            "id": "CALIB-OPT-05",
            "calibration_method": "OPTICAL_TARGET_GRID_CALIBRATION",
            "calibration_reference": "ISO-12233-CHART",
            "calibration_result": "OUT_OF_TOLERANCE",
            "accuracy_tolerance": 0.1,
            "technician": "Optical Systems Specialist",
            "certificate_reference": "CERT-PENDING",
            "calibration_status": "UNCALIBRATED",
            "next_due_days": 0,
        },
    },
    {
        "id": "DEV-VIRT-06",
        "name": "Digital Twin EPANET Emulated Junction Sensor Node",
        "device_type": "VIRTUAL_SIMULATION_DEVICE",
        "manufacturer": "AQUA CREW Digital Twin Engine",
        "hardware_model": "VIRTUAL-SIM-GATEWAY",
        "firmware_version": "v4.0.0-wntr",
        "hardware_revision": "vSim.3",
        "installation_location": "Hydraulic Node J-02, High-Pressure Main",
        "pipeline_segment_id": "PIPE-SEC-4A-10",
        "dma_zone": "DMA-METRO-CENTRAL",
        "latitude": 40.7060,
        "longitude": -74.0110,
        "elevation_m": 15.0,
        "supported_sensor_types": ["pressure", "flow", "acoustic"],
        "communication_protocol": "SIMULATED",
        "status": "ACTIVE",
        "calibration_status": "CALIBRATED",
        "auth_status": "AUTHENTICATED",
        "is_simulated": True,
        "sensors": [
            {
                "id": "SNS-VIRT-PR-06",
                "sensor_type": "pressure",
                "measurement_unit": "bar",
                "min_range": 0.0,
                "max_range": 20.0,
                "accuracy_tolerance": 0.001,
                "sampling_rate_hz": 1.0,
                "latest_reading_value": 4.88,
            },
            {
                "id": "SNS-VIRT-FL-06",
                "sensor_type": "flow",
                "measurement_unit": "L/s",
                "min_range": 0.0,
                "max_range": 400.0,
                "accuracy_tolerance": 0.001,
                "sampling_rate_hz": 1.0,
                "latest_reading_value": 110.2,
            },
        ],
        "calibration": {
            "id": "CALIB-VIRT-06",
            "calibration_method": "NUMERICAL_TOLERANCE_VERIFICATION",
            "calibration_reference": "TODINI_GGA_RESIDUAL_TOLERANCE",
            "calibration_result": "PASS",
            "accuracy_tolerance": 0.001,
            "technician": "Automated Hydraulic Solver",
            "certificate_reference": "ALGO-VERIFY-10-6",
            "calibration_status": "CALIBRATED",
            "next_due_days": 365,
        },
    },
]


class IotRepository:
    @staticmethod
    def hash_credential(secret: str) -> str:
        """Computes secure SHA-256 hash of API key or secret token."""
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_api_key(device_id: str) -> Tuple[str, str, str]:
        """
        Generates a secure API key.
        Returns: (full_plaintext_secret, key_prefix, hashed_secret)
        """
        random_part = secrets.token_urlsafe(32)
        prefix = f"aqdev_{device_id[:6].lower()}_"
        full_key = f"{prefix}{random_part}"
        hashed = hashlib.sha256(full_key.encode("utf-8")).hexdigest()
        return full_key, prefix, hashed

    @staticmethod
    def seed_defaults(db: Session) -> None:
        """Seeds standard IoT devices, sensors, and calibrations if table is empty."""
        count = db.query(IoTDeviceModel).count()
        if count > 0:
            return

        now = datetime.now(timezone.utc)
        for dev_data in DEFAULT_IOT_DEVICES:
            device = IoTDeviceModel(
                id=dev_data["id"],
                name=dev_data["name"],
                device_type=dev_data["device_type"],
                manufacturer=dev_data["manufacturer"],
                hardware_model=dev_data["hardware_model"],
                firmware_version=dev_data["firmware_version"],
                hardware_revision=dev_data["hardware_revision"],
                installation_location=dev_data["installation_location"],
                pipeline_segment_id=dev_data["pipeline_segment_id"],
                dma_zone=dev_data["dma_zone"],
                latitude=dev_data["latitude"],
                longitude=dev_data["longitude"],
                elevation_m=dev_data["elevation_m"],
                supported_sensor_types=dev_data["supported_sensor_types"],
                communication_protocol=dev_data["communication_protocol"],
                status=dev_data["status"],
                last_communication_at=now - timedelta(minutes=2),
                calibration_status=dev_data["calibration_status"],
                auth_status=dev_data["auth_status"],
                is_simulated=dev_data["is_simulated"],
                owner_id="USR-ADMIN-01",
                created_at=now - timedelta(days=30),
                updated_at=now,
            )
            db.add(device)
            db.flush()

            # Seed default API credential
            cred_id = f"CRED-{uuid.uuid4().hex[:8].upper()}"
            default_key = f"aqdev_seed_{dev_data['id'].lower()}_secret2026!"
            hashed_key = hashlib.sha256(default_key.encode("utf-8")).hexdigest()
            cred = DeviceCredentialMetadataModel(
                id=cred_id,
                device_id=device.id,
                credential_type="API_KEY",
                key_prefix=f"aqdev_{device.id[:6].lower()}_",
                hashed_secret=hashed_key,
                allowed_topics=[
                    f"aquacrew/devices/{device.id}/telemetry",
                    f"aquacrew/devices/{device.id}/status",
                    f"aquacrew/devices/{device.id}/events",
                ],
                revoked=False,
                created_at=now - timedelta(days=30),
            )
            db.add(cred)

            # Seed sensors
            for s_data in dev_data["sensors"]:
                sensor = SensorModel(
                    id=s_data["id"],
                    device_id=device.id,
                    sensor_type=s_data["sensor_type"],
                    measurement_unit=s_data["measurement_unit"],
                    min_range=s_data["min_range"],
                    max_range=s_data["max_range"],
                    accuracy_tolerance=s_data["accuracy_tolerance"],
                    sampling_rate_hz=s_data["sampling_rate_hz"],
                    is_active=True,
                    latest_reading_value=s_data.get("latest_reading_value"),
                    latest_reading_time=now - timedelta(minutes=2),
                    created_at=now - timedelta(days=30),
                )
                db.add(sensor)

            # Seed calibration
            calib_info = dev_data["calibration"]
            due_date = now + timedelta(days=calib_info["next_due_days"])
            calib = SensorCalibrationModel(
                id=calib_info["id"],
                sensor_id=dev_data["sensors"][0]["id"],
                device_id=device.id,
                calibration_date=now - timedelta(days=60),
                last_calibration_date=now - timedelta(days=60),
                next_due_date=due_date,
                calibration_method=calib_info["calibration_method"],
                calibration_reference=calib_info["calibration_reference"],
                calibration_result=calib_info["calibration_result"],
                accuracy_tolerance=calib_info["accuracy_tolerance"],
                technician=calib_info["technician"],
                certificate_reference=calib_info["certificate_reference"],
                calibration_status=calib_info["calibration_status"],
                notes="Baseline laboratory calibration verified against ISO municipal water monitoring standards.",
                created_at=now - timedelta(days=60),
            )
            db.add(calib)

            # Seed initial audit record
            audit = DeviceAuditLogModel(
                id=f"AUD-{uuid.uuid4().hex[:10].upper()}",
                device_id=device.id,
                action="REGISTRATION",
                actor="System Provisioner",
                status="SUCCESS",
                ip_address="127.0.0.1",
                details={"seeded": True, "device_name": device.name},
                timestamp=now - timedelta(days=30),
            )
            db.add(audit)

        db.commit()

    @staticmethod
    def get_devices(
        db: Session,
        status: Optional[str] = None,
        device_type: Optional[str] = None,
        dma_zone: Optional[str] = None,
        pipeline_segment_id: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[IoTDeviceModel], int]:
        """Queries devices with filtering, search, and pagination."""
        query = db.query(IoTDeviceModel)

        if status:
            query = query.filter(IoTDeviceModel.status == status.upper())
        if device_type:
            query = query.filter(IoTDeviceModel.device_type == device_type.upper())
        if dma_zone:
            query = query.filter(IoTDeviceModel.dma_zone == dma_zone)
        if pipeline_segment_id:
            query = query.filter(IoTDeviceModel.pipeline_segment_id == pipeline_segment_id)
        if search:
            search_filter = f"%{search.lower()}%"
            query = query.filter(
                or_(
                    IoTDeviceModel.id.ilike(search_filter),
                    IoTDeviceModel.name.ilike(search_filter),
                    IoTDeviceModel.manufacturer.ilike(search_filter),
                    IoTDeviceModel.installation_location.ilike(search_filter),
                )
            )

        total = query.count()
        devices = query.order_by(desc(IoTDeviceModel.created_at)).offset(skip).limit(limit).all()
        return devices, total

    @staticmethod
    def get_device_by_id(db: Session, device_id: str) -> Optional[IoTDeviceModel]:
        """Retrieves a single device by ID with relations."""
        return db.query(IoTDeviceModel).filter(IoTDeviceModel.id == device_id).first()

    @staticmethod
    def create_device(
        db: Session,
        device_id: str,
        name: str,
        device_type: str,
        manufacturer: str = "AQUA CREW Lab",
        hardware_model: str = "ESP32-S3-WROOM",
        firmware_version: str = "v1.4.0-sim",
        hardware_revision: str = "revB.0",
        installation_location: str = "",
        pipeline_segment_id: Optional[str] = None,
        dma_zone: str = "DMA-METRO-CENTRAL",
        latitude: float = 40.7128,
        longitude: float = -74.0060,
        elevation_m: float = 12.0,
        supported_sensor_types: Optional[List[str]] = None,
        communication_protocol: str = "MQTT",
        owner_id: Optional[str] = None,
        is_simulated: bool = True,
    ) -> Tuple[IoTDeviceModel, str]:
        """
        Creates a new IoT device and provisions its initial API key.
        Returns: (IoTDeviceModel, plaintext_secret_key)
        """
        now = datetime.now(timezone.utc)
        device = IoTDeviceModel(
            id=device_id,
            name=name,
            device_type=device_type.upper(),
            manufacturer=manufacturer,
            hardware_model=hardware_model,
            firmware_version=firmware_version,
            hardware_revision=hardware_revision,
            installation_location=installation_location,
            pipeline_segment_id=pipeline_segment_id,
            dma_zone=dma_zone,
            latitude=latitude,
            longitude=longitude,
            elevation_m=elevation_m,
            supported_sensor_types=supported_sensor_types or [],
            communication_protocol=communication_protocol.upper(),
            status="REGISTERED",
            calibration_status="CALIBRATED",
            auth_status="AUTHENTICATED",
            is_simulated=is_simulated,
            owner_id=owner_id,
            created_at=now,
            updated_at=now,
        )
        db.add(device)
        db.flush()

        # Provision initial credential
        full_secret, key_prefix, hashed_secret = IotRepository.generate_api_key(device_id)
        cred = DeviceCredentialMetadataModel(
            id=f"CRED-{uuid.uuid4().hex[:8].upper()}",
            device_id=device.id,
            credential_type="API_KEY",
            key_prefix=key_prefix,
            hashed_secret=hashed_secret,
            allowed_topics=[
                f"aquacrew/devices/{device.id}/telemetry",
                f"aquacrew/devices/{device.id}/status",
                f"aquacrew/devices/{device.id}/events",
                f"aquacrew/devices/{device.id}/diagnostics",
            ],
            revoked=False,
            created_at=now,
        )
        db.add(cred)

        # Audit event
        audit = DeviceAuditLogModel(
            id=f"AUD-{uuid.uuid4().hex[:10].upper()}",
            device_id=device.id,
            action="REGISTRATION",
            actor=owner_id or "system",
            status="SUCCESS",
            ip_address="127.0.0.1",
            details={"action": "device_created", "key_prefix": key_prefix},
            timestamp=now,
        )
        db.add(audit)

        db.commit()
        db.refresh(device)
        return device, full_secret

    @staticmethod
    def verify_device_credential(db: Session, device_id: str, secret: str) -> bool:
        """Verifies device secret against active credentials."""
        device = IotRepository.get_by_id_simple(db, device_id)
        if not device or device.status in ["REVOKED", "QUARANTINED"]:
            return False

        hashed = hashlib.sha256(secret.encode("utf-8")).hexdigest()
        cred = (
            db.query(DeviceCredentialMetadataModel)
            .filter(
                DeviceCredentialMetadataModel.device_id == device_id,
                DeviceCredentialMetadataModel.hashed_secret == hashed,
                DeviceCredentialMetadataModel.revoked == False,
            )
            .first()
        )
        return cred is not None

    @staticmethod
    def rotate_device_credential(db: Session, device_id: str, actor: str = "system") -> str:
        """Rotates credentials: revokes prior keys and issues a new secret."""
        device = IotRepository.get_by_id_simple(db, device_id)
        if not device:
            raise ValueError(f"Device {device_id} not found.")

        now = datetime.now(timezone.utc)
        # Revoke existing
        existing_creds = (
            db.query(DeviceCredentialMetadataModel)
            .filter(
                DeviceCredentialMetadataModel.device_id == device_id,
                DeviceCredentialMetadataModel.revoked == False,
            )
            .all()
        )
        for c in existing_creds:
            c.revoked = True
            c.revoked_at = now
            c.revocation_reason = "credential_rotation"

        # Generate new
        full_secret, key_prefix, hashed = IotRepository.generate_api_key(device_id)
        new_cred = DeviceCredentialMetadataModel(
            id=f"CRED-{uuid.uuid4().hex[:8].upper()}",
            device_id=device_id,
            credential_type="API_KEY",
            key_prefix=key_prefix,
            hashed_secret=hashed,
            allowed_topics=[
                f"aquacrew/devices/{device_id}/telemetry",
                f"aquacrew/devices/{device_id}/status",
                f"aquacrew/devices/{device_id}/events",
            ],
            revoked=False,
            last_rotated_at=now,
            created_at=now,
        )
        db.add(new_cred)

        # Log audit
        audit = DeviceAuditLogModel(
            id=f"AUD-{uuid.uuid4().hex[:10].upper()}",
            device_id=device_id,
            action="CREDENTIAL_ROTATION",
            actor=actor,
            status="SUCCESS",
            ip_address="127.0.0.1",
            details={"key_prefix": key_prefix},
            timestamp=now,
        )
        db.add(audit)
        db.commit()
        return full_secret

    @staticmethod
    def revoke_device(db: Session, device_id: str, reason: str = "administrative_revocation", actor: str = "system") -> None:
        """Revokes all device credentials and marks device REVOKED."""
        device = IotRepository.get_by_id_simple(db, device_id)
        if not device:
            raise ValueError(f"Device {device_id} not found.")

        now = datetime.now(timezone.utc)
        device.status = "REVOKED"
        device.auth_status = "REVOKED"
        device.updated_at = now

        # Revoke credentials
        db.query(DeviceCredentialMetadataModel).filter(
            DeviceCredentialMetadataModel.device_id == device_id
        ).update(
            {"revoked": True, "revoked_at": now, "revocation_reason": reason},
            synchronize_session=False,
        )

        audit = DeviceAuditLogModel(
            id=f"AUD-{uuid.uuid4().hex[:10].upper()}",
            device_id=device_id,
            action="CREDENTIAL_REVOCATION",
            actor=actor,
            status="SUCCESS",
            ip_address="127.0.0.1",
            details={"reason": reason},
            timestamp=now,
        )
        db.add(audit)
        db.commit()

    @staticmethod
    def quarantine_device(db: Session, device_id: str, reason: str, actor: str = "system") -> None:
        """Quarantines a compromised or misbehaving device."""
        device = IotRepository.get_by_id_simple(db, device_id)
        if not device:
            raise ValueError(f"Device {device_id} not found.")

        now = datetime.now(timezone.utc)
        device.status = "QUARANTINED"
        device.auth_status = "QUARANTINED"
        device.updated_at = now

        audit = DeviceAuditLogModel(
            id=f"AUD-{uuid.uuid4().hex[:10].upper()}",
            device_id=device_id,
            action="QUARANTINE",
            actor=actor,
            status="SUCCESS",
            ip_address="127.0.0.1",
            details={"reason": reason},
            timestamp=now,
        )
        db.add(audit)
        db.commit()

    @staticmethod
    def get_by_id_simple(db: Session, device_id: str) -> Optional[IoTDeviceModel]:
        return db.query(IoTDeviceModel).filter(IoTDeviceModel.id == device_id).first()

    @staticmethod
    def log_audit_event(
        db: Session,
        device_id: str,
        action: str,
        actor: str = "system",
        status: str = "SUCCESS",
        ip_address: str = "127.0.0.1",
        details: Optional[Dict[str, Any]] = None,
    ) -> DeviceAuditLogModel:
        """Records a tamper-evident IoT audit event."""
        audit = DeviceAuditLogModel(
            id=f"AUD-{uuid.uuid4().hex[:10].upper()}",
            device_id=device_id,
            action=action.upper(),
            actor=actor,
            status=status.upper(),
            ip_address=ip_address,
            details=details or {},
            timestamp=datetime.now(timezone.utc),
        )
        db.add(audit)
        db.commit()
        return audit

    @staticmethod
    def get_overview_metrics(db: Session) -> Dict[str, Any]:
        """Computes aggregate IoT fleet metrics."""
        devices = db.query(IoTDeviceModel).all()
        now = datetime.now(timezone.utc)
        total = len(devices)
        active = sum(1 for d in devices if d.status == "ACTIVE")
        offline = sum(1 for d in devices if d.status == "OFFLINE")
        degraded = sum(1 for d in devices if d.status == "DEGRADED")
        quarantined = sum(1 for d in devices if d.status == "QUARANTINED")
        calibration_overdue = sum(1 for d in devices if d.calibration_status == "OVERDUE")

        # Telemetries count
        telemetry_count = db.query(DeviceTelemetryModel).count()
        recent_events = db.query(DeviceAuditLogModel).order_by(desc(DeviceAuditLogModel.timestamp)).limit(10).all()

        return {
            "total_devices": total,
            "active_devices": active,
            "offline_devices": offline,
            "degraded_devices": degraded,
            "quarantined_devices": quarantined,
            "calibration_overdue_devices": calibration_overdue,
            "total_telemetries_ingested": telemetry_count,
            "recent_audit_events": [
                {
                    "id": a.id,
                    "device_id": a.device_id,
                    "action": a.action,
                    "status": a.status,
                    "actor": a.actor,
                    "timestamp": a.timestamp.isoformat() if a.timestamp else now.isoformat(),
                }
                for a in recent_events
            ],
        }

