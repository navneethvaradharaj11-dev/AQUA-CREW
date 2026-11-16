"""
Rover Domain Service
Enforces strict autonomous state machine transitions, command dispatches, and safety rules.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.models.rover import RoverModel
from app.repositories.rover_repository import RoverRepository
from app.repositories.event_repository import EventRepository
from app.websocket.connection_manager import ws_manager
from app.core.exceptions import AquaCrewException

# State Transition Rules matching Task 05
VALID_ROVER_TRANSITIONS: Dict[str, List[str]] = {
    "IDLE": ["MOVING", "INSPECTING", "CHARGING", "OFFLINE", "ERROR", "EMERGENCY_STOP"],
    "MOVING": ["INSPECTING", "PAUSED", "RETURNING", "IDLE", "ERROR", "EMERGENCY_STOP", "OFFLINE"],
    "INSPECTING": ["PAUSED", "MOVING", "RETURNING", "IDLE", "ERROR", "EMERGENCY_STOP", "OFFLINE"],
    "PAUSED": ["MOVING", "INSPECTING", "RETURNING", "IDLE", "EMERGENCY_STOP", "OFFLINE", "ERROR"],
    "RETURNING": ["CHARGING", "IDLE", "PAUSED", "EMERGENCY_STOP", "OFFLINE", "ERROR"],
    "CHARGING": ["IDLE", "OFFLINE", "ERROR", "EMERGENCY_STOP"],
    "OFFLINE": ["IDLE", "CHARGING"],
    "ERROR": ["IDLE", "RETURNING", "OFFLINE", "EMERGENCY_STOP"],
    "EMERGENCY_STOP": ["IDLE", "ERROR", "OFFLINE"], # Requires explicit reset
}


def map_operating_state_to_status(state: str) -> str:
    if state in ["MOVING", "INSPECTING", "RETURNING"]:
        return "ACTIVE"
    elif state in ["IDLE", "CHARGING"]:
        return "ONLINE"
    elif state == "PAUSED":
        return "IDLE"
    elif state in ["ERROR", "EMERGENCY_STOP"]:
        return "WARNING"
    elif state == "OFFLINE":
        return "OFFLINE"
    return "ONLINE"


def is_valid_transition(current_state: str, target_state: str) -> bool:
    if current_state == target_state:
        return True
    allowed = VALID_ROVER_TRANSITIONS.get(current_state, [])
    return target_state in allowed


class RoverService:
    @staticmethod
    def get_all_rovers(db: Session, status: Optional[str] = None, operating_state: Optional[str] = None) -> List[RoverModel]:
        return RoverRepository.get_all(db, status=status, operating_state=operating_state)

    @staticmethod
    def get_rover_by_id(db: Session, rover_id: str) -> Optional[RoverModel]:
        return RoverRepository.get_by_id(db, rover_id)

    @staticmethod
    async def execute_command(
        db: Session,
        rover_id: str,
        command: str,
        target_state: Optional[str] = None,
        reason: str = "Operator command",
        triggered_by: str = "OPERATOR"
    ) -> Dict[str, Any]:
        rover = RoverRepository.get_by_id(db, rover_id)
        if not rover:
            raise AquaCrewException(status_code=404, code="ROVER_NOT_FOUND", message=f"Rover {rover_id} was not found.")

        current_state = rover.operating_state
        desired_state = current_state

        cmd_upper = command.upper()
        if cmd_upper == "PAUSE":
            desired_state = "PAUSED"
        elif cmd_upper == "RESUME":
            desired_state = "INSPECTING" if rover.assigned_mission_id else "MOVING"
        elif cmd_upper == "RETURN_BASE":
            desired_state = "RETURNING"
        elif cmd_upper == "EMERGENCY_STOP":
            desired_state = "EMERGENCY_STOP"
            triggered_by = "SAFETY_INTERLOCK"
        elif cmd_upper == "RESET_ESTOP":
            if current_state != "EMERGENCY_STOP":
                raise AquaCrewException(
                    status_code=400,
                    code="INVALID_RESET",
                    message=f"Rover {rover_id} is not in EMERGENCY_STOP (current: {current_state})."
                )
            desired_state = "IDLE"
        elif cmd_upper == "SET_STATE":
            if not target_state:
                raise AquaCrewException(status_code=400, code="MISSING_TARGET_STATE", message="target_state required for SET_STATE")
            desired_state = target_state.upper()
        else:
            raise AquaCrewException(status_code=400, code="UNKNOWN_COMMAND", message=f"Unknown rover command: {command}")

        # Transition validation
        if not is_valid_transition(current_state, desired_state):
            allowed = VALID_ROVER_TRANSITIONS.get(current_state, [])
            raise AquaCrewException(
                status_code=400,
                code="INVALID_STATE_TRANSITION",
                message=f"Cannot transition rover {rover_id} from {current_state} to {desired_state}. Valid targets are: {allowed}."
            )

        # Apply state changes
        new_status = map_operating_state_to_status(desired_state)
        RoverRepository.update_state(db, rover, desired_state, new_status)

        # Kinematic stops for halts
        if desired_state in ["EMERGENCY_STOP", "ERROR", "PAUSED", "OFFLINE", "IDLE"]:
            rover.velocity_mps = 0.0
            rover.target_speed_mps = 0.0
            if desired_state in ["EMERGENCY_STOP", "ERROR", "OFFLINE"]:
                rover.motor_current_amps = 0.0
            db.commit()

        # Log transition & event
        transition_record = EventRepository.log_state_transition(
            db, rover_id, current_state, desired_state, reason, triggered_by
        )
        EventRepository.log_audit_event(
            db,
            event_type="ROVER_STATE_CHANGED",
            details=f"Rover {rover_id} command {command}: {current_state} -> {desired_state}. Reason: {reason}",
            rover_id=rover_id,
        )

        # WebSocket broadcast
        broadcast_payload = {
            "type": "ROVER_STATE_CHANGED",
            "rover_id": rover_id,
            "previous_state": current_state,
            "new_state": desired_state,
            "status": new_status,
            "reason": reason,
            "triggered_by": triggered_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_simulated": True,
            "provenance": "VIRTUAL_SIMULATION_BACKEND",
        }
        await ws_manager.broadcast(broadcast_payload)

        if desired_state == "EMERGENCY_STOP":
            await ws_manager.broadcast({
                "type": "ROVER_EMERGENCY_STOP",
                "rover_id": rover_id,
                "reason": reason,
                "triggered_by": triggered_by,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_simulated": True,
                "provenance": "VIRTUAL_SIMULATION_BACKEND",
            })

        return {
            "success": True,
            "rover_id": rover_id,
            "previous_state": current_state,
            "new_state": desired_state,
            "message": f"Successfully transitioned {rover_id} to {desired_state}.",
        }

