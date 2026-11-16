# AQUA CREW — ADVANCED AI ARCHITECTURE AUDIT
## Baseline AI Capabilities, Model Inventory & Provenance Verification (Task 13 - Phase 1)

```
========================================================================================
AQUA CREW PLATFORM — AUDIT REPORT: EXISTING AI & OPERATIONAL INTELLIGENCE ENGINES
Audit Date: 2026-11-16
Milestone: TASK 13 — Advanced AI & Evidence-Grounded Decision Intelligence
Inspection Scope: Complete Repository Audit (Tasks 01–12)
Simulation Mode: Software-Only Virtual Infrastructure Simulation (is_simulated: true)
Live LLM Provider Status: NOT CONFIGURED (Operating in Verified Deterministic Engine Mode)
========================================================================================
```

---

## 1. Executive Summary

This architecture audit systematically inventories all analytical models, machine learning pipelines, deterministic expert engines, feature extractors, and data representations implemented in AQUA CREW from Tasks 01 through 12.

### Critical Audit Finding:
- **No external LLM provider or cloud API key is currently pre-configured** in the repository or runtime environment.
- The platform's existing intelligence relies on **native Python machine learning models (scikit-learn Random Forest, Isolation Forest)**, scientific computing libraries (WNTR, NumPy, SciPy), OLS regressions, geospatial algorithms (Haversine geodesic DBSCAN), and deterministic multi-criteria decision matrices.
- Therefore, Task 13 must implement a **strict provider abstraction layer** that supports NVIDIA NIM and OpenAI-compatible endpoints when credentials (`AQUA_AI_API_KEY`) are supplied, while providing an **authoritative, 100% functional, and explainable deterministic fallback intelligence engine** when no external LLM is configured.
- Under no circumstances will the system fabricate LLM responses, invent unauthenticated connections, or expose secrets.

---

## 2. Inventory of Existing AI Models & Analytical Services

| Milestone | Service Module | Model Identifier / Version | Architecture & Algorithms | Inputs & Feature Pipelines | Outputs & Data Semantics |
|---|---|---|---|---|---|
| **Task 07** | `leak_classification_service.py` | `v1.2.0-rf-isoforest` | Random Forest Classifier + Isolation Forest (scikit-learn) | Acoustic RMS, ZCR, spectral centroid, spectral rolloff, crest factor, kurtosis, pressure $\Delta P$, flow | `anomaly_score` ($0-1$), classification (`NORMAL`, `LOW/MED/HIGH_LEAK`), `confidence` |
| **Task 07** | `leak_localization_service.py` | `v1.0.0-geodesic-spl` | Geodesic acoustic sound pressure level attenuation ($1/r^2$) | Sensor coordinates, acoustic SPL (dB), dominant frequency (Hz) | `estimated_latitude`, `estimated_longitude`, `uncertainty_m` |
| **Task 08** | `pipeline_routing_service.py` | `v1.0.0-dijkstra-conduit` | Dijkstra shortest-path graph search over pipe topology | Pipeline vertices, segment lengths, roughness | Waypoint trajectories, distance (m), transit duration (s) |
| **Task 08** | `rover_selection_service.py` | `v1.0.0-rover-pareto` | Multi-criteria rover suitability ranking | Battery %, motor temp, distance, operating state | `suitability_score` ($0-100$), eligibility flags |
| **Task 09** | `pipeline_health_service.py` | `v1.0.0-composite-health` | Weighted multi-sensor health index | Acoustic stability, pressure stability, flow stability, moisture | `health_score` ($0-100$), health category (`EXCELLENT` $\to$ `CRITICAL`) |
| **Task 09** | `predictive_risk_service.py` | `v1.0.0-rf-gradient-predictive` | Gradient failure risk projection | Health index, pressure variance, historical leak counts | `failure_prob_24h/7d/30d` ($0-1$), `burst_rupture_risk` |
| **Task 09** | `trend_analysis_service.py` | `v1.0.0-linear-ols` | Ordinary Least Squares linear regression | Time series health records ($N \ge 2$) | `health_slope_per_day`, trend direction |
| **Task 10** | `simulation_runner.py` / `wntr_engine.py` | `v1.2.0-wntr-todini-hybrid` | EPANET 2.2 PDA & Todini Global Gradient Algorithm (GGA) | Junction base demands, pipe Hazen-Williams $C$, reservoir heads | Node pressures (bar), link flows (L/s), headloss (m/km), water loss |
| **Task 11** | `vulnerability_scoring_service.py` | `v1.2.0-hybrid-physics-geodesic` | Multi-factor vulnerability weighting (30% Hyd / 25% Str / 25% Inc / 20% Env) | Pressure, material graphitization factor, diameter, soil corrosivity | `vulnerability_score` ($0-100$), level (`VERY_LOW` $\to$ `CRITICAL`) |
| **Task 11** | `geospatial_clustering_service.py` | `v1.2.0-geodesic-dbscan` | Haversine DBSCAN with antimeridian wrap & 3D Cartesian centroids | Incident coordinates $(\phi, \lambda)$, severity, $\epsilon = 350\text{m}$ | `SpatialIncidentClusterModel`, centroid $(\phi_c, \lambda_c)$, radius |
| **Task 11** | `infrastructure_prediction_service.py` | `v1.2.0-bounded-horizon` | Clamped OLS projection with monotonic CI expansion | Vulnerability score, degradation velocity $\beta_1$ | `projected_risk_24h/7d/30d`, confidence intervals |
| **Task 12** | `operational_prioritisation_service.py` | `v1.0.0-multi-criteria-pareto` | Deterministic 6-factor composite priority scoring | $S_{\text{inc}}$, $S_{\text{vuln}}$, $100-H$, $S_{\text{hyd}}$, $S_{\text{crit}}$, $S_{\text{rec}}$ | `composite_priority_score` ($0-100$), `priority_tier` |
| **Task 12** | `incident_correlation_service.py` | `v1.0.0-physics-correlation` | Multi-sensor physical co-occurrence evaluation | Acoustics, pressure drops, moisture, clusters, pressure zones | Correlation classification, strength ($0-1$), uncertainty |
| **Task 12** | `operational_hydraulic_impact_service.py`| `v1.0.0-torricelli-impact` | Torricelli aperture discharge ($Q = C_d A \sqrt{2gh}$) | Orifice diameter, operating head, network junctions | Estimated water loss ($\text{m}^3/\text{day}$), pressure drop delta |
| **Task 12** | `operational_decision_service.py` | `v1.0.0-human-interlock` | Cryptographic state-machine authorization | Operator identity, justification reason, rover readiness | `OperationalDecisionModel`, SHA-256 hash |

---

## 3. Data Provenance & Evidence Classifications

A critical requirement of Task 13 is strictly distinguishing between six distinct evidentiary classes:

1. **`MEASURED`**: Direct telemetric observation from a physical or simulated hardware sensor (e.g., live acoustic hydrophone sound pressure level in dB, pressure transmitter psi, ground moisture probe percentage).
2. **`SIMULATED`**: Output generated by the numerical hydraulic digital twin or virtual rover kinematic simulator (e.g., WNTR pressure profiles, virtual rover battery consumption, simulated Torricelli orifice discharge).
3. **`DERIVED`**: Deterministic mathematical calculation computed from existing values (e.g., OLS regression slope per day, composite priority score, geodesic Haversine distance).
4. **`PREDICTED`**: Forward-looking probabilistic or trend forecast (e.g., 24h, 7d, 30d failure risk projections, future wall-thinning estimates).
5. **`OPERATOR_ENTERED`**: Values or justifications entered directly by a licensed human operator (e.g., decision approval notes, manual priority overrides).
6. **`UNKNOWN`**: Data points lacking clear provenance metadata or where sensor connectivity is unverified.

---

## 4. Current Limitations & Gaps to Bridge in Task 13

1. **No Cross-System Natural Language Synthesis**:
   - An operator currently has to look at the AI Leak view, the Hydraulic view, and the Priority Queue separately.
   - *Task 13 Objective*: Provide an intelligent conversational assistant that queries these typed services and generates evidence-grounded natural-language answers.
2. **Explainability Transparency**:
   - Upstream ML models output raw anomaly scores ($0.88$) and risk ratings (`CRITICAL`) without deep conversational explanations.
   - *Task 13 Objective*: Provide a dedicated explainability engine explaining *why* an asset is critical, *what* features drove the inference, and *what* data is missing.
3. **Contradictory Evidence Identification**:
   - Upstream engines do not flag when two sensors or models conflict (e.g., high acoustic noise on a brand-new HDPE pipe under zero pressure drop).
   - *Task 13 Objective*: Multi-source reasoning that detects and surfaces physical contradictions.
4. **LLM Provider Isolation & Fallback**:
   - Currently, if an external LLM fails or is unconfigured, there is no AI assistant.
   - *Task 13 Objective*: Build provider abstraction supporting NVIDIA NIM / OpenAI endpoints with a 100% reliable, deterministic fallback engine.

---

## 5. Security & Safety Baseline

- **Hardware Actuation**: Confirmed **disabled**. The backend has no drivers to actuate physical valves, pumps, or rovers directly.
- **SQL Execution**: The assistant will **never** receive direct SQL execution privileges. All retrieval occurs through typed, validated SQLAlchemy service methods.
- **Human Approval**: The assistant can explain and recommend actions, but all rover mission launches remain strictly gated behind human operator approval.

