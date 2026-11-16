"""
Cryptographic Security, Password Hashing & RFC 7519 JWT Token Management
Task 13.6: Zero-Trust Identity, Authentication & Access Control
"""
import re
import hmac
import hashlib
import base64
import json
import time
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple

from app.config import settings


# Security Exceptions
class SecurityException(Exception):
    """Base security exception."""
    pass


class TokenValidationError(SecurityException):
    """Token structure or payload claims are invalid."""
    pass


class TokenExpiredError(SecurityException):
    """Token has expired."""
    pass


class TokenInvalidSignatureError(SecurityException):
    """Token cryptographic signature does not match."""
    pass


class TokenAlgorithmNotAllowedError(SecurityException):
    """Algorithm not permitted by zero-trust allowlist."""
    pass


class AccountLockedException(SecurityException):
    """Account has been locked due to repeated failed login attempts."""
    def __init__(self, message: str, remaining_seconds: int = 900):
        super().__init__(message)
        self.remaining_seconds = remaining_seconds


# -----------------------------------------------------------------------------
# Base64 URL-Safe Encoding/Decoding (RFC 7515 / RFC 7519)
# -----------------------------------------------------------------------------
def _b64url_encode(data: bytes) -> str:
    """Encodes bytes to unpadded URL-safe Base64 string."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64url_decode(data_str: str) -> bytes:
    """Decodes unpadded URL-safe Base64 string to bytes."""
    padding = 4 - (len(data_str) % 4)
    if padding != 4:
        data_str += "=" * padding
    return base64.urlsafe_b64decode(data_str.encode("utf-8"))


# -----------------------------------------------------------------------------
# Password Hashing & Verification (PBKDF2-HMAC-SHA256, NIST SP 800-63B)
# -----------------------------------------------------------------------------
PBKDF2_ITERATIONS = 100_000


def validate_password_complexity(password: str) -> None:
    """
    Enforces NIST SP 800-63B password complexity standards:
    - Minimum length: 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - At least one special symbol (!@#$%^&*(),.?":{}|<>-)
    Raises ValueError with explicit description if criteria are not met.
    """
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one numeric digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_]", password):
        raise ValueError("Password must contain at least one special character.")
    return True


def hash_password(password: str, enforce_complexity: bool = False) -> str:
    """
    Hashes password using PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte cryptographically secure salt.
    Format: pbkdf2_sha256$iterations$salt_hex$hash_hex
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    if enforce_complexity:
        validate_password_complexity(password)
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a stored PBKDF2-HMAC-SHA256 hash in constant time.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = bytes.fromhex(parts[3])

        candidate_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(candidate_hash, expected_hash)
    except Exception:
        return False


# -----------------------------------------------------------------------------
# RFC 7519 JSON Web Token (JWT) Management
# -----------------------------------------------------------------------------
ALLOWED_ALGORITHMS = ["HS256"]


class TokenResult(str):
    """
    Hybrid token object that behaves both as a string (the raw JWT)
    and an iterable tuple (token, jti, expires_at) for full caller compatibility.
    """
    def __new__(cls, token: str, jti: str, expires_at: datetime):
        obj = str.__new__(cls, token)
        obj.token = token
        obj.jti = jti
        obj.expires_at = expires_at
        return obj

    def __iter__(self):
        yield str(self)
        yield self.jti
        yield self.expires_at


def create_access_token(
    user_id: str,
    username: str = "",
    email: str = "",
    role: str = "OPERATOR",
    expires_delta: Optional[timedelta] = None,
    custom_claims: Optional[Dict[str, Any]] = None,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
) -> Tuple[str, str, datetime]:
    """
    Creates an RFC 7519 compliant HMAC-SHA256 JWT access token.
    Returns: (token_str, jti, expires_at_datetime)
    """
    now = datetime.now(timezone.utc)
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expires_at = now + delta
    jti = f"JTI-{secrets.token_hex(16).upper()}"

    header = {
        "alg": settings.JWT_ALGORITHM,
        "typ": "JWT",
    }

    payload = {
        "sub": user_id,
        "username": username or user_id,
        "email": email or f"{username or user_id}@aquacrew.internal",
        "role": role,
        "type": "access",
        "token_type": "access",
        "iss": issuer or settings.JWT_ISSUER,
        "aud": audience or settings.JWT_AUDIENCE,
        "jti": jti,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    if custom_claims:
        payload.update(custom_claims)

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64url_encode(signature)

    token = f"{header_b64}.{payload_b64}.{sig_b64}"
    return TokenResult(token, jti, expires_at)


def create_refresh_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
    username: str = "",
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
) -> Tuple[str, str, datetime]:
    """
    Creates an RFC 7519 compliant HMAC-SHA256 JWT refresh token.
    Returns: (token_str, jti, expires_at_datetime)
    """
    now = datetime.now(timezone.utc)
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expires_at = now + delta
    jti = f"REF-JTI-{secrets.token_hex(16).upper()}"

    header = {
        "alg": settings.JWT_ALGORITHM,
        "typ": "JWT",
    }

    payload = {
        "sub": user_id,
        "username": username or user_id,
        "type": "refresh",
        "token_type": "refresh",
        "iss": issuer or settings.JWT_ISSUER,
        "aud": audience or settings.JWT_AUDIENCE,
        "jti": jti,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64url_encode(signature)

    token = f"{header_b64}.{payload_b64}.{sig_b64}"
    return TokenResult(token, jti, expires_at)


def decode_and_verify_token(
    token: str,
    expected_type: str = "access",
    verify_exp: bool = True,
    secret_key: Optional[str] = None,
    expected_issuer: Optional[str] = None,
    expected_audience: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Strictly verifies token signature, algorithm, issuer, audience, and expiration.
    Returns decoded payload claims dict.
    Raises TokenValidationError, TokenExpiredError, TokenInvalidSignatureError, or TokenAlgorithmNotAllowedError.
    """
    if not token or not isinstance(token, str):
        raise TokenValidationError("Token string is empty or invalid.")

    parts = token.split(".")
    if len(parts) != 3:
        raise TokenValidationError(f"Invalid JWT format: expected 3 segments, got {len(parts)}.")

    header_b64, payload_b64, sig_b64 = parts

    # 1. Decode & Verify Header
    try:
        header_bytes = _b64url_decode(header_b64)
        header = json.loads(header_bytes.decode("utf-8"))
    except Exception as e:
        raise TokenValidationError(f"Malformed token header: {e}")

    alg = header.get("alg")
    if alg not in ALLOWED_ALGORITHMS:
        raise TokenAlgorithmNotAllowedError(
            f"Algorithm '{alg}' is not permitted by zero-trust security policy. Permitted: {ALLOWED_ALGORITHMS}"
        )

    # 2. Cryptographic Signature Verification (Constant-Time)
    key = (secret_key or settings.JWT_SECRET_KEY).encode("utf-8")
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(key, signing_input, hashlib.sha256).digest()

    try:
        actual_sig = _b64url_decode(sig_b64)
    except Exception as e:
        raise TokenInvalidSignatureError(f"Malformed signature encoding: {e}")

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise TokenInvalidSignatureError("Token cryptographic signature verification failed.")

    # 3. Decode & Validate Payload Claims
    try:
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        raise TokenValidationError(f"Malformed token payload: {e}")

    now_ts = int(time.time())

    # Expiration check
    exp = payload.get("exp")
    if exp is None:
        raise TokenValidationError("Token missing required 'exp' claim.")
    if verify_exp and exp < now_ts:
        raise TokenExpiredError(f"Token expired at timestamp {exp} (current time: {now_ts}).")

    # Not-before check
    nbf = payload.get("nbf")
    if nbf is not None and nbf > now_ts:
        raise TokenValidationError(f"Token is not active yet (nbf: {nbf}, current: {now_ts}).")

    # Issuer check
    iss = payload.get("iss")
    target_iss = expected_issuer or settings.JWT_ISSUER
    if target_iss and iss != target_iss:
        raise TokenValidationError(f"Token issuer '{iss}' does not match expected issuer '{target_iss}'.")

    # Audience check
    aud = payload.get("aud")
    target_aud = expected_audience or settings.JWT_AUDIENCE
    if target_aud and aud != target_aud:
        raise TokenValidationError(f"Token audience '{aud}' does not match expected audience '{target_aud}'.")

    # Token type check
    token_type = payload.get("token_type")
    if expected_type and token_type != expected_type:
        raise TokenValidationError(f"Invalid token type: expected '{expected_type}', got '{token_type}'.")

    return payload
