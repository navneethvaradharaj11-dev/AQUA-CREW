# AQUA CREW — TASK 18 TELEMETRY SCHEMA & NORMALIZATION SPECIFICATION

> [!NOTE]
> All telemetry entering AQUA CREW—whether streamed over MQTT or posted via HTTPS REST—is validated against strict JSON schemas, normalized into canonical SI units, audited for physical plausible limits, and assigned an immutable 6-tier provenance classification.

---

## 1. Single Telemetry Ingestion Contract

### JSON Request Schema (`POST /api/v1/iot/telemetry/ingest`)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TelemetryIngestPayload",
  "type": "object",
  "required": ["device_id", "value"],
  "properties": {
    "device_id": {
      "type": "string",
      "description": "Unique device identifier matching registered hardware catalog."
    },
    "sensor_id": {
      "type": "string",
      "description": "Specific sensor component identifier. If omitted, resolved via device mapping."
    },
    "sensor_type": {
      "type": "string",
      "enum": ["acoustic", "pressure", "flow", "moisture", "temperature", "optical"],
      "description": "Measurement domain."
    },
    "value": {
      "type": "number",
      "description": "Raw numeric measurement value."
    },
    "unit": {
      "type": "string",
      "enum": ["dB", "bar", "psi", "kpa", "L/s", "lps", "m3/h", "%", "°C", "°F", "C", "F", "metadata"],
      "description": "Engineering unit of the raw measurement."
    },
    "seq": {
      "type": "integer",
      "minimum": 1,
      "description": "Monotonically increasing sequence number from edge device."
    },
    "provenance": {
      "type": "string",
      "enum": ["MEASURED", "SIMULATED", "DERIVED", "PREDICTED", "OPERATOR_ENTERED", "UNKNOWN"],
      "default": "MEASURED"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp recorded by device RTC."
    },
    "metadata": {
      "type": "object",
      "description": "Optional edge telemetry diagnostics (e.g. RSSI, battery voltage, dominant frequency)."
    }
  }
}
```

---

## 2. 6-Tier Evidence Provenance Rules

| Provenance Level | Description | Enforcement Rule |
|---|---|---|
| `MEASURED` | Ground-truth physical instrument observation. | Valid ONLY if the device is physical (`is_simulated = false`). If a virtual device reports `MEASURED`, the ingestion engine automatically demotes it to `SIMULATED`. |
| `SIMULATED` | Produced by hydraulic digital twin (EPANET) or synthetic physics generator. | Automatically assigned to any reading originating from `is_simulated = true` nodes or `VIRTUAL_SIMULATION_DEVICE` archetypes. |
| `DERIVED` | Calculated deterministically from one or more measurements (e.g. $\Delta P$, hydraulic headloss). | Set when algorithms compute secondary metrics. |
| `PREDICTED` | Output of ML or predictive models (e.g. Task 09 remaining useful life). | Set when values represent prospective forecasts. |
| `OPERATOR_ENTERED` | Manually keyed in by authorized technicians. | Set when values originate from human manual entry. |
| `UNKNOWN` | Unverified origin or mismatched signature. | Fallback when origin metadata is missing. |

---

## 3. Data Quality Classification Taxonomy

Every reading processed by `TelemetryIngestionService` receives a computed `data_quality` status:

| Quality Tier | Condition | System Action |
|---|---|---|
| `VALID` | Passes all range bounds, timestamp checks, and certified calibration is up to date. | Accepted; routed to Task 07 AI and Task 10 Digital Twin. |
| `SUSPECT` | Minor anomaly detected (e.g. sensor calibration is expired/overdue, out-of-order sequence). | Stored with warning metadata; flagged in UI with amber badge. |
| `OUT_OF_BOUNDS` | Value violates physical plausible limits (e.g. negative water pressure $<-0.5$ bar, acoustic noise $> 140$ dB). | Stored with warning metadata; excluded from digital twin baseline updating. |
| `STALE` | Timestamp delta exceeds 24 hours from server ingestion time. | Stored with `STALE` badge; excluded from real-time monitoring. |
| `DUPLICATE` | Identical sequence number and measurement received within deduplication window. | Tagged `DUPLICATE`; duplicate count metric incremented. |
| `UNCALIBRATED` | Ingested from a sensor with zero registered calibration records. | Accepted with warning; flagged for field technician dispatch. |
| `REJECTED` | Originates from a `QUARANTINED` or `REVOKED` device. | Ingestion rejected; raises `TelemetryIngestException` (HTTP 403). |

---

## 4. Physical Plausibility Range Thresholds

| Sensor Type | Engineering Unit | Physical Minimum | Physical Maximum | Plausibility Note |
|---|---|:---:|:---:|---|
| **Acoustic SPL** | dB | 0.0 dB | 140.0 dB | $> 70\text{ dB}$ flags burst turbulence; $> 140\text{ dB}$ is physically impossible inside water pipe. |
| **Hydrostatic Pressure** | bar | 0.0 bar | 25.0 bar | Normal distribution: 2.0 to 8.0 bar; $> 16\text{ bar}$ indicates severe transient water hammer. |
| **Volumetric Flow** | L/s | -50.0 L/s | 1,000.0 L/s | Negative values indicate backflow or back-siphonage. |
| **Soil Moisture** | % | 0.0 % | 100.0 % | Volumetric water content cannot exceed saturation porosity ($100\%$). |
| **Water Temperature** | °C | -10.0 °C | 60.0 °C | Potable municipal water typically resides in 4.0 °C to 25.0 °C range. |
| **Optical Turbidity** | NTU / clarity % | 0.0 | 100.0 | Standard potable drinking water clarity threshold $< 1.0\text{ NTU}$. |

