"""
Rover Fleet REST Endpoints
"""
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone

from app.database.session import get_db
from app.models.rover import RoverModel
from app.services.rover_service import RoverService
from app.repositories.event_repository import EventRepository
from app.schemas.rover import (
    RoverResponse,
    RoverListResponse,
    RoverCommandRequest,
    RoverCommandResponse,
    RoverLocation,
    RoverKinematics,
    RoverDiagnostics,
    RoverPayloadSensors,
)
from app.schemas.events import StateTransitionResponse
from app.core.exceptions import AquaCrewException
from app.core.auth import require_viewer, require_operator
from app.models.user import UserModel

router = APIRouter()


def rover_model_to_schema(rover: RoverModel) -> RoverResponse:
    return RoverResponse(
        isSimulated=rover.is_simulated,
        source="VIRTUAL_SIMULATION_ENGINE",
        simulatedAt=rover.last_heartbeat or datetime.now(timezone.utc),
        id=rover.id,
        name=rover.name,
        model=rover.model,
        status=rover.status,
        operatingState=rover.operating_state,
        connectionStatus=rover.connection_status,
        batteryPercentage=rover.battery_percentage,
        distanceTravelledKm=rover.distance_travelled_km,
        currentMission=rover.current_mission,
        assignedMissionId=rover.assigned_mission_id,
        currentLocation=RoverLocation(
            stationName=rover.station_name,
            pipeSegmentId=rover.pipe_segment_id,
            latitude=rover.latitude,
            longitude=rover.longitude,
            routeProgressPct=rover.route_progress_pct,
        ),
        lastCommunication="1s ago",
        lastHeartbeatTimestamp=rover.last_heartbeat or datetime.now(timezone.utc),
        kinematics=RoverKinematics(
            velocityMps=rover.velocity_mps,
            headingDeg=rover.heading_deg,
            targetSpeedMps=rover.target_speed_mps,
        ),
        diagnostics=RoverDiagnostics(
            internalTempC=rover.internal_temp_c,
            motorTempC=rover.motor_temp_c,
            motorCurrentAmps=rover.motor_current_amps,
            signalRssiDbm=rover.signal_rssi_dbm,
        ),
        payloadSensors=RoverPayloadSensors(
            acousticSplDb=rover.acoustic_spl_db,
            dominantFreqHz=rover.dominant_freq_hz,
            groundMoisturePct=rover.ground_moisture_pct,
        ),
    )


@router.get("", response_model=RoverListResponse, summary="List all rovers")
def list_rovers(
    status: Optional[str] = Query(None, description="Filter by operational status: ONLINE, ACTIVE, IDLE, WARNING, OFFLINE"),
    operating_state: Optional[str] = Query(None, description="Filter by state machine: IDLE, MOVING, INSPECTING, etc."),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    rovers = RoverService.get_all_rovers(db, status=status, operating_state=operating_state)
    return RoverListResponse(
        success=True,
        total=len(rovers),
        rovers=[rover_model_to_schema(r) for r in rovers],
    )


@router.get("/{rover_id}", response_model=RoverResponse, summary="Get rover details by ID")
def get_rover(
    rover_id: str = Path(..., description="Rover ID (e.g. ROV-AQUA-01)"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    rover = RoverService.get_rover_by_id(db, rover_id)
    if not rover:
        raise AquaCrewException(status_code=404, code="ROVER_NOT_FOUND", message=f"Rover {rover_id} not found.")
    return rover_model_to_schema(rover)


@router.post("/{rover_id}/commands", response_model=RoverCommandResponse, summary="Dispatch autonomous command to rover")
async def execute_command(
    rover_id: str = Path(..., description="Rover ID"),
    command_in: RoverCommandRequest = ...,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    result = await RoverService.execute_command(
        db=db,
        rover_id=rover_id,
        command=command_in.command,
        target_state=command_in.target_state,
        reason=command_in.reason,
        triggered_by=current_user.username or command_in.triggered_by,
    )
    return RoverCommandResponse(**result)


@router.get("/{rover_id}/telemetry", response_model=RoverResponse, summary="Get latest telemetry snapshot")
def get_rover_telemetry(
    rover_id: str = Path(..., description="Rover ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    rover = RoverService.get_rover_by_id(db, rover_id)
    if not rover:
        raise AquaCrewException(status_code=404, code="ROVER_NOT_FOUND", message=f"Rover {rover_id} not found.")
    return rover_model_to_schema(rover)


@router.get("/{rover_id}/events", response_model=List[StateTransitionResponse], summary="Get rover transition history")
def get_rover_events(
    rover_id: str = Path(..., description="Rover ID"),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    transitions = EventRepository.get_transitions(db, rover_id=rover_id, limit=limit)
    return [
        StateTransitionResponse(
            id=t.id,
            rover_id=t.rover_id,
            previous_state=t.previous_state,
            new_state=t.new_state,
            timestamp=t.timestamp,
            reason=t.reason,
            triggered_by=t.triggered_by,
            is_simulated=t.is_simulated,
        )
        for t in transitions
    ]

