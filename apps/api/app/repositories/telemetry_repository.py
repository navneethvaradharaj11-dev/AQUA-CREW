"""
Telemetry Repository for Historical Records
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.models.telemetry import TelemetryRecordModel


class TelemetryRepository:
    @staticmethod
    def create(db: Session, telemetry_data: dict) -> TelemetryRecordModel:
        record = TelemetryRecordModel(
            **telemetry_data,
            timestamp=datetime.now(timezone.utc),
            is_simulated=True,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_history(
        db: Session,
        rover_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TelemetryRecordModel]:
        query = db.query(TelemetryRecordModel)
        if rover_id:
            query = query.filter(TelemetryRecordModel.rover_id == rover_id)
        return query.order_by(TelemetryRecordModel.timestamp.desc()).offset(offset).limit(limit).all()

    @staticmethod
    def count(db: Session, rover_id: Optional[str] = None) -> int:
        query = db.query(TelemetryRecordModel)
        if rover_id:
            query = query.filter(TelemetryRecordModel.rover_id == rover_id)
        return query.count()

