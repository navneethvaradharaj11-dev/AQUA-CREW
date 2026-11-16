"""
SQLAlchemy Audit & System Event Model
"""
from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime, timezone

from app.database.session import Base


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    rover_id = Column(String(64), nullable=True, index=True)
    mission_id = Column(String(64), nullable=True, index=True)
    details = Column(String(1024), default="")
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    is_simulated = Column(Boolean, default=True, nullable=False)

