# AQUA CREW — TASK 13.6: SECURITY BASELINE & ARCHITECTURE AUDIT
**Document ID**: `AQUA-DOC-T13.6-001`  
**Milestone**: TASK 13.6 — Zero-Trust Identity, Authorization & Deployment Security Hardening  
**Target Subsystems**: `apps/api/app/`, `apps/web/src/`, Database Schemas, API Endpoints, WebSocket Streams  
**Audit Classification**: Baseline Security Posture & Vulnerability Register  
**Status**: Completed Baseline Assessment  

---

## 1. Executive Summary

A comprehensive, zero-trust security audit was conducted on the AQUA CREW platform following the completion of Task 13.5. While Task 13.5 successfully hardened AI prompt injection defense, non-fabrication grounding, and empirical model disclosures, the underlying identity and access architecture relied on **client-controlled identity headers (`X-User-ID`)** and unauthenticated REST/WebSocket endpoints.

In enterprise water infrastructure and autonomous robotics, trusting client-asserted headers or unverified request bodies constitutes a critical vulnerability. Any unauthenticated network client can impersonate an operational supervisor, approve rover dispatches, access confidential grid topology, or spoof audit records.

This document establishes the authoritative security baseline, catalogues all confirmed vulnerabilities, maps the current trust boundaries, and defines the remediation requirements for Task 13.6.

---

## 2. Current Architecture & Identity Surface Inventory

### 2.1 Backend Identity & Authorization State (`apps/api/`)
A complete recursive search across `apps/api/app/` revealed the following identity handling characteristics:

| Component / File | Current Mechanism | Finding / Vulnerability |
| :--- | :--- | :--- |
| **`api/v1/endpoints/advanced_ai.py`** | `X-User-ID: Optional[str] = Header(None)` | **Insecure**: Relies on client-supplied header; defaults to `"OPERATOR-SUPERVISOR-01"`. Any client can forge headers to impersonate any user. |
| **`services/advanced_ai/operational_ai_assistant.py`** | `user_id = request.user_id or "OPERATOR-SUPERVISOR-01"` | **Insecure**: Checks `conversation.user_id != user_id`, but `user_id` is derived directly from the unverified request. |
| **`api/v1/endpoints/missions.py`** | `op_id = body.operator_id if body else "OPERATOR_CHIEF"` | **Critical**: Mission approval endpoint (`POST /missions/recommendations/{id}/approve`) accepts arbitrary unverified `operator_id` in JSON body. |
| **`api/v1/endpoints/operational_intelligence.py`** | `operator_id = payload.operator_id or "OPERATOR-SUPERVISOR-01"` | **Critical**: Operational recommendation approvals accept arbitrary unverified `operator_id` without authentication. |
| **`api/v1/endpoints/ws.py`** | Anonymous WebSocket connection | **Insecure**: `/api/v1/ws/telemetry` allows unauthenticated clients to connect and stream live network telemetry. |
| **`database/` & `models/`** | No `UserModel`, `RoleModel`, or `TokenModel` | **Missing Core Infrastructure**: The database contains no user credentials, hashed passwords, or role-based access control tables. |
| **`config.py`** | No JWT signing secret, token expiry, or auth configs | **Missing Configuration**: Application configuration lacks JWT signing keys (`JWT_SECRET_KEY`), algorithm specifications, and token lifetimes. |
| **`modules/hardware_gateway/`** | `IS_IMPLEMENTED = False` | **Verified Software-Only**: Module 12 hardware communication gateway is unconfigured; physical hardware is disconnected. |

### 2.2 Frontend Identity Handling (`apps/web/`)
- **`src/services/api/backendApiClient.ts`**: Hardcodes `user_id: "OPERATOR-SUPERVISOR-01"` in AI queries and passes `"X-User-ID": userId` in HTTP requests.
- **`src/components/ai-assistant/AiAssistantView.tsx`**: Hardcodes `user_id: "OPERATOR-SUPERVISOR-01"`.
- **Authentication State**: Zero frontend authentication state, login forms, token storage, or session management exist. The application assumes all users are authenticated as `"OPERATOR-SUPERVISOR-01"`.

---

## 3. Confirmed Vulnerability Register

### VULN-01: Client-Controlled Identity Header Spoofing (`X-User-ID`)
- **Severity**: **HIGH (CVSS 8.5)**
- **Vector**: Network / HTTP Request Header
- **Description**: The advanced AI endpoints use `X-User-ID` to determine conversation ownership and audit attribution. Because this header is set by the client and never cryptographically validated against an authenticated session, an attacker can supply `X-User-ID: ADMIN` or `X-User-ID: USER-A` to access, append to, or delete any user's conversation sessions.
- **Impact**: Cross-user data compromise, unauthorized conversation tampering, audit record falsification.

### VULN-02: Unauthenticated Mission Approval & Kinetic Dispatch Gate
- **Severity**: **CRITICAL (CVSS 9.1)**
- **Vector**: Network / HTTP POST
- **Description**: The mission approval endpoints (`/api/v1/missions/recommendations/{id}/approve` and `/api/v1/operational-intelligence/recommendations/{id}/approve`) execute virtual rover mission dispatches without requiring authentication. Any network client can issue approval requests, supplying arbitrary strings for `operator_id` (e.g. `"OPERATOR_CHIEF"`).
- **Impact**: Unauthorized rover mission dispatches, unreviewed operational decisions, circumvention of human-in-the-loop safety protocols.

### VULN-03: Complete Absence of Centralized Authentication & RBAC
- **Severity**: **CRITICAL (CVSS 9.3)**
- **Vector**: Architecture-wide
- **Description**: The platform contains no user directory, authentication provider, password hashing, or token verification dependency (`get_current_user`). All endpoints (digital twin simulations, pipeline GIS data, incident reports, rover telemetry) are accessible to anonymous requests.
- **Impact**: Zero access control; any network user has unrestricted access to municipal water distribution data.

### VULN-04: Unauthenticated Telemetry WebSocket Streaming
- **Severity**: **MEDIUM (CVSS 6.5)**
- **Vector**: WebSocket Connection
- **Description**: `/api/v1/ws/telemetry` accepts incoming WebSocket connections without token, ticket, or cookie verification.
- **Impact**: Unauthorized eavesdropping on real-time acoustic leak detections and rover positions.

### VULN-05: Insecure Direct Object Reference (IDOR) Potential
- **Severity**: **HIGH (CVSS 7.5)**
- **Vector**: REST Path Parameters
- **Description**: Without verified user identities and tenant/organization scopes, sequential and UUID resource paths can be enumerated or accessed across user boundaries.
- **Impact**: Unauthorized visibility into operational recommendations, mission plans, and diagnostic logs.

---

## 4. Hardware Isolation & Boundary Analysis

Inspection of `apps/api/app/modules/hardware_gateway/` and simulation services verified that:
1. `MODULE_NAME = "hardware_gateway"`, `IS_IMPLEMENTED = False`.
2. No MQTT broker connections, ROS 2 nodes, or serial hardware drivers are initialized on application startup.
3. Health checks expose `hardware_actuators_disabled: true` and `hardware_gateway="standby"`.
4. Digital twin solvers run purely in virtual simulation mode (`is_simulated = True`).

> [!NOTE]
> **Hardware Status**: `HARDWARE NOT CONNECTED`. Physical actuators are completely isolated because hardware gateway modules are currently uninstantiated in the codebase.

---

## 5. Security Architecture Target for Task 13.6

To transform AQUA CREW into a hardened zero-trust platform, Task 13.6 will implement:
1. **Cryptographically Verified Identity**: Centralized FastAPI dependency `get_current_user` enforcing RFC 7519 HMAC-SHA256 (HS256) JWT verification, expiration checks, algorithm allowlisting, and signature integrity.
2. **Elimination of Header Trust**: Complete removal of `X-User-ID` as an authorization mechanism. All principal identities are derived exclusively from verified JWT bearer tokens or secure session tickets.
3. **Role-Based Access Control (RBAC)**: Enforced authorization matrix across four roles:
   - `VIEWER`: Read-only access to dashboards, GIS maps, and telemetry.
   - `OPERATOR`: Acknowledge alerts, view incidents, submit dispatch requests.
   - `ENGINEER`: Run hydraulic digital twin scenarios, evaluate maintenance models, view sensor calibrations.
   - `ADMINISTRATOR`: Manage users, update system settings, inspect audit trails.
4. **Mandatory Human Approval for Kinetic Missions**: Approver identity is derived strictly from the authenticated JWT token and recorded immutably.
5. **WebSocket Authentication**: WebSockets require verified token authentication before connection acceptance.
6. **Defense in Depth**: Zero hardcoded secrets, startup secret validation, constant-time comparisons (`hmac.compare_digest`), and safe error responses.

