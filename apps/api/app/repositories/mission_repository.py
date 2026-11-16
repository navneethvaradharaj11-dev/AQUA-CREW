"""
Mission Repository for Database Persistence
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.models.mission import MissionModel

DEFAULT_MISSIONS = [
    {
        "id": "MSN-2026-042",
        "assigned_rover_id": "ROV-AQUA-01",
        "assigned_rover_name": "Triton-1 Crawler",
        "mission_type": "Acoustic Pipe Survey",
        "progress_percentage": 68,
        "status": "In Progress",
        "start_time": "14:15 UTC (1h 25m elapsed)",
        "estimated_completion_time": "16:00 UTC (~20m remaining)",
        "target_segment_id": "PIPE-SEC-4B-92",
        "waypoint_count": 24,
        "completed_waypoints": 16,
    },
    {
        "id": "MSN-2026-043",
        "assigned_rover_id": "ROV-AQUA-02",
        "assigned_rover_name": "Nautilus Ground Scout",
        "mission_type": "Emergency Intercept",
        "progress_percentage": 42,
        "status": "In Progress",
        "start_time": "15:00 UTC (40m elapsed)",
        "estimated_completion_time": "16:30 UTC (~50m remaining)",
        "target_segment_id": "PIPE-IND-1A-04",
        "waypoint_count": 12,
        "completed_waypoints": 5,
    },
    {
        "id": "MSN-2026-044",
        "assigned_rover_id": "ROV-AQUA-03",
        "assigned_rover_name": "Hydra Pipe Probe",
        "mission_type": "Pressure Transient Test",
        "progress_percentage": 0,
        "status": "Scheduled",
        "start_time": "17:00 UTC (in 1h 20m)",
        "estimated_completion_time": "18:45 UTC",
        "target_segment_id": "PIPE-RES-3C-11",
        "waypoint_count": 18,
        "completed_waypoints": 0,
    },
]


class MissionRepository:
    @staticmethod
    def get_all(db: Session, status: Optional[str] = None) -> List[MissionModel]:
        query = db.query(MissionModel)
        if status:
            query = query.filter(MissionModel.status == status)
        return query.all()

    @staticmethod
    def get_by_id(db: Session, mission_id: str) -> Optional[MissionModel]:
        return db.query(MissionModel).filter(MissionModel.id == mission_id).first()

    @staticmethod
    def create(db: Session, mission_data: dict) -> MissionModel:
        model = MissionModel(
            **mission_data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_simulated=True,
        )
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def seed_defaults(db: Session) -> None:
        if db.query(MissionModel).count() == 0:
            for m in DEFAULT_MISSIONS:
                model = MissionModel(
                    **m,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    is_simulated=True,
                )
                db.add(model)
            db.commit()

