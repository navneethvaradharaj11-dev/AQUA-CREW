# AQUA CREW — TASK 19: REST API CONTRACTS & OPENAPI SPECIFICATION
## Endpoint Definitions, Query Parameters, Request/Response Payloads & RBAC Rules

---

### 1. Base URL & Common Conventions

- **Base URL**: `/api/v1/incidents`
- **Security**: Bearer JWT Token via `Authorization: Bearer <token>`
- **Content-Type**: `application/json`
- **Simulation Invariant**: All responses contain `is_simulated: true` and `evidence_provenance: "SIMULATED"`.

---

### 2. Endpoints Summary

| Method | Path | Role Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/status` | Public / Viewer | Module health, task info, and hardware actuation safety status |
| `GET` | `/stats/overview` | `VIEWER` | Aggregated system-wide KPIs for command center dashboard |
| `GET` | `/` | `VIEWER` | List incidents with optional status, severity, and DMA filtering |
| `POST` | `/` | `OPERATOR` | Manually or programmatically register an incident |
| `GET` | `/{incident_id}` | `VIEWER` | Retrieve full incident workspace payload by ID or code |
| `POST` | `/{incident_id}/transition` | `OPERATOR` | Execute validated forward state transition |
| `POST` | `/{incident_id}/approve` | `OPERATOR` / `ENGINEER` | Record human dispatch approval or certified repair sign-off |
| `POST` | `/{incident_id}/simulation-resolution` | `ENGINEER` | Run post-repair hydraulic simulation delta and close incident |
| `POST` | `/scenarios/master-e2e` | `OPERATOR` | One-click execution of master 10-stage end-to-end acceptance scenario |

---

### 3. Detailed Request/Response Contracts

#### 3.1 GET `/api/v1/incidents/stats/overview`
**Response (200 OK)**:
```json
{
  "total_incidents": 4,
  "active_incidents": 3,
  "closed_incidents": 1,
  "critical_incidents": 1,
  "awaiting_approval_incidents": 2,
  "total_estimated_water_loss_lps": 53.4,
  "by_status": {
    "TRIAGED": 1,
    "INSPECTION_PROPOSED": 1,
    "AWAITING_ENGINEERING_APPROVAL": 1,
    "CLOSED": 1
  },
  "by_severity": {
    "CRITICAL": 1,
    "HIGH": 1,
    "MEDIUM": 1,
    "LOW": 1
  },
  "by_category": {
    "ACOUSTIC_ANOMALY": 2,
    "SUSPECTED_LEAK": 1,
    "BURST": 1
  }
}
```

#### 3.2 POST `/api/v1/incidents/{incident_id}/approve`
**Request Payload**:
```json
{
  "approval_type": "REPAIR_PLAN",
  "approved": true,
  "comments": "Certified municipal engineering sign-off for full-circle clamp installation."
}
```
**Response (200 OK)**:
```json
{
  "id": "INC-2026-0003",
  "incident_code": "INC-2026-003",
  "title": "Critical Circumferential Joint Rupture — Uptown Feed",
  "lifecycle_status": "APPROVED",
  "severity": "CRITICAL",
  "priority": "P1",
  "pipeline_segment_id": "PIPE-003",
  "approvals": [
    {
      "id": "APV-B4C5D6E7",
      "incident_id": "INC-2026-0003",
      "approval_type": "REPAIR_PLAN",
      "status": "APPROVED",
      "approved_by": "USR-ENG-01",
      "approver_role": "ENGINEER",
      "digital_signature": "E9F2A14B8C3D...",
      "comments": "Certified municipal engineering sign-off for full-circle clamp installation.",
      "created_at": "2026-11-16T20:41:42Z"
    }
  ]
}
```

#### 3.3 POST `/api/v1/incidents/scenarios/master-e2e`
**Request Payload**:
```json
{
  "pipeline_segment_id": "PIPE-SEC-4B-92",
  "acoustic_db": 89.5
}
```
**Response (200 OK)**:
```json
{
  "success": true,
  "incident_id": "INC-20261116-A1B2C3",
  "incident_code": "INC-2026-9874",
  "lifecycle_status": "CLOSED",
  "total_workflow_events": 9,
  "total_approvals": 2,
  "final_resolution_data": {
    "post_repair_pressure_gain_bar": 0.52,
    "leak_flow_eliminated_lps": 12.8,
    "hydraulic_stability_verified": true,
    "provenance": "SIMULATED"
  },
  "hardware_actuation_blocked": true,
  "is_simulated": true
}
```

