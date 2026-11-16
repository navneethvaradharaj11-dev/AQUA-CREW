"""
SQLAlchemy Simulation Session Model
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from datetime import datetime, timezone

from app.database.session import Base


class SimulationSessionModel(Base):
    __tablename__ = "simulation_sessions"

    id = Column(String(64), primary_key=True, index=True)
    is_running = Column(Boolean, default=False)
    tick_interval_ms = Column(Integer, default=1000)
    total_ticks = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_tick_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_simulated = Column(Boolean, default=True, nullable=False)

