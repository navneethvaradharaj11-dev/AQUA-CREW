# AQUA CREW — TASK 19: ZERO-TRUST SECURITY & HARDWARE SAFETY ACCEPTANCE
## RBAC Verification, Air-Gap Validation & Actuation Prohibition Audit

---

### 1. Zero-Trust Access Control (RBAC) Architecture

AQUA CREW enforces Zero-Trust Role-Based Access Control on every API request via JWT claim extraction in `app.core.auth`:

| Role | Permissions | Permitted Actions in Incident Subsystem | Prohibited Actions |
| :--- | :--- | :--- | :--- |
| `VIEWER` | Read-only | List incidents, view incident details, view KPI metrics | Create incidents, approve missions, approve repair plans |
| `OPERATOR` | Operational dispatch | Create incidents, approve rover inspection dispatch, manual transitions | Approve certified municipal repair plans |
| `ENGINEER` | Engineering authority | All operator actions, plus certify repair plans, run simulated resolutions | Physical actuation (system-wide prohibition) |
| `ADMIN` | Full authority | Administrative override, user provisioning, global auditing | Physical actuation (system-wide prohibition) |

---

### 2. Penetration & Adversarial Security Test Results

The following attack vectors were actively evaluated against the incident management endpoints:

| Adversarial Attack Vector | Target Endpoint | Expected Behavior | Observed Result | Test Status |
| :--- | :--- | :--- | :--- | :--- |
| **Privilege Escalation** (Viewer approves dispatch) | `POST /incidents/{id}/approve` | HTTP 403 Forbidden | `HTTP 403 Forbidden` | **PASSED** |
| **Unauthorized Engineering Approval** (Operator certifies plan) | `POST /incidents/{id}/approve` (`REPAIR_PLAN`) | HTTP 403 Forbidden | `HTTP 403 Forbidden` (`not authorized`) | **PASSED** |
| **Physical Actuation Injection** (Valve command in notes) | `POST /incidents/{id}/simulation-resolution` | HTTP 403 Forbidden | `HTTP 403 Forbidden` (`HARDWARE_ACTUATION_PROHIBITED`) | **PASSED** |
| **Empty Rejection Reason** | `POST /incidents/{id}/approve` (`approved: false`) | HTTP 422 Unprocessable | `HTTP 422 Unprocessable Entity` | **PASSED** |
| **Malformed Lifecycle State Transition** | `POST /incidents/{id}/transition` | HTTP 422 Unprocessable | `HTTP 422 Unprocessable Entity` | **PASSED** |
| **IDOR / Resource Tampering** | `GET /incidents/{id}` | Read-only access validated | Data returned without leak of private keys | **PASSED** |

---

### 3. Hardware Boundary Verification

The architectural constants in `apps/api/app/modules/hardware_gateway/__init__.py` were verified:

```python
MODULE_NAME = "hardware_gateway"
IS_IMPLEMENTED = False
HARDWARE_STATUS = "HARDWARE NOT CONNECTED"
HARDWARE_ACTUATORS_DISABLED = True
HARDWARE_ACTUATION_ENABLED = False
```

All commands in `PROHIBITED_ACTUATION_COMMANDS` (`CLOSE_VALVE`, `OPEN_VALVE`, `MODULATE_VALVE`, `START_PUMP`, `STOP_PUMP`, `SET_PUMP_SPEED`, `DISPATCH_PHYSICAL_ROVER`, `DRIVE_MOTOR`, `TRIGGER_PHYSICAL_RELAY`, `OVERRIDE_SCADA_PLC`) remain strictly blocked by code inspection and runtime assertions.

