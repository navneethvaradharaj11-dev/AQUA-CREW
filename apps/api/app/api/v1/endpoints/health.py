"""
AQUA CREW — Production Health, Liveness & Readiness Probes (Task 17)
Provides container orchestration probe endpoints:
- GET /health (Classic health check)
- GET /health/liveness (Kubernetes liveness probe)
- GET /health/readiness (Kubernetes readiness probe with database ping)
- GET /health/detailed (Deep subsystem diagnostics)
"""
from fastapi import APIRouter, Depends, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
import time
import os

from app.config import settings
from app.database.session import get_db
from app.schemas.health import HealthCheckResponse, ServiceComponentStatus
from app.services.simulation_service import simulation_service
from app.websocket.connection_manager import ws_manager

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="System Health & Version Check",
    description="Returns the operating status, version, and component health for the AQUA CREW platform.",
)
async def get_health(db: Session = Depends(get_db)) -> HealthCheckResponse:
    # Check DB status
    db_status = "operational"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "degraded"

    sim_status = "running" if simulation_service.is_running else "paused"

    return HealthCheckResponse(
        status="healthy" if db_status == "operational" else "degraded",
        version=settings.API_VERSION,
        environment=settings.API_ENV,
        timestamp=datetime.now(timezone.utc),
        services=ServiceComponentStatus(
            database=db_status,
            simulation_engine=sim_status,
            hardware_gateway="standby",
        ),
    )


@router.get(
    "/health/liveness",
    summary="Kubernetes Liveness Probe",
    description="Returns 200 OK if the Python process event loop is responsive.",
)
async def liveness_probe():
    return {
        "status": "ALIVE",
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_simulated": True,
    }


@router.get(
    "/health/readiness",
    summary="Kubernetes Readiness Probe",
    description="Verifies database connectivity and readiness to receive incoming traffic.",
)
async def readiness_probe(db: Session = Depends(get_db)):
    start_time = time.time()
    try:
        db.execute(text("SELECT 1"))
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "status": "READY",
            "database": "CONNECTED",
            "database_latency_ms": latency_ms,
            "simulation_engine": "RUNNING" if simulation_service.is_running else "PAUSED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_simulated": True,
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "NOT_READY",
                "database": "UNAVAILABLE",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


@router.get(
    "/health/detailed",
    summary="Detailed Subsystem Health Diagnostics",
    description="Returns comprehensive operational telemetry for all platform subsystems.",
)
async def detailed_health(db: Session = Depends(get_db)):
    start_time = time.time()
    db_ok = True
    db_err = None
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_ok = False
        db_err = str(e)
    db_latency = round((time.time() - start_time) * 1000, 2)

    return {
        "status": "OPERATIONAL" if db_ok else "DEGRADED",
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "environment": settings.API_ENV,
        "subsystems": {
            "database": {
                "status": "CONNECTED" if db_ok else "ERROR",
                "engine": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql",
                "ping_latency_ms": db_latency,
                "error": db_err,
            },
            "simulation_engine": {
                "status": "RUNNING" if simulation_service.is_running else "PAUSED",
                "tick_interval_ms": settings.SIMULATION_TICK_INTERVAL_MS,
                "virtual_only": True,
            },
            "websocket_telemetry": {
                "active_connections": ws_manager.client_count,
                "max_allowed": ws_manager.max_connections,
                "status": "ONLINE",
            },
            "advanced_ai": {
                "provider": settings.AI_PROVIDER,
                "model": settings.AI_MODEL,
                "status": "AVAILABLE",
            },
            "security": {
                "zero_trust_auth": settings.REQUIRE_AUTH,
                "rate_limiting": settings.RATE_LIMIT_ENABLED,
                "cors_configured": len(settings.CORS_ORIGINS),
            },
        },
        "provenance": "VIRTUAL_SIMULATION_BACKEND",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


