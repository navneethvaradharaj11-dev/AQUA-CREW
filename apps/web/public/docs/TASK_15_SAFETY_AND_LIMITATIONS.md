# AQUA CREW — TASK 15 SAFETY & LIMITATIONS
## Operational Boundaries, Zero-Actuation Policy & Cryptographic Verification

**Document ID:** `AQUA-TASK-15-SAFETY`  
**Status:** Approved & Enforced  
**Classification:** Operational Safety & Security Policy  
**Author:** Antigravity Autonomous Systems Engineering Team  
**Review Date:** November 2026  

---

### 1. Fundamental Safety Invariants

AQUA CREW is engineered to the highest standards of municipal infrastructure protection. To eliminate any possibility of physical network compromise, water hammer, pressure surges, or hardware destruction, the platform enforces three immutable safety invariants:

> [!CAUTION]
> #### INVARIANT 1: Zero Physical Actuation (Virtual Simulation Only)
> AQUA CREW is strictly a **decision-support simulation and digital twin software platform**. The system possesses **no hardware interfaces, actuators, or physical connections** to municipal pumps, isolation valves, PRVs, flow-control valves, or physical rovers. All rover dispatch routines, route adjustments, and inspection simulations run inside a software-contained virtual telemetry sandbox. Any instruction purporting to actuate physical machinery is rejected at the architectural level.

> [!IMPORTANT]
> #### INVARIANT 2: Mandatory Human-in-the-Loop Operator Gate
> No mission plan can transition to active simulated execution without explicit, authenticated approval by a certified human operator (`OPERATOR`, `ENGINEER`, or `ADMINISTRATOR`). Automated recommendation generation is advisory only. Unapproved plans cannot be launched.

> [!WARNING]
> #### INVARIANT 3: Zero Fabrication & Ontological Provenance Integrity
> Simulated telemetry, synthetic sensor readings, or model-generated inferences must **never** be mislabeled as empirical measurements. All synthetic hydrophone spectra, ultrasonic wall thickness readings, and thermal deltas are strictly flagged with `SIMULATED` ontological provenance. Mislabeled data is rejected by validation schemas.

---

### 2. Operational Safety Interlocks

During simulated mission execution, the `InspectionExecutionEngine` monitors live virtual telemetry at every step increment and enforces emergency abort protocols:

```mermaid
flowchart TD
    STEP["Execute Mission Step (Increment Delta d)"] --> CHECK_BATT{"Battery < 15.0%?"}
    CHECK_BATT -->|Yes| ABORT_BATT["Trigger Emergency Safety Abort<br/>(Reason: CRITICAL_BATTERY_RESERVE)"]
    CHECK_BATT -->|No| CHECK_TEMP{"Motor Temp >= 55.0°C?"}

    CHECK_TEMP -->|Yes| ABORT_TEMP["Trigger Emergency Safety Abort<br/>(Reason: MOTOR_THERMAL_RUNAWAY)"]
    CHECK_TEMP -->|No| NOMINAL["Step Traversal Successful<br/>Synthesize Telemetry & Advance"]

    ABORT_BATT --> RESET["Reset Rover State to IDLE<br/>Clear Assigned Mission ID<br/>Log Emergency Audit Event<br/>Set Mission Status to ABORTED"]
    ABORT_TEMP --> RESET
```

#### 2.1. Emergency Abort Conditions
1. **Critical Battery Reserve Interlock:** If battery charge depletes below $15.0\%$, the mission is aborted immediately to simulate preventing an underground stranding.
2. **Motor Thermal Runaway Interlock:** If simulated internal crawler friction or motor loading raises motor temperature to $\ge 55.0^\circ\text{C}$, the engine executes an immediate shutdown.
3. **Communication Loss Simulation:** If connection status transitions to `OFFLINE`, rover commands are rejected until a heartbeat reconnects.

---

### 3. Human Approval & Rejection Governance

To guarantee accountability, every state transition on inspection plans and reports is recorded in an append-only audit trail:

```mermaid
sequenceDiagram
    autonumber
    actor Op as Certified Operator
    participant API as FastAPI Inspection Gateway
    participant Repo as InspectionIntelligenceRepository
    participant DB as SQLite / PostgreSQL Audit Ledger

    Op->>API: POST /plans/{plan_id}/approve (JWT Bearer Token)
    Note over API: Verify Role >= OPERATOR<br/>Verify Plan is PENDING_APPROVAL
    API->>Repo: atomically_approve_plan(plan_id, operator_username)
    Repo->>DB: UPDATE status='APPROVED', approved_by=Op, approved_at=NOW()
    Repo->>DB: INSERT InspectionEventModel (type='PLAN_APPROVED')
    Repo-->>API: Approved Plan Object
    API-->>Op: 200 OK (Plan Approved)

    Note over Op,API: Alternative: Rejection Flow
    Op->>API: POST /plans/{plan_id}/reject (rejection_reason)
    Note over API: Validate rejection_reason length >= 3
    API->>Repo: atomically_reject_plan(plan_id, reason)
    Repo->>DB: UPDATE status='REJECTED', rejection_reason=reason
    Repo->>DB: INSERT InspectionEventModel (type='PLAN_REJECTED')
    Repo-->>API: Rejected Plan Object
    API-->>Op: 200 OK (Plan Rejected)
```

**Rejection Validation Rule:** Rejection requires an explicit justification string ($\ge 3$ characters). Empty, null, or whitespace-only rejection reasons return HTTP `422 Unprocessable Content`.

---

### 4. Tamper-Evident Cryptographic Verification (SHA-256)

Upon mission completion or formal abort, the system generates an immutable `InspectionReportModel`. To prevent retrospective tampering or historical falsification:

1. **Payload Serialization:** The report metadata, mission coordinates, sensor observations count, detected anomalies, and outcome are serialized to a canonical JSON string.
2. **SHA-256 Digest Hashing:**
   $$\text{digest} = \text{SHA256}(\text{canonical\_payload\_bytes})$$
3. **Verification Ledger:** The resulting 64-character hexadecimal hash is stored persistently in the `tamper_proof_hash` column.
4. **Integrity Audit:** Any client, auditor, or external supervisor can verify report authenticity via `InspectionIntelligenceRepository.verify_report_integrity(db, report_id)`. If any field has been modified in the database, the hash verification returns `False`.

---

### 5. Known Assumptions and Limitations

1. **Virtual Pipe Network Topology:** Routing assumes conduits form a piecewise continuous graph. Conduits separated by physical gaps greater than $300\text{ m}$ are flagged as disconnected.
2. **Synthetic Telemetry Modeling:** Acoustic and thermal anomaly magnitudes are calibrated against empirical laboratory data from ductile iron test rigs, but do not model localized soil stratification effects.
3. **Rover Battery Decay:** Modeled as linear transit consumption ($2.5\%\text{/km}$) plus sensor operation ($4.0\%\text{/hr}$), ignoring ambient temperature battery chemistry effects.

