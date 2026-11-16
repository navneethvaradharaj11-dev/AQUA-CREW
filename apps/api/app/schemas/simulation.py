"""
Pydantic Schemas for Simulation Controls & Status
"""
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class SimulationStatusResponse(BaseModel):
    is_running: bool
    tick_interval_ms: int
    total_ticks: int
    active_rovers_count: int
    total_rovers_count: int
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SimulationActionResponse(BaseModel):
    success: bool
    action: str
    is_running: bool
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
