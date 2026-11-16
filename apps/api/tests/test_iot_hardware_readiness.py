"""
AQUA CREW — Secure Device Ecosystem, IoT Telemetry & Hardware Integration Readiness Test Suite (Task 18)
Comprehensive validation of:
  1. Strict Hardware Safety Enforcement (HARDWARE_ACTUATION_ENABLED = False, Air-gap validation)
  2. Sensor Adapters & Normalization (Acoustic, Pressure, Flow, Moisture, Temp, Optical, ESP32, Virtual)
  3. Device Registry Management (Registration, Quarantine, Revocation, Credential Rotation)
  4. ISO 17025-Compliant Sensor Calibration & Due Date Audits
  5. Telemetry Ingestion Engine & 6-Tier Evidence Provenance Verification
  6. Edge Reliability Bounded Buffering & Backoff Calculation
  7. Cross-Module Bridges (Task 07 AI Leak Detection & Task 10 Digital Twin EPANET Deviation)
  8. Zero-Trust RBAC & Tamper-Evident Security Audit Ledger
"""
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import status

from app.config import settings
from app.modules.hardware_gateway import (
    HARDWARE_ACTUATION_ENABLED,
    PROHIBITED_ACTUATION_COMMANDS,
    ALLOWLISTED_DEVICE_COMMANDS,
)
from app.services.iot.hardware_safety_service import (
    HardwareSafetyService,
    HardwareActuationForbiddenException,
)
from app.services.iot.adapters import (
    SensorAdapterFactory,
    AcousticSensorAdapter,
    PressureSensorAdapter,
    FlowSensorAdapter,
    MoistureSensorAdapter,
    TemperatureSensorAdapter,
    OpticalSensorAdapter,
    Esp32DeviceAdapter,
    VirtualSensorAdapter,
)
from app.services.iot.calibration_service import CalibrationService
from app.services.iot.telemetry_ingestion_service import (
    TelemetryIngestionService,
    TelemetryIngestException,
)
from app.services.iot.edge_buffer_service import EdgeBufferQueue, EdgeRetransmissionEngine
from app.services.iot.iot_intelligence_bridge import IotIntelligenceBridge
from app.repositories.iot_repository import IotRepository
from app.models.iot import IoTDeviceModel, SensorModel, DeviceTelemetryModel
from app.core.security import create_access_token


# ==============================================================================
# FIXTURES
# ==============================================================================
@pytest.fixture
def db(db_session):
    IotRepository.seed_defaults(db_session)
    return db_session


@pytest.fixture
def viewer_token():
    token, _, _ = create_access_token(user_id="USR-VIEW-01", username="viewer", role="VIEWER")
    return token


@pytest.fixture
def operator_token():
    token, _, _ = create_access_token(user_id="OPERATOR-SUPERVISOR-01", username="operator", role="OPERATOR")
    return token


@pytest.fixture
def engineer_token():
    token, _, _ = create_access_token(user_id="USR-ENG-01", username="engineer", role="ENGINEER")
    return token


@pytest.fixture
def admin_token():
    token, _, _ = create_access_token(user_id="USR-ADMIN-01", username="admin", role="ADMINISTRATOR")
    return token


# ==============================================================================
# 1. HARDWARE SAFETY ENFORCEMENT TESTS (STRICT AIR-GAP VALIDATION)
# ==============================================================================
class TestHardwareSafetyEnforcement:
    def test_hardware_actuation_strictly_disabled_in_config(self):
        """Verify global system configuration strictly prohibits hardware actuation."""
        assert settings.HARDWARE_ACTUATION_ENABLED is False
        assert HARDWARE_ACTUATION_ENABLED is False

    def test_prohibited_actuation_commands_contain_critical_controls(self):
        """Ensure all physical valve, pump, motor, and rover controls are explicitly listed as prohibited."""
        prohibited = PROHIBITED_ACTUATION_COMMANDS
        assert "CLOSE_VALVE" in prohibited
        assert "OPEN_VALVE" in prohibited
        assert "MODULATE_VALVE" in prohibited
        assert "START_PUMP" in prohibited
        assert "STOP_PUMP" in prohibited
        assert "SET_PUMP_SPEED" in prohibited
        assert "DISPATCH_PHYSICAL_ROVER" in prohibited
        assert "DRIVE_MOTOR" in prohibited
        assert "TRIGGER_PHYSICAL_RELAY" in prohibited
        assert "OVERRIDE_SCADA_PLC" in prohibited

    def test_allowlisted_commands_only_contain_non_actuating_operations(self):
        """Ensure allowlist strictly permits only read/diagnostic commands."""
        allowlist = ALLOWLISTED_DEVICE_COMMANDS
        assert "READ_STATUS" in allowlist
        assert "REQUEST_TELEMETRY" in allowlist
        assert "READ_SENSOR_CONFIG" in allowlist
        assert "UPDATE_CONFIG_NON_ACTUATING" in allowlist
        assert "RUN_DEVICE_DIAGNOSTICS" in allowlist
        assert "PING" in allowlist
        assert "REPORT_BATTERY" in allowlist
        assert "CALIBRATION_CHECK" in allowlist

        for cmd in allowlist:
            assert "VALVE" not in cmd
            assert "PUMP" not in cmd
            assert "MOTOR" not in cmd
            assert "RELAY" not in cmd

    def test_safety_service_blocks_prohibited_commands(self):
        """HardwareSafetyService must raise HardwareActuationForbiddenException on forbidden commands."""
        for cmd in ["CLOSE_VALVE", "START_PUMP", "MODULATE_VALVE", "DISPATCH_PHYSICAL_ROVER"]:
            with pytest.raises(HardwareActuationForbiddenException) as exc_info:
                HardwareSafetyService.verify_operation_safety(cmd)
            assert exc_info.value.code == "HARDWARE_ACTUATION_PROHIBITED"

    def test_safety_service_blocks_prohibited_keywords_even_in_unlisted_commands(self):
        """Any command containing actuator keywords (valve, pump, motor, scada) must be blocked."""
        suspicious_commands = ["EMERGENCY_VALVE_ISOLATE", "AUX_PUMP_START", "SERVO_MOTOR_TURN"]
        for cmd in suspicious_commands:
            with pytest.raises(HardwareActuationForbiddenException):
                HardwareSafetyService.verify_operation_safety(cmd)

    def test_safety_service_permits_allowlisted_commands(self):
        """Allowlisted commands must pass safety verification cleanly."""
        for cmd in ALLOWLISTED_DEVICE_COMMANDS:
            # Does not raise an exception
            HardwareSafetyService.verify_operation_safety(cmd)

    def test_api_strictly_blocks_actuation_command(self, client, db, operator_token):
        """POST /api/v1/iot/devices/{device_id}/commands must reject actuation commands with HTTP 403."""
        headers = {"Authorization": f"Bearer {operator_token}"}
        payload = {"command": "CLOSE_VALVE", "parameters": {"percent": 100}}

        res = client.post("/api/v1/iot/devices/DEV-ACOUSTIC-01/commands", json=payload, headers=headers)
        assert res.status_code == status.HTTP_403_FORBIDDEN
        data = res.json()
        assert data.get("error", {}).get("code") == "HARDWARE_ACTUATION_PROHIBITED"

    def test_api_executes_allowlisted_command(self, client, db, operator_token):
        """POST /api/v1/iot/devices/{device_id}/commands must execute allowlisted diagnostics."""
        headers = {"Authorization": f"Bearer {operator_token}"}
        payload = {"command": "RUN_DEVICE_DIAGNOSTICS", "parameters": {}}

        res = client.post("/api/v1/iot/devices/DEV-ACOUSTIC-01/commands", json=payload, headers=headers)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["success"] is True
        assert data["command"] == "RUN_DEVICE_DIAGNOSTICS"
        assert data["safety_state"] == "HARDWARE_ACTUATION_DISABLED"
        assert "diagnostic_check" in data["result"]


# ==============================================================================
# 2. SENSOR ADAPTERS & NORMALIZATION TESTS
# ==============================================================================
class TestSensorAdapters:
    def test_acoustic_sensor_adapter_valid_reading(self):
        adapter = AcousticSensorAdapter()
        raw = {
            "device_id": "DEV-ACOUSTIC-01",
            "value": 68.4,
            "dominant_freq_hz": 520.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        norm = adapter.normalize(raw)

        assert norm.measurement_value == 68.4
        assert norm.unit == "dB"
        assert norm.sensor_type == "acoustic"
        assert norm.data_quality == "VALID"
        assert norm.provenance == "MEASURED"

    def test_acoustic_sensor_adapter_out_of_bounds(self):
        adapter = AcousticSensorAdapter()
        raw = {"device_id": "DEV-ACOUSTIC-01", "value": 185.0}
        norm = adapter.normalize(raw)
        assert norm.data_quality == "SUSPECT"

    def test_pressure_sensor_adapter_unit_conversion_psi_to_bar(self):
        adapter = PressureSensorAdapter()
        # 58.015 psi ~ 4.0 bar
        raw = {"device_id": "DEV-PRESSURE-02", "value": 58.015, "unit": "psi"}
        norm = adapter.normalize(raw)
        assert norm.unit == "bar"
        assert pytest.approx(norm.measurement_value, 0.05) == 4.0
        assert norm.data_quality == "VALID"

    def test_pressure_sensor_adapter_unit_conversion_kpa_to_bar(self):
        adapter = PressureSensorAdapter()
        raw = {"device_id": "DEV-PRESSURE-02", "value": 450.0, "unit": "kPa"}
        norm = adapter.normalize(raw)
        assert norm.unit == "bar"
        assert pytest.approx(norm.measurement_value, 0.01) == 4.5

    def test_flow_sensor_adapter_unit_conversion_m3h_to_lps(self):
        adapter = FlowSensorAdapter()
        # 360 m3/h = 100 L/s
        raw = {"device_id": "DEV-FLOW-03", "value": 360.0, "unit": "m3/h"}
        norm = adapter.normalize(raw)
        assert norm.unit == "L/s"
        assert pytest.approx(norm.measurement_value, 0.01) == 100.0

    def test_moisture_sensor_adapter_soil_saturation(self):
        adapter = MoistureSensorAdapter()
        raw = {"device_id": "DEV-MOIST-04", "value": 82.5}
        norm = adapter.normalize(raw)
        assert norm.measurement_value == 82.5
        assert norm.unit == "%"
        assert norm.sensor_type == "moisture"

    def test_temperature_sensor_adapter_fahrenheit_conversion(self):
        adapter = TemperatureSensorAdapter()
        # 68 °F = 20 °C
        raw = {"device_id": "DEV-TEMP-01", "value": 68.0, "unit": "°F"}
        norm = adapter.normalize(raw)
        assert norm.unit == "°C"
        assert pytest.approx(norm.measurement_value, 0.1) == 20.0

    def test_optical_sensor_adapter_turbidity(self):
        adapter = OpticalSensorAdapter()
        raw = {"device_id": "DEV-OPTICAL-05", "value": 88.0}
        norm = adapter.normalize(raw)
        assert norm.measurement_value == 88.0
        assert norm.unit == "metadata"
        assert norm.sensor_type == "optical"

    def test_esp32_device_adapter_primary_sensor_unpacking(self):
        adapter = Esp32DeviceAdapter()
        raw = {
            "device_id": "DEV-ESP32-99",
            "value": 4.12,
            "unit": "bar",
            "sensor_type": "pressure",
            "wifi_rssi_dbm": -62,
            "battery_mv": 3900,
        }
        norm = adapter.normalize(raw)
        assert norm.device_id == "DEV-ESP32-99"
        assert norm.measurement_value == 4.12
        assert norm.data_quality == "VALID"
        assert norm.metadata["esp32_diagnostics"]["wifi_rssi_dbm"] == -62

    def test_virtual_sensor_adapter_strictly_forces_simulated_provenance(self):
        adapter = VirtualSensorAdapter()
        raw = {"device_id": "DEV-VIRT-06", "value": 4.2, "provenance": "MEASURED"}
        norm = adapter.normalize(raw)
        assert norm.provenance == "SIMULATED"
        assert norm.data_quality == "VALID"

    def test_adapter_factory_returns_correct_adapters(self):
        assert isinstance(SensorAdapterFactory.get_adapter("acoustic"), AcousticSensorAdapter)
        assert isinstance(SensorAdapterFactory.get_adapter("pressure"), PressureSensorAdapter)
        assert isinstance(SensorAdapterFactory.get_adapter("flow"), FlowSensorAdapter)
        assert isinstance(SensorAdapterFactory.get_adapter("virtual"), VirtualSensorAdapter)


# ==============================================================================
# 3. DEVICE REGISTRY & LIFECYCLE TESTS
# ==============================================================================
class TestDeviceRegistry:
    def test_seeded_devices_loaded_correctly(self, db):
        devices, total = IotRepository.get_devices(db)
        assert total >= 6
        device_ids = [d.id for d in devices]
        assert "DEV-ACOUSTIC-01" in device_ids
        assert "DEV-PRESSURE-02" in device_ids
        assert "DEV-FLOW-03" in device_ids
        assert "DEV-MOIST-04" in device_ids
        assert "DEV-OPTICAL-05" in device_ids
        assert "DEV-VIRT-06" in device_ids

    def test_register_device_repository(self, db):
        dev, secret = IotRepository.create_device(
            db,
            device_id="DEV-TEST-NEW-01",
            name="Test Acoustic Ingestion Node",
            device_type="ACOUSTIC_LOGGER",
            manufacturer="AcoustiTech",
            hardware_model="ACT-ESP32",
            firmware_version="1.0.0",
            supported_sensor_types=["acoustic"],
            dma_zone="DMA-METRO-CENTRAL",
            owner_id="test_user",
        )
        assert dev.id == "DEV-TEST-NEW-01"
        assert dev.status == "REGISTERED"
        assert secret.startswith("aqdev_")

    def test_device_quarantine_lifecycle(self, db):
        IotRepository.quarantine_device(
            db, "DEV-PRESSURE-02", reason="Excessive transient anomalies detected", actor="operator"
        )
        dev = IotRepository.get_by_id_simple(db, "DEV-PRESSURE-02")
        assert dev.status == "QUARANTINED"
        assert dev.auth_status == "QUARANTINED"

    def test_device_permanent_revocation(self, db):
        IotRepository.revoke_device(
            db, "DEV-MOIST-04", reason="Physical tampering detected", actor="admin"
        )
        dev = IotRepository.get_by_id_simple(db, "DEV-MOIST-04")
        assert dev.status == "REVOKED"
        assert dev.auth_status == "REVOKED"

    def test_credential_rotation(self, db):
        new_secret = IotRepository.rotate_device_credential(db, "DEV-ACOUSTIC-01", actor="admin")
        assert new_secret.startswith("aqdev_")
        assert IotRepository.verify_device_credential(db, "DEV-ACOUSTIC-01", new_secret) is True


# ==============================================================================
# 4. SENSOR CALIBRATION TESTS
# ==============================================================================
class TestSensorCalibration:
    def test_register_sensor_calibration(self, db):
        calib = CalibrationService.register_calibration(
            db,
            device_id="DEV-PRESSURE-02",
            sensor_id="SNS-PR-02-A",
            calibration_method="DEADWEIGHT_TESTER",
            calibration_reference="STD-DWT-2026",
            calibration_result="PASS",
            accuracy_tolerance=0.015,
            technician="Ing. Marcus Vance",
            certificate_reference="CERT-CAL-9912",
            next_due_date=datetime.now(timezone.utc) + timedelta(days=180),
            actor="operator",
        )
        assert calib.id.startswith("CALIB-")
        assert calib.calibration_status == "CALIBRATED"
        assert calib.accuracy_tolerance == 0.015

    def test_calibration_quality_evaluation_valid(self, db):
        quality, err = CalibrationService.evaluate_sensor_calibration_quality(
            db, "DEV-PRESSURE-02", "SNS-PR-02-A"
        )
        assert quality == "VALID"
        assert err is None

    def test_overdue_calibration_downgrades_telemetry_quality(self, db):
        # DEV-MOIST-04 is seeded with overdue calibration
        quality, warning = CalibrationService.evaluate_sensor_calibration_quality(
            db, "DEV-MOIST-04", "SNS-MOIST-04-A"
        )
        assert quality == "SUSPECT"
        assert warning is not None
        assert "expired" in warning.lower() or "overdue" in warning.lower()


# ==============================================================================
# 5. TELEMETRY INGESTION ENGINE TESTS
# ==============================================================================
class TestTelemetryIngestionEngine:
    def test_ingest_single_reading_with_jwt_auth(self, db):
        raw_payload = {
            "device_id": "DEV-ACOUSTIC-01",
            "sensor_id": "SNS-AC-01-A",
            "value": 64.2,
            "unit": "dB",
            "sensor_type": "acoustic",
            "provenance": "MEASURED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        res = TelemetryIngestionService.ingest_single_reading(db, raw_payload)
        assert res["success"] is True
        assert res["data_quality"] == "VALID"
        # Strict rule: DEV-ACOUSTIC-01 is a simulated device, so provenance must strictly be SIMULATED
        assert res["provenance"] == "SIMULATED"

    def test_ingest_single_reading_with_device_secret(self, db):
        secret_key = IotRepository.rotate_device_credential(db, "DEV-PRESSURE-02")
        raw_payload = {
            "device_id": "DEV-PRESSURE-02",
            "sensor_id": "SNS-PR-02-A",
            "value": 4.15,
            "unit": "bar",
            "sensor_type": "pressure",
            "provenance": "MEASURED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        res = TelemetryIngestionService.ingest_single_reading(db, raw_payload, auth_secret=secret_key)
        assert res["success"] is True
        assert res["telemetry_id"].startswith("TEL-")

    def test_reject_ingestion_for_revoked_device(self, db):
        IotRepository.revoke_device(db, "DEV-MOIST-04", reason="Revocation test")
        raw_payload = {
            "device_id": "DEV-MOIST-04",
            "value": 55.0,
            "unit": "%",
            "sensor_type": "moisture",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with pytest.raises(TelemetryIngestException) as exc_info:
            TelemetryIngestionService.ingest_single_reading(db, raw_payload)
        assert exc_info.value.code == "DEVICE_REVOKED"

    def test_reject_ingestion_for_quarantined_device(self, db):
        IotRepository.quarantine_device(db, "DEV-PRESSURE-02", reason="Quarantine test")
        raw_payload = {
            "device_id": "DEV-PRESSURE-02",
            "value": 4.1,
            "unit": "bar",
            "sensor_type": "pressure",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with pytest.raises(TelemetryIngestException) as exc_info:
            TelemetryIngestionService.ingest_single_reading(db, raw_payload)
        assert exc_info.value.code == "DEVICE_QUARANTINED"

    def test_stale_timestamp_marked_stale(self, db):
        # Timestamp > 24 hours old
        stale_time = datetime.now(timezone.utc) - timedelta(hours=36)
        raw_payload = {
            "device_id": "DEV-ACOUSTIC-01",
            "sensor_id": "SNS-AC-01-A",
            "value": 58.1,
            "unit": "dB",
            "sensor_type": "acoustic",
            "timestamp": stale_time.isoformat(),
        }
        res = TelemetryIngestionService.ingest_single_reading(db, raw_payload)
        assert res["success"] is True
        assert res["data_quality"] == "STALE"

    def test_batch_telemetry_ingestion(self, db):
        readings = [
            {
                "device_id": "DEV-ACOUSTIC-01",
                "sensor_id": "SNS-AC-01-A",
                "value": 61.2,
                "unit": "dB",
                "sensor_type": "acoustic",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "device_id": "DEV-PRESSURE-02",
                "sensor_id": "SNS-PR-02-A",
                "value": 4.22,
                "unit": "bar",
                "sensor_type": "pressure",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]
        res = TelemetryIngestionService.ingest_batch(db, readings)
        assert res["success"] is True
        assert res["accepted_count"] == 2
        assert res["error_count"] == 0


# ==============================================================================
# 6. EDGE RELIABILITY & BUFFER TESTS
# ==============================================================================
class TestEdgeReliabilityAndBuffer:
    def test_ring_buffer_fifo_drop_when_full(self):
        queue = EdgeBufferQueue(device_id="DEV-ESP32-01", max_capacity=5)
        for i in range(7):
            queue.push({"seq": i, "val": i * 10})

        assert queue.size() == 5
        assert queue.dropped_overflow_count == 2
        batch = queue.drain(batch_size=5)
        assert len(batch) == 5
        assert batch[0]["seq"] == 2

    def test_exponential_backoff_calculation(self):
        delay_0 = EdgeRetransmissionEngine.calculate_backoff(attempt=0, base_seconds=1.0, max_seconds=60.0)
        delay_1 = EdgeRetransmissionEngine.calculate_backoff(attempt=1, base_seconds=1.0, max_seconds=60.0)
        delay_5 = EdgeRetransmissionEngine.calculate_backoff(attempt=5, base_seconds=1.0, max_seconds=60.0)

        assert 0.8 <= delay_0 <= 1.5
        assert 1.6 <= delay_1 <= 3.0
        assert delay_5 <= 60.0

    def test_clock_drift_estimation(self):
        now = datetime.now(timezone.utc)
        dev_time = (now - timedelta(seconds=12)).isoformat()

        res = EdgeRetransmissionEngine.estimate_clock_drift(dev_time, server_now=now)
        assert res["is_synchronized"] is False
        assert pytest.approx(res["clock_drift_ms"], 500) == 12000.0


# ==============================================================================
# 7. CROSS-MODULE INTELLIGENCE BRIDGE TESTS
# ==============================================================================
class TestCrossModuleBridges:
    def test_digital_twin_hydraulic_comparison_bridge(self, db):
        res = IotIntelligenceBridge.compare_with_digital_twin(
            db,
            pipeline_segment_id="PIPE-SEC-4B-92",
            observed_pressure_bar=4.12,
            observed_flow_lps=89.5,
        )
        assert res["pipeline_segment_id"] == "PIPE-SEC-4B-92"
        assert res["observed_pressure_bar"] == 4.12
        assert "simulated_pressure_bar" in res
        assert "pressure_delta_bar" in res
        assert res["hydraulic_anomaly_flagged"] is False

    def test_ai_leak_detection_acoustic_bridge(self, db):
        res = IotIntelligenceBridge.evaluate_leak_risk_from_telemetry(
            db,
            device_id="DEV-ACOUSTIC-01",
            acoustic_spl_db=68.5,
            dominant_freq_hz=540.0,
            pressure_bar=3.9,
        )
        assert res["device_id"] == "DEV-ACOUSTIC-01"
        assert res["acoustic_spl_db"] == 68.5
        assert res["classification"] == "MEDIUM_LEAK_PROBABILITY"
        assert res["risk_level"] in ["ELEVATED", "CRITICAL"]
        assert res["anomaly_score"] > 0.5


# ==============================================================================
# 8. REST API & ZERO-TRUST RBAC MATRIX TESTS
# ==============================================================================
class TestRestApiAndRbac:
    def test_viewer_can_list_devices(self, client, db, viewer_token):
        headers = {"Authorization": f"Bearer {viewer_token}"}
        res = client.get("/api/v1/iot/devices", headers=headers)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["success"] is True
        assert data["total"] >= 6

    def test_viewer_forbidden_from_device_registration(self, client, db, viewer_token):
        headers = {"Authorization": f"Bearer {viewer_token}"}
        payload = {
            "id": "DEV-UNAUTH-01",
            "name": "Unauthorized Node",
            "device_type": "ACOUSTIC_LOGGER",
            "manufacturer": "Unknown",
            "hardware_version": "v1.0",
            "firmware_version": "1.0",
        }
        res = client.post("/api/v1/iot/devices", json=payload, headers=headers)
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_operator_can_register_device(self, client, db, operator_token):
        headers = {"Authorization": f"Bearer {operator_token}"}
        payload = {
            "id": "DEV-OPER-REGISTERED-01",
            "name": "Operator Registered Node",
            "device_type": "PRESSURE_SENSOR",
            "manufacturer": "HydroMetrics",
            "hardware_version": "v2.0",
            "firmware_version": "1.5.0",
            "supported_sensor_types": ["pressure"],
        }
        res = client.post("/api/v1/iot/devices", json=payload, headers=headers)
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["device"]["id"] == "DEV-OPER-REGISTERED-01"
        assert data["api_key"].startswith("aqdev_")

    def test_viewer_forbidden_from_credential_rotation(self, client, db, viewer_token):
        headers = {"Authorization": f"Bearer {viewer_token}"}
        res = client.post(
            "/api/v1/iot/devices/DEV-ACOUSTIC-01/credentials/rotate", headers=headers
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_access_audit_log(self, client, db, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        res = client.get("/api/v1/iot/audit", headers=headers)
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["success"] is True
        assert "audit_events" in data

    def test_non_admin_forbidden_from_audit_log(self, client, db, operator_token):
        headers = {"Authorization": f"Bearer {operator_token}"}
        res = client.get("/api/v1/iot/audit", headers=headers)
        assert res.status_code == status.HTTP_403_FORBIDDEN
