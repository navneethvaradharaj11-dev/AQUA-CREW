"""
AQUA CREW — Predictive Failure Risk Engine (Task 09)
Estimates multi-horizon failure probabilities (24h, 7d, 30d), evaluates structural burst/leak risk,
computes explainable factor contributions, and broadcasts predictive alerts.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import uuid

from sqlalchemy.orm import Session
from app.models.predictive_maintenance import PredictiveRiskModel
from app.services.pipeline_health_service import PipelineHealthService
from app.services.trend_analysis_service import TrendAnalysisService
from app.services.historical_telemetry_service import HistoricalTelemetryService
from app.websocket.connection_manager import ws_manager


class PredictiveRiskService:
    MODEL_VERSION = "v1.0.0-rf-gradient-predictive"

    @classmethod
    def evaluate_predictive_risk(
        cls,
        db: Session,
        segment_id: str,
        lookback_hours: int = 24,
    ) -> PredictiveRiskModel:
        """
        Computes multi-horizon failure probabilities for a pipeline segment.
        """
        telemetry = HistoricalTelemetryService.aggregate_telemetry(db, segment_id, lookback_hours)
        health_rec = PipelineHealthService.get_latest_health(db, segment_id)
        if not health_rec:
            health_rec = PipelineHealthService.calculate_health(db, segment_id, lookback_hours)

        trend_rec = TrendAnalysisService.get_latest_trend(db, segment_id)
        if not trend_rec:
            trend_rec = TrendAnalysisService.analyze_trend(db, segment_id, window_days=30)

        ac = telemetry["acoustic"]
        pr = telemetry["pressure"]
        fl = telemetry["flow"]
        env = telemetry["environmental"]
        hist = telemetry["history"]
        meta = telemetry["pipeline_meta"]

        health_deficit = max(0.0, 100.0 - health_rec.health_score) / 100.0
        pressure_drop = max(0.0, pr["nominal_bar"] - pr["mean_bar"])
        slope_penalty = max(0.0, -trend_rec.health_slope_per_day) * 0.15

        contributing_factors: Dict[str, float] = {}

        # ---------------------------------------------------------------------
        # 1. 24-Hour Horizon Failure Probability (Acute Transients)
        # ---------------------------------------------------------------------
        acute_risk = 0.01  # Baseline background failure rate
        if pressure_drop >= 1.0:
            acute_risk += 0.35
            contributing_factors["acute_pressure_drop_loss"] = 0.35
        elif pressure_drop >= 0.5:
            acute_risk += 0.15
            contributing_factors["moderate_pressure_loss"] = 0.15

        if ac["mean_spl_db"] >= 75.0:
            acute_risk += 0.30
            contributing_factors["high_acoustic_spl_emissions"] = 0.30
        elif ac["mean_spl_db"] >= 65.0:
            acute_risk += 0.12
            contributing_factors["moderate_acoustic_hiss"] = 0.12

        if pr["std_bar"] >= 0.4:
            acute_risk += 0.10
            contributing_factors["pressure_water_hammer_variance"] = 0.10

        p_24h = min(0.95, round(acute_risk, 3))

        # ---------------------------------------------------------------------
        # 2. 7-Day Horizon Failure Probability (Cumulative Degradation)
        # ---------------------------------------------------------------------
        short_term_risk = p_24h + (health_deficit * 0.40) + slope_penalty
        if fl["imbalance_pct"] >= 15.0:
            short_term_risk += 0.12
            contributing_factors["flow_mass_deficit_trend"] = 0.12

        if env["is_moisture_anomalous"]:
            short_term_risk += 0.15
            contributing_factors["ground_saturation_anomaly"] = 0.15

        p_7d = min(0.98, max(p_24h, round(short_term_risk, 3)))

        # ---------------------------------------------------------------------
        # 3. 30-Day Horizon Failure Probability (Structural Wear & Age)
        # ---------------------------------------------------------------------
        medium_term_risk = p_7d + (health_deficit * 0.25) + (hist["total_leak_detections"] * 0.08)
        mat_lower = meta.get("material", "").lower()
        if "concrete" in mat_lower:
            medium_term_risk += 0.08
            contributing_factors["material_cylinder_corrosion_vulnerability"] = 0.08
        elif "iron" in mat_lower:
            medium_term_risk += 0.05
            contributing_factors["graphitization_wear"] = 0.05

        p_30d = min(0.99, max(p_7d, round(medium_term_risk, 3)))

        # Overall Qualitative Risk Level
        if p_7d >= 0.70 or p_24h >= 0.50:
            overall_risk = "CRITICAL"
        elif p_7d >= 0.40 or p_30d >= 0.65:
            overall_risk = "HIGH"
        elif p_30d >= 0.25:
            overall_risk = "MODERATE"
        else:
            overall_risk = "LOW"

        leak_prob = round(min(0.95, (p_7d * 0.8) + (health_deficit * 0.3)), 3)
        burst_risk = round(min(0.85, (p_24h * 0.6) + (pr["std_bar"] * 0.3)), 3)

        explanation = (
            f"Segment {segment_id} failure probability: {p_24h * 100:.1f}% (24h), "
            f"{p_7d * 100:.1f}% (7d), {p_30d * 100:.1f}% (30d). "
            f"Overall Risk Category: {overall_risk}. Leak Probability: {leak_prob * 100:.1f}%, "
            f"Burst/Rupture Risk: {burst_risk * 100:.1f}%. Current Trend: {trend_rec.trend_direction}."
        )

        pred_id = f"PRD-2026-{uuid.uuid4().hex[:6].upper()}"
        record = PredictiveRiskModel(
            id=pred_id,
            pipeline_segment_id=segment_id,
            failure_prob_24h=p_24h,
            failure_prob_7d=p_7d,
            failure_prob_30d=p_30d,
            overall_risk_level=overall_risk,
            leak_probability=leak_prob,
            burst_rupture_risk=burst_risk,
            model_version=cls.MODEL_VERSION,
            confidence=0.88,
            uncertainty_margin=0.06,
            contributing_factors=json.dumps(contributing_factors),
            risk_explanation=explanation,
            assessed_at=datetime.now(timezone.utc),
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # Broadcast events
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast({
                "type": "PREDICTIVE_RISK_GENERATED",
                "pipeline_segment_id": segment_id,
                "overall_risk_level": overall_risk,
                "failure_prob_24h": p_24h,
                "failure_prob_7d": p_7d,
                "failure_prob_30d": p_30d,
                "timestamp": record.assessed_at.isoformat(),
                "is_simulated": True,
            }))
            if overall_risk in ["HIGH", "CRITICAL"]:
                loop.create_task(ws_manager.broadcast({
                    "type": "HIGH_RISK_PIPELINE_IDENTIFIED",
                    "pipeline_segment_id": segment_id,
                    "overall_risk_level": overall_risk,
                    "explanation": explanation,
                    "timestamp": record.assessed_at.isoformat(),
                    "is_simulated": True,
                }))
        except RuntimeError:
            pass

        return record

    @classmethod
    def get_latest_risk(cls, db: Session, segment_id: str) -> Optional[PredictiveRiskModel]:
        return db.query(PredictiveRiskModel).filter(
            PredictiveRiskModel.pipeline_segment_id == segment_id
        ).order_by(PredictiveRiskModel.assessed_at.desc()).first()

    @classmethod
    def list_risk_assessments(cls, db: Session, limit: int = 50) -> List[PredictiveRiskModel]:
        return db.query(PredictiveRiskModel).order_by(PredictiveRiskModel.assessed_at.desc()).limit(limit).all()

