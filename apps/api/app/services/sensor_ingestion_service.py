"""
Sensor Ingestion and Quality Validation Service
Ingests multi-modal pipeline and rover sensor readings with quality scoring.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid
import math

from sqlalchemy.orm import Session
from app.models.sensor_reading import SensorReadingModel
from app.schemas.ai import SensorReadingCreate
from app.websocket.connection_manager import ws_manager
import asyncio


# Valid operational physical boundaries for outlier filtering
SENSOR_BOUNDS = {
    "acoustic": {"min": 10.0, "max": 130.0, "unit": "dB"},
    "rover_acoustic": {"min": 10.0, "max": 130.0, "unit": "dB"},
    "pressure": {"min": 0.0, "max": 16.0, "unit": "bar"},
    "flow": {"min": 0.0, "max": 500.0, "unit": "m3/h"},
    "ground_moisture": {"min": 0.0, "max": 100.0, "unit": "%"},
    "temperature": {"min": -10.0, "max": 60.0, "unit": "degC"},
}


class SensorIngestionService:
    @staticmethod
    def validate_reading(data: SensorReadingCreate) -> Dict[str, Any]:
        """
        Validates physical unit, bounds, and assigns a data quality score.
        """
        stype = data.sensor_type.lower()
        val = data.measurement_value
        quality = "EXCELLENT"

        if stype not in SENSOR_BOUNDS:
            return {"valid": False, "reason": f"Unknown sensor type '{stype}'", "quality": "FAULT"}

        bounds = SENSOR_BOUNDS[stype]
        if data.measurement_unit.lower() != bounds["unit"].lower():
            quality = "DEGRADED"

        if math.isnan(val) or math.isinf(val):
            return {"valid": False, "reason": "Measurement value is NaN or Inf", "quality": "FAULT"}

        if val < bounds["min"] or val > bounds["max"]:
            # Extreme physical outlier
            return {"valid": False, "reason": f"Value {val} exceeds physical bounds [{bounds['min']}, {bounds['max']}]", "quality": "FAULT"}

        # Check for slight drift or borderline measurements
        if val > bounds["max"] * 0.9 or val < bounds["min"] + (bounds["max"] - bounds["min"]) * 0.05:
            quality = "GOOD"

        return {"valid": True, "reason": "OK", "quality": quality}

    @staticmethod
    def ingest_reading(db: Session, reading_in: SensorReadingCreate) -> SensorReadingModel:
        """
        Validates, records quality score, and persists a sensor reading.
        """
        val_res = SensorIngestionService.validate_reading(reading_in)
        if not val_res["valid"]:
            # Record with FAULT quality
            reading_id = f"SNS-ERR-{uuid.uuid4().hex[:8]}"
            record = SensorReadingModel(
                id=reading_id,
                sensor_id=reading_in.sensor_id,
                sensor_type=reading_in.sensor_type,
                pipeline_segment_id=reading_in.pipeline_segment_id,
                measurement_value=reading_in.measurement_value,
                measurement_unit=reading_in.measurement_unit,
                sampling_rate_hz=reading_in.sampling_rate_hz or 1.0,
                quality_indicator=val_res["quality"],
                created_at=datetime.now(timezone.utc),
                is_simulated=True,
                source="VIRTUAL_SIMULATION_ENGINE",
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record

        reading_id = f"READ-{uuid.uuid4().hex[:10]}"
        record = SensorReadingModel(
            id=reading_id,
            sensor_id=reading_in.sensor_id,
            sensor_type=reading_in.sensor_type,
            pipeline_segment_id=reading_in.pipeline_segment_id,
            measurement_value=reading_in.measurement_value,
            measurement_unit=reading_in.measurement_unit,
            sampling_rate_hz=reading_in.sampling_rate_hz or 1.0,
            quality_indicator=val_res["quality"],
            created_at=datetime.now(timezone.utc),
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        try:
            loop = asyncio.get_running_loop()
            event_type = "SENSOR_ANOMALY_DETECTED" if record.quality_indicator == "FAULT" else "SENSOR_READING_RECEIVED"
            loop.create_task(
                ws_manager.broadcast(
                    {
                        "type": event_type,
                        "sensor_id": record.sensor_id,
                        "sensor_type": record.sensor_type,
                        "pipeline_segment_id": record.pipeline_segment_id,
                        "measurement_value": record.measurement_value,
                        "measurement_unit": record.measurement_unit,
                        "quality_indicator": record.quality_indicator,
                        "timestamp": record.created_at.isoformat(),
                        "is_simulated": True,
                        "source": record.source,
                    }
                )
            )
        except RuntimeError:
            pass

        return record

    @staticmethod
    def get_latest_readings_by_segment(db: Session, segment_id: str, limit: int = 10) -> List[SensorReadingModel]:
        return (
            db.query(SensorReadingModel)
            .filter(SensorReadingModel.pipeline_segment_id == segment_id)
            .order_by(SensorReadingModel.created_at.desc())
            .limit(limit)
            .all()
        )
