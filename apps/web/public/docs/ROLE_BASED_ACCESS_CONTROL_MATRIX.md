# AQUA CREW — Role-Based Access Control (RBAC) Matrix

**Document ID**: `AC-SEC-13-6-02`  
**Classification**: Security Specifications & Compliance Guide  
**Status**: APPROVED & IMPLEMENTED  
**Target Release**: AQUA CREW Core Platform v0.1.0 (Task 13.6 Hardening)

---

## 1. Role Hierarchy and Principles

AQUA CREW enforces a strict hierarchical Role-Based Access Control (RBAC) model across all HTTP REST endpoints and WebSocket channels:

$$\text{ADMINISTRATOR} \supset \text{ENGINEER} \supset \text{OPERATOR} \supset \text{VIEWER}$$

- **`VIEWER` (Level 1)**: Read-only access to GIS maps, telemetry streams, completed mission logs, hydraulic results, and operational summaries. Cannot mutate system state, trigger recommendations, dispatch rovers, or alter user accounts.
- **`OPERATOR` (Level 2)**: All `VIEWER` privileges, plus the authority to approve or reject mission recommendations, log manual field inspections, trigger rover recalls, and conduct interactive AI consultations.
- **`ENGINEER` (Level 3)**: All `OPERATOR` privileges, plus hydraulic scenario authoring, what-if leak injection in the digital twin, risk weighting model calibration, and physical parameter adjustments.
- **`ADMINISTRATOR` (Level 4)**: All `ENGINEER` privileges, plus user account provisioning, role modification, token revocation, system security audits, and cross-user conversation review/deletion.

> [!CAUTION]
> **Physical Actuator Air-Gap**: Under no circumstances does ANY role—including `ADMINISTRATOR`—possess the ability to actuate real-world valves, motorized pumps, or physical excavation equipment. All actions route through the virtual simulation engine.

---

## 2. Endpoint Authorization Matrix

The following matrix provides the definitive authorization policy enforced across the platform:

| HTTP Method | Route / Resource Path | Minimum Required Role | Description & Authorization Rules |
|---|---|---|---|
| **AUTH & IDENTITY** |
| `POST` | `/api/v1/auth/login` | Public (Unauthenticated) | Issues access & refresh JWTs upon valid credentials |
| `POST` | `/api/v1/auth/refresh` | Valid Refresh Token | Rotates refresh token and issues fresh access token |
| `POST` | `/api/v1/auth/logout` | Authenticated (`VIEWER`+) | Revokes current access and refresh token JTIs |
| `GET` | `/api/v1/auth/me` | Authenticated (`VIEWER`+) | Returns profile of current authenticated user |
| `GET` | `/api/v1/auth/users` | `ADMINISTRATOR` | Lists all registered users (excluding password hashes) |
| `POST` | `/api/v1/auth/users` | `ADMINISTRATOR` | Creates new user account with designated role |
| `GET` | `/api/v1/auth/audit-logs` | `ADMINISTRATOR` | Retrieves system security audit log records |
| **ADVANCED AI & CONVERSATION** |
| `POST` | `/api/v1/advanced-ai/chat` | Authenticated (`VIEWER`+) | Natural-language query; binds conversation to user `sub` |
| `GET` | `/api/v1/advanced-ai/conversations` | Authenticated (`VIEWER`+) | Lists user's own conversations; Admin can inspect all |
| `DELETE` | `/api/v1/advanced-ai/conversations/{id}`| Owner or `ADMINISTRATOR` | Deletes conversation; prevents IDOR across users |
| `GET` | `/api/v1/advanced-ai/health` | Public / `VIEWER`+ | Subsystem health; asserts actuators disabled |
| `GET` | `/api/v1/advanced-ai/providers` | Authenticated (`VIEWER`+) | Provider status; API credentials masked |
| `POST` | `/api/v1/advanced-ai/compare/pipelines`| `OPERATOR`+ | Multi-pipeline tradeoff analysis |
| `GET` | `/api/v1/advanced-ai/summaries/operational`| `VIEWER`+ | High-level situation summaries |
| **MISSION PLANNING & HUMAN DISPATCH** |
| `GET` | `/api/v1/missions` | Authenticated (`VIEWER`+) | Lists current and completed rover missions |
| `GET` | `/api/v1/missions/recommendations` | Authenticated (`VIEWER`+) | Lists pending mission recommendations |
| `POST` | `/api/v1/missions/recommendations/{id}/approve` | `OPERATOR`+ | Approves recommendation; records approver `sub` |
| `POST` | `/api/v1/missions/recommendations/{id}/reject` | `OPERATOR`+ | Rejects recommendation with mandatory reason |
| `POST` | `/api/v1/missions/recommendations/{id}/recalculate`| `OPERATOR`+ | Re-evaluates dispatch trajectory |
| **OPERATIONAL INTELLIGENCE DECISIONS** |
| `GET` | `/api/v1/operational-intelligence/overview`| `VIEWER`+ | Situational dashboard and metric summaries |
| `GET` | `/api/v1/operational-intelligence/recommendations`| `VIEWER`+ | Prioritized maintenance recommendations |
| `POST` | `/api/v1/operational-intelligence/recommendations/{id}/approve`| `OPERATOR`+ | Approves operational recommendation |
| `POST` | `/api/v1/operational-intelligence/recommendations/{id}/reject`| `OPERATOR`+ | Rejects operational recommendation |
| **DIGITAL TWIN & SIMULATION** |
| `GET` | `/api/v1/digital-twin/scenarios` | Authenticated (`VIEWER`+) | Lists simulated hydraulic scenarios |
| `POST` | `/api/v1/digital-twin/scenarios` | `ENGINEER`+ | Authors what-if hydraulic simulation scenario |
| `POST` | `/api/v1/digital-twin/simulate` | `ENGINEER`+ | Executes hydraulic network simulation |
| `POST` | `/api/v1/digital-twin/handoff-rover-dispatch`| `ENGINEER`+ | Generates recommendation for human sign-off |
| **GIS & TELEMETRY** |
| `GET` | `/api/v1/gis/network` | Authenticated (`VIEWER`+) | Network topology GeoJSON |
| `GET` | `/api/v1/rovers` | Authenticated (`VIEWER`+) | Fleet state, battery, and kinematics telemetry |
| `WS` | `/api/v1/ws/telemetry` | Authenticated (`VIEWER`+) | Real-time WebSocket telemetry stream |

---

## 3. Enforcement Implementation

RBAC is enforced declaratively using FastAPI dependency injection in [`apps/api/app/core/auth.py`](file:///e:/BRIDGE%20ASSIGNMENTS/Aqua%20Crew/apps/api/app/core/auth.py):

```python
def require_roles(allowed_roles: List[str]):
    def dependency(user: UserModel = Depends(get_current_user)) -> UserModel:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Insufficient privileges. Role '{user.role}' not permitted."
            )
        return user
    return dependency

require_admin = require_roles(["ADMINISTRATOR"])
require_engineer = require_roles(["ENGINEER", "ADMINISTRATOR"])
require_operator = require_roles(["OPERATOR", "ENGINEER", "ADMINISTRATOR"])
require_viewer = require_roles(["VIEWER", "OPERATOR", "ENGINEER", "ADMINISTRATOR"])
```

Any attempt by a user to access an endpoint beyond their role clearance immediately triggers an HTTP 403 Forbidden response and logs an `UNAUTHORIZED_ROLE_ACCESS` security audit entry.

