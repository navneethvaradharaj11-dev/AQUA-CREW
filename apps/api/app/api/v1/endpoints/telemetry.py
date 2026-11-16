"""
Telemetry REST Endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone

from app.database.session import get_db
from app.repositories.rover_repository import RoverRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.schemas.rover import RoverResponse, RoverListResponse
from app.schemas.telemetry import (
    TelemetryHistoryResponse,
    TelemetryHistoryItem,
    TelemetryHealthSummary,
)
from app.api.v1.endpoints.rovers import rover_model_to_schema
from app.core.auth import require_viewer
from app.models.user import UserModel

router = APIRouter()


@router.get("/latest", response_model=RoverListResponse, summary="Get latest telemetry snapshot for all rovers")
def get_latest_telemetry(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    rovers = RoverRepository.get_all(db)
    return RoverListResponse(
        success=True,
        total=len(rovers),
        rovers=[rover_model_to_schema(r) for r in rovers],
    )


@router.get("/history", response_model=TelemetryHistoryResponse, summary="Get paginated historical telemetry records")
def get_telemetry_history(
    rover_id: Optional[str] = Query(None, description="Optional rover ID filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    offset = (page - 1) * page_size
    records = TelemetryRepository.get_history(db, rover_id=rover_id, limit=page_size, offset=offset)
    total_count = TelemetryRepository.count(db, rover_id=rover_id)

    return TelemetryHistoryResponse(
        success=True,
        rover_id=rover_id,
        count=total_count,
        page=page,
        page_size=page_size,
        records=[
            TelemetryHistoryItem(
                id=rec.id,
                rover_id=rec.rover_id,
                timestamp=rec.timestamp,
                latitude=rec.latitude,
                longitude=rec.longitude,
                velocity_mps=rec.velocity_mps,
                heading_deg=rec.heading_deg,
                battery_pct=rec.battery_pct,
                motor_temp_c=rec.motor_temp_c,
                internal_temp_c=rec.internal_temp_c,
                signal_rssi_dbm=rec.signal_rssi_dbm,
                acoustic_spl_db=rec.acoustic_spl_db,
                operating_state=rec.operating_state,
                pipe_segment_id=rec.pipe_segment_id,
                is_simulated=rec.is_simulated,
            )
            for rec in records
        ],
    )


@router.get("/health", response_model=TelemetryHealthSummary, summary="Get telemetry health and sensor summary")
def get_telemetry_health(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    rovers = RoverRepository.get_all(db)
    total = len(rovers) or 1
    active = sum(1 for r in rovers if r.operating_state in ["MOVING", "INSPECTING", "RETURNING"])
    avg_battery = sum(r.battery_percentage for r in rovers) / total
    temp_alerts = sum(1 for r in rovers if r.motor_temp_c > 50.0)

    return TelemetryHealthSummary(
        active_rovers=active,
        total_rovers=len(rovers),
        average_battery_pct=round(avg_battery, 1),
        signal_health_pct=98.5,
        temperature_alerts=temp_alerts,
        is_simulated=True,
    )

