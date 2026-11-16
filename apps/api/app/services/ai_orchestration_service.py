"""
AI Leak Detection Orchestration Service
Coordinates ingestion, feature extraction, ML inference, risk rating, and real-time event dispatch.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import uuid
import asyncio

from sqlalchemy.orm import Session
from app.models.ai_detection import AiDetectionModel
from app.schemas.ai import LeakAnalyzeRequest, LeakAnalyzeBatchRequest, AiDetectionResponse
from app.repositories.pipeline_repository import PipelineRepository, DEFAULT_PIPELINES
from app.services.feature_extraction_service import FeatureExtractionService
from app.services.anomaly_detection_service import anomaly_engine
from app.services.leak_classification_service import classifier_engine
from app.services.risk_assessment_service import RiskAssessmentService
from app.services.leak_localization_service import LeakLocalizationService
from app.websocket.connection_manager import ws_manager


class AiOrchestrationService:
    @staticmethod
    def _get_pipe_metadata(db: Session, segment_id: str) -> Dict[str, Any]:
        """
        Retrieves segment metadata from database or default seed list.
        """
        seg = PipelineRepository.get_by_id(db, segment_id)
        if seg:
            return {
                "id": seg.id,
                "name": seg.name,
                "category": seg.category,
                "material": seg.material,
                "diameter_mm": seg.diameter_mm,
                "length_m": seg.length_m,
                "coordinates": seg.coordinates_json,
                "operating_pressure_bar": round((seg.nominal_pressure_psi or 65.0) * 0.0689476, 2),
            }

        # Check default list
        for d in DEFAULT_PIPELINES:
            if d["id"] == segment_id:
                return {
                    "id": d["id"],
                    "name": d["name"],
                    "category": d["category"],
                    "material": d["material"],
                    "diameter_mm": d["diameter_mm"],
                    "length_m": d["length_m"],
                    "coordinates": d["coordinates"],
                    "operating_pressure_bar": round(d.get("nominal_pressure_psi", 65.0) * 0.0689476, 2),
                }

        # Fallback default
        return {
            "id": segment_id,
            "name": f"Pipeline Segment {segment_id}",
            "category": "secondary",
            "material": "ductile_iron",
            "diameter_mm": 300,
            "length_m": 1200.0,
            "coordinates": [[-74.0150, 40.7100], [-74.0060, 40.7128]],
            "operating_pressure_bar": 4.5,
        }

    @classmethod
    def analyze_segment(cls, db: Session, req: LeakAnalyzeRequest) -> AiDetectionModel:
        """
        Executes complete multi-modal AI leak analysis pipeline for a pipeline segment.
        """
        pipe_meta = cls._get_pipe_metadata(db, req.pipeline_segment_id)

        # 1. Feature Extraction
        vector, named_features = FeatureExtractionService.extract_feature_vector(req, pipe_meta)

        # 2. Anomaly Detection (Isolation Forest)
        anomaly_score, is_anomaly = anomaly_engine.compute_anomaly_score(vector)

        # 3. Supervised Classification (Random Forest)
        classification, confidence, attributions = classifier_engine.classify_features(vector, named_features)

        # 4. Severity & Risk Assessment
        risk_level, loss_lph, explanation = RiskAssessmentService.evaluate_risk(
            classification=classification,
            confidence=confidence,
            anomaly_score=anomaly_score,
            features=named_features,
            pipe_meta=pipe_meta,
        )

        # 5. Localization (TDOA)
        # Use acoustic SNR from features or default 12 dB
        snr = float(named_features.get("snr_db", 14.0)) if "snr_db" in named_features else 14.0
        est_lat, est_lng, uncertainty_m, loc_quality, loc_method = LeakLocalizationService.estimate_location_tdoa(
            pipe_meta=pipe_meta,
            snr_db=snr,
        )

        # 6. Database Persistence
        detection_id = f"DET-{datetime.now(timezone.utc).strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
        detection = AiDetectionModel(
            id=detection_id,
            pipeline_segment_id=req.pipeline_segment_id,
            anomaly_score=anomaly_score,
            classification=classification,
            confidence=confidence,
            risk_level=risk_level,
            estimated_loss_lph=loss_lph,
            estimated_latitude=est_lat,
            estimated_longitude=est_lng,
            localization_uncertainty_m=uncertainty_m,
            localization_quality=loc_quality,
            status="PENDING_REVIEW",
            contributing_features=json.dumps(attributions),
            risk_explanation=explanation,
            model_version=classifier_engine.model_version,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        )
        db.add(detection)
        db.commit()
        db.refresh(detection)

        # 7. WebSocket Event Broadcast (Non-blocking)
        try:
            loop = asyncio.get_running_loop()
            event_payload = {
                "type": "LEAK_CLASSIFICATION_COMPLETED",
                "detection_id": detection.id,
                "pipeline_segment_id": detection.pipeline_segment_id,
                "classification": detection.classification,
                "confidence": detection.confidence,
                "anomaly_score": detection.anomaly_score,
                "risk_level": detection.risk_level,
                "estimated_loss_lph": detection.estimated_loss_lph,
                "location": {
                    "latitude": detection.estimated_latitude,
                    "longitude": detection.estimated_longitude,
                    "uncertainty_m": detection.localization_uncertainty_m,
                    "quality": detection.localization_quality,
                },
                "status": detection.status,
                "timestamp": detection.created_at.isoformat(),
                "is_simulated": True,
            }
            loop.create_task(ws_manager.broadcast(event_payload))
        except RuntimeError:
            pass

        return detection

    @classmethod
    def analyze_batch(cls, db: Session, batch_req: LeakAnalyzeBatchRequest) -> List[AiDetectionModel]:
        results = []
        for req in batch_req.requests:
            res = cls.analyze_segment(db, req)
            results.append(res)
        return results

    @staticmethod
    def list_detections(
        db: Session,
        segment_id: Optional[str] = None,
        risk_level: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[AiDetectionModel]:
        q = db.query(AiDetectionModel)
        if segment_id:
            q = q.filter(AiDetectionModel.pipeline_segment_id == segment_id)
        if risk_level:
            q = q.filter(AiDetectionModel.risk_level == risk_level.upper())
        if status:
            q = q.filter(AiDetectionModel.status == status.upper())
        return q.order_by(AiDetectionModel.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_detection_by_id(db: Session, detection_id: str) -> Optional[AiDetectionModel]:
        return db.query(AiDetectionModel).filter(AiDetectionModel.id == detection_id).first()

    @staticmethod
    def update_detection_status(
        db: Session, detection_id: str, new_status: str, notes: Optional[str] = None
    ) -> Optional[AiDetectionModel]:
        detection = db.query(AiDetectionModel).filter(AiDetectionModel.id == detection_id).first()
        if not detection:
            return None

        detection.status = new_status.upper()
        if notes:
            explanation = detection.risk_explanation or ""
            detection.risk_explanation = f"{explanation} | Operator Notes: {notes}"
        detection.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(detection)
        return detection

    @staticmethod
    def get_ai_health(db: Session) -> Dict[str, Any]:
        total = db.query(AiDetectionModel).count()
        unreviewed = db.query(AiDetectionModel).filter(AiDetectionModel.status == "PENDING_REVIEW").count()
        high_crit = (
            db.query(AiDetectionModel)
            .filter(AiDetectionModel.risk_level.in_(["HIGH", "CRITICAL"]))
            .count()
        )
        return {
            "status": "HEALTHY",
            "active_models": [
                "RandomForestClassifier (v1.2.0)",
                "IsolationForest (Anomaly Engine)",
                "LogisticRegression (Calibrated)",
                "TDOA Acoustic Localization",
            ],
            "total_detections": total,
            "unreviewed_detections": unreviewed,
            "high_critical_count": high_crit,
            "is_simulated": True,
        }
