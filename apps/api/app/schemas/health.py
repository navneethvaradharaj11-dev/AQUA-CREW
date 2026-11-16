"""
Health Check and Service Status Schemas
"""
from typing import Dict
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ServiceComponentStatus(BaseModel):
    database: str = Field(default="unconfigured", description="PostgreSQL/PostGIS connection status")
    simulation_engine: str = Field(default="standby", description="Virtual rover/sensor simulation status")
    hardware_gateway: str = Field(default="standby", description="Physical hardware gateway status")


class HealthCheckResponse(BaseModel):
    status: str = Field(..., description="Overall health: healthy, degraded, unhealthy")
    version: str = Field(..., description="Application semantic version")
    environment: str = Field(..., description="Active runtime environment (development, staging, production)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of the check")
    services: ServiceComponentStatus = Field(default_factory=ServiceComponentStatus)


class HealthEnvelope(BaseModel):
    success: bool = True
    data: HealthCheckResponse
    message: str = "System is operational"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

