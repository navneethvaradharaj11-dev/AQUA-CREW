"""
Pydantic Schemas for System and Audit Events
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone


class StateTransitionResponse(BaseModel):
    id: str
    rover_id: str
    previous_state: str
    new_state: str
    timestamp: datetime
    reason: str
    triggered_by: str
    is_simulated: bool = True


class AuditEventResponse(BaseModel):
    id: str
    event_type: str
    rover_id: Optional[str] = None
    mission_id: Optional[str] = None
    details: str
    timestamp: datetime
    is_simulated: bool = True


class EventListResponse(BaseModel):
    success: bool = True
    total: int
    events: List[AuditEventResponse]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
