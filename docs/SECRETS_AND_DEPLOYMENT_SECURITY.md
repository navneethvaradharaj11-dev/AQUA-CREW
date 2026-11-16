# AQUA CREW — Secrets Management & Production Deployment Security

**Document ID**: `AC-SEC-13-6-08`  
**Classification**: DevOps & Cloud Infrastructure Security Standard  
**Status**: APPROVED & IMPLEMENTED  
**Target Release**: AQUA CREW Core Platform v0.1.0 (Task 13.6 Hardening)

---

## 1. Secrets Management Architecture

AQUA CREW enforces comprehensive secret management and environment hygiene to prevent secret leakage in source repositories, log files, Docker images, and client responses.

### 1.1 Secret Classification & Environment Mapping

| Secret Identifier | Minimum Length | Allowed Environments | Description & Usage |
|---|---|---|---|
| `JWT_SECRET_KEY` | 32 characters | All (Must change in prod) | Symmetric key used to sign HS256 access and refresh tokens. |
| `DATABASE_URL` | N/A | Dev: SQLite; Prod: PostgreSQL | Database connection string with embedded credentials. |
| `OPENAI_API_KEY` | 20 characters | Optional / External | API key for OpenAI provider. Masked in all responses. |
| `NVIDIA_NIM_API_KEY`| 20 characters | Optional / External | API key for NVIDIA NIM inference. Masked in all responses. |

---

## 2. Production Security Validator (`validate_production_security`)

To prevent accidental deployments with insecure development defaults, the platform incorporates an automated startup gate in [`apps/api/app/config.py`](file:///e:/BRIDGE%20ASSIGNMENTS/Aqua%20Crew/apps/api/app/config.py):

```python
def validate_production_security(self) -> None:
    if self.API_ENV.lower() == "production":
        insecure_keys = [
            "aqua-crew-dev-insecure-secret-key-32-chars-min",
            "secret",
            "changeme",
            "default",
            "password",
        ]
        if self.JWT_SECRET_KEY in insecure_keys:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: Production deployment detected with default JWT_SECRET_KEY. "
                "You must provide a high-entropy secret key of at least 32 characters."
            )
        if len(self.JWT_SECRET_KEY) < 32:
            raise RuntimeError(
                f"CRITICAL SECURITY CONFIGURATION ERROR: JWT_SECRET_KEY length ({len(self.JWT_SECRET_KEY)}) "
                "is below the minimum required 32 characters for production."
            )
        if "sqlite" in self.DATABASE_URL.lower():
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: SQLite database is prohibited in production. "
                "Configure a production-grade PostgreSQL or Cloud SQL database."
            )
        if not self.REQUIRE_AUTH:
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: REQUIRE_AUTH must be set to True in production."
            )
```

This check is invoked on application startup (`lifespan` in `apps/api/app/main.py`). If any check fails, the application aborts immediately with an exit code of 1, preventing the service from launching in an insecure state.

---

## 3. Information Leakage Prevention

### 3.1 AI Provider Credential Masking
The endpoint `GET /api/v1/advanced-ai/providers` exposes active LLM provider configurations for system telemetry. To prevent credential harvesting:
- Raw API keys (`sk-...`, `nvapi-...`) are never serialized.
- Status values only indicate `"ACTIVE"`, `"AVAILABLE"`, or `"CONFIGURED"`.

### 3.2 Security Audit Redaction
When auditing token events in `SecurityAuditEventModel`, the raw JWT token string is never logged in plaintext. Only the non-sensitive token ID (`jti`) and token type (`access` or `refresh`) are retained in audit metadata.

### 3.3 Stack Trace Masking in Production
Standard exception handlers catch uncaught server exceptions:
- In `development`, diagnostic error details aid debugging.
- In `production`, internal file paths, module names, line numbers, and tracebacks are stripped, returning a sanitized JSON error payload:
  ```json
  {
    "success": false,
    "error": {
      "code": "INTERNAL_SERVER_ERROR",
      "message": "An internal server error occurred. Please contact the administrator."
    }
  }
  ```

---

## 4. Verification Test Suite

Ten dedicated automated tests in `TestSecretAndEnvironmentSecurity` confirm:
- `test_secret_01`: Default JWT secret is rejected in production.
- `test_secret_02`: Short JWT secret (< 32 chars) is rejected in production.
- `test_secret_03`: SQLite database is prohibited in production.
- `test_secret_04`: Strong production configuration validates successfully.
- `test_secret_05`: Provider telemetry masks raw API keys.
- `test_secret_06`: Error responses do not leak tracebacks or file paths.
- `test_secret_07`: Plaintext JWT tokens are never logged to security audit tables.
- `test_secret_08`: Password hash is never serialized in `/auth/me`.
- `test_secret_09`: Password hash is never serialized in `/auth/users`.
- `test_secret_10`: Deactivated user tokens are rejected with `HTTP 403 Forbidden`.

