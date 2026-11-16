"""
Standard API Response Envelopes & Health Schemas
"""
from typing import Generic, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime, timezone

T = TypeVar("T")


class ServiceStatus(BaseModel):
    database: str = "unconfigured"
    simulation_engine: str = "standby"
    hardware_gateway: str = "standby"


class HealthStatusResponse(BaseModel):
    status: str = Field(..., description="Service health state: healthy, degraded, or unhealthy")
    version: str = Field(..., description="Semantic version of API service")
    environment: str = Field(..., description="Current runtime environment")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    services: ServiceStatus = Field(default_factory=ServiceStatus)


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorDetail(BaseModel):
    field: Optional[str] = None
    issue: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: List[ErrorDetail] = Field(default_factory=list)


class ApiErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

