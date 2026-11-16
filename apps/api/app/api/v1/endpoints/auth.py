"""
Authentication, Session Lifecycle & RBAC User Management Endpoints
Task 13.6: Zero-Trust Identity, Authentication & Access Control
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.database.session import get_db
from app.models.user import UserModel, SecurityAuditEventModel
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserProfileResponse,
    UserCreateRequest,
    UserUpdateRequest,
    LogoutResponse,
    SecurityAuditEventSchema,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_and_verify_token,
    TokenExpiredError,
    TokenValidationError,
    AccountLockedException,
    validate_password_complexity,
)
from app.core.auth import (
    get_current_user,
    require_admin,
    require_roles,
    http_bearer_scheme,
)
from app.config import settings

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Authenticate user and issue JWT tokens")
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticates user credentials and issues short-lived access token and refresh token.
    Records login attempts in the security audit log.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    try:
        user = UserRepository.authenticate(db, payload.username_or_email, payload.password)
    except AccountLockedException as e:
        UserRepository.log_security_event(
            db=db,
            event_type="ACCOUNT_LOCKED",
            username=payload.username_or_email,
            status="BLOCKED",
            ip_address=client_ip,
            user_agent=user_agent,
            details={"reason": str(e), "remaining_seconds": e.remaining_seconds},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
            headers={"Retry-After": str(e.remaining_seconds)},
        )

    if not user:
        UserRepository.log_security_event(
            db=db,
            event_type="LOGIN_FAILURE",
            username=payload.username_or_email,
            status="BLOCKED",
            ip_address=client_ip,
            user_agent=user_agent,
            details={"attempted_identifier": payload.username_or_email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials: username/email or password incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue access token & refresh token
    access_token, access_jti, access_exp = create_access_token(
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
    )
    refresh_token, refresh_jti, refresh_exp = create_refresh_token(user_id=user.id)

    UserRepository.log_security_event(
        db=db,
        event_type="LOGIN_SUCCESS",
        user_id=user.id,
        username=user.username,
        status="SUCCESS",
        ip_address=client_ip,
        user_agent=user_agent,
        details={"jti": access_jti, "role": user.role},
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in_seconds=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        user=UserProfileResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Rotate refresh token and issue new access token")
def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Validates refresh token, checks revocation, and rotates both access and refresh tokens.
    """
    client_ip = request.client.host if request.client else "unknown"

    try:
        claims = decode_and_verify_token(payload.refresh_token, expected_type="refresh")
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Refresh token expired. Please log in again.")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid refresh token: {e}")

    jti = claims.get("jti")
    if jti and UserRepository.is_token_revoked(db, jti):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked.")

    user_id = claims.get("sub")
    user = UserRepository.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User account is invalid or deactivated.")

    # Revoke old refresh token (refresh token rotation)
    UserRepository.revoke_token(
        db=db,
        token_id=jti,
        user_id=user.id,
        expires_at=datetime.fromtimestamp(claims["exp"], tz=timezone.utc),
        token_type="refresh",
        reason="rotation",
    )

    # Issue new pair
    access_token, access_jti, _ = create_access_token(
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
    )
    new_refresh_token, _, _ = create_refresh_token(user_id=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in_seconds=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        user=UserProfileResponse.model_validate(user),
    )


@router.post("/logout", response_model=LogoutResponse, summary="Invalidate session and revoke token")
def logout(
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    bearer_creds=Depends(http_bearer_scheme),
    db: Session = Depends(get_db),
):
    """
    Revokes the current JWT access token JTI and logs user out.
    """
    if bearer_creds and bearer_creds.credentials:
        try:
            claims = decode_and_verify_token(bearer_creds.credentials, verify_exp=False)
            jti = claims.get("jti")
            exp = claims.get("exp")
            if jti:
                exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc)
                UserRepository.revoke_token(
                    db=db,
                    token_id=jti,
                    user_id=current_user.id,
                    expires_at=exp_dt,
                    token_type="access",
                    reason="user_logout",
                )
        except Exception:
            pass

    UserRepository.log_security_event(
        db=db,
        event_type="LOGOUT",
        user_id=current_user.id,
        username=current_user.username,
        status="SUCCESS",
        ip_address=request.client.host if request.client else "unknown",
    )

    return LogoutResponse()


@router.get("/me", response_model=UserProfileResponse, summary="Get verified profile of current authenticated user")
def get_current_user_profile(
    current_user: UserModel = Depends(get_current_user),
):
    """
    Returns verified cryptographic identity of the authenticated user.
    """
    return UserProfileResponse.model_validate(current_user)


@router.get("/users", response_model=List[UserProfileResponse], summary="List all users (Admin only)")
def list_users(
    admin_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Lists system accounts. Restricted strictly to administrators.
    """
    users = db.query(UserModel).order_by(UserModel.created_at.desc()).all()
    return [UserProfileResponse.model_validate(u) for u in users]


@router.post("/users", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED, summary="Create a new user (Admin only)")
def create_new_user(
    payload: UserCreateRequest,
    admin_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Registers a new operator, engineer, or administrator account. Restricted to administrators.
    """
    valid_roles = {"VIEWER", "OPERATOR", "ENGINEER", "ADMINISTRATOR"}
    if payload.role.upper() not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role '{payload.role}'. Must be one of {valid_roles}.")

    existing_user = UserRepository.get_by_username(db, payload.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered.")

    existing_email = UserRepository.get_by_email(db, payload.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered.")

    try:
        validate_password_complexity(payload.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Password does not meet complexity requirements: {e}")

    new_id = f"USR-{payload.role[:3].upper()}-{payload.username.upper()[:8]}"
    created = UserRepository.create_user(
        db=db,
        user_id=new_id,
        username=payload.username,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        role=payload.role,
    )
    return UserProfileResponse.model_validate(created)


@router.post("/users/{user_id}/revoke-sessions", summary="Revoke all active sessions for a user (Admin only)")
def revoke_user_sessions(
    user_id: str,
    admin_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Revokes all active JWT tokens for specified user.
    """
    target = UserRepository.get_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")
    UserRepository.revoke_all_user_tokens(db, user_id, reason="admin_session_invalidation")
    return {"success": True, "message": f"All sessions revoked for user '{target.username}'."}


@router.post("/users/{user_id}/unlock", summary="Unlock a locked user account (Admin only)")
def unlock_user_account(
    user_id: str,
    admin_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Clears failed login attempts and resets account lockout.
    """
    target = UserRepository.get_by_id(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")
    target.failed_login_attempts = 0
    target.locked_until = None
    db.commit()
    return {"success": True, "status": "UNLOCKED", "message": f"Account '{target.username}' has been unlocked."}


@router.get("/audit-logs", response_model=List[SecurityAuditEventSchema], summary="List security audit events (Admin only)")
def list_security_audit_logs(
    limit: int = 50,
    admin_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Lists recent security events (failed logins, token anomalies, authorization decisions).
    """
    events = (
        db.query(SecurityAuditEventModel)
        .order_by(SecurityAuditEventModel.created_at.desc())
        .limit(limit)
        .all()
    )
    return [SecurityAuditEventSchema.model_validate(e) for e in events]
