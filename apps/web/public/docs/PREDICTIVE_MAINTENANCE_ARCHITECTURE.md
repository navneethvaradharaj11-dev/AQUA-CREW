# AQUA CREW — Predictive Maintenance & Infrastructure Health Architecture
**Task 09 Technical Architecture — Proactive Degradation Forecasting & Autonomous Dispatch Integration**

## 1. System Vision & Paradigm Shift

**AQUA CREW Task 09** advances the municipal pipeline intelligence platform from a **reactive** response system (detecting leaks after acoustic breach) into a **proactive, predictive infrastructure intelligence platform**.

By continuously aggregating multi-modal historical and streaming sensor readings (acoustics, pressure transients, flow mass balances, ground moisture saturation) and cross-referencing with past inspection findings and AI leak incidents, the system detects micro-deterioration signatures, forecasts failure probabilities across multiple operational horizons (24 hours, 7 days, 30 days), and generates explainable maintenance recommendations for human-supervised autonomous rover inspection.

> [!IMPORTANT]
> **SIMULATION PROVENANCE**: All predictive risk scores, degradation curves, historical aggregations, and failure probabilities are computed using virtual simulation data models. No real-world municipal infrastructure claims are made. Physical repairs are never automatically triggered.

---

## 2. End-to-End System Architecture

```
  [Real-Time & Historical Sensor Telemetry]
  (Acoustic SPL, Pressure, Flow Rate, Soil Moisture, Rover Passes)
                       │
                       ▼
    ┌─────────────────────────────────────────┐
    │     Historical Telemetry Service        │
    │ (Windowed Aggregations: 15m, 1h, 24h, 7d, 30d) │
    └──────────────────┬──────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
┌───────────────────────┐   ┌───────────────────────────┐
│ Pipeline Health Index │   │  Temporal Trend Analyzer  │
│    (0–100 Scoring)    │   │ (Regression Slopes, Rate) │
└──────────┬────────────┘   └─────────────┬─────────────┘
           │                              │
           └──────────────┬───────────────┘
                          ▼
            ┌───────────────────────────┐
            │ Predictive Risk Engine    │
            │ (P_24h, P_7d, P_30d)      │
            └─────────────┬─────────────┘
                          │
                          ▼
            ┌───────────────────────────┐
            │ Maintenance Rec Engine    │
            │ (Actions, Urgency, Scope) │
            └─────────────┬─────────────┘
                          │
         ┌────────────────┴────────────────┐
         ▼                                 ▼
┌─────────────────────────────────┐   ┌────────────────────────────────┐
│ Human Operator Review Gate      │   │ Task 08 Autonomous Dispatch    │
│ [Acknowledge / Dismiss / Notes] │   │ (Rover Inspection Routing)     │
└─────────────────────────────────┘   └────────────────────────────────┘
```

---

## 3. Core Engine Components

### 3.1 Historical Sensor Telemetry Service (`historical_telemetry_service.py`)
Aggregates time-series sensor observations across multiple lookback windows ($15\text{ min}, 1\text{ hr}, 24\text{ hr}, 7\text{ days}, 30\text{ days}$):
- **Acoustic**: Sound pressure level (RMS & peak), dominant frequency shift, acoustic anomaly count.
- **Pressure**: Mean operating pressure, standard deviation, peak-to-trough pressure transient delta $\Delta P$, drop count.
- **Flow**: Observed vs. expected flow rate ratio, mass-balance deviation.
- **Environmental**: Ground moisture gradient, ambient temperature.
- **Data Quality & Coverage**: Computes sensor reliability ratio; flags segments with insufficient history.

### 3.2 Pipeline Health Scoring Engine (`pipeline_health_service.py`)
Computes an explainable Health Score $H \in [0, 100]$:
\[
H = 100 - (\Delta H_{\text{acoustic}} + \Delta H_{\text{pressure}} + \Delta H_{\text{flow}} + \Delta H_{\text{moisture}} + \Delta H_{\text{history}}) \times \omega_{\text{material}}
\]

#### Health Classifications:
- `EXCELLENT`: $90 - 100$ (Optimal operating parameters, zero anomalous transients)
- `GOOD`: $75 - 89$ (Normal operational wear, stable pressure)
- `FAIR`: $50 - 74$ (Moderate fluctuations, elevated baseline noise, monitoring advised)
- `POOR`: $25 - 49$ (Significant pressure instability, acoustic hiss, moisture anomaly)
- `CRITICAL`: $0 - 24$ (Imminent rupture risk, severe pressure loss, persistent acoustic emissions)

### 3.3 Predictive Failure Risk Engine (`predictive_risk_service.py`)
Estimates the probability of pipeline failure or active leakage over three standard forecasting horizons:
1. **$P_{24h}$ (Next 24 Hours)**: Driven by immediate transient instability and acute pressure drops.
2. **$P_{7d}$ (Next 7 Days)**: Driven by progressive acoustic degradation and recurring flow imbalance.
3. **$P_{30d}$ (Next 30 Days)**: Driven by pipe age, material vulnerability, and cumulative stress cycles.

Model outputs:
- Predicted failure probability per horizon ($0.0 \le P \le 1.0$)
- Qualitative risk level (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`)
- Model confidence and prediction uncertainty intervals
- Contributing risk factor breakdown

### 3.4 Temporal Trend Analysis Engine (`trend_analysis_service.py`)
Computes linear regression slopes $\beta = \frac{d(\text{Metric})}{dt}$ over historical intervals:
- `IMPROVING`: Health score increasing ($\beta > +0.5/\text{day}$)
- `STABLE`: Negligible metric drift ($|\beta| \le 0.5/\text{day}$)
- `DETERIORATING`: Steady metric degradation ($-2.0 \le \beta < -0.5/\text{day}$)
- `RAPIDLY_DETERIORATING`: Severe exponential degradation ($\beta < -2.0/\text{day}$)
- `INSUFFICIENT_DATA`: Fewer than 3 historical checkpoints in lookback window

### 3.5 Maintenance Recommendation Engine (`maintenance_recommendation_service.py`)
Synthesizes health score, risk forecast, and trend status into actionable maintenance directives:
- `CONTINUE_MONITORING`: Healthy pipe, standard sensor polling
- `INCREASE_SENSOR_MONITORING`: Elevate telemetry sampling frequency
- `SCHEDULE_ACOUSTIC_INSPECTION`: Non-urgent acoustic sweep within 7 days
- `SCHEDULE_PRESSURE_INSPECTION`: Investigate hydraulic transients within 48 hours
- `DISPATCH_INSPECTION_ROVER`: High urgency; pass directly to Task 08 Dispatch Engine
- `PRIORITIZE_HUMAN_INSPECTION`: Complex valve/junction verification required
- `RECOMMEND_PIPELINE_REPAIR_ASSESSMENT`: Critical structural integrity risk

---

## 4. Integration Bridges

### 4.1 Integration with Task 07 (AI Leak Detection)
- Differentiates active confirmed leaks (`AiDetectionModel`) from future deterioration forecasts.
- Incorporates historical leak count on a segment as an input weight into predictive risk models.
- If an active leak is detected, the segment health score reflects acute degradation.

### 4.2 Integration with Task 08 (Autonomous Rover Dispatch)
- When a segment reaches `HIGH` or `CRITICAL` predictive risk, the recommendation engine generates a dispatch recommendation.
- Directly invokes `MissionPlanningService.plan_mission_for_detection()` or dedicated predictive inspection route generator.
- Generates a `MissionRecommendationModel` in `PENDING_APPROVAL` status.
- Strict human operator approval is maintained; no autonomous physical rover moves without operator sign-off.

---

## 5. Database Architecture & Persistence

Extends SQLAlchemy models:
1. `PipelineHealthAssessmentModel` (`pipeline_health_assessments`): Segment health score, category, contributing factors, positive indicators, data coverage.
2. `PredictiveRiskAssessmentModel` (`predictive_risk_assessments`): Probabilities ($P_{24h}, P_{7d}, P_{30d}$), risk level, prediction uncertainty, model version.
3. `MaintenanceRecommendationModel` (`maintenance_recommendations`): Recommended action, urgency, affected segment, suggested timeframe, operator review state, linked mission ID.
4. `HistoricalTrendSummaryModel` (`historical_trend_summaries`): Time-series trend direction, slope, metric checkpoints.

All models carry:
- `is_simulated = Column(Boolean, default=True)`
- `source = Column(String, default="VIRTUAL_SIMULATION_ENGINE")`

---

## 6. Real-Time WebSocket Events

The existing WebSocket manager broadcasts:
- `PIPELINE_HEALTH_UPDATED`: Real-time health score changes
- `PREDICTIVE_RISK_GENERATED`: Updated failure probability forecasts
- `PIPELINE_TREND_CHANGED`: Degradation trend status alterations
- `MAINTENANCE_RECOMMENDATION_CREATED`: New maintenance proposal
- `MAINTENANCE_RECOMMENDATION_REVIEWED`: Operator review updates
- `HIGH_RISK_PIPELINE_IDENTIFIED`: Critical warning alert broadcast

---

## 7. Frontend User Experience (`/app/maintenance`)

Dedicated view in `apps/web/src/components/maintenance/PredictiveMaintenanceView.tsx` with:
- **A. Health Overview Cards**: Counts of segments in Excellent, Good, Fair, Poor, Critical.
- **B. Pipeline Health Map**: Color-coded GIS layer matching health status.
- **C. Predictive Risk Matrix**: Top at-risk segments ranked by 24h, 7d, 30d risk.
- **D. Temporal Trend Graphs**: Interactive time-series charts for pressure, flow, acoustic noise.
- **E. Maintenance Action Queue**: One-click review, dismiss, or dispatch to Task 08.
- **F. Segment Deep-Dive Inspector**: Full metadata, acoustic spectrum, and history.

