# AQUA CREW — TASK 19: EVENT ARCHITECTURE & AUDIT TRAIL
## Asynchronous Event Bus, Workflow Telemetry & Tamper-Evident Ledgers

---

### 1. Event-Driven Architecture Overview

The AQUA CREW integration layer operates on an append-only event ledger architecture. Every state change, automated recommendation, operator dispatch, and engineering sign-off emits a strongly typed event to the database table `incident_workflow_events`.

```
                  ┌─────────────────────────────────────────┐
                  │        Domain Event Publisher           │
                  └──────────────────┬──────────────────────┘
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│ Workflow Event Log  │   │ Approval Signatures │   │ WebSocket Broadcast │
│ (incident_workflow_ │   │ (incident_approvals │   │ (Frontend Command   │
│  events)            │   │  ledger)            │   │  Center Updates)    │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
```

---

### 2. Standard Event Schema

Every event emitted by the system conforms to the following schema:

```json
{
  "id": "IWE-A1B2C3D4",
  "incident_id": "INC-2026-0001",
  "from_status": "TRIAGED",
  "to_status": "INVESTIGATING",
  "stage_number": 4,
  "actor_id": "SYSTEM_HYDRAULIC_ENGINE",
  "actor_role": "SYSTEM",
  "action": "DIGITAL_TWIN_SIMULATED",
  "notes": "Hydraulic twin simulated headloss delta of 4.25m with 12.8 L/s estimated loss.",
  "payload": {
    "headloss_delta_m": 4.25,
    "estimated_loss_lps": 12.8,
    "pipe_segment": "PIPE-SEC-4B-92"
  },
  "timestamp": "2026-11-16T20:41:40.123456Z"
}
```

---

### 3. Enumerated Domain Events

| Event Code | Stage | Trigger | Emitted By | Payload Contents |
| :--- | :--- | :--- | :--- | :--- |
| `INCIDENT_DETECTED` | 1 | Sensor threshold exceeded | Edge Ingestion Engine | Sensor ID, Raw dB, Frequency |
| `AI_TRIAGE_COMPLETED` | 2 | Acoustic classification | AI Classifier | Leak Probability, Severity, Priority |
| `DIGITAL_TWIN_SIMULATED` | 4 | Hydraulic solver run | Digital Twin Service | Headloss Delta, Discharge Rate |
| `INSPECTION_MISSION_PROPOSED` | 5 | Multi-factor risk calculation | Asset Risk Service | Risk Score, Proposed Action |
| `ROVER_SUITABILITY_EVALUATED` | 6 | Fleet matcher | Fleet Dispatch Service | Rover ID, Battery, Sensors |
| `MISSION_DISPATCHED` | 7 | Operator approval | Human Operator | Operator ID, Digital Signature |
| `INSPECTION_COMPLETED` | 7 | Virtual rover crawl finished | Rover Agent | Crack Dimensions, Defect Type |
| `REPAIR_PLAN_FORMULATED` | 8 | Repair planner | Repair Intelligence | Method, Estimated Cost USD, Urgency |
| `REPAIR_PLAN_CERTIFIED` | 9 | Certified engineer approval | Municipal Engineer | Engineer ID, SHA-256 Signature |
| `SIMULATION_RESOLUTION_VERIFIED`| 10 | Post-repair twin delta run | Digital Twin Service | Pressure Gain, Water Saved |
| `INCIDENT_CLOSED` | 10 | Final resolution archival | System / Engineer | Final Status, Closure Reason |

---

### 4. Tamper-Evident Digital Signatures

For high-consequence human approvals (`INSPECTION_DISPATCH` and `REPAIR_PLAN`), the system generates a verifiable digital signature:

$$\text{Signature} = \text{SHA256}(\text{approval\_id} \parallel \text{incident\_id} \parallel \text{decision} \parallel \text{actor\_id} \parallel \text{role} \parallel \text{timestamp})[:32]$$

This ensures that once an approval or rejection is logged, the decision cannot be repudiated or altered without invalidating the audit ledger.

