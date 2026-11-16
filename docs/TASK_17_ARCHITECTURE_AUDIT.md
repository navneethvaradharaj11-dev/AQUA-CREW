# AQUA CREW — TASK 17 ARCHITECTURE AUDIT
## Comprehensive Platform-Wide Security, Reliability & Production Readiness Audit

---

## 1. Executive Summary

This architecture audit evaluates the entire AQUA CREW platform across all reported development milestones (Tasks 01 through 16). The audit encompasses the Next.js 14 frontend, FastAPI Python backend, SQLAlchemy 2.x ORM layer, Alembic database migrations, JWT authentication and RBAC authorization, WebSocket telemetry streaming, AI intelligence services, GIS spatial pipelines, WNTR/EPANET hydraulic digital twin simulations, autonomous rover orchestration, inspection intelligence, repair management, and deployment configurations.

The primary objective is to identify and catalogue architectural weaknesses, security vulnerabilities, reliability risks, and performance bottlenecks, establishing a prioritized remediation blueprint for Task 17 hardening.

---

## 2. Prioritized Risk Register

| Risk ID | Vulnerability / Weakness | Severity | Likelihood | Impact | Affected Subsystems | Remediation Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SEC-01** | **Unprotected REST Endpoints**: Simulation controls (`/simulation/start`, `/pause`, `/reset`), rover command execution (`/rovers/{id}/commands`), and mission scheduling (`/missions/plan`, `assign`, `start`, `cancel`) lack explicit authentication and role-based authorization guards when invoked. | **CRITICAL** | High | Severe | `api/v1/endpoints/simulation.py`<br>`api/v1/endpoints/rovers.py`<br>`api/v1/endpoints/missions.py` | Bind endpoints to centralized `require_operator` / `require_engineer` dependencies; enforce server-side role validation. |
| **SEC-02** | **Missing Brute-Force & Account Lockout Controls**: The login endpoint (`/auth/login`) permits unlimited consecutive failed authentication attempts without rate limiting, exponential backoff, or temporary account lockout. | **HIGH** | High | High | `api/v1/endpoints/auth.py`<br>`repositories/user_repository.py`<br>`models/user.py` | Add `failed_login_attempts` and `locked_until` fields to `UserModel`; implement 5-attempt threshold with 15-minute lockout and IP sliding window rate limit. |
| **SEC-03** | **Unrestricted WebSocket Handshake & Frame Injection**: Telemetry WebSockets (`/ws`, `/api/v1/ws/telemetry`) permit unauthenticated connections when `REQUIRE_AUTH=False`, do not restrict incoming frame sizes (vulnerable to memory exhaustion), and lack channel-based event authorization. | **HIGH** | Medium | High | `websocket/connection_manager.py`<br>`api/v1/endpoints/ws.py` | Enforce mandatory token handshake; establish 64 KB frame size limits, connection caps (100 total / 10 per IP), idle timeouts (60s), and topic-based authorization. |
| **SEC-04** | **Missing HTTP Security Response Headers**: Neither FastAPI backend nor Next.js frontend emits standard defensive security headers (CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy). | **HIGH** | High | Medium | `apps/api/app/main.py`<br>`apps/web/next.config.mjs` | Implement automated security headers middleware in FastAPI and HTTP security response headers in Next.js. |
| **SEC-05** | **Absence of Request Size Limiting**: Backend accepts unbounded HTTP request bodies, exposing the application to Denial-of-Service (DoS) via memory exhaustion on JSON parsing. | **HIGH** | Medium | High | `apps/api/app/main.py` | Implement request body size middleware enforcing a 10 MB maximum payload limit (`HTTP 413 Payload Too Large`). |
| **SEC-06** | **Global Rate Limiting Absence**: REST API endpoints possess no sliding-window rate limiting, allowing unbounded traffic bursts and automated scraping. | **HIGH** | High | Medium | `apps/api/app/main.py` | Implement in-memory sliding-window rate limiter with per-IP and per-user limits, returning `HTTP 429` with `Retry-After`. |
| **SEC-07** | **Object-Level Authorization Inconsistencies (IDOR)**: While Task 13.6 hardened AI conversations, several operational and inspection entities lack standardized ownership validation, allowing authenticated users with equal roles to mutate cross-user entities. | **HIGH** | Medium | High | `api/v1/endpoints/advanced_ai.py`<br>`api/v1/endpoints/inspection_intelligence.py`<br>`api/v1/endpoints/repair_management.py` | Introduce centralized `verify_resource_ownership()` helper to enforce strict object-level access boundaries. |
| **REL-01** | **Database Concurrency Race Conditions**: Simultaneous requests to assign a rover to a mission can assign the same `IDLE` rover to multiple concurrent missions due to lack of atomic row-level locking or optimistic state checks. | **HIGH** | Medium | Severe | `repositories/rover_repository.py`<br>`services/mission_service.py` | Implement atomic state transition queries (`UPDATE rovers SET operating_state = 'ASSIGNED' WHERE id = :id AND operating_state = 'IDLE'`) with transaction boundaries. |
| **REL-02** | **Unbound Connection Pooling & Missing Transaction Rollback**: SQLite/PostgreSQL engine initialization lacks configured pool limits (`pool_size`, `max_overflow`), and `get_db()` does not rollback uncommitted transactions on exception before connection close. | **MEDIUM** | Medium | High | `database/session.py` | Add explicit pool parameters for production PostgreSQL (`pool_size=20`, `max_overflow=10`, `pool_timeout=30`) and wrap `get_db()` with `except Exception: db.rollback(); raise`. |
| **REL-03** | **Missing Operational Liveness & Readiness Probes**: Backend `/health` endpoint provides static telemetry without probing active database connectivity, simulation engine state, or memory availability. | **MEDIUM** | Low | High | `api/v1/endpoints/health.py` | Deploy Kubernetes/Docker-standard `/health/liveness` and `/health/readiness` probes with live DB ping. |
| **AI-01** | **Indirect Prompt Injection in External AI Context**: While system prompts instruct LLMs to ignore instructions in evidence, dynamic user prompts and untrusted inspection logs could manipulate conversational tone or claim verification if not sanitized. | **MEDIUM** | Medium | Medium | `services/advanced_ai/providers/openai_nim_provider.py`<br>`services/advanced_ai/operational_ai_assistant.py` | Enforce strict input prompt sanitization stripping prompt escape delimiters (`<system>`, `ignore previous`); validate output schema against rigid Pydantic models. |
| **OPS-01** | **Incomplete Production Configuration Blueprint**: `.env.example` lacks Task 13–16 settings (JWT keys, AI provider parameters, RBAC flags), and `.gitignore` does not explicitly exclude `.sqlite3` or `.pem` cryptographic files. | **MEDIUM** | High | Low | `.env.example`<br>`.gitignore`<br>`app/config.py` | Expand `.env.example` with full configuration schema; patch `.gitignore` to prevent secret and database check-ins. |

---

## 3. Detailed Component-by-Component Audit

### 3.1 Next.js 14 Frontend (`apps/web`)
- **Routing & Rendering**: All 17 static routes prerender cleanly under Next.js 14 App Router.
- **Authentication State**: Uses localStorage for token storage. Needs defensive handling for expired JWTs (automatic redirect on HTTP 401).
- **Security Headers**: `next.config.mjs` has no Content Security Policy (CSP), frame options, or XSS filters configured.
- **Dependency Hygiene**: Next.js packages are current, with no critical reported vulnerabilities.

### 3.2 FastAPI Backend Core (`apps/api/app`)
- **Application Lifecycle**: Lifespan context manager starts simulation service and validates production secrets.
- **CORS Configuration**: `CORS_ORIGINS` allows localhost origins in dev, but defaults to wildcard `["*"]` if misconfigured, which is unsafe for production.
- **Exception Handlers**: Centralized handlers catch `AquaCrewException`, `RequestValidationError`, `StarletteHTTPException`, and generic `Exception`. Stack traces are suppressed from client responses, but responses lack standardized `request_id` correlation tracking.
- **Middleware Pipeline**: Currently only contains `CORSMiddleware`. Lacks request size limiting, request tracing, rate limiting, and security header injection.

### 3.3 Zero-Trust Identity & Authentication (`app/core/security.py`, `app/core/auth.py`)
- **Password Hashing**: Implements PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte cryptographically secure salts. Constant-time verification is correctly implemented.
- **JWT Implementation**: Generates RFC 7519 compliant tokens with `iss`, `aud`, `exp`, `nbf`, `sub`, and `jti`. Strictly checks `ALLOWED_ALGORITHMS = ["HS256"]`.
- **Token Revocation**: Validates token JTI against `token_revocations` table. Refresh token rotation is implemented.
- **Gaps**: Missing password complexity validator (minimum 8 chars, uppercase, lowercase, numeric, special characters); missing account lockout after repeated failed attempts.

### 3.4 Role-Based Access Control (`app/core/auth.py`)
- **Role Hierarchy**: `ADMINISTRATOR` $\to$ `ENGINEER` $\to$ `OPERATOR` $\to$ `VIEWER`.
- **Endpoint Protection**: Endpoints in `repair_management.py` and `advanced_ai.py` enforce RBAC dependencies. However, legacy endpoints in `simulation.py`, `rovers.py`, and `missions.py` omit dependencies, allowing unauthenticated mutation.
- **Object-Level Ownership**: Missing generalized object-level authorization dependency (`verify_resource_ownership`).

### 3.5 WebSocket Infrastructure (`app/websocket`, `app/api/v1/endpoints/ws.py`)
- **Connection Management**: `ConnectionManager` maintains active connections set.
- **Broadcasting**: Broadcasts all telemetry globally without channel filtering.
- **Security Gaps**: No frame size limits, no connection rate limits per IP, and no authentication required when `REQUIRE_AUTH=False`.

### 3.6 Database Layer & Data Integrity (`app/database`, `app/models`, `app/repositories`)
- **SQLAlchemy Models**: 20 distinct models across 16 tasks.
- **Session Lifecycle**: `get_db()` yields session, but does not explicitly rollback on unhandled exceptions in the route handler before closing.
- **PostgreSQL Readiness**: Engine initialization lacks pool tuning arguments (`pool_size`, `max_overflow`, `pool_timeout`) for enterprise relational engines.

### 3.7 AI & External Model Integrations (`app/services/advanced_ai`)
- **Provider Architecture**: Supports `DETERMINISTIC`, `NVIDIA_NIM`, and `OPENAI`.
- **Prompt Isolation**: Injects retrieved context inside partitioned `<untrusted_database_evidence>` XML tags.
- **Safety Boundaries**: AI cannot execute physical actuator commands; all plans require human engineering sign-off.
- **Gaps**: Lacks explicit regex sanitization on incoming user chat messages to filter adversarial prompt injection tags.

---

## 4. Remediation Action Plan (Tasks 17.1 – 17.17)

1. **Phase 2**: Harden Authentication & Passwords (lockout, password complexity, bulk revocation).
2. **Phase 3**: Harden RBAC & Object-Level Authorization (patch legacy endpoints, IDOR verification).
3. **Phase 4**: Implement API Security Middlewares (Request ID, Security Headers, Rate Limiting, Request Size Limiter, Structured Errors).
4. **Phase 5**: Secure WebSocket Infrastructure (frame size caps, connection limits, idle timeouts, topic authorization).
5. **Phase 6**: Harden Database Reliability & Concurrency (connection pool tuning, rollback in `get_db()`, atomic rover assignment).
6. **Phase 7**: Secrets & Environment Hardening (`.env.example`, `.gitignore`, enhanced production validator).
7. **Phase 8**: AI Safety & Injection Defenses (prompt sanitization, strict output validation, circuit breakers).
8. **Phase 9**: Fault Tolerance & Reliability (readiness/liveness probes, bounded retries).
9. **Phase 10**: Performance Benchmarking (measure API latency, query performance, digital twin execution).
10. **Phase 11**: Observability & Monitoring (structured JSON logging, Prometheus `/metrics`).
11. **Phase 12**: Backup & Disaster Recovery (backup/restore scripts, RPO/RTO specifications).
12. **Phase 13**: Frontend Security Hardening (Next.js security headers, token expiration handling).
13. **Phase 14**: Deployment Readiness (Dockerfiles, docker-compose, production guide).
14. **Phase 15**: Comprehensive Security Testing (120+ security test suite).
15. **Phase 16**: Full Monorepo Regression (100% test pass rate across Tasks 01–17).
16. **Phase 17**: Complete Engineering Documentation (14 technical documents in `docs/`).

