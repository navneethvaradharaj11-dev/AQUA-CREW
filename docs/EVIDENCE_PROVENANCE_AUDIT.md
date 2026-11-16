# AQUA CREW — EVIDENCE PROVENANCE AUDIT
## Phase 2 Engineering Verification Report (Task 13.5)

**Audited Component**: 6-Class Ontological Evidence Framework & Subsystem Provenance  
**Date**: November 2026  
**Auditor**: Principal AI Systems Architect & Hydraulic Reliability Engineer  
**Status**: AUDITED & DEFECTS IDENTIFIED

---

### 1. The Six Evidence Classifications

AQUA CREW relies on an explicit ontological segregation model to guarantee that synthetic, estimated, and simulated values are never confused with empirical measurements.

```
+-------------------+----------------------------------------------------------------------------------+
| CLASSIFICATION    | AUTHORITATIVE DEFINITION & PLATFORM GROUNDING                                    |
+-------------------+----------------------------------------------------------------------------------+
| MEASURED          | Physical telemetric observations directly obtained from calibrated hardware      |
|                   | sensors (hydrophones, acoustic loggers, pressure transducers, flowmeters).       |
+-------------------+----------------------------------------------------------------------------------+
| SIMULATED         | Numerical digital twin outputs, EPANET/WNTR solver solutions, Torricelli orifice |
|                   | discharge estimations, and kinematic virtual rover state simulations.            |
+-------------------+----------------------------------------------------------------------------------+
| DERIVED           | Mathematical aggregations, linear regression deterioration slopes, normalized     |
|                   | infrastructure vulnerability scores (Task 11), and composite priority rankings.  |
+-------------------+----------------------------------------------------------------------------------+
| PREDICTED         | Empirical multi-horizon failure risk scores (24h, 7d, 30d hazard calculations).   |
+-------------------+----------------------------------------------------------------------------------+
| OPERATOR_ENTERED  | Human authorizations, supervisor mission sign-offs, and administrative overrides.|
+-------------------+----------------------------------------------------------------------------------+
| UNKNOWN           | Data points where sensors are missing, uncalibrated, expired, or unmeasured.     |
+-------------------+----------------------------------------------------------------------------------+
```

---

### 2. Provenance Audit Findings

#### 2.1 Audit of `MEASURED` Data
- **Hardware Connection Status**:
  All platform telemetry currently originates from the `VIRTUAL_SIMULATION_ENGINE` (`is_simulated = True`). There is currently no active physical RS-485, Modbus, or MQTT bridge connected to physical municipal water hardware in this development environment.
- **Defect Identified**:
  In Task 13, GIS conduit metadata (`PipelineSegmentModel`) was tagged as `classification="MEASURED"`.
- **Finding**: Static asset records (e.g. diameter, nominal pressure, pipe material) are **asset registry specifications**, not dynamic telemetric measurements. Furthermore, synthetic sensor readings from `sensor_readings` lacked calibration certificates.
- **Remediation**:
  Asset specifications are explicitly tagged as `ASSET_REGISTRY_RECORD` with `calibration_status="ASSET_REGISTRY_RECORD"` and `hardware_connected=False`. Telemetric records must explicitly carry `calibration_status="UNVERIFIED_VIRTUAL"` to prevent false claims of physical hardware calibration.

#### 2.2 Audit of `SIMULATED` Data
- **Sources Audited**:
  1. WNTR/EPANET pressure-driven analysis (PDA) and demand-driven analysis (DDA) network simulations (Task 10).
  2. Torricelli orifice discharge calculations ($Q = C_d A \sqrt{2gh}$ where $C_d = 0.62$).
  3. Virtual rover odometry and kinematic telemetry (Task 05/06).
- **Finding**: **PASS**. All hydraulic simulation outputs and virtual rover telemetry are correctly tagged with `classification="SIMULATED"`, `is_simulated=True`, and `source="VIRTUAL_SIMULATION_ENGINE"`. The system strictly prohibits presenting Torricelli discharge ($184.2\text{ m}^3/\text{day}$) as a metered utility billing loss.

#### 2.3 Audit of `DERIVED` Data
- **Sources Audited**:
  1. Multi-factor vulnerability score (Task 11): Weighted aggregation of hydraulic, structural, incident, and environmental components.
  2. Structural health index (Task 09): Multi-sensor regression index on $[0, 100]$.
  3. Composite Priority Index (CPI) (Task 12): Pareto multi-criteria ranking.
- **Finding**: **PASS**. Mathematical aggregations and composite scores are correctly categorized as `DERIVED`. Component weights are fully auditable.

#### 2.4 Audit of `PREDICTED` Data (Crucial Investigation)
- **Investigation Objective**:
  Task 13 documentation repeatedly referenced a *"Gradient-Boosted Survival Hazard & Random Forest Classifier (`v1.0.0-rf-gradient-predictive`)"* producing 24h, 7d, and 30d failure probabilities. We audited `apps/api/app/services/predictive_risk_service.py` and `apps/api/app/services/pipeline_health_service.py` to inspect the actual model implementation.
- **Critical Finding**:
  **NO TRAINED SURVIVAL-ANALYSIS MODELS EXIST IN THE CODEBASE.**
  - There is no Cox proportional hazards model.
  - There is no Kaplan-Meier survival estimator.
  - There is no Random Survival Forest or Gradient-Boosted survival hazard tree.
  - There is no training dataset, no right-censoring treatment, no train/test split, and no Brier score calibration metric.
  - The actual implementation in `PredictiveRiskService.evaluate_predictive_risk()` uses a **heuristic deterministic rule formula**:
    $$\text{acute\_risk} = 0.01 + 0.35 \cdot \mathbf{1}_{(\Delta P \ge 1.0\text{ bar})} + 0.25 \cdot \text{health\_deficit} + 0.15 \cdot (-\text{slope})$$
- **Remediation**:
  1. All claims of "trained random forest survival models" or "gradient-boosted hazard curves" have been **REMOVED**.
  2. The calculation is honestly re-labeled as an **"Empirical Multi-Horizon Degradation Risk Index (Heuristic Rule-Based Regression)"**.
  3. The assistant explicitly informs operators that failure probabilities are rule-based hazard scores rather than machine-learning survival probabilities.

#### 2.5 Audit of `OPERATOR_ENTERED` Data
- **Sources Audited**:
  `OperationalDecisionModel` records from Task 12 (`decision_type`, `operator_name`, `operator_id`, `decision_reason`, `decision_timestamp`).
- **Finding**: **PASS**. Operator actions carry immutable timestamps, user IDs, and explicit attribution.

#### 2.6 Audit of `UNKNOWN` Data
- **Finding**:
  In Task 13, unmeasured quantities (such as borehole soil resistivity, redox potential, and night-flow DMA calibration) were described in text but not consistently returned as distinct `UNKNOWN` evidence items in the structured schema.
- **Remediation**:
  `EvidenceIntelligenceService` now explicitly injects `classification="UNKNOWN"`, `confidence=0.0`, and `validation_status="DATA_UNAVAILABLE"` evidence records (e.g., `EVID-UNK-SOIL-{segment_id}`) so sensor blind spots are visible to both machines and humans.

---

### 3. Provenance Summary Table

| Evidence Type | Claimed Classification | Audited Classification | Provenance Source | Calibration Status |
| :--- | :--- | :--- | :--- | :--- |
| **Pipeline Segment Metadata** | `MEASURED` | `MEASURED` (Asset Spec) | GIS Asset Registry | `ASSET_REGISTRY_RECORD` |
| **Hydrophone Sensor Readings**| `MEASURED` | `SIMULATED` | Simulation Telemetry Engine | `UNVERIFIED_VIRTUAL` |
| **Acoustic Leak Detection** | `DERIVED` | `DERIVED` | Anomaly Classification Service | `NOT_APPLICABLE` |
| **Torricelli Discharge** | `SIMULATED` | `SIMULATED` | WNTR / EPANET Solver | `SIMULATED_MODEL` |
| **Multi-Factor Vulnerability**| `DERIVED` | `DERIVED` | Geospatial Risk Engine | `NOT_APPLICABLE` |
| **7-Day Failure Risk** | `PREDICTED` (Survival ML) | `PREDICTED` (Heuristic Index)| Empirical Rule Calculation | `NOT_APPLICABLE` |
| **Operator Decision** | `OPERATOR_ENTERED` | `OPERATOR_ENTERED` | Command Center Workflows | `NOT_APPLICABLE` |
| **Borehole Soil Resistivity** | `UNKNOWN` | `UNKNOWN` | Unmeasured / Missing | `UNMEASURED` |

