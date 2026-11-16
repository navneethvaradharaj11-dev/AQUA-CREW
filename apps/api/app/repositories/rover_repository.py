"""
Rover Repository for Database Persistence
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.models.rover import RoverModel

DEFAULT_ROVERS = [
    {
        "id": "ROV-AQUA-01",
        "name": "Triton-1 Crawler",
        "model": "In-Pipe Acoustic Crawler MK-IV",
        "status": "ACTIVE",
        "operating_state": "INSPECTING",
        "connection_status": "ONLINE",
        "battery_percentage": 86.0,
        "distance_travelled_km": 14.8,
        "current_mission": "Acoustic Survey Segment NY-402",
        "assigned_mission_id": "MSN-2026-042",
        "station_name": "Sector 4 — Station 1200m",
        "pipe_segment_id": "PIPE-SEC-4B-92",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "velocity_mps": 0.28,
        "heading_deg": 178.4,
        "target_speed_mps": 0.28,
        "route_progress_pct": 65,
        "internal_temp_c": 31.4,
        "motor_temp_c": 38.5,
        "motor_current_amps": 1.85,
        "signal_rssi_dbm": -64.0,
        "acoustic_spl_db": 46.2,
        "dominant_freq_hz": 1240.0,
        "ground_moisture_pct": 18.5,
    },
    {
        "id": "ROV-AQUA-02",
        "name": "Nautilus Ground Scout",
        "model": "Autonomous Ground Rover G-200",
        "status": "ACTIVE",
        "operating_state": "MOVING",
        "connection_status": "ONLINE",
        "battery_percentage": 92.0,
        "distance_travelled_km": 8.4,
        "current_mission": "Manhole Surface Acoustic Grid Scan",
        "assigned_mission_id": "MSN-2026-043",
        "station_name": "East Avenue — Valve Box 12",
        "pipe_segment_id": "PIPE-IND-1A-04",
        "latitude": 40.7145,
        "longitude": -74.0021,
        "velocity_mps": 0.55,
        "heading_deg": 92.1,
        "target_speed_mps": 0.55,
        "route_progress_pct": 42,
        "internal_temp_c": 28.9,
        "motor_temp_c": 34.2,
        "motor_current_amps": 2.1,
        "signal_rssi_dbm": -58.0,
        "acoustic_spl_db": 38.1,
        "dominant_freq_hz": 420.0,
        "ground_moisture_pct": 12.0,
    },
    {
        "id": "ROV-AQUA-03",
        "name": "Hydra Pipe Probe",
        "model": "Micro-Submersible Sewer & Pipe Sonar",
        "status": "ONLINE",
        "operating_state": "IDLE",
        "connection_status": "ONLINE",
        "battery_percentage": 74.0,
        "distance_travelled_km": 5.1,
        "current_mission": "Standby Patrol Route 3",
        "assigned_mission_id": None,
        "station_name": "Northern Gate Pump Station",
        "pipe_segment_id": "PIPE-RES-3C-11",
        "latitude": 40.7198,
        "longitude": -74.0089,
        "velocity_mps": 0.0,
        "heading_deg": 0.0,
        "target_speed_mps": 0.0,
        "route_progress_pct": 0,
        "internal_temp_c": 26.5,
        "motor_temp_c": 24.8,
        "motor_current_amps": 0.4,
        "signal_rssi_dbm": -72.0,
        "acoustic_spl_db": 34.0,
        "dominant_freq_hz": 180.0,
        "ground_moisture_pct": 10.4,
    },
    {
        "id": "ROV-AQUA-04",
        "name": "Aquila Surface Drone",
        "model": "Overhead Thermal Leak Mapper",
        "status": "ACTIVE",
        "operating_state": "RETURNING",
        "connection_status": "DEGRADED",
        "battery_percentage": 24.0,
        "distance_travelled_km": 19.3,
        "current_mission": "Returning to Docking Cradle B",
        "assigned_mission_id": None,
        "station_name": "Harbor Transit Line B",
        "pipe_segment_id": "PIPE-HRB-02-19",
        "latitude": 40.7091,
        "longitude": -74.0115,
        "velocity_mps": 0.85,
        "heading_deg": 270.0,
        "target_speed_mps": 0.85,
        "route_progress_pct": 70,
        "internal_temp_c": 39.8,
        "motor_temp_c": 45.1,
        "motor_current_amps": 3.4,
        "signal_rssi_dbm": -82.0,
        "acoustic_spl_db": 40.5,
        "dominant_freq_hz": 850.0,
        "ground_moisture_pct": 22.1,
    },
    {
        "id": "ROV-AQUA-05",
        "name": "Scylla Depth Unit",
        "model": "Heavy Deep-Trunk Crawler",
        "status": "OFFLINE",
        "operating_state": "OFFLINE",
        "connection_status": "OFFLINE",
        "battery_percentage": 0.0,
        "distance_travelled_km": 2.2,
        "current_mission": "Scheduled Depot Maintenance",
        "assigned_mission_id": None,
        "station_name": "Central Maintenance Facility Bay 3",
        "pipe_segment_id": "PIPE-SEC-4A-10",
        "latitude": 40.7040,
        "longitude": -74.0060,
        "velocity_mps": 0.0,
        "heading_deg": 0.0,
        "target_speed_mps": 0.0,
        "route_progress_pct": 0,
        "internal_temp_c": 22.0,
        "motor_temp_c": 22.0,
        "motor_current_amps": 0.0,
        "signal_rssi_dbm": -110.0,
        "acoustic_spl_db": 0.0,
        "dominant_freq_hz": 0.0,
        "ground_moisture_pct": 0.0,
    },
]


class RoverRepository:
    @staticmethod
    def get_all(db: Session, status: Optional[str] = None, operating_state: Optional[str] = None) -> List[RoverModel]:
        query = db.query(RoverModel)
        if status:
            query = query.filter(RoverModel.status == status)
        if operating_state:
            query = query.filter(RoverModel.operating_state == operating_state)
        return query.all()

    @staticmethod
    def get_by_id(db: Session, rover_id: str) -> Optional[RoverModel]:
        return db.query(RoverModel).filter(RoverModel.id == rover_id).first()

    @staticmethod
    def seed_defaults(db: Session) -> None:
        if db.query(RoverModel).count() == 0:
            for r in DEFAULT_ROVERS:
                model = RoverModel(
                    **r,
                    last_heartbeat=datetime.now(timezone.utc),
                    is_simulated=True,
                )
                db.add(model)
            db.commit()

    @staticmethod
    def update_state(db: Session, rover: RoverModel, new_state: str, new_status: str) -> RoverModel:
        rover.operating_state = new_state
        rover.status = new_status
        rover.last_heartbeat = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rover)
        return rover

    @staticmethod
    def update_operating_state(db: Session, rover_id: str, new_state: str) -> Optional[RoverModel]:
        rover = db.query(RoverModel).filter(RoverModel.id == rover_id).first()
        if rover:
            rover.operating_state = new_state
            rover.last_heartbeat = datetime.now(timezone.utc)
            db.commit()
            db.refresh(rover)
        return rover

    @staticmethod
    def update_assigned_mission(db: Session, rover_id: str, mission_id: Optional[str]) -> Optional[RoverModel]:
        rover = db.query(RoverModel).filter(RoverModel.id == rover_id).first()
        if rover:
            rover.assigned_mission_id = mission_id
            db.commit()
            db.refresh(rover)
        return rover

    @staticmethod
    def update_position(db: Session, rover_id: str, lat: float, lng: float) -> Optional[RoverModel]:
        rover = db.query(RoverModel).filter(RoverModel.id == rover_id).first()
        if rover:
            rover.latitude = lat
            rover.longitude = lng
            rover.last_heartbeat = datetime.now(timezone.utc)
            db.commit()
            db.refresh(rover)
        return rover

    @staticmethod
    def update_battery(db: Session, rover_id: str, battery: float) -> Optional[RoverModel]:
        rover = db.query(RoverModel).filter(RoverModel.id == rover_id).first()
        if rover:
            rover.battery_percentage = battery
            db.commit()
            db.refresh(rover)
        return rover

