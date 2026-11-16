"""
User, Token Revocation & Security Audit Event Repository
Task 13.6: Zero-Trust Identity, Authentication & Access Control
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import json
import logging
import uuid

from app.models.user import UserModel, TokenRevocationModel, SecurityAuditEventModel
from app.core.security import hash_password, verify_password, AccountLockedException

logger = logging.getLogger("aqua_crew.auth.repository")


DEFAULT_USERS = [
    {
        "id": "USR-ADMIN-01",
        "username": "admin",
        "email": "admin@aquacrew.internal",
        "full_name": "System Administrator",
        "role": "ADMINISTRATOR",
        "password": "AquaCrewAdmin2026!",
    },
    {
        "id": "USR-ENG-01",
        "username": "engineer",
        "email": "engineer@aquacrew.internal",
        "full_name": "Lead Hydraulic Engineer",
        "role": "ENGINEER",
        "password": "AquaCrewEng2026!",
    },
    {
        "id": "OPERATOR-SUPERVISOR-01",
        "username": "operator",
        "email": "operator@aquacrew.internal",
        "full_name": "Lead Operations Supervisor",
        "role": "OPERATOR",
        "password": "AquaCrewOp2026!",
    },
    {
        "id": "OPERATOR_CHIEF",
        "username": "chief_operator",
        "email": "chief@aquacrew.internal",
        "full_name": "Chief Field Dispatcher",
        "role": "OPERATOR",
        "password": "AquaCrewChief2026!",
    },
    {
        "id": "USR-VIEW-01",
        "username": "viewer",
        "email": "viewer@aquacrew.internal",
        "full_name": "Municipal Network Observer",
        "role": "VIEWER",
        "password": "AquaCrewView2026!",
    },
]


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[UserModel]:
        """Retrieves user by primary ID."""
        return db.query(UserModel).filter(UserModel.id == user_id).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[UserModel]:
        """Retrieves user by username."""
        return db.query(UserModel).filter(UserModel.username == username.lower().strip()).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[UserModel]:
        """Retrieves user by email address."""
        return db.query(UserModel).filter(UserModel.email == email.lower().strip()).first()

    @staticmethod
    def get_by_identifier(db: Session, identifier: str) -> Optional[UserModel]:
        """Retrieves user by username, email, or user ID."""
        cleaned = identifier.strip()
        user = db.query(UserModel).filter(
            (UserModel.username == cleaned.lower()) |
            (UserModel.email == cleaned.lower()) |
            (UserModel.id == cleaned)
        ).first()
        return user

    @staticmethod
    def authenticate(
        db: Session,
        identifier: str,
        plain_password: str,
        max_failed_attempts: int = 5,
        lockout_duration_minutes: int = 15,
    ) -> Optional[UserModel]:
        """
        Authenticates user against hashed password using constant-time verification.
        Enforces brute-force protection with automatic temporary account lockout (Task 17).
        Raises AccountLockedException if account is currently locked out.
        Returns UserModel if valid, None otherwise.
        """
        user = UserRepository.get_by_identifier(db, identifier)
        if not user or not user.is_active:
            return None

        now = datetime.now(timezone.utc)

        # Check account lockout status
        if user.locked_until:
            locked_dt = user.locked_until
            if locked_dt.tzinfo is None:
                locked_dt = locked_dt.replace(tzinfo=timezone.utc)
            if locked_dt > now:
                remaining_sec = int((locked_dt - now).total_seconds())
                raise AccountLockedException(
                    message=f"Account '{user.username}' is temporarily locked due to excessive failed attempts. Please retry in {remaining_sec} seconds.",
                    remaining_seconds=remaining_sec,
                )
            else:
                # Lockout window has elapsed, reset counters
                user.locked_until = None
                user.failed_login_attempts = 0
                db.commit()

        if not verify_password(plain_password, user.hashed_password):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= max_failed_attempts:
                user.locked_until = now + timedelta(minutes=lockout_duration_minutes)
                db.commit()
                remaining_sec = lockout_duration_minutes * 60
                raise AccountLockedException(
                    message=f"Account '{user.username}' locked due to {max_failed_attempts} failed login attempts. Retry in {remaining_sec} seconds.",
                    remaining_seconds=remaining_sec,
                )
            db.commit()
            return None

        # Successful authentication: reset failed attempt counter
        if (user.failed_login_attempts and user.failed_login_attempts > 0) or user.locked_until:
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()

        return user

    @staticmethod
    def is_token_revoked(db: Session, token_id: str, user_id: Optional[str] = None) -> bool:
        """Checks if a JTI has been revoked or if all tokens for the user were invalidated."""
        rev = db.query(TokenRevocationModel).filter(TokenRevocationModel.token_id == token_id).first()
        if rev is not None:
            return True
        if user_id:
            all_rev = db.query(TokenRevocationModel).filter(
                TokenRevocationModel.user_id == user_id,
                TokenRevocationModel.token_type == "all",
            ).first()
            if all_rev is not None:
                return True
        return False

    @staticmethod
    def revoke_all_user_tokens(db: Session, user_id: str, reason: str = "security_session_invalidation") -> int:
        """Invalidates all existing sessions for a user."""
        now = datetime.now(timezone.utc)
        wildcard_rev = TokenRevocationModel(
            token_id=f"REV-ALL-{user_id}-{uuid.uuid4().hex[:8].upper()}",
            user_id=user_id,
            token_type="all",
            revoked_at=now,
            expires_at=now + timedelta(days=7),
            reason=reason,
        )
        db.add(wildcard_rev)
        db.commit()
        return 1

    @staticmethod
    def create_user(
        db: Session,
        user_id: str,
        username: str,
        email: str,
        password: str,
        full_name: str = "",
        role: str = "VIEWER",
        is_active: bool = True,
    ) -> UserModel:
        """Creates and stores a new user with hashed password."""
        hashed = hash_password(password)
        user = UserModel(
            id=user_id,
            username=username.lower().strip(),
            email=email.lower().strip(),
            hashed_password=hashed,
            full_name=full_name,
            role=role.upper(),
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def is_token_revoked(db: Session, token_id: str) -> bool:
        """Checks if a JTI has been revoked."""
        rev = db.query(TokenRevocationModel).filter(TokenRevocationModel.token_id == token_id).first()
        return rev is not None

    @staticmethod
    def revoke_token(
        db: Session,
        token_id: str,
        user_id: str,
        expires_at: datetime,
        token_type: str = "access",
        reason: str = "logout",
    ) -> TokenRevocationModel:
        """Records token revocation in the blacklist database."""
        rev = TokenRevocationModel(
            token_id=token_id,
            user_id=user_id,
            token_type=token_type,
            expires_at=expires_at,
            reason=reason,
        )
        db.add(rev)
        db.commit()
        return rev

    @staticmethod
    def log_security_event(
        db: Session,
        event_type: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "SUCCESS",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> SecurityAuditEventModel:
        """Records a tamper-evident security audit event."""
        details_str = json.dumps(details, default=str) if details else None
        audit = SecurityAuditEventModel(
            user_id=user_id,
            username=username,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=details_str,
        )
        db.add(audit)
        try:
            db.commit()
            db.refresh(audit)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to log security audit event: {e}")
        return audit

    @staticmethod
    def seed_defaults(db: Session) -> None:
        """Seeds standard role accounts if database is empty."""
        for u in DEFAULT_USERS:
            existing = db.query(UserModel).filter(UserModel.id == u["id"]).first()
            if not existing:
                user = UserModel(
                    id=u["id"],
                    username=u["username"],
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    full_name=u["full_name"],
                    role=u["role"],
                    is_active=True,
                )
                db.add(user)
        try:
            db.commit()
            logger.info("Successfully seeded default identity accounts.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error seeding default users: {e}")

