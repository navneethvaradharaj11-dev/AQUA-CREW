"""
Mission Domain Service
Handles mission planning, assignment validation, lifecycle progression, and event broadcasts.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.models.mission import MissionModel
from app.models.rover import RoverModel
from app.repositories.mission_repository import MissionRepository
from app.repositories.rover_repository import RoverRepository
from app.repositories.event_repository import EventRepository
from app.services.rover_service import RoverService
from app.websocket.connection_manager import ws_manager
from app.core.exceptions import AquaCrewException


class MissionService:
    @staticmethod
    def list_missions(db: Session, status: Optional[str] = None) -> List[MissionModel]:
        return MissionRepository.get_all(db, status=status)

    @staticmethod
    def get_mission_by_id(db: Session, mission_id: str) -> Optional[MissionModel]:
        return MissionRepository.get_by_id(db, mission_id)

    @staticmethod
    def create_mission(db: Session, mission_in: dict) -> MissionModel:
        existing = MissionRepository.get_by_id(db, mission_in["id"])
        if existing:
            raise AquaCrewException(
                status_code=400,
                code="MISSION_ALREADY_EXISTS",
                message=f"Mission ID {mission_in['id']} already exists."
            )
        return MissionRepository.create(db, mission_in)

    @staticmethod
    async def assign_mission(db: Session, mission_id: str, rover_id: str) -> Dict[str, Any]:
        mission = MissionRepository.get_by_id(db, mission_id)
        if not mission:
            raise AquaCrewException(status_code=404, code="MISSION_NOT_FOUND", message=f"Mission {mission_id} not found.")

        rover = RoverRepository.get_by_id(db, rover_id)
        if not rover:
            raise AquaCrewException(status_code=404, code="ROVER_NOT_FOUND", message=f"Rover {rover_id} not found.")

        # Guard 1: Rover must be in IDLE state
        if rover.operating_state != "IDLE":
            raise AquaCrewException(
                status_code=400,
                code="ROVER_NOT_IDLE",
                message=f"Rover {rover_id} cannot be assigned: state is {rover.operating_state} (must be IDLE)."
            )

        # Guard 2: Prevent duplicate assignment if another rover is actively executing this mission
        active_assignment = db.query(RoverModel).filter(
            RoverModel.assigned_mission_id == mission_id,
            RoverModel.id != rover_id,
            RoverModel.operating_state.in_(["MOVING", "INSPECTING", "PAUSED", "RETURNING"])
        ).first()

        if active_assignment:
            raise AquaCrewException(
                status_code=400,
                code="MISSION_ALREADY_ASSIGNED",
                message=f"Mission {mission_id} is already actively assigned to {active_assignment.id}."
            )

        # Guard 3: Atomic check-and-set to prevent double-assignment concurrency race conditions
        updated_count = db.query(RoverModel).filter(
            RoverModel.id == rover_id,
            RoverModel.operating_state == "IDLE",
            (RoverModel.assigned_mission_id == None) | (RoverModel.assigned_mission_id == "") | (RoverModel.assigned_mission_id == mission_id)
        ).update({
            "assigned_mission_id": mission_id,
        })
        if updated_count == 0:
            raise AquaCrewException(
                status_code=409,
                code="ROVER_ASSIGNMENT_CONFLICT",
                message=f"Rover {rover_id} is no longer available or was concurrently assigned by another operation."
            )

        # Update Mission
        mission.assigned_rover_id = rover.id
        mission.assigned_rover_name = rover.name
        mission.status = "In Progress"
        mission.start_time = f"{datetime.now(timezone.utc).strftime('%H:%M')} UTC (Dispatched)"
        mission.updated_at = datetime.now(timezone.utc)

        # Update Rover
        rover.current_mission = f"{mission.mission_type} ({mission.id})"
        rover.pipe_segment_id = mission.target_segment_id
        rover.route_progress_pct = 0
        db.commit()

        # Transition rover to INSPECTING
        await RoverService.execute_command(
            db,
            rover_id=rover.id,
            command="SET_STATE",
            target_state="INSPECTING",
            reason=f"Assigned to mission {mission.id} ({mission.mission_type})",
            triggered_by="OPERATOR"
        )

        # Log & broadcast
        EventRepository.log_audit_event(
            db,
            event_type="ROVER_MISSION_EVENT",
            details=f"Rover {rover.id} assigned to mission {mission.id}",
            rover_id=rover.id,
            mission_id=mission.id,
        )

        await ws_manager.broadcast({
            "type": "ROVER_MISSION_EVENT",
            "action": "ASSIGNED",
            "rover_id": rover.id,
            "mission_id": mission.id,
            "details": f"Rover {rover.name} assigned to mission {mission.mission_type} on segment {mission.target_segment_id}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_simulated": True,
            "provenance": "VIRTUAL_SIMULATION_BACKEND",
        })

        return {
            "success": True,
            "mission_id": mission.id,
            "rover_id": rover.id,
            "message": f"Successfully assigned {rover.id} to mission {mission.id}.",
        }

    @staticmethod
    async def update_mission_status(db: Session, mission_id: str, new_status: str, reason: str = "") -> Dict[str, Any]:
        mission = MissionRepository.get_by_id(db, mission_id)
        if not mission:
            raise AquaCrewException(status_code=404, code="MISSION_NOT_FOUND", message=f"Mission {mission_id} not found.")

        mission.status = new_status
        mission.updated_at = datetime.now(timezone.utc)

        if new_status == "Cancelled" and mission.assigned_rover_id:
            rover = RoverRepository.get_by_id(db, mission.assigned_rover_id)
            if rover:
                rover.assigned_mission_id = None
                rover.current_mission = "Standby (Mission Cancelled)"
                await RoverService.execute_command(
                    db,
                    rover_id=rover.id,
                    command="SET_STATE",
                    target_state="IDLE",
                    reason=f"Mission {mission.id} cancelled: {reason}",
                    triggered_by="OPERATOR"
                )

        db.commit()

        await ws_manager.broadcast({
            "type": "ROVER_MISSION_EVENT",
            "action": new_status.upper(),
            "rover_id": mission.assigned_rover_id or "UNASSIGNED",
            "mission_id": mission.id,
            "details": f"Mission {mission.id} status updated to {new_status}. {reason}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_simulated": True,
            "provenance": "VIRTUAL_SIMULATION_BACKEND",
        })

        return {"success": True, "mission_id": mission.id, "status": new_status}

