"""
SQLAlchemy Rover State Transition Audit Model
"""
from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime, timezone

from app.database.session import Base


class StateTransitionModel(Base):
    __tablename__ = "state_transitions"

    id = Column(String(64), primary_key=True, index=True)
    rover_id = Column(String(64), nullable=False, index=True)
    previous_state = Column(String(32), nullable=False)
    new_state = Column(String(32), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    reason = Column(String(512), nullable=False)
    triggered_by = Column(String(64), default="OPERATOR")
    is_simulated = Column(Boolean, default=True, nullable=False)

