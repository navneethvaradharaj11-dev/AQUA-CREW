"""
Centralized Zero-Trust Identity, Authentication & Role-Based Authorization Dependencies
Task 13.6: Zero-Trust Identity, Authorization & Deployment Security Hardening
"""
from typing import Optional, List, Dict, Any, Union
from fastapi import Depends, HTTPException, status, Header, Query, Request, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from app.database.session import get_db
from app.models.user import UserModel
from app.repositories.user_repository import UserRepository
from app.config import settings
from app.core.security import (
    decode_and_verify_token,
    TokenExpiredError,
    TokenInvalidSignatureError,
    TokenAlgorithmNotAllowedError,
    TokenValidationError,
)

logger = logging.getLogger("aqua_crew.auth")

http_bearer_scheme = HTTPBearer(auto_error=False)

# Role hierarchy definition
ROLE_HIERARCHY = {
    "ADMINISTRATOR": ["ADMINISTRATOR", "ENGINEER", "OPERATOR", "VIEWER"],
    "ENGINEER": ["ENGINEER", "OPERATOR", "VIEWER"],
    "OPERATOR": ["OPERATOR", "VIEWER"],
    "VIEWER": ["VIEWER"],
}


def get_current_user(
    request: Request,
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer_scheme),
    x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db),
) -> UserModel:
    """
    Centralized zero-trust authentication dependency.
    Extracts, cryptographically verifies, and binds the request to the verified UserModel.
    Strictly forbids client-asserted identity headers from overriding cryptographic identity.
    """
    token = None
    if bearer_creds and bearer_creds.credentials:
        token = bearer_creds.credentials.strip()
    elif x_auth_token:
        token = x_auth_token.strip()

    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    if not token:
        if x_user_id:
            UserRepository.log_security_event(
                db=db,
                event_type="IDENTITY_SPOOF_ATTEMPT",
                status="BLOCKED",
                ip_address=client_ip,
                user_agent=user_agent,
                details={"claimed_user_id": x_user_id, "reason": "X-User-ID header without valid bearer token"},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Direct identity assertion via X-User-ID header is forbidden. Cryptographic authentication required.",
            )

        is_auth_route = request.url.path.startswith("/api/v1/auth/")
        if settings.REQUIRE_AUTH or is_auth_route:
            UserRepository.log_security_event(
                db=db,
                event_type="UNAUTHORIZED_ACCESS",
                status="BLOCKED",
                ip_address=client_ip,
                user_agent=user_agent,
                details={"path": str(request.url.path), "reason": "Missing authorization token"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: No Bearer token provided.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # In dev mode when REQUIRE_AUTH is False, fall back to default operator
        user = UserRepository.get_by_username(db, "operator")
        if not user:
            UserRepository.seed_defaults(db)
            user = UserRepository.get_by_username(db, "operator")
        return user

    try:
        payload = decode_and_verify_token(token, expected_type="access")
    except TokenExpiredError as e:
        UserRepository.log_security_event(
            db=db,
            event_type="TOKEN_EXPIRED",
            status="BLOCKED",
            ip_address=client_ip,
            user_agent=user_agent,
            details={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token expired: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (TokenInvalidSignatureError, TokenAlgorithmNotAllowedError, TokenValidationError) as e:
        UserRepository.log_security_event(
            db=db,
            event_type="TOKEN_INVALID",
            status="BLOCKED",
            ip_address=client_ip,
            user_agent=user_agent,
            details={"error": str(e)},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Check token revocation (JTI)
    jti = payload.get("jti")
    if jti and UserRepository.is_token_revoked(db, jti):
        UserRepository.log_security_event(
            db=db,
            event_type="TOKEN_REVOKED",
            status="BLOCKED",
            ip_address=client_ip,
            user_agent=user_agent,
            details={"jti": jti},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please authenticate again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    user = UserRepository.get_by_id(db, user_id)
    if not user:
        UserRepository.log_security_event(
            db=db,
            event_type="UNKNOWN_USER_TOKEN",
            status="BLOCKED",
            ip_address=client_ip,
            user_agent=user_agent,
            details={"user_id": user_id},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists in system registry.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        UserRepository.log_security_event(
            db=db,
            event_type="INACTIVE_USER_ACCESS",
            user_id=user.id,
            username=user.username,
            status="BLOCKED",
            ip_address=client_ip,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    # 3. Detect and Reject Conflicting X-User-ID Spoofing Attempts
    if x_user_id and x_user_id.strip() != user.id and user.role != "ADMINISTRATOR":
        UserRepository.log_security_event(
            db=db,
            event_type="IDENTITY_SPOOF_ATTEMPT",
            user_id=user.id,
            username=user.username,
            status="BLOCKED",
            ip_address=client_ip,
            user_agent=user_agent,
            details={"attempted_spoof_id": x_user_id, "actual_user_id": user.id},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Security violation: Client-supplied X-User-ID '{x_user_id}' conflicts with authenticated identity '{user.id}'.",
        )

    return user


def get_current_active_user(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """Verifies user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


def get_current_user_optional(
    request: Request,
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer_scheme),
    x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token"),
    db: Session = Depends(get_db),
) -> Optional[UserModel]:
    """
    Optional authentication dependency.
    Returns authenticated UserModel if valid Bearer token provided, otherwise None.
    Does not raise HTTPException on missing credentials.
    """
    token = None
    if bearer_creds and bearer_creds.credentials:
        token = bearer_creds.credentials.strip()
    elif x_auth_token:
        token = x_auth_token.strip()

    if not token:
        return None

    try:
        payload = decode_and_verify_token(token, expected_type="access")
        jti = payload.get("jti")
        if jti and UserRepository.is_token_revoked(db, jti):
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = UserRepository.get_by_id(db, user_id)
        if not user or not user.is_active:
            return None
        return user
    except Exception:
        return None


def require_roles(allowed_roles: Union[str, List[str]]):
    """
    Role-Based Access Control (RBAC) dependency factory.
    Verifies that the authenticated principal possesses sufficient authorization.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def role_verifier(
        request: Request,
        current_user: UserModel = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> UserModel:
        user_role = current_user.role.upper()
        # Administrators inherit all operational roles
        effective_roles = ROLE_HIERARCHY.get(user_role, [user_role])

        has_permission = any(role in effective_roles for role in allowed_roles)
        if not has_permission:
            client_ip = request.client.host if request.client else "unknown"
            UserRepository.log_security_event(
                db=db,
                event_type="INSUFFICIENT_ROLE",
                user_id=current_user.id,
                username=current_user.username,
                resource_type="ENDPOINT",
                resource_id=str(request.url.path),
                status="BLOCKED",
                ip_address=client_ip,
                details={"required_roles": allowed_roles, "user_role": user_role},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: User role '{user_role}' has insufficient privileges. Required: {allowed_roles}.",
            )

        return current_user

    return role_verifier


# Role Shortcut Dependencies
require_admin = require_roles(["ADMINISTRATOR"])
require_engineer = require_roles(["ENGINEER"])
require_operator = require_roles(["OPERATOR"])
require_viewer = require_roles(["VIEWER"])


def verify_resource_ownership(
    current_user: UserModel,
    resource_owner_id: Optional[str],
    resource_type: str = "RESOURCE",
    allow_roles: Optional[List[str]] = None,
) -> None:
    """
    Enforces object-level authorization (IDOR protection).
    Permits access if:
    1. current_user.id matches resource_owner_id, OR
    2. current_user has role 'ADMINISTRATOR', OR
    3. current_user role is in allow_roles.
    Otherwise raises HTTP 403 Forbidden.
    """
    if not resource_owner_id:
        return
    if current_user.id == resource_owner_id:
        return
    if current_user.role == "ADMINISTRATOR":
        return
    if allow_roles and current_user.role in allow_roles:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Access denied: You do not own this {resource_type} and lack administrative privileges.",
    )


async def authenticate_websocket(
    websocket: WebSocket,
    db: Session,
    token: Optional[str] = None,
) -> UserModel:
    """
    Authenticates incoming WebSocket connection.
    Token can be supplied in query parameter 'token' or subprotocol.
    Rejects unauthorized connections with WebSocket 1008 (Policy Violation).
    """
    query_token = token or websocket.query_params.get("token")
    if not query_token:
        # Check Authorization header if present
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            query_token = auth_header.split(" ", 1)[1]

    if not query_token:
        if settings.REQUIRE_AUTH:
            logger.warning("WebSocket connection rejected: Missing authentication token.")
            await websocket.close(code=1008, reason="Authentication token required")
            raise HTTPException(status_code=401, detail="Authentication token required")
        user = UserRepository.get_by_username(db, "operator")
        return user

    try:
        payload = decode_and_verify_token(query_token, expected_type="access")
        jti = payload.get("jti")
        if jti and UserRepository.is_token_revoked(db, jti):
            await websocket.close(code=1008, reason="Token revoked")
            raise HTTPException(status_code=401, detail="Token revoked")

        user_id = payload.get("sub")
        user = UserRepository.get_by_id(db, user_id)
        if not user or not user.is_active:
            await websocket.close(code=1008, reason="User deactivated or not found")
            raise HTTPException(status_code=403, detail="User deactivated or not found")

        return user
    except Exception as e:
        logger.warning(f"WebSocket connection rejected: Invalid token ({e}).")
        await websocket.close(code=1008, reason=f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication error: {e}")
