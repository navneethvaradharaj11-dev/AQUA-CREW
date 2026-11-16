# AQUA CREW — TASK 19: MODULE INTEGRATION MATRIX
## Cross-Task Dependency Map, Data Exchange Contracts & Protocol Bindings

---

### 1. Master Cross-Task Matrix

| Origin Task | Consuming Task | Integration Artifact | Data Structure / Contract | Protocol | Test Coverage File |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Task 18 (IoT Readiness)** | Task 07 (AI Leak Detection) | `NormalizedTelemetry` | `AcousticSensorReading` (dB, freq_hz, noise_rms) | Internal In-memory / REST | `test_iot_hardware_readiness.py` |
| **Task 07 (AI Detection)** | Task 19 (Unified Incident) | `AiDetectionResult` | `AiDetectionModel` (leak_prob, confidence, classification) | SQLAlchemy / Service Call | `test_system_integration_acceptance.py` |
| **Task 04 (GIS Intelligence)**| Task 19 (Unified Incident) | `PipelineSegment` | `PipelineSegmentModel` (id, dma, coordinates, material) | SQLAlchemy Repository | `test_system_integration_acceptance.py` |
| **Task 10 (Digital Twin)** | Task 19 (Unified Incident) | `HydraulicSimulation` | `HydraulicHeadlossDelta` (headloss_m, loss_lps) | EPANET / WNTR Solver | `test_system_integration_acceptance.py` |
| **Task 09 (Predictive Maint)**| Task 19 (Unified Incident) | `AssetRiskProfile` | `RiskScore` (0.0 to 100.0, Priority P1-P4) | Risk Assessment TVF | `test_system_integration_acceptance.py` |
| **Task 08 (Mission Planning)**| Task 15 (Inspection Intel) | `MissionModel` | `InspectionPlan` (rover_id, trajectory, target_segment) | REST API / DB Model | `test_inspection_intelligence.py` |
| **Task 15 (Inspection Intel)**| Task 16 (Repair Management)| `InspectionReport` | `DamageFindings` (crack_len, defect_type, score) | REST API / JSON Blob | `test_repair_management.py` |
| **Task 16 (Repair Planning)** | Task 19 (Unified Incident) | `RepairPlanModel` | `RepairPlan` (method, cost_usd, urgency, materials) | SQLAlchemy / REST API | `test_system_integration_acceptance.py` |
| **Task 13.6 (Zero-Trust RBAC)**| Task 19 (Approvals) | `JWTClaims` | `UserModel` (roles: VIEWER, OPERATOR, ENGINEER, ADMIN) | FastAPI Dependency | `test_system_integration_acceptance.py` |
| **Task 19 (Sim Resolution)** | Task 10 (Digital Twin) | `ResolutionComparison` | `PostRepairDelta` (gain_bar, flow_eliminated, stable) | Digital Twin Verification | `test_system_integration_acceptance.py` |

---

### 2. Upstream & Downstream Contract Specifications

#### 2.1 Sensor Telemetry to AI Leak Engine
- **Upstream Input**: Sensor ID, normalized acoustic decibel reading (0–140 dB), dominant frequency (Hz), ISO calibration timestamp.
- **Contract Guard**: If sensor is uncalibrated or out-of-bounds, AI confidence is capped at 0.70 (30% penalty) to prevent false alerts.
- **Downstream Output**: `leak_probability: float` (0.0 to 1.0), `classification: "LEAK_DETECTED" | "NORMAL_FLOW"`.

#### 2.2 Anomaly to Hydraulic Digital Twin
- **Upstream Input**: Anomaly probability, localized pipeline segment ID (`PIPE-SEC-4B-92`), DMA zone (`DMA-METRO-CENTRAL`).
- **Contract Guard**: Segment existence validated against `PipelineSegmentModel`.
- **Downstream Output**: Hydraulic headloss delta (m), estimated water discharge rate (L/s), nodal pressure delta curve.

#### 2.3 Rover Inspection Findings to Repair Formulation
- **Upstream Input**: Virtual rover crawl telemetry, visual defect classification (`LONGITUDINAL_CRACK`, `CIRCUMFERENTIAL_CRACK`, `JOINT_FAILURE`), crack length (mm), crack width (mm).
- **Contract Guard**: Visual confidence $\ge 0.80$; requires simulation-mode tag.
- **Downstream Output**: Selected engineering method (`FULL_CIRCLE_STAINLESS_CLAMP`, `EPOXY_SLEEVE_INJECTION`, `PIPE_SECTION_REPLACEMENT`), material cost estimate (USD), crew allocation.

#### 2.4 Repair Plan to Engineering Sign-off & Closure
- **Upstream Input**: Formulated repair plan, urgency tier (`EMERGENCY_24H`, `HIGH_PRIORITY_48H`, `PLANNED_7D`).
- **Contract Guard**: Certified Municipal Engineer or Admin role required. Digital signature generated via SHA-256 over incident ID, status, actor, and timestamp.
- **Downstream Output**: Verified hydraulic recovery (+0.35 bar), 0 L/s water loss rate, transition to `CLOSED`.

