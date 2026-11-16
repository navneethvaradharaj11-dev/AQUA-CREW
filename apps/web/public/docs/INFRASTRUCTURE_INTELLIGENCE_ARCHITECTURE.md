# AQUA CREW — Infrastructure Intelligence & Geospatial Risk Prediction Architecture
## Technical Architectural Specification (Task 11)

```
========================================================================================
AQUA CREW PLATFORM — INFRASTRUCTURE INTELLIGENCE SYSTEM ARCHITECTURE
Document ID: AC-T11-ARCH-2026-V1
Classification: Municipal Water Utility Operational Intelligence Specification
Simulation Mode: Software-Only Virtual Infrastructure Simulation
Provenance: VIRTUAL_SIMULATION_ENGINE (is_simulated: true)
========================================================================================
```

---

## 1. Executive Summary & Purpose

The **Infrastructure Intelligence & Geospatial Risk Prediction Platform (Task 11)** serves as the high-level decision and risk-forecasting orchestration layer for the AQUA CREW metropolitan water management ecosystem. It bridges previously siloed operational and engineering domains into a unified infrastructure intelligence platform:

1. **GIS Pipeline Asset Data (Task 04)**: Diameter, material composition, length, and coordinate topology.
2. **AI-Powered Leak Detection & Acoustic Inferences (Task 07)**: Acoustic anomaly scores, loss volume estimations ($L/h$), and localization coordinates.
3. **Autonomous Mission Planning & Rover Dispatch (Task 08)**: Dijkstra routing, rover suitability ranking, energy reserves, and human operator approval gates.
4. **Predictive Maintenance & Health Telemetry (Task 09)**: Real-time sensor stability indices, empirical degradation slopes ($d\text{Health}/dt$), and component wear.
5. **Digital Twin & Hydraulic Water Network Simulation (Task 10/10.5/10.6)**: Todini GGA pressure distributions, Hazen-Williams friction losses, Torricelli pressure-dependent leak flows, and booster pump hydraulics.

By synthesizing these streams, the platform directly answers the **7 core municipal operational questions**:
- *Which pipeline segments are most vulnerable to catastrophic rupture?*
- *Where are leaks and acoustic anomalies physically clustered across the city?*
- *Which pipeline conduits are deteriorating at the fastest rate?*
- *What infrastructure characteristics (age, material, diameter, pressure) drive risk?*
- *Which assets must autonomous rovers inspect first?*
- *Which maintenance interventions should water utility dispatchers prioritize?*
- *How can existing rovers and hydraulic digital twins collaborate to inspect high-risk areas?*

---

## 2. System Architecture & Topology

```
+---------------------------------------------------------------------------------------------------+
|                               AQUA CREW OPERATIONAL COMMAND CENTER                                |
|                        Next.js 14 / React Dashboard (/app/infrastructure-intelligence)            |
+---------------------------------------------------------------------------------------------------+
       |                                       |                                      |
       v                                       v                                      v
+------------------+                 +--------------------+                 +---------------------+
| Vulnerability    |                 | Geospatial Cluster |                 | Prioritized Rover   |
| 4-Factor Matrix  |                 | & Hotspot Map View |                 | Inspection Queue    |
+------------------+                 +--------------------+                 +---------------------+
       ^                                       ^                                      ^
       |                                       |                                      |
================================== FastAPI Backend API Layer =======================================
       |                                       |                                      |
+---------------------------------------------------------------------------------------------------+
|                          INFRASTRUCTURE INTELLIGENCE ENGINE (Task 11)                             |
|  - VulnerabilityScoringService          - GeospatialClusteringService (DBSCAN)                    |
|  - SpatialAnalysisService               - RiskTrendService (dRisk/dt)                             |
|  - InfrastructurePredictionService      - InspectionPriorityService                               |
+---------------------------------------------------------------------------------------------------+
       |                    |                       |                     |                  |
       v                    v                       v                     v                  v
+--------------+   +-----------------+   +--------------------+   +---------------+   +-------------+
| GIS Conduits |   | AI Leak Detections| | Telemetry & Health |   | Digital Twin  |   | Virtual     |
| (Task 04)    |   | (Task 07)       |   | Indices (Task 09)  |   | Simulation    |   | Rover Fleet |
| - Material   |   | - Anomaly Score |   | - Pressure Stability|  | (Task 10)     |   | (Task 05/08)|
| - Diameter   |   | - Recurrence    |   | - Acoustic Delta   |   | - Velocity    |   | - Battery   |
| - Coordinates|   | - Loss Rate     |   | - Hist. Trend Slope|   | - Headloss    |   | - Location  |
+--------------+   +-----------------+   +--------------------+   +---------------+   +-------------+
```

---

## 3. Core Engine Components

### 3.1. Vulnerability Scoring Service (`VulnerabilityScoringService`)
- Evaluates multi-factor vulnerability on a continuous $0.0 \le V \le 100.0$ scale.
- Combines 4 orthogonal dimensions:
  1. **Hydraulic Stress (30%)**: Friction headloss gradients, velocity overruns ($>1.8\text{ m/s}$), and pressure zone boundary fluctuations.
  2. **Structural Infrastructure (25%)**: Material vulnerability curve ($\text{Cast Iron} > \text{Concrete} > \text{Ductile Iron} > \text{Steel} > \text{HDPE}$), transmission diameter consequence ($\ge 600\text{ mm}$), and conduit service age.
  3. **Incident & AI History (25%)**: Count of AI leak detections, acoustic anomaly severity ($>0.65$), and unverified/unresolved detection alarms.
  4. **Environmental & Spatial Risk (20%)**: Proximity to dense incident clusters ($\le 150\text{ m}$), subsurface soil moisture saturation, and coastal saline proximity.
- Quantifies **Data Completeness** ($0-100\%$), **Inference Confidence** ($0.0-1.0$), and **Uncertainty Bounds** ($\pm \sigma$).

### 3.2. Geospatial Clustering Engine (`GeospatialClusteringService`)
- Executes density-based spatial clustering (DBSCAN) using Haversine great-circle distances:
  $$d = 2 R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
- Hyperparameters:
  - $\epsilon = 350.0\text{ meters}$ (geodesic neighborhood).
  - $\text{MinPts} = 2$ (minimum incidents to seed a dense cluster).
- Outputs:
  - Cluster centroid coordinates $(\bar{\phi}, \bar{\lambda})$.
  - Minimum bounding cluster radius ($r_{\min} = 150\text{ m}$).
  - Dominant pipe material and aggregate hotspot intensity ($0.0-1.0$).
  - List of affected pipeline segment IDs.

### 3.3. Spatial Zone & Heatmap Analysis (`SpatialAnalysisService`)
- Resolves municipal pressure zones (`PZ-01` Downtown High-Pressure, `PZ-02` Eastern Industrial, `PZ-03` Northern Residential, `PZ-04` Harbor Utility).
- Maps each pipeline conduit to its geographic risk zone and calculates minimum distance to active hotspots.
- Generates high-resolution spatial heatmap coordinate arrays with normalized intensity weights for interactive GIS rendering.

### 3.4. Temporal Deterioration Velocity (`RiskTrendService`)
- Computes risk change rates over 3 discrete operational horizons:
  - 24-hour delta ($d\text{Risk}/dt_{24h}$).
  - 7-day delta ($d\text{Risk}/dt_{7d}$).
  - 30-day delta ($d\text{Risk}/dt_{30d}$).
- Classifies structural direction into `DETERIORATING`, `STABLE`, or `IMPROVING`.
- Employs graceful fallback handling when historical telemetry is sparse, publishing explicit `data_sufficiency` ratings (`HIGH`, `MODERATE`, `LOW`).

### 3.5. Predictive Forecasting (`InfrastructurePredictionService`)
- Projects vulnerability scores forward to $T+24\text{h}$, $T+7\text{d}$, and $T+30\text{d}$.
- Accounts for non-linear saturation bounded in $[0.0, 100.0]$.
- Models expanding confidence intervals over longer time horizons ($\text{CI}_{30\text{d}} > \text{CI}_{7\text{d}} > \text{CI}_{24\text{h}}$).
- Identifies explainable primary risk drivers and recommends mitigation urgency (`IMMEDIATE`, `SHORT_TERM`, `PLANNED`, `ROUTINE`).

### 3.6. Intelligent Inspection Prioritisation (`InspectionPriorityService`)
- Ranks candidate conduits for inspection using composite utility:
  $$\text{Priority} = 0.40 V + 0.25 W_{\text{det}} + 0.20 W_{\text{prox}} + 0.15 W_{\text{crit}}$$
- Enables operators to `acknowledge`, `dismiss`, or `request_inspection`.
- Seamlessly handoffs to Task 08 `MissionPlanningService`, establishing a formal `MissionRecommendationModel` and maintaining human operator approval requirements (`operator_approval_required: true`).

---

## 4. Architectural Guarantees & Constraints

1. **Simulation Isolation**: All database models, API payloads, and frontend visualizations retain `is_simulated: true` and `source: "VIRTUAL_SIMULATION_ENGINE"`.
2. **No Hardware Actuation**: Under no circumstances does the platform command physical pumps, valves, or real rovers.
3. **Mandatory Human-in-the-Loop Gate**: Rover inspection requests generate recommendations that require explicit operator sign-off (`APPROVED`) before mission execution.
4. **Deterministic & Explainable Scoring**: Risk scores are strictly reproducible and backed by published weights, formulas, and contributing factor dictionaries. No black-box unexplainable decisions.
5. **Zero Platform Regressions**: Tasks 01 through 10.6 remain intact and fully passing (160/160 backend test suite passing).

