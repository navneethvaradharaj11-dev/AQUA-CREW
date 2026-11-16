"""
Backend Authoritative Simulation Service
Manages discrete background simulation tick loop, autonomous kinematics,
pipeline route interpolation, safety interlocks, and real-time broadcasts.
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.database.session import SessionLocal
from app.repositories.rover_repository import RoverRepository
from app.repositories.mission_repository import MissionRepository
from app.repositories.pipeline_repository import PipelineRepository
from app.repositories.telemetry_repository import TelemetryRepository
from app.repositories.event_repository import EventRepository
from app.services.telemetry_service import interpolate_route_position
from app.websocket.connection_manager import ws_manager
from app.config import settings

logger = logging.getLogger("aqua_crew.simulation")


class SimulationService:
    _instance: Optional["SimulationService"] = None

    def __init__(self):
        self.is_running: bool = False
        self.tick_interval_s: float = settings.SIMULATION_TICK_INTERVAL_MS / 1000.0
        self.tick_count: int = 0
        self._task: Optional[asyncio.Task] = None
        self._kinematic_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_instance(cls) -> "SimulationService":
        if cls._instance is None:
            cls._instance = SimulationService()
        return cls._instance

    def initialize_kinematics(self, db):
        rovers = RoverRepository.get_all(db)
        for r in rovers:
            if r.id not in self._kinematic_cache:
                initial_dist = 1200.0 if r.id == "ROV-AQUA-01" else 350.0 if r.id == "ROV-AQUA-02" else 540.0 if r.id == "ROV-AQUA-04" else 0.0
                direction = -1 if r.operating_state == "RETURNING" else 1
                self._kinematic_cache[r.id] = {
                    "current_distance_m": initial_dist,
                    "direction": direction,
                    "total_distance_m": r.distance_travelled_km * 1000.0,
                }

    def start(self) -> Dict[str, Any]:
        if self.is_running:
            return {"success": True, "message": "Simulation is already active.", "is_running": True}

        self.is_running = True
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._simulation_loop())
        except RuntimeError:
            self._task = None
        logger.info(f"Simulation engine loop started (interval: {self.tick_interval_s}s)")

        # Broadcast state change
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast({
                "type": "SIMULATION_STATUS_CHANGED",
                "is_running": True,
                "interval_ms": int(self.tick_interval_s * 1000),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_simulated": True,
                "provenance": "VIRTUAL_SIMULATION_BACKEND",
            }))
        except RuntimeError:
            pass

        return {"success": True, "message": "Simulation engine started.", "is_running": True}

    def pause(self) -> Dict[str, Any]:
        if not self.is_running:
            return {"success": True, "message": "Simulation is already paused.", "is_running": False}

        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None
        logger.info("Simulation engine loop paused.")

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast({
                "type": "SIMULATION_STATUS_CHANGED",
                "is_running": False,
                "interval_ms": int(self.tick_interval_s * 1000),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_simulated": True,
                "provenance": "VIRTUAL_SIMULATION_BACKEND",
            }))
        except RuntimeError:
            pass

        return {"success": True, "message": "Simulation engine paused.", "is_running": False}

    def reset(self) -> Dict[str, Any]:
        self.pause()
        self.tick_count = 0
        self._kinematic_cache.clear()

        # Re-seed database to pristine baseline
        db = SessionLocal()
        try:
            from app.models.rover import RoverModel
            from app.models.mission import MissionModel
            db.query(RoverModel).delete()
            db.query(MissionModel).delete()
            db.commit()

            RoverRepository.seed_defaults(db)
            MissionRepository.seed_defaults(db)
            self.initialize_kinematics(db)
        finally:
            db.close()

        logger.info("Simulation engine and rover states reset to pristine defaults.")
        return {"success": True, "message": "Simulation engine reset to baseline defaults.", "is_running": False}

    async def _simulation_loop(self):
        try:
            while self.is_running:
                await asyncio.sleep(self.tick_interval_s)
                await self.execute_tick()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in simulation tick loop: {e}", exc_info=True)
            self.is_running = False

    async def execute_tick(self):
        self.tick_count += 1
        db = SessionLocal()
        try:
            RoverRepository.seed_defaults(db)
            MissionRepository.seed_defaults(db)
            PipelineRepository.seed_defaults(db)

            if not self._kinematic_cache:
                self.initialize_kinematics(db)

            rovers = RoverRepository.get_all(db)
            pipelines = {p.id: json.loads(p.coordinates_json) for p in PipelineRepository.get_all(db)}
            active_count = 0

            for rover in rovers:
                state = rover.operating_state
                k_data = self._kinematic_cache.get(rover.id, {
                    "current_distance_m": 0.0,
                    "direction": 1,
                    "total_distance_m": rover.distance_travelled_km * 1000.0,
                })

                # Determine speed based on state
                target_speed = 0.0
                if state == "MOVING":
                    target_speed = 0.55
                    k_data["direction"] = 1
                elif state == "INSPECTING":
                    target_speed = 0.28
                    k_data["direction"] = 1
                elif state == "RETURNING":
                    target_speed = 0.85
                    k_data["direction"] = -1
                elif state in ["IDLE", "PAUSED", "CHARGING", "OFFLINE", "ERROR", "EMERGENCY_STOP"]:
                    target_speed = 0.0

                if target_speed > 0:
                    active_count += 1

                # Safety interlocks
                # 1. Low battery (<12%) safety auto-return
                if rover.battery_percentage <= 12.0 and state in ["MOVING", "INSPECTING"]:
                    rover.operating_state = "RETURNING"
                    rover.status = "ACTIVE"
                    k_data["direction"] = -1
                    EventRepository.log_state_transition(
                        db, rover.id, state, "RETURNING",
                        "Low battery safety interlock triggered (<12%). Returning to base.",
                        "SAFETY_INTERLOCK"
                    )

                # 2. Thermal cut-off (>= 58°C) safety auto-pause
                if rover.motor_temp_c >= 58.0 and state not in ["PAUSED", "EMERGENCY_STOP", "OFFLINE"]:
                    rover.operating_state = "PAUSED"
                    rover.status = "IDLE"
                    target_speed = 0.0
                    EventRepository.log_state_transition(
                        db, rover.id, state, "PAUSED",
                        f"Motor temperature high limit cut-off ({rover.motor_temp_c}°C >= 58°C). Paused.",
                        "SAFETY_INTERLOCK"
                    )

                # Smooth velocity adjustment
                current_vel = rover.velocity_mps or 0.0
                if target_speed > current_vel:
                    current_vel = min(target_speed, current_vel + 0.15)
                elif target_speed < current_vel:
                    current_vel = max(target_speed, current_vel - 0.25)
                else:
                    current_vel = target_speed

                rover.velocity_mps = round(current_vel, 2)
                rover.target_speed_mps = round(target_speed, 2)

                # Position advancement
                coords = pipelines.get(rover.pipe_segment_id, [])
                if coords and current_vel > 0:
                    delta_d = current_vel * self.tick_interval_s
                    k_data["current_distance_m"] += k_data["direction"] * delta_d
                    k_data["total_distance_m"] += delta_d

                    interp = interpolate_route_position(
                        coords,
                        k_data["current_distance_m"],
                        is_returning=(k_data["direction"] == -1)
                    )

                    rover.longitude = interp["longitude"]
                    rover.latitude = interp["latitude"]
                    rover.heading_deg = interp["heading_deg"]
                    rover.route_progress_pct = int(interp["fraction"] * 100)
                    rover.station_name = f"Station {int(k_data['current_distance_m'])}m"
                    rover.distance_travelled_km = round(k_data["total_distance_m"] / 1000.0, 2)

                    # Route end reached -> Auto return
                    if k_data["current_distance_m"] >= interp["total_length_m"]:
                        k_data["current_distance_m"] = interp["total_length_m"]
                        if state in ["MOVING", "INSPECTING"]:
                            rover.operating_state = "RETURNING"
                            rover.status = "ACTIVE"
                            k_data["direction"] = -1
                            if rover.assigned_mission_id:
                                m = MissionRepository.get_by_id(db, rover.assigned_mission_id)
                                if m:
                                    m.status = "Completed"
                                    m.progress_percentage = 100
                                    m.completed_waypoints = m.waypoint_count

                    # Base reached -> Charging / Standby
                    elif k_data["current_distance_m"] <= 0:
                        k_data["current_distance_m"] = 0
                        if state == "RETURNING":
                            if rover.battery_percentage >= 85.0:
                                rover.operating_state = "IDLE"
                                rover.status = "ONLINE"
                                rover.current_mission = "Standby (Mission Complete)"
                            else:
                                rover.operating_state = "CHARGING"
                                rover.status = "ONLINE"
                                rover.current_mission = "Recharging at Dock"
                            rover.assigned_mission_id = None
                            k_data["direction"] = 1

                # Battery modeling
                if rover.operating_state == "CHARGING":
                    rover.battery_percentage = min(100.0, round(rover.battery_percentage + 0.4, 1))
                    if rover.battery_percentage >= 100.0:
                        rover.operating_state = "IDLE"
                        rover.current_mission = "Standby (Fully Charged)"
                elif current_vel > 0:
                    rover.battery_percentage = max(0.0, round(rover.battery_percentage - 0.05, 2))

                # Thermal modeling
                if current_vel > 0:
                    rover.motor_temp_c = min(65.0, round(rover.motor_temp_c + 0.12, 1))
                    rover.internal_temp_c = min(42.0, round(rover.internal_temp_c + 0.04, 1))
                    rover.motor_current_amps = round(1.2 + current_vel * 1.5, 2)
                else:
                    rover.motor_temp_c = max(23.5, round(rover.motor_temp_c - 0.15, 1))
                    rover.internal_temp_c = max(23.5, round(rover.internal_temp_c - 0.05, 1))
                    rover.motor_current_amps = 0.0

                rover.last_heartbeat = datetime.now(timezone.utc)
                self._kinematic_cache[rover.id] = k_data

                # Synchronize mission progress
                if rover.assigned_mission_id and rover.operating_state in ["MOVING", "INSPECTING"]:
                    m = MissionRepository.get_by_id(db, rover.assigned_mission_id)
                    if m and m.status == "In Progress":
                        m.progress_percentage = rover.route_progress_pct
                        m.completed_waypoints = int((rover.route_progress_pct / 100.0) * m.waypoint_count)
                        total_route = m.route_distance_m or 1000.0
                        m.inspected_distance_m = round((rover.route_progress_pct / 100.0) * total_route, 1)

                        if rover.route_progress_pct >= 100:
                            m.status = "Completed"
                            await ws_manager.broadcast({
                                "type": "MISSION_COMPLETED",
                                "mission_id": m.id,
                                "rover_id": rover.id,
                                "target_segment_id": m.target_segment_id,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "is_simulated": True,
                            })

                # Broadcast live telemetry update
                await ws_manager.broadcast({
                    "type": "ROVER_TELEMETRY_UPDATED",
                    "rover_id": rover.id,
                    "operating_state": rover.operating_state,
                    "status": rover.status,
                    "battery_percentage": rover.battery_percentage,
                    "distance_travelled_km": rover.distance_travelled_km,
                    "velocity_mps": rover.velocity_mps,
                    "heading_deg": rover.heading_deg,
                    "latitude": rover.latitude,
                    "longitude": rover.longitude,
                    "station_name": rover.station_name,
                    "pipe_segment_id": rover.pipe_segment_id,
                    "route_progress_pct": rover.route_progress_pct,
                    "motor_temp_c": rover.motor_temp_c,
                    "internal_temp_c": rover.internal_temp_c,
                    "motor_current_amps": rover.motor_current_amps,
                    "signal_rssi_dbm": rover.signal_rssi_dbm,
                    "acoustic_spl_db": rover.acoustic_spl_db,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "is_simulated": True,
                    "provenance": "VIRTUAL_SIMULATION_BACKEND",
                })

            db.commit()

            # Broadcast simulation tick pulse
            await ws_manager.broadcast({
                "type": "SIMULATION_TICK",
                "tick_number": self.tick_count,
                "active_rover_count": active_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_simulated": True,
                "provenance": "VIRTUAL_SIMULATION_BACKEND",
            })

            # Every 10 ticks, persist telemetry snapshots to historical table
            if self.tick_count % 10 == 0:
                for rover in rovers:
                    TelemetryRepository.create(db, {
                        "rover_id": rover.id,
                        "latitude": rover.latitude,
                        "longitude": rover.longitude,
                        "velocity_mps": rover.velocity_mps,
                        "heading_deg": rover.heading_deg,
                        "battery_pct": rover.battery_percentage,
                        "motor_temp_c": rover.motor_temp_c,
                        "internal_temp_c": rover.internal_temp_c,
                        "motor_current_amps": rover.motor_current_amps,
                        "signal_rssi_dbm": rover.signal_rssi_dbm,
                        "acoustic_spl_db": rover.acoustic_spl_db,
                        "dominant_freq_hz": rover.dominant_freq_hz,
                        "ground_moisture_pct": rover.ground_moisture_pct,
                        "operating_state": rover.operating_state,
                        "pipe_segment_id": rover.pipe_segment_id,
                    })

        finally:
            db.close()


simulation_service = SimulationService.get_instance()
