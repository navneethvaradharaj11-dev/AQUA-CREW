"""
SQLAlchemy Models for User, Roles, Token Revocation, and Security Audit Logging
Task 13.6: Zero-Trust Identity, Authentication & Access Control
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer
from datetime import datetime, timezone
import uuid

from app.database.session import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    email = Column(String(256), unique=True, index=True, nullable=False)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(128), default="", nullable=False)
    role = Column(String(32), default="VIEWER", nullable=False, index=True)  # VIEWER, OPERATOR, ENGINEER, ADMINISTRATOR
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Brute-force & Lockout Protection (Task 17)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TokenRevocationModel(Base):
    __tablename__ = "token_revocations"

    id = Column(String(64), primary_key=True, default=lambda: f"REV-{uuid.uuid4().hex[:12].upper()}")
    token_id = Column(String(64), unique=True, index=True, nullable=False)  # JTI
    user_id = Column(String(64), nullable=False, index=True)
    token_type = Column(String(32), default="access", nullable=False)  # access or refresh
    revoked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    reason = Column(String(256), default="logout", nullable=False)


class SecurityAuditEventModel(Base):
    __tablename__ = "security_audit_events"

    id = Column(String(64), primary_key=True, default=lambda: f"SEC-AUD-{uuid.uuid4().hex[:12].upper()}")
    user_id = Column(String(64), nullable=True, index=True)
    username = Column(String(64), nullable=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    # Event Types:
    # LOGIN_SUCCESS, LOGIN_FAILURE, TOKEN_EXPIRED, TOKEN_INVALID, UNAUTHORIZED_ACCESS,
    # MISSION_APPROVED, MISSION_REJECTED, ROLE_CHANGED, HARDWARE_COMMAND_BLOCKED, WEBSOCKET_AUTH_FAILED
    resource_type = Column(String(64), nullable=True)
    resource_id = Column(String(128), nullable=True)
    status = Column(String(32), default="SUCCESS", nullable=False)  # SUCCESS, FAILURE, BLOCKED
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(256), nullable=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

