"""
AQUA CREW — Maintenance Recommendation Engine & Dispatch Integration (Task 09)
Generates explainable maintenance directives based on health indices, predictive risk forecasts,
and degradation trends, with human-in-the-loop review and Task 08 Autonomous Dispatch linkage.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import uuid

from sqlalchemy.orm import Session
from app.models.predictive_maintenance import (
    MaintenanceRecommendationModel,
    PipelineHealthModel,
    PredictiveRiskModel,
    HistoricalTrendModel,
)
from app.models.ai_detection import AiDetectionModel
from app.services.pipeline_health_service import PipelineHealthService
from app.services.predictive_risk_service import PredictiveRiskService
from app.services.trend_analysis_service import TrendAnalysisService
from app.services.historical_telemetry_service import HistoricalTelemetryService
from app.services.mission_planning_service import MissionPlanningService
from app.websocket.connection_manager import ws_manager
from app.core.exceptions import AquaCrewException


class MaintenanceRecommendationService:
    @classmethod
    def generate_recommendation(
        cls,
        db: Session,
        segment_id: str,
        force_regenerate: bool = False,
    ) -> MaintenanceRecommendationModel:
        """
        Synthesizes health score, risk forecast, and trends into an actionable maintenance recommendation.
        Prevents duplicate active recommendations for the same segment.
        """
        if not force_regenerate:
            existing = db.query(MaintenanceRecommendationModel).filter(
                MaintenanceRecommendationModel.pipeline_segment_id == segment_id,
                MaintenanceRecommendationModel.status.in_(["PENDING_REVIEW", "ACKNOWLEDGED"])
            ).first()
            if existing:
                return existing

        health = PipelineHealthService.get_latest_health(db, segment_id)
        if not health:
            health = PipelineHealthService.calculate_health(db, segment_id)

        risk = PredictiveRiskService.get_latest_risk(db, segment_id)
        if not risk:
            risk = PredictiveRiskService.evaluate_predictive_risk(db, segment_id)

        trend = TrendAnalysisService.get_latest_trend(db, segment_id)
        if not trend:
            trend = TrendAnalysisService.analyze_trend(db, segment_id)

        telemetry = HistoricalTelemetryService.aggregate_telemetry(db, segment_id)

        h_score = health.health_score
        r_level = risk.overall_risk_level
        p_24h = risk.failure_prob_24h
        t_dir = trend.trend_direction

        # Recommendation Decision Matrix
        if r_level == "CRITICAL" or h_score < 25.0 or p_24h >= 0.50:
            action = "DISPATCH_INSPECTION_ROVER"
            urgency = "CRITICAL"
            timeframe_days = 1
            explanation = (
                f"Critical structural risk: Health score {h_score:.0f}/100 with 24h failure probability of {p_24h * 100:.1f}%. "
                f"Trend is {t_dir}. Autonomous crawler inspection recommended immediately to avert pipe rupture."
            )
        elif r_level == "HIGH" or h_score < 50.0 or t_dir == "RAPIDLY_DETERIORATING":
            action = "DISPATCH_INSPECTION_ROVER"
            urgency = "HIGH"
            timeframe_days = 2
            explanation = (
                f"High infrastructure risk: Health score {h_score:.0f}/100 with persistent hydraulic/acoustic degradation. "
                f"Autonomous crawler inspection recommended within 48 hours for localized acoustic verification."
            )
        elif telemetry["acoustic"]["anomaly_count"] > 2:
            action = "SCHEDULE_ACOUSTIC_INSPECTION"
            urgency = "MEDIUM"
            timeframe_days = 7
            explanation = (
                f"Elevated acoustic anomaly count ({telemetry['acoustic']['anomaly_count']} spikes). "
                f"Acoustic hydrophone sweep recommended within 7 days."
            )
        elif telemetry["pressure"]["drop_count"] > 2 or telemetry["pressure"]["std_bar"] >= 0.35:
            action = "SCHEDULE_PRESSURE_INSPECTION"
            urgency = "MEDIUM"
            timeframe_days = 7
            explanation = (
                f"Hydraulic pressure transient instability detected (std {telemetry['pressure']['std_bar']} bar). "
                f"Pressure valve manifold inspection recommended within 7 days."
            )
        elif h_score < 75.0 or t_dir == "DETERIORATING":
            action = "INCREASE_SENSOR_MONITORING"
            urgency = "MEDIUM"
            timeframe_days = 14
            explanation = (
                f"Moderate infrastructure wear: Health score {h_score:.0f}/100. "
                f"Recommend increasing telemetry polling frequency to track micro-degradation."
            )
        else:
            action = "CONTINUE_MONITORING"
            urgency = "ROUTINE"
            timeframe_days = 30
            explanation = (
                f"Nominal operating parameters: Health score {h_score:.0f}/100 ({health.health_category}). "
                f"Continue routine background telemetry monitoring."
            )

        evidence = {
            "health_score": h_score,
            "health_category": health.health_category,
            "overall_risk_level": r_level,
            "failure_prob_24h": p_24h,
            "failure_prob_7d": risk.failure_prob_7d,
            "trend_direction": t_dir,
            "mean_spl_db": telemetry["acoustic"]["mean_spl_db"],
            "mean_pressure_bar": telemetry["pressure"]["mean_bar"],
            "flow_imbalance_pct": telemetry["flow"]["imbalance_pct"],
            "soil_moisture_pct": telemetry["environmental"]["mean_moisture_pct"],
        }

        rec_id = f"MNT-2026-{uuid.uuid4().hex[:6].upper()}"
        record = MaintenanceRecommendationModel(
            id=rec_id,
            pipeline_segment_id=segment_id,
            health_score=h_score,
            predicted_risk=r_level,
            urgency=urgency,
            recommended_action=action,
            timeframe_days=timeframe_days,
            status="PENDING_REVIEW",
            explanation=explanation,
            sensor_evidence=json.dumps(evidence),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        try:
            import asyncio
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast({
                "type": "MAINTENANCE_RECOMMENDATION_CREATED",
                "recommendation_id": record.id,
                "pipeline_segment_id": segment_id,
                "recommended_action": action,
                "urgency": urgency,
                "timestamp": record.created_at.isoformat(),
                "is_simulated": True,
            }))
        except RuntimeError:
            pass

        return record

    @classmethod
    def review_recommendation(
        cls,
        db: Session,
        recommendation_id: str,
        action: str,  # ACKNOWLEDGE, DISMISS, DISPATCH
        operator_id: str = "OPERATOR_CHIEF",
        operator_notes: Optional[str] = None,
    ) -> MaintenanceRecommendationModel:
        rec = db.query(MaintenanceRecommendationModel).filter(
            MaintenanceRecommendationModel.id == recommendation_id
        ).first()

        if not rec:
            raise AquaCrewException(
                status_code=404,
                code="RECOMMENDATION_NOT_FOUND",
                message=f"Maintenance recommendation '{recommendation_id}' not found.",
            )

        action_upper = action.upper()
        if action_upper not in ["ACKNOWLEDGE", "DISMISS", "DISPATCH"]:
            raise AquaCrewException(
                status_code=400,
                code="INVALID_REVIEW_ACTION",
                message=f"Action '{action}' is invalid. Must be ACKNOWLEDGE, DISMISS, or DISPATCH.",
            )

        if action_upper == "ACKNOWLEDGE":
            rec.status = "ACKNOWLEDGED"
        elif action_upper == "DISMISS":
            rec.status = "DISMISSED"
        elif action_upper == "DISPATCH":
            rec.status = "DISPATCHED"

            # Integration with Task 08 Autonomous Dispatch:
            # Create synthetic AI detection record for preventive inspection if none exists
            detection = db.query(AiDetectionModel).filter(
                AiDetectionModel.pipeline_segment_id == rec.pipeline_segment_id
            ).order_by(AiDetectionModel.created_at.desc()).first()

            if not detection:
                det_id = f"DET-PREV-{uuid.uuid4().hex[:6].upper()}"
                detection = AiDetectionModel(
                    id=det_id,
                    pipeline_segment_id=rec.pipeline_segment_id,
                    anomaly_score=0.82,
                    classification="MEDIUM_LEAK_PROBABILITY",
                    confidence=0.88,
                    risk_level=rec.urgency if rec.urgency in ["HIGH", "CRITICAL"] else "HIGH",
                    estimated_loss_lph=250.0,
                    status="PENDING_REVIEW",
                    risk_explanation=f"Preventive inspection dispatched from maintenance recommendation {rec.id}",
                    model_version="v1.0.0-preventive-dispatch",
                    is_simulated=True,
                    source="VIRTUAL_SIMULATION_ENGINE",
                )
                db.add(detection)
                db.commit()
                db.refresh(detection)

            # Generate formal Task 08 Mission Recommendation
            mission_rec = MissionPlanningService.plan_mission_for_detection(
                db=db,
                detection_id=detection.id,
                priority_override=rec.urgency,
            )
            rec.dispatched_mission_id = mission_rec.id

        rec.reviewed_by = operator_id
        rec.operator_notes = operator_notes
        rec.reviewed_at = datetime.now(timezone.utc)
        rec.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rec)

        try:
            import asyncio
            loop = asyncio.get_running_loop()
            loop.create_task(ws_manager.broadcast({
                "type": "MAINTENANCE_RECOMMENDATION_REVIEWED",
                "recommendation_id": rec.id,
                "status": rec.status,
                "operator_id": operator_id,
                "dispatched_mission_id": rec.dispatched_mission_id,
                "timestamp": rec.updated_at.isoformat(),
                "is_simulated": True,
            }))
        except RuntimeError:
            pass

        return rec

    @classmethod
    def list_recommendations(
        cls,
        db: Session,
        status: Optional[str] = None,
        urgency: Optional[str] = None,
        limit: int = 50,
    ) -> List[MaintenanceRecommendationModel]:
        q = db.query(MaintenanceRecommendationModel)
        if status:
            q = q.filter(MaintenanceRecommendationModel.status == status.upper())
        if urgency:
            q = q.filter(MaintenanceRecommendationModel.urgency == urgency.upper())
        return q.order_by(MaintenanceRecommendationModel.created_at.desc()).limit(limit).all()

    @classmethod
    def get_recommendation_by_id(cls, db: Session, rec_id: str) -> Optional[MaintenanceRecommendationModel]:
        return db.query(MaintenanceRecommendationModel).filter(MaintenanceRecommendationModel.id == rec_id).first()

