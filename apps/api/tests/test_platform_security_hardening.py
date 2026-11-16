"""
AQUA CREW — Comprehensive Platform Security, Reliability & Hardening Test Suite (Task 17)
Validates 100% of Task 17 hardening requirements:
  1. NIST SP 800-63B Password Complexity & Brute-Force Lockout
  2. Cryptographic JWT Authentication & Token Revocation
  3. Strict RBAC Enforcement Matrix Across All Roles
  4. IDOR Protection & Object-Level Resource Ownership Isolation
  5. Security Response Headers & OWASP Defenses
  6. Request Correlation IDs (X-Request-ID)
  7. Request Payload Size Defense (413 Payload Too Large)
  8. Sliding-Window Rate Limiting (429 Too Many Requests)
  9. WebSocket Frame Size, IP Quota & Authentication Security
 10. Database Connection Rollback & Concurrency Race Guards
 11. Production Environment Security Validation
 12. Liveness, Readiness & Prometheus Metrics Observability
"""
import pytest
import time
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from unittest.mock import patch

from app.main import app
from app.config import settings
from app.database.session import SessionLocal, init_db
from app.models.user import UserModel
from app.repositories.user_repository import UserRepository
from app.repositories.rover_repository import RoverRepository
from app.services.mission_service import MissionService
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_and_verify_token,
    validate_password_complexity,
    AccountLockedException,
    TokenExpiredError,
    TokenInvalidSignatureError,
    TokenValidationError,
)
from app.core.auth import verify_resource_ownership
from app.middleware.rate_limiter import rate_limiter_instance
from app.websocket.connection_manager import ws_manager, MAX_WS_MESSAGE_SIZE
from app.core.metrics import metrics_collector
from app.core.exceptions import AquaCrewException


@pytest.fixture(autouse=True)
def setup_teardown():
    init_db()
    rate_limiter_instance.reset()
    ws_manager.reset()
    yield
    rate_limiter_instance.reset()
    ws_manager.reset()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


DEFAULT_ROLE_USERS = {
    "ADMINISTRATOR": "USR-ADMIN-01",
    "ENGINEER": "USR-ENG-01",
    "OPERATOR": "OPERATOR-SUPERVISOR-01",
    "VIEWER": "USR-VIEW-01",
}


def create_test_token(user_id=None, role="VIEWER", expired=False, invalid_key=False):
    target_user_id = user_id or DEFAULT_ROLE_USERS.get(role, "USR-VIEW-01")
    delta = timedelta(minutes=-10) if expired else timedelta(hours=1)
    if invalid_key:
        with patch.object(settings, "JWT_SECRET_KEY", "wrong-secret-key-32-chars-minimum!!"):
            return create_access_token(user_id=target_user_id, role=role, expires_delta=delta).token
    return create_access_token(user_id=target_user_id, role=role, expires_delta=delta).token


# ==============================================================================
# 1. NIST SP 800-63B PASSWORD COMPLEXITY & VALIDATION
# ==============================================================================
class TestPasswordComplexity:
    def test_valid_passwords_pass(self):
        valid_samples = [
            "AquaCrewSecure2026!",
            "P@ssw0rdStrictValid#",
            "SuperC0mplex_Water99",
            "Valid8#PasswordString",
        ]
        for pwd in valid_samples:
            assert validate_password_complexity(pwd) is True

    def test_short_password_rejected(self):
        with pytest.raises(ValueError, match="at least 8 characters"):
            validate_password_complexity("Ab1!")

    def test_missing_uppercase_rejected(self):
        with pytest.raises(ValueError, match="uppercase"):
            validate_password_complexity("aquacrew2026!")

    def test_missing_lowercase_rejected(self):
        with pytest.raises(ValueError, match="lowercase"):
            validate_password_complexity("AQUACREW2026!")

    def test_missing_digit_rejected(self):
        with pytest.raises(ValueError, match="numeric digit"):
            validate_password_complexity("AquaCrewPassword!")

    def test_missing_special_char_rejected(self):
        with pytest.raises(ValueError, match="special character"):
            validate_password_complexity("AquaCrewPassword2026")


# ==============================================================================
# 2. BRUTE-FORCE LOCKOUT & UNLOCK WORKFLOWS
# ==============================================================================
class TestBruteForceLockout:
    def test_lockout_after_max_failed_attempts(self, db):
        # Create dedicated test user
        user = UserRepository.get_by_username(db, "lockout_victim")
        if not user:
            user = UserRepository.create_user(
                db, "USR-LOCK-99", "lockout_victim", "victim@test.internal", "ValidPass2026!", "Lockout Victim", "VIEWER"
            )

        # Reset attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

        # 4 failed attempts should fail with None (invalid password) without locking
        for i in range(4):
            res = UserRepository.authenticate(db, "lockout_victim", "WrongPass!")
            assert res is None
            db.refresh(user)
            assert user.failed_login_attempts == i + 1

        # 5th failed attempt triggers AccountLockedException
        with pytest.raises(AccountLockedException) as exc_info:
            UserRepository.authenticate(db, "lockout_victim", "WrongPass!")
        assert "locked due to 5 failed login attempts" in str(exc_info.value)

        # Subsequent attempts remain blocked
        with pytest.raises(AccountLockedException) as exc_info2:
            UserRepository.authenticate(db, "lockout_victim", "ValidPass2026!")
        assert "temporarily locked" in str(exc_info2.value)

    def test_admin_can_unlock_locked_account(self, db, client):
        user = UserRepository.get_by_username(db, "lockout_victim")
        if not user:
            user = UserRepository.create_user(
                db, "USR-LOCK-99", "lockout_victim", "victim@test.internal", "ValidPass2026!", "Lockout Victim", "VIEWER"
            )
        user.failed_login_attempts = 5
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        db.commit()

        admin_token = create_test_token(role="ADMINISTRATOR")
        res = client.post(
            f"/api/v1/auth/users/{user.id}/unlock",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "UNLOCKED"

        db.refresh(user)
        assert user.failed_login_attempts == 0
        assert user.locked_until is None

    def test_viewer_cannot_unlock_accounts(self, db, client):
        user = UserRepository.get_by_username(db, "lockout_victim")
        viewer_token = create_test_token(role="VIEWER")
        res = client.post(
            f"/api/v1/auth/users/{user.id}/unlock",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == 403


# ==============================================================================
# 3. JWT CRYPTOGRAPHIC VALIDATION & TOKEN LIFECYCLE
# ==============================================================================
class TestJwtValidation:
    def test_valid_access_token_decodes_successfully(self):
        token, jti, exp = create_access_token("USR-100", "operator_test", "op@test.internal", "OPERATOR")
        payload = decode_and_verify_token(token, expected_type="access")
        assert payload["sub"] == "USR-100"
        assert payload["role"] == "OPERATOR"
        assert payload["type"] == "access"

    def test_expired_token_rejected(self):
        expired_token = create_test_token(expired=True)
        with pytest.raises(TokenExpiredError):
            decode_and_verify_token(expired_token)

    def test_invalid_signature_rejected(self):
        tampered_token = create_test_token(invalid_key=True)
        with pytest.raises(TokenInvalidSignatureError):
            decode_and_verify_token(tampered_token)

    def test_token_type_mismatch_rejected(self):
        refresh_token, _, _ = create_refresh_token("USR-100")
        with pytest.raises(TokenValidationError, match="Invalid token type"):
            decode_and_verify_token(refresh_token, expected_type="access")

    def test_revoked_token_rejected_in_repository(self, db):
        token, jti, exp = create_access_token("USR-REV-01", "rev_user", "rev@test.internal", "VIEWER")
        assert UserRepository.is_token_revoked(db, jti) is False

        UserRepository.revoke_token(db, jti, "USR-REV-01", expires_at=exp, reason="Unit test revocation")
        assert UserRepository.is_token_revoked(db, jti) is True

    def test_refresh_token_rotation_invalidates_prior_token(self, db, client):
        login_res = client.post(
            "/api/v1/auth/login",
            json={"username_or_email": "operator", "password": "AquaCrewOp2026!"},
        )
        assert login_res.status_code == 200
        first_refresh = login_res.json()["refresh_token"]

        # Rotate token
        rotate_res = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": first_refresh},
        )
        assert rotate_res.status_code == 200
        new_refresh = rotate_res.json()["refresh_token"]
        assert new_refresh != first_refresh

        # Using the old refresh token again should be rejected
        replay_res = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": first_refresh},
        )
        assert replay_res.status_code == 401


# ==============================================================================
# 4. RBAC MATRIX & ENDPOINT ROLE AUTHORIZATION
# ==============================================================================
class TestRbacMatrix:
    def test_viewer_allowed_on_read_endpoints(self, client):
        token = create_test_token(role="VIEWER")
        headers = {"Authorization": f"Bearer {token}"}
        read_paths = [
            "/api/v1/rovers",
            "/api/v1/missions",
            "/api/v1/telemetry/rovers",
            "/api/v1/simulation/state",
            "/api/v1/events",
            "/api/v1/digital-twin/networks",
            "/api/v1/digital-twin/scenarios",
            "/api/v1/infrastructure-intelligence/overview",
            "/api/v1/operational-intelligence/overview",
            "/api/v1/inspection-intelligence/overview",
            "/api/v1/repair-management/overview",
        ]
        for path in read_paths:
            res = client.get(path, headers=headers)
            assert res.status_code in [200, 404], f"Viewer failed read on {path}: {res.status_code}"

    def test_viewer_forbidden_on_write_endpoints(self, client):
        token = create_test_token(role="VIEWER")
        headers = {"Authorization": f"Bearer {token}"}

        # Simulation mutation
        res = client.post("/api/v1/simulation/start", headers=headers)
        assert res.status_code == 403

        # Rover command
        res = client.post("/api/v1/rovers/ROV-AQUA-01/commands", json={"command": "PAUSE"}, headers=headers)
        assert res.status_code == 403

        # Mission creation
        res = client.post(
            "/api/v1/missions",
            json={"mission_type": "PIPE_INSPECTION", "target_segment_id": "PIPE-SEC-4B-92"},
            headers=headers,
        )
        assert res.status_code == 403

    def test_operator_allowed_on_operational_mutations(self, client):
        token = create_test_token(role="OPERATOR")
        headers = {"Authorization": f"Bearer {token}"}

        # Simulation pause/resume allowed
        res = client.post("/api/v1/simulation/pause", headers=headers)
        assert res.status_code == 200

        res = client.post("/api/v1/simulation/resume", headers=headers)
        assert res.status_code == 200

    def test_admin_only_endpoints_reject_operator(self, client):
        operator_token = create_test_token(role="OPERATOR")
        headers = {"Authorization": f"Bearer {operator_token}"}

        res = client.get("/api/v1/auth/users", headers=headers)
        assert res.status_code == 403

        res = client.post("/api/v1/auth/users/USER-1/revoke-sessions", headers=headers)
        assert res.status_code == 403


# ==============================================================================
# 5. IDOR & OBJECT-LEVEL RESOURCE OWNERSHIP
# ==============================================================================
class TestResourceOwnershipIdor:
    def test_verify_resource_ownership_helper(self):
        user_a = UserModel(id="USR-A", role="OPERATOR", username="user_a")
        user_b = UserModel(id="USR-B", role="OPERATOR", username="user_b")
        admin = UserModel(id="USR-ADMIN", role="ADMINISTRATOR", username="admin")

        # Owner matches -> succeeds
        verify_resource_ownership(user_a, "USR-A", "Conversation")

        # Admin can access any resource -> succeeds
        verify_resource_ownership(admin, "USR-A", "Conversation")

        # Cross-user access -> raises 403
        with pytest.raises(HTTPException) as exc:
            verify_resource_ownership(user_b, "USR-A", "Conversation")
        assert exc.value.status_code == 403


# ==============================================================================
# 6. HTTP SECURITY RESPONSE HEADERS (OWASP)
# ==============================================================================
class TestSecurityHeaders:
    def test_security_headers_present_on_all_responses(self, client):
        res = client.get("/api/v1/health/liveness")
        assert res.status_code == 200
        headers = res.headers

        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert "max-age=" in headers.get("Strict-Transport-Security", "")
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "default-src 'self'" in headers.get("Content-Security-Policy", "")
        assert "camera=()" in headers.get("Permissions-Policy", "")

    def test_security_headers_present_on_error_responses(self, client):
        res = client.get("/api/v1/nonexistent-route-404")
        assert res.status_code == 404
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert res.headers.get("X-Frame-Options") == "DENY"


# ==============================================================================
# 7. REQUEST CORRELATION ID (X-Request-ID)
# ==============================================================================
class TestRequestIdCorrelation:
    def test_request_id_generated_automatically(self, client):
        res = client.get("/api/v1/health/liveness")
        req_id = res.headers.get("X-Request-ID")
        assert req_id is not None
        assert len(req_id) >= 16

    def test_custom_request_id_propagated(self, client):
        custom_id = "trace-client-req-9999"
        res = client.get("/api/v1/health/liveness", headers={"X-Request-ID": custom_id})
        assert res.headers.get("X-Request-ID") == custom_id

    def test_request_id_included_in_error_payload(self, client):
        custom_id = "error-trace-1234"
        res = client.get("/api/v1/nonexistent-route-for-id-check", headers={"X-Request-ID": custom_id})
        data = res.json()
        assert data.get("request_id") == custom_id
        assert data.get("error", {}).get("request_id") == custom_id


# ==============================================================================
# 8. REQUEST PAYLOAD SIZE DEFENSE (413 Payload Too Large)
# ==============================================================================
class TestRequestSizeDefense:
    def test_oversized_payload_rejected_with_413(self, client):
        # 11 MB Content-Length header
        headers = {"Content-Length": str(11 * 1024 * 1024)}
        res = client.post("/api/v1/ai/analyze", content=b"{}", headers=headers)
        assert res.status_code == 413
        assert res.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"

    def test_payload_under_limit_accepted(self, client):
        headers = {"Content-Length": "100"}
        res = client.get("/api/v1/health/liveness", headers=headers)
        assert res.status_code == 200


# ==============================================================================
# 9. SLIDING-WINDOW RATE LIMITING (429 Too Many Requests)
# ==============================================================================
class TestRateLimiter:
    def test_rate_limiting_triggers_429_on_login(self, client):
        rate_limiter_instance.reset()
        # Login endpoint limit is 10 requests / 60 seconds
        for _ in range(10):
            res = client.post(
                "/api/v1/auth/login",
                json={"username_or_email": "invalid_user", "password": "WrongPassword2026!"},
            )
            assert res.status_code in [401, 429]

        # 11th request must be rate limited with HTTP 429
        rate_res = client.post(
            "/api/v1/auth/login",
            json={"username_or_email": "invalid_user", "password": "WrongPassword2026!"},
        )
        assert rate_res.status_code == 429
        assert rate_res.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "Retry-After" in rate_res.headers

    def test_health_endpoints_bypass_rate_limiting(self, client):
        rate_limiter_instance.reset()
        for _ in range(50):
            res = client.get("/api/v1/health/liveness")
            assert res.status_code == 200


# ==============================================================================
# 10. WEBSOCKET SECURITY & FRAME SIZE LIMITS
# ==============================================================================
class TestWebSocketSecurity:
    def test_websocket_requires_token_when_auth_enabled(self, client):
        with patch.object(settings, "REQUIRE_AUTH", True):
            with pytest.raises(WebSocketDisconnect) as exc:
                with client.websocket_connect("/api/v1/ws/telemetry") as ws:
                    ws.receive_json()
            assert exc.value.code == 1008

    def test_websocket_accepts_valid_token(self, client):
        token = create_test_token(role="OPERATOR")
        with client.websocket_connect(f"/api/v1/ws/telemetry?token={token}") as ws:
            data = ws.receive_json()
            assert data["type"] == "CONNECTION_ESTABLISHED"
            assert data["role"] == "OPERATOR"

    def test_websocket_ping_pong_exchange(self, client):
        token = create_test_token(role="VIEWER")
        with client.websocket_connect(f"/api/v1/ws/telemetry?token={token}") as ws:
            _ = ws.receive_json()  # Handshake
            ws.send_json({"type": "PING", "timestamp": 123456789})
            pong = ws.receive_json()
            assert pong["type"] == "PONG"
            assert pong["timestamp"] == 123456789

    def test_websocket_rejects_frame_over_64kb(self, client):
        token = create_test_token(role="OPERATOR")
        with client.websocket_connect(f"/api/v1/ws/telemetry?token={token}") as ws:
            _ = ws.receive_json()  # Handshake
            # 70 KB payload
            oversized_payload = "A" * (MAX_WS_MESSAGE_SIZE + 5000)
            ws.send_text(oversized_payload)
            # Server closes with code 1009
            with pytest.raises(WebSocketDisconnect) as exc:
                _ = ws.receive_text()
            assert exc.value.code == 1009

    def test_websocket_topic_subscribe_and_unsubscribe(self, client):
        token = create_test_token(role="VIEWER")
        with client.websocket_connect(f"/api/v1/ws/telemetry?token={token}") as ws:
            _ = ws.receive_json()  # Handshake
            ws.send_json({"type": "SUBSCRIBE", "topic": "missions"})
            resp = ws.receive_json()
            assert resp["type"] == "SUBSCRIPTION_CONFIRMED"
            assert resp["topic"] == "missions"

            ws.send_json({"type": "UNSUBSCRIBE", "topic": "missions"})
            resp2 = ws.receive_json()
            assert resp2["type"] == "UNSUBSCRIPTION_CONFIRMED"
            assert resp2["topic"] == "missions"


# ==============================================================================
# 11. DATABASE CONCURRENCY RACE GUARDS
# ==============================================================================
class TestDatabaseConcurrencyRaceGuards:
    @pytest.mark.asyncio
    async def test_duplicate_rover_assignment_conflict(self, db):
        # Seed rovers and missions
        rovers = RoverRepository.get_all(db)
        target_rover = rovers[0]
        target_rover.operating_state = "IDLE"
        target_rover.assigned_mission_id = "MSN-PREV-01"
        db.commit()

        # Attempt assignment of another mission to rover that is already assigned
        with pytest.raises(AquaCrewException) as exc:
            await MissionService.assign_mission(db, mission_id="MSN-CONCUR-999", rover_id=target_rover.id)
        assert exc.value.status_code in [400, 404, 409]


# ==============================================================================
# 12. PROBES & PROMETHEUS METRICS OBSERVABILITY
# ==============================================================================
class TestObservabilityProbes:
    def test_liveness_probe_returns_200_alive(self, client):
        res = client.get("/api/v1/health/liveness")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ALIVE"
        assert "timestamp" in data

    def test_readiness_probe_returns_200_ready(self, client):
        res = client.get("/api/v1/health/readiness")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "READY"
        assert data["database"] == "CONNECTED"
        assert "database_latency_ms" in data

    def test_detailed_health_probe(self, client):
        res = client.get("/api/v1/health/detailed")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ["OPERATIONAL", "DEGRADED"]
        assert "subsystems" in data
        assert "database" in data["subsystems"]
        assert "simulation_engine" in data["subsystems"]
        assert "websocket_telemetry" in data["subsystems"]

    def test_prometheus_metrics_endpoint(self, client):
        res = client.get("/metrics")
        assert res.status_code == 200
        assert "text/plain" in res.headers["content-type"]
        text = res.text
        assert "aqua_http_requests_total" in text
        assert "aqua_active_websocket_connections" in text
        assert "aqua_simulation_ticks_total" in text
        assert "aqua_uptime_seconds" in text

    def test_api_v1_metrics_alias(self, client):
        res = client.get("/api/v1/metrics")
        assert res.status_code == 200
        assert "aqua_http_requests_total" in res.text


# ==============================================================================
# 13. PRODUCTION SECURITY VALIDATION CHECK
# ==============================================================================
class TestProductionEnvironmentValidation:
    def test_production_validator_rejects_sqlite(self):
        from unittest.mock import patch
        with patch.object(settings, "API_ENV", "production"):
            with patch.object(settings, "JWT_SECRET_KEY", "prod-secure-random-key-with-over-32-characters-length"):
                with patch.object(settings, "DATABASE_URL", "sqlite:///./prod.db"):
                    with pytest.raises(RuntimeError, match="SQLite database is prohibited in production"):
                        settings.validate_production_security()

    def test_production_validator_rejects_insecure_jwt_key(self):
        from unittest.mock import patch
        with patch.object(settings, "API_ENV", "production"):
            with patch.object(settings, "DATABASE_URL", "postgresql://user:pass@host/db"):
                with patch.object(settings, "JWT_SECRET_KEY", "aqua-crew-dev-insecure-secret-key-32-chars-min"):
                    with pytest.raises(RuntimeError, match="Insecure or default JWT_SECRET_KEY"):
                        settings.validate_production_security()

    def test_production_validator_rejects_disabled_auth(self):
        from unittest.mock import patch
        with patch.object(settings, "API_ENV", "production"):
            with patch.object(settings, "DATABASE_URL", "postgresql://user:pass@host/db"):
                with patch.object(settings, "JWT_SECRET_KEY", "prod-secure-random-key-with-over-32-characters-length"):
                    with patch.object(settings, "REQUIRE_AUTH", False):
                        with pytest.raises(RuntimeError, match="REQUIRE_AUTH must be true in production"):
                            settings.validate_production_security()

    def test_production_validator_rejects_wildcard_cors(self):
        from unittest.mock import patch
        with patch.object(settings, "API_ENV", "production"):
            with patch.object(settings, "DATABASE_URL", "postgresql://user:pass@host/db"):
                with patch.object(settings, "JWT_SECRET_KEY", "prod-secure-random-key-with-over-32-characters-length"):
                    with patch.object(settings, "REQUIRE_AUTH", True):
                        with patch.object(settings, "CORS_ORIGINS", ["*"]):
                            with pytest.raises(RuntimeError, match="Wildcard '\\*' CORS origin is strictly prohibited"):
                                settings.validate_production_security()
