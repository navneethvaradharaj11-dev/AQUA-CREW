# AQUA CREW — TASK 17: PLATFORM SECURITY ARCHITECTURE & ZERO-TRUST FRAMEWORK

## 1. Executive Security Architecture Summary

AQUA CREW is a mission-critical autonomous municipal water pipeline leak detection, inspection, and repair-planning platform. As a cyber-physical advisory and virtual simulation platform, maintaining zero-trust architectural integrity is paramount to prevent data exfiltration, unauthorized operational commands, hydraulic simulation tampering, or injection attacks into downstream decision engines.

Task 17 hardens the platform across the complete OSI stack and application surface:
- **Zero-Trust Identity**: Continuous verification of every request; no ambient authority.
- **Strict Role-Based Access Control (RBAC)**: Fine-grained multi-tier authorization (`VIEWER`, `OPERATOR`, `ENGINEER`, `ADMINISTRATOR`).
- **Cryptographic Session & Token Lifecycle**: RFC 7519 HMAC-SHA256 JWT tokens with single-use refresh token rotation and real-time JTI revocation blacklisting.
- **Layered API Defenses**: Strict HTTP response security headers (OWASP ASVS Level 3), sliding-window per-IP rate limiting, 10MB payload size restriction, and ubiquitous `X-Request-ID` correlation tracking.
- **Real-Time WebSocket Hardening**: Connection quotas, IP rate limits, 64KB max frame size enforcement, and authenticated topic-based subscriptions.
- **Physical Actuator Air-Gap Isolation**: Strict software boundary guarantees ensuring virtual rovers and simulated EPANET actuators cannot bridge to real-world industrial control systems (ICS/SCADA) without human engineering sign-off.

---

## 2. Threat Model & Attack Surface Analysis (STRIDE)

| Threat Category | Target Subsystem | Attack Vector | Countermeasure & Hardening Implementation |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Identity & Auth | Credential stuffing, brute-force dictionary attacks, forged JWTs | NIST SP 800-63B password complexity, 5-attempt brute-force lockout with 15-minute freeze, strict cryptographic HMAC-SHA256 signature verification with secret key $\ge 32$ chars. |
| **Tampering** | Hydraulic Twin / Telemetry | Man-in-the-middle request tampering, payload alteration, parameter pollution | Strict Pydantic input validation, Content Security Policy, HSTS (`Strict-Transport-Security: max-age=31536000`), transactional DB rollbacks on exception. |
| **Repudiation** | Operator Actions & Dispatches | Denying dispatch orders, unlogged mission cancellations | Structured security audit logging (`SecurityAuditEventModel`) capturing user ID, IP address, user-agent, timestamp, action, and payload checksum. |
| **Information Disclosure** | API Endpoints & Error Handlers | Stack trace leakage, database error messages, IDOR cross-tenant access | Uniform sanitized error payloads via `AquaCrewException`, object-level ownership checks (`verify_resource_ownership`), generic error codes (`INTERNAL_SERVER_ERROR`). |
| **Denial of Service** | API & WebSocket Gateways | Slowloris attacks, unbounded payload upload, socket exhaustion, rate abuse | 10MB request size limit (`RequestSizeLimitMiddleware`), sliding-window rate limiter (120 req/min general, 10 req/min auth), max 100 WebSocket connections total, max 10 WS per IP, 64KB frame limit. |
| **Elevation of Privilege** | RBAC & Admin Routes | Role spoofing, parameter tampering, horizontal IDOR privilege escalation | Dependency injection authorization guards (`require_viewer`, `require_operator`, `require_engineer`, `require_admin`), token-type verification (`expected_type="access"`), strict token revocation checking on every request. |

---

## 3. Defense-in-Depth Architecture

```mermaid
flowchart TD
    Client[Web Client / Mobile App / CLI] --> Edge[Edge Ingress / Reverse Proxy (NGINX/Caddy)]
    
    subgraph Middlewares ["FastAPI Security Middleware Pipeline"]
        Edge --> MW1["1. RequestIDMiddleware (UUID4 X-Request-ID)"]
        MW1 --> MW2["2. CORSMiddleware (Origin Allowlist, No Wildcards)"]
        MW2 --> MW3["3. RateLimiterMiddleware (Sliding Window: 120/min API, 10/min Auth)"]
        MW3 --> MW4["4. RequestSizeLimitMiddleware (10MB Max Body)"]
        MW4 --> MW5["5. SecurityHeadersMiddleware (CSP, HSTS, X-Frame-Options: DENY, nosniff)"]
    end

    subgraph AuthLayer ["Zero-Trust Identity & Authorization Layer"]
        MW5 --> AuthCheck{"Endpoint Auth Guard"}
        AuthCheck -->|Public Health| HealthEndpoint["/health /liveness /readiness"]
        AuthCheck -->|Protected Route| JWTValidate["Cryptographic JWT HMAC-SHA256 Verification"]
        JWTValidate --> BlacklistCheck{"JTI Blacklisted in DB?"}
        BlacklistCheck -->|Yes| HTTP401["HTTP 401 Token Revoked"]
        BlacklistCheck -->|No| ActiveCheck{"User Active & Unlocked?"}
        ActiveCheck -->|Locked/Inactive| HTTP401b["HTTP 401 User Inactive/Locked"]
        ActiveCheck -->|Active| RBACGuard{"Role >= Required Role?"}
        RBACGuard -->|Insufficient| HTTP403["HTTP 403 Forbidden"]
        RBACGuard -->|Authorized| IDORGuard{"Owns Resource or Admin?"}
        IDORGuard -->|Unauthorized IDOR| HTTP403b["HTTP 403 Access Denied (IDOR)"]
        IDORGuard -->|Authorized| EndpointExec["Endpoint Business Logic Execution"]
    end

    subgraph DataIntegrity ["Database & Engine Layer"]
        EndpointExec --> TxBoundary["Transactional Boundary (Atomic Commit / Rollback)"]
        TxBoundary --> PostGIS[("PostgreSQL 16 + PostGIS / SQLite Dev")]
        EndpointExec --> ActuatorGuard{"Physical Hardware Actuation?"}
        ActuatorGuard -->|Attempted Hardware Control| Block["HARDWARE AIR-GAP EXCEPTION (Simulated Only)"]
        ActuatorGuard -->|Virtual Simulation| SimEngine["Virtual Rover & EPANET Hydraulic Twin"]
    end
```

---

## 4. Zero-Trust Access Control Principles

1. **Explicit Identity Verification**: Every request to a non-public endpoint must present an unexpired, cryptographically signed Bearer token issued by `aqua-crew-auth` with audience `aqua-crew-api`.
2. **Least Privilege Enforcement**: Users operate strictly under their assigned role. A `VIEWER` can inspect maps, rovers, and analytics, but cannot dispatch rovers, pause simulations, or alter repair plans.
3. **Continuous Revocation Validation**: Tokens are checked against `TokenRevocationModel` in real time. Calling `/api/v1/auth/logout` or triggering admin session revocation immediately invalidates all active tokens.
4. **Assume Breach & Blast Radius Containment**: All exceptions are trapped and sanitized; sensitive stack traces are never sent over the wire. Database operations run within transactional context managers ensuring automatic rollbacks on error.
5. **Physical Air-Gap**: The platform operates strictly in an advisory and virtual simulation capacity. Any command simulating valve shutoff, pressure adjustment, or rover propulsion is flagged with `is_simulated=True` and tagged with `VIRTUAL_SIMULATION_BACKEND`. Direct hardware actuation is architecturally prohibited.

---

## 5. Security Architecture Compliance Matrix

| Standard / Framework | Requirement | AQUA CREW Implementation | Status |
| :--- | :--- | :--- | :--- |
| **NIST SP 800-63B** | Memorized Secret Verifiers (Passwords) | PBKDF2-HMAC-SHA256 with 100,000 iterations, 8+ chars, upper, lower, numeric, special char complexity. | **COMPLIANT** |
| **NIST SP 800-63B** | Rate Limiting & Account Lockout | 5 consecutive failed attempts lock account for 15 minutes; rate limiting on auth endpoints (10 req/min). | **COMPLIANT** |
| **RFC 7519 / RFC 7515** | JSON Web Signature (JWS) / JWT | HMAC-SHA256 signing, unpadded URL-safe Base64, verified `iss`, `aud`, `nbf`, `exp`, and `jti` claims. | **COMPLIANT** |
| **OWASP Top 10: A01** | Broken Access Control | Granular RBAC dependencies on every router (`require_viewer`, `require_operator`, `require_engineer`, `require_admin`) and `verify_resource_ownership`. | **COMPLIANT** |
| **OWASP Top 10: A02** | Cryptographic Failures | Strong PBKDF2 hashing, HMAC-SHA256 tokens, HSTS with 1-year max-age and preload, constant-time `hmac.compare_digest`. | **COMPLIANT** |
| **OWASP Top 10: A04** | Insecure Design | Explicit physical actuator air-gap, 6-tier evidence ontology (`MEASURED`, `SIMULATED`, `DERIVED`, `PREDICTED`, `OPERATOR_ENTERED`, `UNKNOWN`). | **COMPLIANT** |
| **OWASP Top 10: A05** | Security Misconfiguration | Production validator (`validate_production_security()`) enforcing non-SQLite DB, secret key $\ge 32$ chars, `REQUIRE_AUTH=True`, no wildcard CORS. | **COMPLIANT** |
| **OWASP Top 10: A09** | Security Logging and Monitoring | Real-time security audit events in DB, structured JSON logging option, standard Prometheus `/metrics` exposition. | **COMPLIANT** |

