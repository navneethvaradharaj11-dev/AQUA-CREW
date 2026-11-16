"""
AQUA CREW — Pipeline Health Scoring Engine (Task 09)
Computes multi-criteria 0–100 infrastructure health index, evaluates acoustic/hydraulic stability,
identifies positive indicators, and persists health assessments.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import uuid

from sqlalchemy.orm import Session
from app.models.predictive_maintenance import PipelineHealthModel
from app.services.historical_telemetry_service import HistoricalTelemetryService
from app.websocket.connection_manager import ws_manager


class PipelineHealthService:
    @classmethod
    def calculate_health(
        cls,
        db: Session,
        segment_id: str,
        lookback_hours: int = 24,
    ) -> PipelineHealthModel:
        """
        Calculates and persists pipeline health assessment for a pipeline segment.
        """
        telemetry = HistoricalTelemetryService.aggregate_telemetry(db, segment_id, lookback_hours)
        meta = telemetry["pipeline_meta"]
        ac = telemetry["acoustic"]
        pr = telemetry["pressure"]
        fl = telemetry["flow"]
        env = telemetry["environmental"]
        hist = telemetry["history"]

        # Base Health Score
        score = 100.0
        contributing_factors: Dict[str, float] = {}
        positive_indicators: List[str] = []

        # 1. Acoustic Stability Deduction
        ac_penalty = 0.0
        if ac["mean_spl_db"] >= 75.0:
            ac_penalty += 22.0
            contributing_factors["acoustic_high_spl"] = 22.0
        elif ac["mean_spl_db"] >= 60.0:
            ac_penalty += 12.0
            contributing_factors["acoustic_elevated_spl"] = 12.0
        elif ac["mean_spl_db"] >= 50.0:
            ac_penalty += 5.0
            contributing_factors["acoustic_minor_noise"] = 5.0
        else:
            positive_indicators.append(f"Acoustic emissions low ({ac['mean_spl_db']} dB SPL baseline)")

        if ac["anomaly_count"] > 0:
            anom_p = min(15.0, ac["anomaly_count"] * 2.5)
            ac_penalty += anom_p
            contributing_factors["acoustic_transient_spikes"] = anom_p

        acoustic_score = max(0.0, round(100.0 - ac_penalty * 2.5, 1))

        # 2. Pressure Stability Deduction
        pr_penalty = 0.0
        pressure_drop = max(0.0, pr["nominal_bar"] - pr["mean_bar"])
        if pressure_drop >= 1.0:
            pr_penalty += 25.0
            contributing_factors["severe_pressure_loss"] = 25.0
        elif pressure_drop >= 0.5:
            pr_penalty += 14.0
            contributing_factors["moderate_pressure_loss"] = 14.0
        elif pressure_drop < 0.2:
            positive_indicators.append(f"Operating pressure nominal ({pr['mean_bar']} bar, stable)")

        if pr["std_bar"] >= 0.35:
            pr_penalty += 10.0
            contributing_factors["hydraulic_pressure_instability"] = 10.0

        if pr["drop_count"] > 2:
            dr_p = min(12.0, pr["drop_count"] * 2.0)
            pr_penalty += dr_p
            contributing_factors["recurrent_pressure_dips"] = dr_p

        pressure_score = max(0.0, round(100.0 - pr_penalty * 2.2, 1))

        # 3. Flow Stability Deduction
        fl_penalty = 0.0
        if fl["imbalance_pct"] >= 20.0:
            fl_penalty += 15.0
            contributing_factors["flow_mass_imbalance"] = 15.0
        elif fl["imbalance_pct"] >= 10.0:
            fl_penalty += 8.0
            contributing_factors["minor_flow_deviation"] = 8.0
        else:
            positive_indicators.append("Flow mass balance continuous and balanced")

        flow_score = max(0.0, round(100.0 - fl_penalty * 4.0, 1))

        # 4. Environmental & Moisture Deduction
        env_penalty = 0.0
        if env["mean_moisture_pct"] >= 50.0:
            env_penalty += 18.0
            contributing_factors["high_ground_saturation"] = 18.0
        elif env["mean_moisture_pct"] >= 30.0:
            env_penalty += 8.0
            contributing_factors["elevated_soil_moisture"] = 8.0
        else:
            positive_indicators.append("Surrounding soil moisture dry and stable")

        moisture_score = max(0.0, round(100.0 - env_penalty * 3.5, 1))

        # 5. History & Material Vulnerability Multiplier
        hist_penalty = min(25.0, hist["total_leak_detections"] * 8.0)
        if hist_penalty > 0:
            contributing_factors["historical_leak_recurrence"] = hist_penalty

        mat_lower = meta.get("material", "").lower()
        mat_mult = 1.15 if "concrete" in mat_lower else 1.1 if "iron" in mat_lower else 0.9

        total_deductions = (ac_penalty + pr_penalty + fl_penalty + env_penalty + hist_penalty) * mat_mult
        score = max(0.0, min(100.0, round(100.0 - total_deductions, 1)))

        # Categorization
        if score >= 90.0:
            category = "EXCELLENT"
        elif score >= 75.0:
            category = "GOOD"
        elif score >= 50.0:
            category = "FAIR"
        elif score >= 25.0:
            category = "POOR"
        else:
            category = "CRITICAL"

        coverage = telemetry["data_coverage_pct"]
        confidence = 0.95 if coverage >= 80.0 else 0.85 if coverage >= 50.0 else 0.65

        # Rationale Narrative
        explanation = (
            f"Pipeline {segment_id} classified as {category} with health index {score:.0f}/100. "
            f"Acoustic stability: {acoustic_score:.0f}%, Pressure stability: {pressure_score:.0f}%, "
            f"Flow balance: {flow_score:.0f}%, Soil moisture: {moisture_score:.0f}%. "
            f"Data coverage: {coverage:.0f}% (Confidence: {confidence * 100:.0f}%)."
        )

        assessment_id = f"HLT-2026-{uuid.uuid4().hex[:6].upper()}"
        record = PipelineHealthModel(
            id=assessment_id,
            pipeline_segment_id=segment_id,
            health_score=score,
            health_category=category,
            acoustic_stability_score=acoustic_score,
            pressure_stability_score=pressure_score,
            flow_stability_score=flow_score,
            moisture_anomaly_score=moisture_score,
            data_coverage_pct=coverage,
            confidence=confidence,
            contributing_factors=json.dumps(contributing_factors),
            positive_indicators=json.dumps(positive_indicators),
            explanation=explanation,
            assessed_at=datetime.now(timezone.utc),
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # Broadcast event
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast({
                "type": "PIPELINE_HEALTH_UPDATED",
                "pipeline_segment_id": segment_id,
                "health_score": score,
                "health_category": category,
                "timestamp": record.assessed_at.isoformat(),
                "is_simulated": True,
            }))
        except RuntimeError:
            pass

        return record

    @classmethod
    def get_latest_health(cls, db: Session, segment_id: str) -> Optional[PipelineHealthModel]:
        return db.query(PipelineHealthModel).filter(
            PipelineHealthModel.pipeline_segment_id == segment_id
        ).order_by(PipelineHealthModel.assessed_at.desc()).first()

    @classmethod
    def list_health_assessments(cls, db: Session, limit: int = 50) -> List[PipelineHealthModel]:
        return db.query(PipelineHealthModel).order_by(PipelineHealthModel.assessed_at.desc()).limit(limit).all()

