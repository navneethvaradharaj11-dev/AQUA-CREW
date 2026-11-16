"""
Audit & State Event REST Endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database.session import get_db
from app.repositories.event_repository import EventRepository
from app.models.user import UserModel
from app.core.auth import require_viewer
from app.schemas.events import (
    AuditEventResponse,
    EventListResponse,
)

router = APIRouter()


@router.get("", response_model=EventListResponse, summary="List audit events")
def list_events(
    limit: int = Query(50, ge=1, le=200),
    rover_id: Optional[str] = Query(None, description="Filter by Rover ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    events = EventRepository.get_events(db, limit=limit, rover_id=rover_id, event_type=event_type)
    return EventListResponse(
        success=True,
        total=len(events),
        events=[
            AuditEventResponse(
                id=e.id,
                event_type=e.event_type,
                rover_id=e.rover_id,
                mission_id=e.mission_id,
                details=e.details,
                timestamp=e.timestamp,
                is_simulated=e.is_simulated,
            )
            for e in events
        ],
    )


@router.get("/recent", response_model=List[AuditEventResponse], summary="Get recent audit events for timeline")
def get_recent_events(
    limit: int = Query(25, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    events = EventRepository.get_events(db, limit=limit)
    return [
        AuditEventResponse(
            id=e.id,
            event_type=e.event_type,
            rover_id=e.rover_id,
            mission_id=e.mission_id,
            details=e.details,
            timestamp=e.timestamp,
            is_simulated=e.is_simulated,
        )
        for e in events
    ]

