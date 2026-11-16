# AQUA CREW — TASK 16 API REFERENCE
## REST API Endpoint Specification for Repair Planning & Management

---

## 1. Overview & Base Configuration

All Task 16 endpoints are mounted under `/api/v1/repair-management` and require standard HTTP Bearer token authentication in the `Authorization` header:

```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
Content-Type: application/json
```

Role requirements follow the platform's 4-tier Zero-Trust RBAC hierarchy:
`VIEWER` $\le$ `OPERATOR` $\le$ `ENGINEER` $\le$ `ADMINISTRATOR`.

---

## 2. Endpoint Index

| Method | Endpoint Path | Minimum Role | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/overview` | `VIEWER` | System-wide repair KPIs, expenditure, and volume saved. |
| `GET` | `/assessments` | `VIEWER` | List historical and active damage assessments. |
| `POST` | `/assessments/evaluate` | `OPERATOR` | Execute multi-factor damage assessment on a pipe segment. |
| `GET` | `/assessments/{assessment_id}` | `VIEWER` | Retrieve full damage assessment details and provenance. |
| `GET` | `/recommendations/{assessment_id}` | `VIEWER` | Retrieve repair method options and engineering rationale. |
| `GET` | `/plans` | `VIEWER` | List repair master plans with optional status filtering. |
| `POST` | `/plans/generate` | `OPERATOR` | Formulate a complete end-to-end master repair plan. |
| `GET` | `/plans/{plan_id}` | `VIEWER` | Retrieve master repair plan details with BOM and schedule. |
| `POST` | `/plans/{plan_id}/approve` | `ENGINEER` | **Certified PE Approval**: Advances plan to `APPROVED`. |
| `POST` | `/plans/{plan_id}/reject` | `ENGINEER` | **Certified PE Rejection**: Rejects plan with justification. |
| `POST` | `/plans/{plan_id}/transition` | `OPERATOR` | Transition plan lifecycle state with audit logging. |
| `GET` | `/plans/{plan_id}/resources` | `VIEWER` | Retrieve itemized bill of materials and equipment roster. |
| `GET` | `/plans/{plan_id}/costs` | `VIEWER` | Retrieve transparent itemized cost breakdown and bounds. |
| `GET` | `/plans/{plan_id}/schedule` | `VIEWER` | Retrieve virtual crew dispatch schedule and transit route. |
| `GET` | `/plans/{plan_id}/simulation` | `VIEWER` | Retrieve pre/post digital twin hydraulic simulation metrics. |
| `POST` | `/plans/{plan_id}/verify` | `ENGINEER` | **Certified Quality Signoff**: Issues SHA-256 certificate. |
| `GET` | `/plans/{plan_id}/verification` | `VIEWER` | Retrieve post-repair verification certificate and hash. |
| `GET` | `/plans/{plan_id}/events` | `VIEWER` | Retrieve immutable workflow audit event log. |
| `GET` | `/crews` | `VIEWER` | List virtual repair crews and real-time depot telemetry. |

---

## 3. Detailed Endpoint Contracts

### 3.1 GET `/overview`
- **Minimum Role**: `VIEWER`
- **Response**: `200 OK`
```json
{
  "system_status": "OPERATIONAL",
  "active_assessments_count": 12,
  "pending_engineering_reviews_count": 3,
  "approved_plans_count": 5,
  "active_repairs_count": 2,
  "verified_repairs_count": 18,
  "total_water_loss_prevented_m3": 4825.4,
  "total_repair_expenditure_usd": 74320.50,
  "average_repair_duration_hours": 7.2,
  "supported_damage_categories": ["PIPE_LEAK", "PIPE_BURST", "JOINT_FAILURE", "CORROSION", "STRUCTURAL_CRACK", "PRESSURE_DAMAGE", "VALVE_FAILURE", "UNKNOWN_DAMAGE"],
  "supported_repair_methods": ["CLAMP_REPAIR", "JOINT_REPAIR_REPLACEMENT", "PIPE_SECTION_REPLACEMENT", "INTERNAL_LINING_REHABILITATION", "CORROSION_PROTECTION", "VALVE_REPLACEMENT", "PRESSURE_MANAGEMENT", "FURTHER_INSPECTION_REQUIRED"],
  "is_simulated": true
}
```

---

### 3.2 POST `/assessments/evaluate`
- **Minimum Role**: `OPERATOR`
- **Request Body**:
```json
{
  "pipeline_segment_id": "PIPE-SEC-01",
  "source_inspection_report_id": "INSP-REP-2026-001",
  "notes": "Acoustic sensor detected 180 L/h continuous leak signature"
}
```
- **Response**: `200 OK` (`DamageAssessmentSchema`)
```json
{
  "id": "DMG-PIPE-SEC-01-A4B92C",
  "pipeline_segment_id": "PIPE-SEC-01",
  "segment_name": "East Main Trunk 01",
  "source_inspection_report_id": "INSP-REP-2026-001",
  "damage_category": "PIPE_LEAK",
  "severity": "HIGH",
  "pipe_material": "Ductile Iron",
  "pipe_diameter_mm": 300.0,
  "pipe_age_years": 28.5,
  "nominal_pressure_psi": 65.0,
  "estimated_water_loss_lph": 180.0,
  "structural_vulnerability_score": 62.5,
  "previous_repair_count": 1,
  "inspection_confidence": 0.88,
  "evidence_completeness_pct": 100.0,
  "missing_information": [],
  "engineering_review_required": true,
  "supporting_evidence": [
    {
      "evidence_id": "EVID-ASSET-PIPE-SEC-01",
      "source_subsystem": "TASK_04_GIS",
      "classification": "MEASURED",
      "metric_name": "pipe_diameter_material",
      "metric_value": {"diameter_mm": 300.0, "material": "Ductile Iron"},
      "description": "Conduit 'East Main Trunk 01' (Ductile Iron, 300mm, Nominal 65.0 PSI).",
      "confidence": 1.0,
      "observed_at": "2026-11-16T12:00:00Z"
    }
  ],
  "assessment_notes": "Acoustic survey confirms 180 L/h leak signature.",
  "assessed_by": "SYSTEM_REPAIR_ENGINE",
  "assessed_at": "2026-11-16T12:05:00Z",
  "is_simulated": true
}
```

---

### 3.3 POST `/plans/generate`
- **Minimum Role**: `OPERATOR`
- **Request Body**:
```json
{
  "pipeline_segment_id": "PIPE-SEC-01",
  "source_inspection_report_id": "INSP-REP-2026-001",
  "plan_name": "East Main Immediate Clamping Operation",
  "selected_method": "CLAMP_REPAIR",
  "preferred_crew_id": "CREW-MECH-01",
  "operator_notes": "Traffic permits submitted to municipal highway dept"
}
```
- **Response**: `200 OK` (`RepairPlanSchema`)
```json
{
  "id": "PLAN-PIPE-SEC-01-F93C1D",
  "plan_name": "East Main Immediate Clamping Operation",
  "pipeline_segment_id": "PIPE-SEC-01",
  "segment_name": "East Main Trunk 01",
  "damage_assessment_id": "DMG-PIPE-SEC-01-A4B92C",
  "repair_recommendation_id": "REC-REP-PIPE-SEC-01-A4B92C",
  "selected_method": "CLAMP_REPAIR",
  "workflow_status": "ENGINEERING_REVIEW_PENDING",
  "priority": {
    "pipeline_segment_id": "PIPE-SEC-01",
    "repair_priority_score": 72.5,
    "priority_category": "HIGH",
    "contributing_factors": {
      "damage_severity": 75.0,
      "water_loss_volume": 36.0,
      "conduit_criticality": 50.0,
      "structural_vulnerability": 62.5,
      "spatial_hotspot_risk": 20.0
    },
    "uncertainty_margin": 5.0,
    "recommended_response_time_hours": 72,
    "escalation_requirements": ["MUNICIPAL_TRAFFIC_DIVERT_PERMIT"],
    "calculated_at": "2026-11-16T12:06:00Z"
  },
  "resources": {
    "repair_plan_id": "PLAN-PIPE-SEC-01-F93C1D",
    "selected_method": "CLAMP_REPAIR",
    "items": [],
    "equipment": [],
    "total_material_cost_usd": 850.0,
    "total_equipment_cost_usd": 1415.0,
    "required_crew_specialization": "PIPELINE_MECHANICAL",
    "minimum_crew_size": 3,
    "has_hazardous_materials": false,
    "notes": "Standard split-sleeve mechanical installation."
  },
  "cost_estimate": {
    "id": "EST-PIPE-SEC-01-F93C1D",
    "damage_assessment_id": "DMG-PIPE-SEC-01-A4B92C",
    "pipeline_segment_id": "PIPE-SEC-01",
    "components": [],
    "total_material_cost_usd": 850.0,
    "total_equipment_cost_usd": 1415.0,
    "total_labour_cost_usd": 1296.0,
    "inspection_cost_usd": 450.0,
    "estimated_water_loss_cost_usd": 24.0,
    "restoration_cost_usd": 600.0,
    "contingency_cost_usd": 463.50,
    "total_estimated_cost_usd": 5098.50,
    "estimated_downtime_hours": 6.0,
    "cost_uncertainty_lower_bound_usd": 4588.65,
    "cost_uncertainty_upper_bound_usd": 5608.35,
    "financial_disclaimer": "SYNTHETIC ESTIMATE DISCLAIMER: Synthetic engineering estimate generated for operational planning. Not an active commercial quotation or guaranteed expenditure.",
    "created_at": "2026-11-16T12:06:00Z",
    "is_simulated": true
  },
  "schedule": {
    "schedule_id": "SCH-PIPE-SEC-01-F93C1D",
    "repair_plan_id": "PLAN-PIPE-SEC-01-F93C1D",
    "crew_id": "CREW-MECH-01",
    "crew_name": "Metro Rapid Mechanical Repair Crew",
    "scheduled_start": "2026-11-17T08:00:00Z",
    "scheduled_end": "2026-11-17T14:15:00Z",
    "estimated_duration_hours": 6.0,
    "travel_distance_km": 4.2,
    "travel_time_hours": 0.25,
    "has_schedule_conflicts": false,
    "schedule_conflict_details": null,
    "scheduling_notes": "Virtual crew schedule assigned to Metro Rapid Mechanical Repair Crew."
  },
  "approved_by": null,
  "approved_at": null,
  "rejection_reason": null,
  "operator_notes": "Traffic permits submitted to municipal highway dept",
  "digital_twin_scenario_id": "SCEN-REPAIR-PIPE-SEC-01-9F2B",
  "created_by": "operator_dan",
  "created_at": "2026-11-16T12:06:00Z",
  "updated_at": "2026-11-16T12:06:00Z",
  "is_simulated": true
}
```

---

### 3.4 POST `/plans/{plan_id}/approve`
- **Minimum Role**: `ENGINEER` (`ADMINISTRATOR` permitted; `OPERATOR`/`VIEWER` return `HTTP 403 Forbidden`).
- **Request Body**:
```json
{
  "engineer_notes": "Hydraulic perturbation simulated. AWWA C230 clamp certified by PE."
}
```
- **Response**: `200 OK` (Updates `workflow_status` to `"APPROVED"` and logs audit event).

---

### 3.5 POST `/plans/{plan_id}/verify`
- **Minimum Role**: `ENGINEER`
- **Request Body**:
```json
{
  "repair_plan_id": "PLAN-PIPE-SEC-01-F93C1D",
  "measured_post_repair_pressure_bar": 4.25,
  "measured_post_repair_flow_lps": 14.8,
  "acoustic_sensor_reading_db": 38.5,
  "visual_inspection_notes": "Clamp seated with torque wrench to 110 ft-lbs. Zero weeping under line pressure.",
  "engineer_signoff_notes": "Pressure restored to normal gradient. Acoustic leak signature cleared."
}
```
- **Response**: `200 OK` (`RepairVerificationSchema`)
```json
{
  "id": "VERIF-PIPE-SEC-01-F93C1D",
  "repair_plan_id": "PLAN-PIPE-SEC-01-F93C1D",
  "pipeline_segment_id": "PIPE-SEC-01",
  "verification_outcome": "VERIFIED_SUCCESS",
  "pre_repair_leakage_lph": 180.0,
  "post_repair_leakage_lph": 3.6,
  "leakage_reduction_pct": 98.0,
  "acoustic_anomaly_cleared": true,
  "pressure_gradient_restored": true,
  "remaining_uncertainty_pct": 5.0,
  "supporting_evidence": [],
  "verified_by": "engineer_sarah",
  "verified_at": "2026-11-16T14:30:00Z",
  "tamper_proof_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "is_simulated": true
}
```

