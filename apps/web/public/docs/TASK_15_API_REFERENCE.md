# AQUA CREW — TASK 15 API REFERENCE
## Autonomous Inspection Intelligence REST & Telemetry Specification

**Document ID:** `AQUA-TASK-15-API`  
**Base Path:** `/api/v1/inspection-intelligence`  
**Protocol:** HTTP/1.1 REST + JSON / WebSocket Telemetry  
**Security Standard:** Bearer JWT (Zero-Trust RBAC)  

---

### 1. Role-Based Access Control (RBAC) Matrix

All endpoints require cryptographic authentication via Bearer JWT tokens. Permissions are strictly mapped to operator roles:

| Endpoint | Method | Permitted Roles | Description |
| :--- | :---: | :--- | :--- |
| `/overview` | `GET` | `VIEWER`, `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | System health, counts, and capabilities |
| `/recommendations` | `GET` | `VIEWER`, `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Retrieve active inspection recommendations |
| `/recommendations/generate` | `POST` | `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Trigger multi-factor urgency evaluation |
| `/rovers/suitability` | `GET` | `VIEWER`, `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Rank fleet for target coordinates |
| `/plans/generate` | `POST` | `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Formulate multi-rover coordinated plan |
| `/plans` | `GET` | `VIEWER`, `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | List historical and pending plans |
| `/plans/{plan_id}` | `GET` | `VIEWER`, `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Retrieve full plan details and route legs |
| `/plans/{plan_id}/approve` | `POST` | `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Formally approve plan for execution |
| `/plans/{plan_id}/reject` | `POST` | `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Reject plan with mandatory reason |
| `/missions/{plan_id}/launch/{rover_id}` | `POST` | `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Launch approved mission into active execution |
| `/missions/{mission_id}/step` | `POST` | `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Advance mission step along route |
| `/missions/{mission_id}/adapt` | `POST` | `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Dynamically adapt route for anomaly |
| `/missions/{mission_id}/progress` | `GET` | `VIEWER`, `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Real-time progress, telemetry, anomalies |
| `/reports` | `GET` | `VIEWER`, `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | List completed inspection reports |
| `/reports/{report_id}` | `GET` | `VIEWER`, `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Retrieve report with SHA-256 digest |
| `/reports/{report_id}/review` | `POST` | `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Operator review and archival sign-off |
| `/events` | `GET` | `VIEWER`, `OPERATOR`, `ENGINEER`, `ADMINISTRATOR` | Query audit log of inspection events |

---

### 2. Core Endpoint Specifications

#### 2.1. System Overview
```http
GET /api/v1/inspection-intelligence/overview
Authorization: Bearer <jwt_token>
```
**Response (200 OK):**
```json
{
  "system_status": "ONLINE",
  "active_recommendations_count": 5,
  "pending_approval_plans_count": 1,
  "active_missions_count": 1,
  "completed_reports_count": 12,
  "supported_methods": [
    "ACOUSTIC_CORRELATION",
    "VISUAL_CCTV",
    "THERMAL_INFRARED",
    "MULTI_SENSOR_CRAWLER",
    "ULTRASONIC_THICKNESS"
  ],
  "is_simulated": true
}
```

---

#### 2.2. Generate Recommendations
```http
POST /api/v1/inspection-intelligence/recommendations/generate?min_urgency=30.0
Authorization: Bearer <jwt_token>
```
**Response (200 OK):**
```json
[
  {
    "id": "INSP-REC-PIPE-SEC-4B-92",
    "pipeline_segment_id": "PIPE-SEC-4B-92",
    "segment_name": "Metro Central Main Trunk Line B",
    "priority_score": 82.5,
    "priority_category": "CRITICAL",
    "urgency_factors": {
      "network_consequence": 100.0,
      "vulnerability": 88.0,
      "degradation_rate": 65.0,
      "active_leak_detection": 92.0,
      "hydraulic_stress": 72.0,
      "cluster_proximity": 80.0
    },
    "supporting_evidence": [
      {
        "evidence_id": "EVID-ASSET-PIPE-SEC-4B-92",
        "source_subsystem": "TASK_04_GIS",
        "classification": "MEASURED",
        "metric_name": "pipe_diameter_mm",
        "metric_value": 600,
        "description": "Conduit 'Metro Central Main Trunk Line B' (Material: Ductile Iron, Diameter: 600mm).",
        "confidence": 1.0,
        "observed_at": "2026-11-16T10:00:00Z"
      },
      {
        "evidence_id": "EVID-LEAK-DET-01",
        "source_subsystem": "TASK_07_AI_LEAKS",
        "classification": "MEASURED",
        "metric_name": "acoustic_leak_confidence",
        "metric_value": 0.94,
        "description": "Acoustic anomaly detected (Classification: HIGH_LEAK_PROBABILITY, Anomaly: 0.92, Est Loss: 320.0 L/h).",
        "confidence": 0.94,
        "observed_at": "2026-11-16T11:15:00Z"
      }
    ],
    "primary_classification": "DERIVED",
    "confidence": 0.88,
    "uncertainty_radius_m": 15.0,
    "recommended_method": "ACOUSTIC_CORRELATION",
    "estimated_duration_minutes": 45,
    "required_rover_capabilities": [
      "pipe_navigation",
      "hydrophone_acoustic"
    ],
    "recommended_action": "Dispatch acoustic hydrophone rover to pinpoint acoustic cross-correlation leak center.",
    "human_approval_status": "PENDING_APPROVAL",
    "created_at": "2026-11-16T11:30:00Z",
    "is_simulated": true
  }
]
```

---

#### 2.3. Formulate Coordinated Inspection Plan
```http
POST /api/v1/inspection-intelligence/plans/generate
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "plan_name": "Downtown High-Risk Conduits Campaign",
  "min_urgency": 50.0,
  "max_targets_per_rover": 2,
  "safety_reserve_pct": 20.0
}
```
**Response (200 OK):**
```json
{
  "id": "PLAN-A19F8E",
  "plan_name": "Downtown High-Risk Conduits Campaign",
  "allocations": [
    {
      "rover_id": "ROV-AQUA-01",
      "rover_name": "Triton-1 Crawler",
      "assigned_targets": [
        {
          "target_id": "TGT-PIPE-SEC-4B-92",
          "pipeline_segment_id": "PIPE-SEC-4B-92",
          "target_coordinates": [-74.006, 40.7128],
          "inspection_method": "ACOUSTIC_CORRELATION",
          "priority_score": 82.5,
          "estimated_duration_minutes": 45
        }
      ],
      "route_waypoints": [
        [-74.006, 40.7128],
        [-74.001, 40.714],
        [-74.006, 40.7128]
      ],
      "segments_traversed": ["PIPE-SEC-4B-92"],
      "total_route_distance_m": 940.5,
      "estimated_mission_duration_s": 4410.0,
      "estimated_battery_drain_pct": 5.4,
      "projected_reserve_after_return_pct": 89.6,
      "return_to_base_feasible": true,
      "route_selection_reason": "Optimized shortest connected pipeline path visiting [PIPE-SEC-4B-92] covering 941m across 1 underground pipe segments with safe return-to-base reserve of 89.6% (Required: 20.0%)."
    }
  ],
  "unreachable_targets": [],
  "conflict_checks_passed": true,
  "total_rovers_assigned": 1,
  "total_targets_covered": 1,
  "human_approval_status": "PENDING_APPROVAL",
  "approved_by": null,
  "approved_at": null,
  "rejection_reason": null,
  "created_at": "2026-11-16T11:32:00Z",
  "is_simulated": true
}
```

---

#### 2.4. Approve Inspection Plan
```http
POST /api/v1/inspection-intelligence/plans/PLAN-A19F8E/approve
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "operator_notes": "Hydraulic conditions verified. Route approved for autonomous execution."
}
```
**Response (200 OK):**
```json
{
  "id": "PLAN-A19F8E",
  "human_approval_status": "APPROVED",
  "approved_by": "operator",
  "approved_at": "2026-11-16T11:35:00Z"
}
```

---

#### 2.5. Launch Mission
```http
POST /api/v1/inspection-intelligence/missions/PLAN-A19F8E/launch/ROV-AQUA-01
Authorization: Bearer <jwt_token>
```
**Response (200 OK):**
```json
{
  "mission_id": "MIS-INSP-A19F8E-ROV-AQUA-01",
  "rover_id": "ROV-AQUA-01",
  "plan_id": "PLAN-A19F8E",
  "status": "IN_PROGRESS",
  "progress_percentage": 0.0,
  "current_coordinates": [-74.006, 40.7128],
  "distance_traversed_m": 0.0,
  "total_distance_m": 940.5,
  "battery_percentage": 95.0,
  "motor_temperature_c": 26.5,
  "recent_observations": [],
  "active_anomalies_detected": 0,
  "route_adapted": false,
  "adaptation_history": [],
  "last_updated": "2026-11-16T11:36:00Z",
  "is_simulated": true
}
```

---

#### 2.6. Advance Mission Step
```http
POST /api/v1/inspection-intelligence/missions/MIS-INSP-A19F8E-ROV-AQUA-01/step?step_increment_m=150.0
Authorization: Bearer <jwt_token>
```
**Response (200 OK):**
```json
{
  "mission_id": "MIS-INSP-A19F8E-ROV-AQUA-01",
  "rover_id": "ROV-AQUA-01",
  "plan_id": "PLAN-A19F8E",
  "status": "IN_PROGRESS",
  "progress_percentage": 15.9,
  "current_coordinates": [-74.0045, 40.7132],
  "distance_traversed_m": 150.0,
  "total_distance_m": 940.5,
  "battery_percentage": 94.6,
  "motor_temperature_c": 27.2,
  "recent_observations": [
    {
      "observation_id": "OBS-001-A19F",
      "timestamp": "2026-11-16T11:37:00Z",
      "coordinates": [-74.0045, 40.7132],
      "pipeline_segment_id": "PIPE-SEC-4B-92",
      "sensor_type": "HYDROPHONE",
      "metric_name": "acoustic_energy_rms",
      "measured_value": 0.042,
      "unit": "V_rms",
      "anomaly_detected": false,
      "classification": "SIMULATED"
    },
    {
      "observation_id": "OBS-002-A19F",
      "timestamp": "2026-11-16T11:37:00Z",
      "coordinates": [-74.0045, 40.7132],
      "pipeline_segment_id": "PIPE-SEC-4B-92",
      "sensor_type": "THERMAL",
      "metric_name": "temperature_differential_k",
      "measured_value": 0.28,
      "unit": "K",
      "anomaly_detected": false,
      "classification": "SIMULATED"
    }
  ],
  "active_anomalies_detected": 0,
  "route_adapted": false,
  "adaptation_history": [],
  "last_updated": "2026-11-16T11:37:00Z",
  "is_simulated": true
}
```

---

#### 2.7. Trigger Adaptive Route Reroute
```http
POST /api/v1/inspection-intelligence/missions/MIS-INSP-A19F8E-ROV-AQUA-01/adapt
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "adaptation_reason": "High-frequency acoustic anomaly detected at chainage 450m",
  "detour_coordinates": [-74.0035, 40.7135]
}
```
**Response (200 OK):**
```json
{
  "mission_id": "MIS-INSP-A19F8E-ROV-AQUA-01",
  "status": "IN_PROGRESS",
  "route_adapted": true,
  "adaptation_history": [
    {
      "timestamp": "2026-11-16T11:38:00Z",
      "reason": "High-frequency acoustic anomaly detected at chainage 450m",
      "detour_coordinate": [-74.0035, 40.7135]
    }
  ]
}
```

---

#### 2.8. Retrieve Evidence-Grounded Inspection Report
```http
GET /api/v1/inspection-intelligence/reports/INSP-REP-A19F8E-ROV-AQUA-01
Authorization: Bearer <jwt_token>
```
**Response (200 OK):**
```json
{
  "id": "INSP-REP-A19F8E-ROV-AQUA-01",
  "plan_id": "PLAN-A19F8E",
  "mission_id": "MIS-INSP-A19F8E-ROV-AQUA-01",
  "rover_id": "ROV-AQUA-01",
  "pipeline_segment_id": "PIPE-SEC-4B-92",
  "segment_name": "Metro Central Main Trunk Line B",
  "inspection_method": "ACOUSTIC_CORRELATION",
  "start_time": "2026-11-16T11:36:00Z",
  "completion_time": "2026-11-16T11:45:00Z",
  "route_distance_m": 940.5,
  "inspected_distance_m": 940.5,
  "sensor_observations_count": 18,
  "detected_anomalies": [
    {
      "timestamp": "2026-11-16T11:41:00Z",
      "coordinates": [-74.0035, 40.7135],
      "pipeline_segment_id": "PIPE-SEC-4B-92",
      "sensor_type": "HYDROPHONE",
      "metric_name": "acoustic_energy_rms",
      "measured_value": 0.485,
      "unit": "V_rms",
      "anomaly_detected": true,
      "classification": "SIMULATED"
    }
  ],
  "evidence_provenance": "SIMULATED",
  "updated_infrastructure_risk": 78.4,
  "inspection_outcome": "SUCCESS",
  "unresolved_uncertainties": [],
  "recommended_next_action": "Schedule excavation and acoustic correlation verification clamp on joint 4B-92.",
  "reviewed_by": null,
  "reviewed_at": null,
  "tamper_proof_hash": "a5e8f497dc38010471b4a62269a84e3146e224e77dd6234b92b67f40778c8942",
  "created_at": "2026-11-16T11:45:00Z",
  "is_simulated": true
}
```

