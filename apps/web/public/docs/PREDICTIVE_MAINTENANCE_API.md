# AQUA CREW — Predictive Maintenance & Health Intelligence API Specification
**Task 09 Technical Documentation — REST API Endpoints & WebSocket Events**

## 1. Overview

The **Predictive Maintenance API** exposes programmatic interfaces for querying pipeline health indices, multi-horizon failure probabilities, temporal degradation trends, maintenance recommendations, and ML model evaluation metrics.

Base URL:
`http://localhost:8000/api/v1/maintenance`

All responses include explicit simulation provenance fields:
```json
{
  "is_simulated": true,
  "source": "VIRTUAL_SIMULATION_ENGINE"
}
```

---

## 2. Infrastructure Overview & System Health

### 2.1 Get Infrastructure Overview
- **Endpoint**: `GET /api/v1/maintenance/overview`
- **Description**: Returns network-wide summary KPIs, health distribution, and count of high-risk segments.
- **Response (200 OK)**:
  ```json
  {
    "total_segments_monitored": 8,
    "excellent_count": 3,
    "good_count": 3,
    "fair_count": 1,
    "poor_count": 1,
    "critical_count": 0,
    "insufficient_data_count": 0,
    "average_health_score": 81.4,
    "high_risk_segment_count": 1,
    "pending_recommendation_count": 2,
    "timestamp": "2026-11-15T23:55:00Z",
    "is_simulated": true
  }
  ```

---

## 3. Pipeline Health Endpoints

### 3.1 List Health Assessments
- **Endpoint**: `GET /api/v1/maintenance/health`
- **Query Parameters**: `limit` (int, default: 50)
- **Response (200 OK)**: Array of `PipelineHealthResponse` objects.

### 3.2 Get Segment Health
- **Endpoint**: `GET /api/v1/maintenance/health/{segment_id}`
- **Response (200 OK)**:
  ```json
  {
    "id": "HLT-2026-7A1B2C",
    "pipeline_segment_id": "PIPE-SEC-4B-92",
    "health_score": 42.0,
    "health_category": "POOR",
    "acoustic_stability_score": 45.0,
    "pressure_stability_score": 38.0,
    "flow_stability_score": 60.0,
    "moisture_anomaly_score": 30.0,
    "data_coverage_pct": 95.0,
    "confidence": 0.92,
    "contributing_factors": {
      "severe_pressure_loss": 25.0,
      "acoustic_high_spl": 22.0,
      "high_ground_saturation": 18.0
    },
    "positive_indicators": [
      "Ductile iron class 54 structural tensile capacity intact"
    ],
    "explanation": "Pipeline PIPE-SEC-4B-92 classified as POOR with health index 42/100...",
    "assessed_at": "2026-11-15T23:55:00Z",
    "is_simulated": true,
    "source": "VIRTUAL_SIMULATION_ENGINE"
  }
  ```

### 3.3 Trigger On-Demand Health Analysis
- **Endpoint**: `POST /api/v1/maintenance/health/analyze`
- **Request Body**:
  ```json
  {
    "pipeline_segment_id": "PIPE-SEC-4B-92",
    "lookback_hours": 24
  }
  ```

---

## 4. Predictive Risk Endpoints

### 4.1 List Predictive Risk Assessments
- **Endpoint**: `GET /api/v1/maintenance/predictions`
- **Query Parameters**: `limit` (int, default: 50)
- **Response (200 OK)**: Array of `PredictiveRiskResponse` objects.

### 4.2 Get Segment Predictive Risk
- **Endpoint**: `GET /api/v1/maintenance/predictions/{segment_id}`
- **Response (200 OK)**:
  ```json
  {
    "id": "PRD-2026-8C2D3E",
    "pipeline_segment_id": "PIPE-SEC-4B-92",
    "failure_prob_24h": 0.48,
    "failure_prob_7d": 0.74,
    "failure_prob_30d": 0.89,
    "overall_risk_level": "CRITICAL",
    "leak_probability": 0.78,
    "burst_rupture_risk": 0.42,
    "model_version": "v1.0.0-rf-gradient-predictive",
    "confidence": 0.88,
    "uncertainty_margin": 0.06,
    "contributing_factors": {
      "acute_pressure_drop_loss": 0.35,
      "high_acoustic_spl_emissions": 0.30
    },
    "risk_explanation": "Segment PIPE-SEC-4B-92 failure probability: 48.0% (24h), 74.0% (7d)...",
    "assessed_at": "2026-11-15T23:55:00Z",
    "is_simulated": true,
    "source": "VIRTUAL_SIMULATION_ENGINE"
  }
  ```

---

## 5. Temporal Trend Endpoints

### 5.1 Get Segment Historical Trend
- **Endpoint**: `GET /api/v1/maintenance/trends/{segment_id}`
- **Query Parameters**: `days` (int, default: 30)
- **Response (200 OK)**:
  ```json
  {
    "id": "TRD-2026-9E4F5A",
    "pipeline_segment_id": "PIPE-SEC-4B-92",
    "trend_direction": "DETERIORATING",
    "health_slope_per_day": -2.4,
    "pressure_variance": 0.32,
    "flow_anomaly_rate": 0.22,
    "acoustic_emission_count": 6,
    "historical_leak_count": 2,
    "window_days": 30,
    "time_series_points": [
      {
        "timestamp": "2026-10-16T23:55:00Z",
        "day_offset": 30.0,
        "health_score": 75.0,
        "pressure_bar": 4.5,
        "flow_lps": 120.0,
        "acoustic_spl_db": 42.0
      }
    ],
    "assessed_at": "2026-11-15T23:55:00Z",
    "is_simulated": true
  }
  ```

---

## 6. Maintenance Recommendations & Review

### 6.1 List Maintenance Recommendations
- **Endpoint**: `GET /api/v1/maintenance/recommendations`
- **Query Parameters**:
  - `status` (string, optional): `PENDING_REVIEW`, `ACKNOWLEDGED`, `DISMISSED`, `DISPATCHED`
  - `urgency` (string, optional): `ROUTINE`, `MEDIUM`, `HIGH`, `CRITICAL`
  - `limit` (int, default: 50)

### 6.2 Review Maintenance Recommendation
- **Endpoint**: `POST /api/v1/maintenance/recommendations/{recommendation_id}/review`
- **Request Body**:
  ```json
  {
    "action": "DISPATCH",
    "operator_id": "QA_OPERATOR_CHIEF",
    "operator_notes": "Acoustic emissions confirmed via telemetry. Dispatch authorized."
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "id": "MNT-2026-A101",
    "pipeline_segment_id": "PIPE-SEC-4B-92",
    "status": "DISPATCHED",
    "dispatched_mission_id": "REC-2026-F9812A",
    "reviewed_by": "QA_OPERATOR_CHIEF",
    "reviewed_at": "2026-11-15T23:58:00Z",
    "is_simulated": true
  }
  ```

---

## 7. Model Evaluation & Telemetry Metrics

### 7.1 Get Model Metadata
- **Endpoint**: `GET /api/v1/maintenance/models`

### 7.2 Get Evaluation Metrics
- **Endpoint**: `GET /api/v1/maintenance/metrics`
- **Response (200 OK)**:
  ```json
  {
    "model_version": "v1.0.0-rf-gradient-predictive",
    "evaluation_dataset": "SIMULATED_METRO_HYDRAULIC_TEST_CORPUS_2026",
    "sample_count": 1250,
    "metrics": {
      "accuracy": 0.912,
      "precision": 0.884,
      "recall": 0.908,
      "f1_score": 0.895,
      "roc_auc": 0.941
    },
    "confusion_matrix": {
      "true_positive": 412,
      "false_positive": 54,
      "true_negative": 728,
      "false_negative": 56
    },
    "is_simulated": true
  }
  ```

---

## 8. Real-Time WebSocket Events

Broadcast over `ws://localhost:8000/api/v1/ws/telemetry` and `ws://localhost:8000/ws`:

| Event Type | Key Payload Fields | Description |
| :--- | :--- | :--- |
| `PIPELINE_HEALTH_UPDATED` | `pipeline_segment_id`, `health_score`, `health_category` | Broadcast when health calculation changes |
| `PREDICTIVE_RISK_GENERATED` | `pipeline_segment_id`, `overall_risk_level`, `failure_prob_24h` | Broadcast when risk evaluation completes |
| `PIPELINE_TREND_CHANGED` | `pipeline_segment_id`, `trend_direction`, `health_slope_per_day` | Broadcast when degradation velocity alters |
| `MAINTENANCE_RECOMMENDATION_CREATED` | `recommendation_id`, `pipeline_segment_id`, `urgency` | Broadcast when new proposal is generated |
| `MAINTENANCE_RECOMMENDATION_REVIEWED` | `recommendation_id`, `status`, `dispatched_mission_id` | Broadcast when operator signs off on review |
| `HIGH_RISK_PIPELINE_IDENTIFIED` | `pipeline_segment_id`, `overall_risk_level`, `explanation` | Broadcast when critical structural hazard detected |

