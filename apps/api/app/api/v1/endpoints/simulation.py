"""
Simulation Lifecycle REST Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database.session import get_db
from app.repositories.rover_repository import RoverRepository
from app.services.simulation_service import simulation_service
from app.core.auth import require_viewer, require_operator
from app.models.user import UserModel
from app.schemas.simulation import (
    SimulationStatusResponse,
    SimulationActionResponse,
)

router = APIRouter()


@router.get("/status", response_model=SimulationStatusResponse, summary="Get simulation engine status")
def get_simulation_status(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    rovers = RoverRepository.get_all(db)
    active = sum(1 for r in rovers if r.operating_state in ["MOVING", "INSPECTING", "RETURNING"])

    return SimulationStatusResponse(
        is_running=simulation_service.is_running,
        tick_interval_ms=int(simulation_service.tick_interval_s * 1000),
        total_ticks=simulation_service.tick_count,
        active_rovers_count=active,
        total_rovers_count=len(rovers),
        is_simulated=True,
        source="VIRTUAL_SIMULATION_ENGINE",
    )


@router.post("/start", response_model=SimulationActionResponse, summary="Start simulation loop")
def start_simulation(current_user: UserModel = Depends(require_operator)):
    res = simulation_service.start()
    return SimulationActionResponse(
        success=res["success"],
        action="START",
        is_running=res["is_running"],
        message=res["message"],
    )


@router.post("/pause", response_model=SimulationActionResponse, summary="Pause simulation loop")
def pause_simulation(current_user: UserModel = Depends(require_operator)):
    res = simulation_service.pause()
    return SimulationActionResponse(
        success=res["success"],
        action="PAUSE",
        is_running=res["is_running"],
        message=res["message"],
    )


@router.post("/resume", response_model=SimulationActionResponse, summary="Resume simulation loop")
def resume_simulation(current_user: UserModel = Depends(require_operator)):
    res = simulation_service.start()
    return SimulationActionResponse(
        success=res["success"],
        action="RESUME",
        is_running=res["is_running"],
        message=res["message"],
    )


@router.post("/reset", response_model=SimulationActionResponse, summary="Reset simulation states to baseline")
def reset_simulation(current_user: UserModel = Depends(require_operator)):
    res = simulation_service.reset()
    return SimulationActionResponse(
        success=res["success"],
        action="RESET",
        is_running=res["is_running"],
        message=res["message"],
    )

