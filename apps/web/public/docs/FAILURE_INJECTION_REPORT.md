# Failure Injection & System Resilience Audit Report
## AQUA CREW — Task 10.6 Deliverable 6

### Executive Summary

To guarantee operational robustness and safety in autonomous robotic water operations, AQUA CREW was subjected to a comprehensive failure injection protocol spanning **14 distinct failure modes**.

All failure scenarios were executed and verified in `apps/api/tests/test_failure_injection.py`. In every case, the platform demonstrated **graceful degradation, explicit error codes, and strict absence of silent fallbacks**.

---

### 1. Failure Modes & Resilience Matrix

| # | Injected Failure Mode | Component Under Test | Injected Condition | Expected Behavior | Observed Result & Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | Missing Benchmark File | `EPANETBenchmarkValidator` | Requested `NON_EXISTENT_NET_999` | Structured failure dict (`status: FAILED`), no crash | **PASSED** (Clear error message) |
| **02** | Invalid INP Network Syntax | Hydraulic INP Parser | Non-existent or malformed INP path | Returns `None` / structured error; prevents crash | **PASSED** (Graceful rejection) |
| **03** | Disconnected Topology | `TodiniGlobalGradientSolver` | Isolated junction with no source path | Raises `ValueError: Disconnected junction nodes` | **PASSED** (Explicit exception) |
| **04** | Unsolvable Hydraulics / No Datum | Global Gradient Algorithm | Network lacking reservoir or tank | Raises `ValueError: System lacks pressure datum` | **PASSED** (No silent false numbers) |
| **05** | Invalid Leak Parameters | Torricelli Efflux Engine | $\Delta P \le 0$ or $A \le 0$ | Returns $0.0\text{ m}^3/\text{s}$ flow; no math domain crash | **PASSED** (Safe boundary clamp) |
| **06** | Database Transaction Failure | SQLAlchemy Session Manager | Simulated crash during rover update | Rolls back transaction; state reverts to original | **PASSED** (Atomicity preserved) |
| **07** | WebSocket Disconnect | `ConnectionManager` | Client socket abruptly disconnected | Disconnect cleans list without zombie connections | **PASSED** (No socket leak) |
| **08** | Corrupted / Bad Telemetry | AI Ingestion Route (`/ai/analyze`) | SPL $-500\text{ dB}$, Pressure $-10\text{ bar}$ | Rejected with 422 or handled cleanly without 500 | **PASSED** (No server crash) |
| **09** | Dispatch Non-Existent Target | Mission Planning Service | `DET-NON-EXISTENT-9999` | Returns HTTP 404 `DETECTION_NOT_FOUND` | **PASSED** (Domain exception) |
| **10** | Rover Fleet Exhaustion | `RoverSelectionService` | All rovers in `MAINTENANCE`/`OFFLINE` | Ranks 0 eligible rovers; flags fleet exhaustion | **PASSED** (Clear warning) |
| **11** | Low Battery Reserve Violation | Rover Battery Constraint Engine | All rover batteries set to $10\%$ ($< 20\%$) | Excludes rovers failing operational reserve ($20\%$) | **PASSED** (Safety gate active) |
| **12** | Non-Existent Recommendation | Approval Endpoint | `REC-DOES-NOT-EXIST` | Returns HTTP 404 `RECOMMENDATION_NOT_FOUND` | **PASSED** (State guard) |
| **13** | Duplicate Approval / Rejection | Recommendation State Machine | Rejecting an already `REJECTED` rec | Returns HTTP 400 `INVALID_RECOMMENDATION_STATE` | **PASSED** (State machine sealed) |
| **14** | Invalid Scenario Execution | Scenario Runner Endpoint | `SCEN-TOTALLY-INVALID` | Returns HTTP 404 `Simulation scenario not found` | **PASSED** (REST clean 404) |

---

### 2. Key Reliability Guardrails Verified

#### 2.1 Absence of Silent Solver Fallback (Architectural Rule 11)
A critical flaw in legacy systems is attempting a secondary solver when the primary solver fails without alerting operators. In AQUA CREW:
- If `wntr.sim.EpanetSimulator` or `WNTRSimulator` fails, the system throws an explicit `RuntimeError` or `HTTPException`.
- The `TodiniGlobalGradientSolver` is marked `EXPERIMENTAL` and is never silently swapped in place of the primary engine.

#### 2.2 Database Transaction Rollback & Data Provenance
When transactions encounter simulated faults midway:
- The SQLAlchemy session manager automatically issues `db.rollback()`.
- Rover operating state, battery reserve, and assigned mission IDs are restored to their pre-transaction values.
- All simulated telemetry and scenario results persist mandatory provenance flags:
  ```json
  {
    "is_simulated": true,
    "source": "VIRTUAL_SIMULATION_ENGINE"
  }
  ```

#### 2.3 Rover Fleet Safety Constraints
The mission planner enforces non-negotiable physical constraints:
- Minimum operational battery reserve: $20.0\%$.
- A rover with $10\%$ battery is disqualified even if it is physically closest to the leak site.
- Ineligible rovers carry clear reason codes (`INSUFFICIENT_BATTERY`, `MAINTENANCE_REQUIRED`).

