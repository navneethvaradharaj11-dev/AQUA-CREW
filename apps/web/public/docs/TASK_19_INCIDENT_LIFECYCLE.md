# AQUA CREW — TASK 19: MASTER INCIDENT LIFECYCLE
## Formal State Machine, Transition Rules, Preconditions & Recovery Protocols

---

### 1. State Machine Definition

The AQUA CREW Master Incident Lifecycle consists of an 11-state, strictly guarded finite state machine.

```
       [ NONE ]
           │ (1. Telemetry Ingestion)
           ▼
      [ DETECTED ]
           │ (2. Automated AI Triage)
           ▼
       [ TRIAGED ]
           │ (3. Hydraulic Digital Twin Simulation)
           ▼
    [ INVESTIGATING ]
           │ (4. Multi-Factor Risk Scoring)
           ▼
  [ INSPECTION_PROPOSED ] ──(Operator Rejection)──► [ CLOSED ]
           │ (5. Human Operator Dispatch Approval)
           ▼
      [ APPROVED ] (Inspection Phase)
           │ (6. Rover Departure)
           ▼
 [ INSPECTION_IN_PROGRESS ]
           │ (7. Rover Crawl Complete)
           ▼
      [ ASSESSED ]
           │ (8. Repair Plan Formulation)
           ▼
   [ REPAIR_PLANNED ]
           │ (Automatic Submission)
           ▼
[ AWAITING_ENGINEERING_APPROVAL ] ──(Engineer Rejection w/ Feedback)──► [ REPAIR_PLANNED ]
           │ (9. Certified Municipal Engineer Sign-off)
           ▼
      [ APPROVED ] (Repair Phase)
           │ (10. Post-Repair Sim Twin Run)
           ▼
 [ SIMULATED_RESOLUTION ]
           │ (Verification Confirmed)
           ▼
       [ CLOSED ]
```

---

### 2. State-by-State Transition Specification

| From State | To State | Trigger / Action | Actor | Preconditions | Postconditions |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `NONE` | `DETECTED` | Telemetry ingestion anomaly detected | System / Edge Sensor | Telemetry dB > baseline threshold; calibrated | New `UnifiedIncidentModel` record created; Stage 1 event logged |
| `DETECTED` | `TRIAGED` | Automated AI acoustic classification | System AI Engine | Feature extraction complete; leak prob calculated | Severity & Priority assigned; Stage 2 event logged |
| `TRIAGED` | `INVESTIGATING` | Hydraulic digital twin simulation executed | System Hydraulic Engine | Pipeline segment mapped in GIS network | Headloss delta (m) & water loss (L/s) populated; Stage 4 event logged |
| `INVESTIGATING`| `INSPECTION_PROPOSED`| Multi-factor risk calculation | System Risk Engine | Risk score calculated (0-100) | Approval request created for Operator; Stage 5 event logged |
| `INSPECTION_PROPOSED`| `APPROVED` | Operator mission sign-off | Operator / Admin | Valid JWT token; role $\ge$ OPERATOR | Approval recorded with digital signature; Stage 6 event logged |
| `INSPECTION_PROPOSED`| `CLOSED` | Operator marks false positive | Operator / Admin | Justification comment $\ge 5$ chars | Incident marked CLOSED with resolution summary |
| `APPROVED` | `INSPECTION_IN_PROGRESS`| Rover dispatched to site | System Fleet Engine | Rover assigned (`ROV-001`); battery > 40% | Rover state set to IN_MISSION; Stage 7 event logged |
| `INSPECTION_IN_PROGRESS`| `ASSESSED` | Virtual inspection crawl completed | Rover Agent | Pipe segment crawl completed; defect measured | Synthetic findings JSON stored (crack len, defect); Stage 7 event logged |
| `ASSESSED` | `REPAIR_PLANNED` | Repair intelligence formulation | System Repair Engine| Pipe material, diameter, and defect known | Repair method chosen, BOM generated; Stage 8 event logged |
| `REPAIR_PLANNED`| `AWAITING_ENGINEERING_APPROVAL`| Formal plan submission | System Repair Engine| Cost estimate & urgency tier calculated | Engineering approval request created; Stage 8 event logged |
| `AWAITING_ENGINEERING_APPROVAL`| `APPROVED` | Certified municipal engineer sign-off | Engineer / Admin | Valid JWT token; role $\in$ {ENGINEER, ADMIN} | SHA-256 digital signature recorded; Stage 9 event logged |
| `AWAITING_ENGINEERING_APPROVAL`| `REPAIR_PLANNED` | Engineer rejects repair plan | Engineer / Admin | Mandatory non-empty engineering justification | Status reverted for re-formulation with feedback; Stage 9 event logged |
| `APPROVED` | `SIMULATED_RESOLUTION`| Virtual repair executed & twin delta verified | Engineer / Admin | Plan approved; no physical actuation commands | Simulated headloss cleared; pressure recovery logged; Stage 10 event logged |
| `SIMULATED_RESOLUTION`| `CLOSED` | Final resolution archival | System / Engineer | Twin stability confirmed; 0 L/s loss verified | Final resolution summary saved; incident archived |

---

### 3. Error Handling & Invariant Enforcement

1. **Attempted Illegal Stage Skip**:
   Calling transition `POST /incidents/{id}/transition` with an invalid target state (e.g., `DETECTED` $\rightarrow$ `CLOSED`) immediately raises an `IncidentLifecycleError` returned as HTTP 422 Unprocessable Entity.
2. **Attempted Physical Actuation**:
   Including SCADA commands (`CLOSE_VALVE`, `START_PUMP`, `OVERRIDE_SCADA_PLC`) in verification notes immediately raises an HTTP 403 Forbidden with code `HARDWARE_ACTUATION_PROHIBITED`.
3. **Role Violations**:
   An operator attempting to approve a repair plan receives an HTTP 403 Forbidden (`Role 'OPERATOR' is not authorized to approve repair plans. Requires ENGINEER or ADMIN`).

