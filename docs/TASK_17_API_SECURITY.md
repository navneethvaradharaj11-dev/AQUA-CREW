# AQUA CREW — TASK 17: API SECURITY & MIDDLEWARE HARDENING

## 1. Overview & Security Objectives

AQUA CREW exposes a high-throughput REST API supporting telemetry ingestion, mission dispatches, digital twin simulations, AI queries, and repair operations. Under Task 17, the API layer has been hardened to eliminate denial-of-service risks, information disclosure vulnerabilities, cross-origin tampering, and parameter pollution.

---

## 2. Middleware Pipeline Architecture

The FastAPI middleware stack executes in a deterministic, defense-in-depth sequence:

```
[Inbound HTTP Request]
          │
          ▼
┌─────────────────────────────────┐
│ 1. RequestIDMiddleware          │ ──► Injects/validates UUID4 X-Request-ID
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│ 2. CORSMiddleware               │ ──► Origin allowlist matching (Strict, No '*')
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│ 3. RateLimiterMiddleware        │ ──► Sliding-window IP rate limiter (120 general / 10 auth)
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│ 4. RequestSizeLimitMiddleware   │ ──► 10MB payload size enforcement (HTTP 413)
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│ 5. SecurityHeadersMiddleware    │ ──► CSP, HSTS, X-Frame-Options: DENY, nosniff
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│ Endpoint Business Logic         │ ──► Handlers, DB Queries & Solvers
└─────────────────────────────────┘
```

---

## 3. Middleware Specifications & Implementation Details

### 1. Request Correlation ID Middleware (`RequestIDMiddleware`)
- **Location**: `apps/api/app/middleware/request_id.py`
- **Behavior**:
  - Checks for incoming `X-Request-ID` header.
  - If present and valid (UUID4 format or non-empty string), preserves it; otherwise generates a new `uuid.uuid4()`.
  - Attaches `request_id` to `request.state.request_id`.
  - Injects `X-Request-ID` into every HTTP response header.
  - Injects `request_id` into all structured log entries and error responses.
  - Increments Prometheus counter `aqua_http_requests_total` labeled by method, path, and status code.

### 2. HTTP Security Response Headers Middleware (`SecurityHeadersMiddleware`)
- **Location**: `apps/api/app/middleware/security_headers.py`
- **Compliance**: OWASP ASVS 4.0 Level 3
- **Headers Injected**:
  - `Content-Security-Policy`:
    ```
    default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' ws: wss:; frame-ancestors 'none';
    ```
  - `Strict-Transport-Security`: `max-age=31536000; includeSubDomains; preload`
  - `X-Content-Type-Options`: `nosniff`
  - `X-Frame-Options`: `DENY`
  - `X-XSS-Protection`: `1; mode=block`
  - `Referrer-Policy`: `strict-origin-when-cross-origin`
  - `Permissions-Policy`: `camera=(), microphone=(), geolocation=(), payment=()`

### 3. Request Payload Size Defense (`RequestSizeLimitMiddleware`)
- **Location**: `apps/api/app/middleware/request_size.py`
- **Limit**: Maximum 10 MB (`10 * 1024 * 1024` bytes).
- **Behavior**:
  - Inspects `Content-Length` header on inbound requests.
  - If length exceeds 10MB, halts processing immediately and returns HTTP 413 Payload Too Large without parsing the body.
  - Guards against memory exhaustion and volumetric JSON payload attacks.

### 4. Sliding-Window IP Rate Limiter (`RateLimiterMiddleware`)
- **Location**: `apps/api/app/middleware/rate_limiter.py`
- **Algorithm**: In-memory thread-safe sliding window tracking epoch timestamps.
- **Rules**:
  - **Standard Endpoints**: 120 requests per 60-second sliding window per client IP.
  - **Authentication Endpoints (`/api/v1/auth/login`)**: 10 requests per 60-second sliding window per client IP.
  - **Exemptions**: System liveness/readiness probes (`/health`, `/api/v1/health/*`) and Prometheus metrics exposition (`/metrics`).
  - **Response on Violation**: HTTP 429 Too Many Requests with header `Retry-After: <seconds>` and structured error code `RATE_LIMIT_EXCEEDED`.

---

## 4. Error Sanitization & Safe Error Handling

All unhandled exceptions, database errors, and validation errors are intercepted by centralized exception handlers in `apps/api/app/core/exceptions.py`.

### Uniform Error Response Schema
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Rover ROV-AQUA-99 not found in active fleet.",
    "details": [],
    "request_id": "7f8b9e12-34a5-4678-90ab-cdef12345678"
  },
  "request_id": "7f8b9e12-34a5-4678-90ab-cdef12345678",
  "timestamp": "2026-11-16T19:20:00.000000Z"
}
```

- **Stack Trace Suppression**: Raw Python tracebacks and internal SQL queries are strictly withheld from clients in all environments.
- **Traceability**: The unique `request_id` allows developers and site reliability engineers to immediately locate the corresponding stack trace in application log aggregators.

