"""
Event and State Transition Repository
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.models.state_transition import StateTransitionModel
from app.models.event import AuditEventModel


class EventRepository:
    @staticmethod
    def log_state_transition(
        db: Session,
        rover_id: str,
        previous_state: str,
        new_state: str,
        reason: str,
        triggered_by: str = "OPERATOR"
    ) -> StateTransitionModel:
        record_id = f"TR-{uuid.uuid4().hex[:8].upper()}"
        model = StateTransitionModel(
            id=record_id,
            rover_id=rover_id,
            previous_state=previous_state,
            new_state=new_state,
            timestamp=datetime.now(timezone.utc),
            reason=reason,
            triggered_by=triggered_by,
            is_simulated=True,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def log_audit_event(
        db: Session,
        event_type: str,
        details: str,
        rover_id: Optional[str] = None,
        mission_id: Optional[str] = None
    ) -> AuditEventModel:
        record_id = f"EV-{uuid.uuid4().hex[:8].upper()}"
        model = AuditEventModel(
            id=record_id,
            event_type=event_type,
            details=details,
            rover_id=rover_id,
            mission_id=mission_id,
            timestamp=datetime.now(timezone.utc),
            is_simulated=True,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_events(
        db: Session,
        limit: int = 50,
        rover_id: Optional[str] = None,
        event_type: Optional[str] = None
    ) -> List[AuditEventModel]:
        query = db.query(AuditEventModel)
        if rover_id:
            query = query.filter(AuditEventModel.rover_id == rover_id)
        if event_type:
            query = query.filter(AuditEventModel.event_type == event_type)
        return query.order_by(AuditEventModel.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_transitions(
        db: Session,
        rover_id: Optional[str] = None,
        limit: int = 50
    ) -> List[StateTransitionModel]:
        query = db.query(StateTransitionModel)
        if rover_id:
            query = query.filter(StateTransitionModel.rover_id == rover_id)
        return query.order_by(StateTransitionModel.timestamp.desc()).limit(limit).all()

