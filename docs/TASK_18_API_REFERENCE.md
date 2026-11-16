# AQUA CREW — TASK 18 REST API REFERENCE
## IoT & Hardware Gateway API Specification

> [!NOTE]
> All endpoints are mounted under `/api/v1/iot` and return standardized JSON responses. Authentication requires an HTTP Bearer JWT token or direct `X-Device-Secret` header for edge telemetry ingestion.

---

## 1. Fleet Status & Health Probes

### `GET /api/v1/iot/status`
Returns high-level fleet overview metrics, active device counts by type and DMA, and MQTT gateway operational status.
- **Authorization**: `VIEWER` or higher.
- **Response**: `200 OK`
```json
{
  "success": true,
  "metrics": {
    "total_devices": 6,
    "active_devices": 5,
    "offline_devices": 0,
    "degraded_devices": 1,
    "quarantined_devices": 0,
    "revoked_devices": 0,
    "total_sensors": 10,
    "calibrated_sensors": 8,
    "overdue_calibrations": 2,
    "telemetry_readings_24h": 18450,
    "data_quality_pct": 98.4
  },
  "mqtt_status": {
    "connected": false,
    "broker_host": "127.0.0.1",
    "broker_port": 8883,
    "simulation_mode": true
  },
  "hardware_safety": "SIMULATION_FIRST_MODE_ACTIVE",
  "timestamp": "2026-11-16T14:35:00.000Z"
}
```

### `GET /api/v1/iot/health`
Lightweight unauthenticated health probe for load balancers and orchestrators.
- **Response**: `200 OK`
```json
{
  "status": "HEALTHY",
  "gateway": "SIMULATION_FIRST_GATEWAY",
  "mqtt_connected": false,
  "hardware_actuators": "DISABLED_AIR_GAP"
}
```

---

## 2. Device Registry & Credential Management

### `GET /api/v1/iot/devices`
List registered IoT devices with optional filters.
- **Query Parameters**:
  - `status` (string, optional): `ACTIVE`, `OFFLINE`, `DEGRADED`, `QUARANTINED`, `REVOKED`.
  - `device_type` (string, optional): Filter by archetype.
  - `dma_zone` (string, optional): Filter by municipal DMA.
  - `search` (string, optional): Search ID, name, manufacturer.
  - `skip` (int, default: 0), `limit` (int, default: 50).
- **Authorization**: `VIEWER` or higher.

### `POST /api/v1/iot/devices`
Registers a new physical or virtual sensor node.
- **Authorization**: `OPERATOR` or higher.
- **Request Body**:
```json
{
  "id": "DEV-ACOUSTIC-09",
  "name": "District 4 Spine Hydrophone",
  "device_type": "ACOUSTIC_LOGGER",
  "manufacturer": "AquaSense Nordic",
  "hardware_model": "HYD-ESP32-S3",
  "firmware_version": "v1.4.2",
  "dma_zone": "DMA-METRO-CENTRAL",
  "pipeline_segment_id": "PIPE-SEC-4B-92",
  "supported_sensor_types": ["acoustic"],
  "is_simulated": false
}
```
- **Response**: `201 Created`
```json
{
  "success": true,
  "device": { "id": "DEV-ACOUSTIC-09", "status": "REGISTERED", ... },
  "api_key": "aqdev_dev-ac_x819204812301...",
  "message": "Device registered successfully. Store API key safely."
}
```

### `POST /api/v1/iot/devices/{device_id}/quarantine`
Places a misbehaving or suspicious device into security quarantine.
- **Authorization**: `ADMINISTRATOR`.
- **Request Body**: `{ "reason": "High frequency acoustic spikes detected" }`

### `POST /api/v1/iot/devices/{device_id}/revoke`
Permanently revokes a device and all associated credentials.
- **Authorization**: `ADMINISTRATOR`.
- **Request Body**: `{ "reason": "Hardware decommissioned" }`

### `POST /api/v1/iot/devices/{device_id}/credentials/rotate`
Invalidates active credentials and issues a fresh API key.
- **Authorization**: `ADMINISTRATOR`.
- **Response**: `200 OK` `{ "success": true, "key_prefix": "aqdev_...", "version": 2, ... }`

---

## 3. Device Commands (Allowlisted Only)

### `POST /api/v1/iot/devices/{device_id}/commands`
Dispatches an allowlisted non-actuating command to the target device.
- **Authorization**: `OPERATOR` or higher.
- **Request Body**:
```json
{
  "command": "RUN_DEVICE_DIAGNOSTICS",
  "parameters": {}
}
```
- **Response**: `200 OK`
```json
{
  "success": true,
  "device_id": "DEV-ACOUSTIC-01",
  "command": "RUN_DEVICE_DIAGNOSTICS",
  "status": "EXECUTED",
  "result": { "diagnostic_check": "PASSED", "battery_level_pct": 94.0 },
  "safety_state": "HARDWARE_ACTUATION_DISABLED"
}
```
- **Rejection of Actuation**:
Submitting any actuation command (e.g., `{"command": "CLOSE_VALVE"}`) returns `403 Forbidden`:
```json
{
  "success": false,
  "error": {
    "code": "HARDWARE_ACTUATION_PROHIBITED",
    "message": "Physical infrastructure actuation 'CLOSE_VALVE' is strictly prohibited by platform safety policy."
  }
}
```

---

## 4. Telemetry Ingestion & Quality

### `POST /api/v1/iot/telemetry/ingest`
Ingests, validates, and normalizes a single telemetry packet.
- **Headers**: `Authorization: Bearer <jwt>` OR `X-Device-Secret: <api_key>`.
- **Request Body**:
```json
{
  "device_id": "DEV-ACOUSTIC-01",
  "sensor_id": "SNS-AC-01-A",
  "sensor_type": "acoustic",
  "value": 64.2,
  "unit": "dB",
  "provenance": "MEASURED"
}
```

### `POST /api/v1/iot/telemetry/ingest/batch`
Ingests up to 100 buffered telemetry readings from an edge concentrator.
- **Headers**: `Authorization: Bearer <jwt>` OR `X-Device-Secret: <api_key>`.
- **Request Body**: `{ "readings": [ ... ] }`

---

## 5. Sensor Calibration

### `GET /api/v1/iot/calibration`
List calibration records with optional filtering by `device_id` or `sensor_id`.
- **Authorization**: `VIEWER` or higher.

### `POST /api/v1/iot/calibration`
Register a newly certified calibration standard.
- **Authorization**: `OPERATOR` or higher.
- **Request Body**:
```json
{
  "device_id": "DEV-PRESSURE-02",
  "sensor_id": "SNS-PR-02-A",
  "calibration_method": "DEADWEIGHT_TESTER",
  "calibration_reference": "STD-DWT-2026",
  "calibration_result": "PASS",
  "accuracy_tolerance": 0.015,
  "technician": "Ing. Marcus Vance",
  "certificate_reference": "CERT-2026-PR-902",
  "next_due_date": "2027-02-15T00:00:00Z"
}
```

---

## 6. Cross-Module Bridges

### `GET /api/v1/iot/digital-twin-comparison`
Evaluates hydraulic deviation between sensor observation and EPANET baseline model.
- **Parameters**: `pipeline_segment_id`, `observed_pressure_bar`, `observed_flow_lps`.
- **Response**: `200 OK` `{ "pressure_delta_bar": -0.38, "pressure_deviation_pct": -8.44, ... }`

### `GET /api/v1/iot/leak-analysis`
Routes acoustic observations to Task 07 AI acoustic classifier.
- **Parameters**: `device_id`, `acoustic_spl_db`, `dominant_freq_hz`, `pressure_bar`.
- **Response**: `200 OK` `{ "classification": "MEDIUM_LEAK_PROBABILITY", "anomaly_score": 0.65, ... }`

### `GET /api/v1/iot/audit`
Returns immutable ledger of security events, key rotations, and rejected commands.
- **Authorization**: `ADMINISTRATOR` only.

