# AQUA CREW — AI Leak Detection & Telemetry API Specification
**Version 1.0.0 — Task 07 REST & WebSocket Endpoints**

## 1. REST Endpoints Overview

All AI endpoints are versioned under prefix `/api/v1/ai`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/ai/analyze` | Run single pipeline segment multi-modal AI leak analysis |
| `POST` | `/api/v1/ai/analyze/batch` | Batch execution across multiple segments |
| `GET` | `/api/v1/ai/detections` | List recent AI detections (filters: segment, severity, status) |
| `GET` | `/api/v1/ai/detections/{id}` | Inspect full diagnostic details for a specific detection |
| `PATCH`| `/api/v1/ai/detections/{id}/status` | Operator review action (VERIFIED_BY_OPERATOR, FALSE_POSITIVE, etc.) |
| `POST` | `/api/v1/ai/waveform/synthesize` | Generate synthetic acoustic waveform & FFT spectrum |
| `POST` | `/api/v1/ai/sensors/ingest` | Ingest multi-modal sensor telemetry with quality scoring |
| `GET` | `/api/v1/ai/models` | List registered active ML models |
| `GET` | `/api/v1/ai/models/metrics` | Retrieve un-manufactured synthetic evaluation metrics |
| `GET` | `/api/v1/ai/health` | AI subsystem health and throughput statistics |

---

## 2. Request & Response Schemas

### 2.1 `POST /api/v1/ai/analyze`

**Request Body**:
```json
{
  "pipeline_segment_id": "PIPE-SEC-4B-92",
  "acoustic_spl_db": 84.5,
  "dominant_freq_hz": 1420.0,
  "pressure_bar": 3.8,
  "flow_rate_m3h": 145.0,
  "ground_moisture_pct": 78.0,
  "acoustic_scenario": "MODERATE_LEAK"
}
```

**Response Body (200 OK)**:
```json
{
  "id": "DET-2026-B81E29",
  "pipeline_segment_id": "PIPE-SEC-4B-92",
  "anomaly_score": 0.88,
  "classification": "HIGH_LEAK_PROBABILITY",
  "confidence": 0.92,
  "risk_level": "CRITICAL",
  "estimated_loss_lph": 2450.0,
  "estimated_latitude": 40.7118,
  "estimated_longitude": -74.0095,
  "localization_uncertainty_m": 14.5,
  "localization_quality": "HIGH",
  "status": "PENDING_REVIEW",
  "contributing_features": {
    "acoustic_spl_db": 0.42,
    "dominant_freq_hz": 0.28,
    "pressure_deviation": 0.18,
    "ground_moisture_pct": 0.12
  },
  "risk_explanation": "Acoustic spectral signature (84 dB at 1,420 Hz) combined with severe pressure drop indicates active rupture.",
  "model_version": "v1.2.0-rf-explainable",
  "created_at": "2026-11-15T22:50:00Z",
  "is_simulated": true,
  "source": "VIRTUAL_SIMULATION_ENGINE"
}
```

---

## 3. Real-Time WebSocket Events

AQUA CREW broadcasts live events via WebSocket at `/api/v1/ws/telemetry`.

### Event Types:

1. `LEAK_CLASSIFICATION_COMPLETED`
   Broadcasted immediately when a leak analysis produces a detection record.
   ```json
   {
     "type": "LEAK_CLASSIFICATION_COMPLETED",
     "detection_id": "DET-2026-B81E29",
     "pipeline_segment_id": "PIPE-SEC-4B-92",
     "classification": "HIGH_LEAK_PROBABILITY",
     "confidence": 0.92,
     "anomaly_score": 0.88,
     "risk_level": "CRITICAL",
     "estimated_loss_lph": 2450.0,
     "location": {
       "latitude": 40.7118,
       "longitude": -74.0095,
       "uncertainty_m": 14.5,
       "quality": "HIGH"
     },
     "status": "PENDING_REVIEW",
     "timestamp": "2026-11-15T22:50:00Z",
     "is_simulated": true
   }
   ```

2. `SENSOR_READING_RECEIVED` / `SENSOR_ANOMALY_DETECTED`
   Broadcasted upon sensor ingestion with quality tagging (`EXCELLENT`, `GOOD`, `DEGRADED`, `FAULT`).

