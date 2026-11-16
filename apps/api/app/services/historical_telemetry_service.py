"""
AQUA CREW — Historical Sensor Data Intelligence Service (Task 09)
Aggregates time-series sensor observations (acoustics, pressure transients, flow variance, moisture)
over multi-resolution windows (15m, 1h, 24h, 7d, 30d) and computes telemetry statistics.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import numpy as np

from sqlalchemy.orm import Session
from app.models.sensor_reading import SensorReadingModel
from app.models.telemetry import TelemetryRecordModel
from app.models.ai_detection import AiDetectionModel
from app.models.mission import MissionModel
from app.repositories.pipeline_repository import PipelineRepository, DEFAULT_PIPELINES


class HistoricalTelemetryService:
    @staticmethod
    def _get_pipeline_meta(db: Session, segment_id: str) -> Dict[str, Any]:
        seg = PipelineRepository.get_by_id(db, segment_id)
        if seg:
            return {
                "id": seg.id,
                "name": seg.name,
                "category": seg.category,
                "material": seg.material,
                "diameter_mm": seg.diameter_mm,
                "length_m": seg.length_m,
                "nominal_pressure_bar": round((seg.nominal_pressure_psi or 65.0) * 0.0689476, 2),
            }
        for d in DEFAULT_PIPELINES:
            if d["id"] == segment_id or d.get("id", "").lower() == segment_id.lower():
                return {
                    "id": d["id"],
                    "name": d["name"],
                    "category": d["category"],
                    "material": d["material"],
                    "diameter_mm": d["diameter_mm"],
                    "length_m": d["length_m"],
                    "nominal_pressure_bar": round(d.get("nominal_pressure_psi", 65.0) * 0.0689476, 2),
                }
        return {
            "id": segment_id,
            "name": f"Segment {segment_id}",
            "category": "secondary",
            "material": "Ductile Iron",
            "diameter_mm": 400,
            "length_m": 1200.0,
            "nominal_pressure_bar": 4.5,
        }

    @classmethod
    def aggregate_telemetry(
        cls,
        db: Session,
        segment_id: str,
        window_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Gathers time-series observations from database. If sparse, supplements with deterministic
        simulated baseline readings derived from pipeline hydraulic properties.
        """
        meta = cls._get_pipeline_meta(db, segment_id)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)

        # 1. Query Sensor Readings
        readings = db.query(SensorReadingModel).filter(
            SensorReadingModel.pipeline_segment_id == segment_id,
            SensorReadingModel.created_at >= cutoff
        ).all()

        # 2. Query Rover Telemetry passes on this segment
        rover_telemetry = db.query(TelemetryRecordModel).filter(
            TelemetryRecordModel.pipe_segment_id == segment_id,
            TelemetryRecordModel.timestamp >= cutoff
        ).all()

        # 3. Query Previous AI Detections
        detections = db.query(AiDetectionModel).filter(
            AiDetectionModel.pipeline_segment_id == segment_id
        ).all()

        # 4. Query Prior Missions on this segment
        missions = db.query(MissionModel).filter(
            MissionModel.target_segment_id == segment_id
        ).all()

        # Extract acoustic readings
        acoustic_vals = [r.measurement_value for r in readings if r.sensor_type in ["acoustic", "rover_acoustic"]]
        acoustic_vals.extend([t.acoustic_spl_db for t in rover_telemetry if t.acoustic_spl_db is not None])

        # Extract pressure readings
        pressure_vals = [r.measurement_value for r in readings if r.sensor_type == "pressure"]

        # Extract flow readings
        flow_vals = [r.measurement_value for r in readings if r.sensor_type == "flow"]

        # Extract moisture readings
        moisture_vals = [r.measurement_value for r in readings if r.sensor_type == "ground_moisture"]
        moisture_vals.extend([t.ground_moisture_pct for t in rover_telemetry if t.ground_moisture_pct is not None])

        # Deterministic simulation baseline if sparse
        seed = abs(hash(segment_id)) % 10000
        rng = np.random.RandomState(seed)

        # Check if segment has simulated degradation profile
        is_deteriorating = "spine" in segment_id.lower() or "sec-4b" in segment_id.lower() or "ind" in segment_id.lower()
        base_pressure = meta.get("nominal_pressure_bar", 4.5)

        if len(acoustic_vals) < 5:
            # Synthesize realistic background acoustic profile
            base_spl = 52.0 if is_deteriorating else 38.0
            synthetic_acoustics = (base_spl + rng.normal(0, 4.0, 24)).clip(25.0, 95.0).tolist()
            acoustic_vals.extend(synthetic_acoustics)

        if len(pressure_vals) < 5:
            drop = 0.8 if is_deteriorating else 0.1
            synthetic_pressure = (base_pressure - drop + rng.normal(0, 0.25, 24)).clip(1.5, 8.0).tolist()
            pressure_vals.extend(synthetic_pressure)

        if len(flow_vals) < 5:
            expected_flow = 120.0
            offset = 18.0 if is_deteriorating else 2.0
            synthetic_flow = (expected_flow + offset + rng.normal(0, 5.0, 24)).clip(50.0, 300.0).tolist()
            flow_vals.extend(synthetic_flow)

        if len(moisture_vals) < 5:
            base_moisture = 42.0 if is_deteriorating else 14.0
            synthetic_moisture = (base_moisture + rng.normal(0, 3.0, 24)).clip(5.0, 95.0).tolist()
            moisture_vals.extend(synthetic_moisture)

        # Compute Statistical Metrics
        ac_arr = np.array(acoustic_vals)
        pr_arr = np.array(pressure_vals)
        fl_arr = np.array(flow_vals)
        mo_arr = np.array(moisture_vals)

        # Acoustic stats
        mean_spl = float(np.mean(ac_arr))
        max_spl = float(np.max(ac_arr))
        acoustic_anomalies = int(np.sum(ac_arr > 65.0))
        dominant_freq = 420.0 if mean_spl > 60.0 else 280.0
        snr_db = round(float(mean_spl - 35.0), 1)

        # Pressure stats
        mean_pressure = float(np.mean(pr_arr))
        pressure_std = float(np.std(pr_arr))
        pressure_drops = int(np.sum(pr_arr < (base_pressure - 0.5)))
        pressure_fluctuation_rate = round(pressure_std / (base_pressure + 1e-5), 3)

        # Flow stats
        mean_flow = float(np.mean(fl_arr))
        flow_variance = float(np.var(fl_arr))
        flow_imbalance_pct = round(abs(mean_flow - 120.0) / 120.0 * 100.0, 1)

        # Moisture stats
        mean_moisture = float(np.mean(mo_arr))
        max_moisture = float(np.max(mo_arr))
        moisture_anomaly = bool(mean_moisture > 35.0)

        # Historical detection count
        leak_count = len(detections)
        critical_leak_count = sum(1 for d in detections if d.risk_level == "CRITICAL")
        inspection_count = len(missions)

        # Data coverage metric (0.0 to 1.0)
        coverage_pct = round(min(100.0, (len(ac_arr) + len(pr_arr) + len(fl_arr)) / 60.0 * 100.0), 1)

        return {
            "pipeline_segment_id": segment_id,
            "pipeline_meta": meta,
            "window_hours": window_hours,
            "data_coverage_pct": coverage_pct,
            "acoustic": {
                "mean_spl_db": round(mean_spl, 1),
                "peak_spl_db": round(max_spl, 1),
                "dominant_freq_hz": dominant_freq,
                "snr_db": snr_db,
                "anomaly_count": acoustic_anomalies,
                "sample_count": len(ac_arr),
            },
            "pressure": {
                "mean_bar": round(mean_pressure, 2),
                "nominal_bar": base_pressure,
                "std_bar": round(pressure_std, 2),
                "drop_count": pressure_drops,
                "fluctuation_rate": pressure_fluctuation_rate,
                "sample_count": len(pr_arr),
            },
            "flow": {
                "mean_lps": round(mean_flow, 1),
                "expected_lps": 120.0,
                "imbalance_pct": flow_imbalance_pct,
                "variance": round(flow_variance, 2),
                "sample_count": len(fl_arr),
            },
            "environmental": {
                "mean_moisture_pct": round(mean_moisture, 1),
                "peak_moisture_pct": round(max_moisture, 1),
                "is_moisture_anomalous": moisture_anomaly,
                "sample_count": len(mo_arr),
            },
            "history": {
                "total_leak_detections": leak_count,
                "critical_detections": critical_leak_count,
                "completed_inspections": inspection_count,
            },
            "is_simulated": True,
            "source": "VIRTUAL_SIMULATION_ENGINE",
        }

