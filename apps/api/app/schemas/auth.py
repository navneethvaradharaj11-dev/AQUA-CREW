"""
Pydantic Schemas for Authentication, Tokens, Users, and RBAC
Task 13.6: Zero-Trust Identity, Authentication & Access Control
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="User password")


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserProfileResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid JWT refresh token")


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=128)
    role: str = Field(default="VIEWER", description="Role: VIEWER, OPERATOR, ENGINEER, ADMINISTRATOR")


class UserUpdateRequest(BaseModel):
    email: Optional[str] = Field(None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class LogoutResponse(BaseModel):
    status: str = "logged_out"
    message: str = "Session invalidated and token revoked successfully"


class SecurityAuditEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str]
    username: Optional[str]
    event_type: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    status: str
    created_at: datetime
