"""
AI Leak Detection, Signal Processing & Ingestion Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json

from app.database.session import get_db
from app.schemas.ai import (
    SensorReadingCreate,
    SensorReadingResponse,
    SyntheticWaveformRequest,
    SyntheticWaveformResponse,
    LeakAnalyzeRequest,
    LeakAnalyzeBatchRequest,
    AiDetectionResponse,
    AiDetectionStatusUpdate,
    AiModelMetrics,
    AiHealthResponse,
)
from app.services.sensor_ingestion_service import SensorIngestionService
from app.services.signal_processing_service import SignalProcessingService
from app.services.leak_classification_service import classifier_engine
from app.services.ai_orchestration_service import AiOrchestrationService
from app.models.user import UserModel
from app.core.auth import require_viewer, require_operator


router = APIRouter()


def _format_detection(d) -> Dict[str, Any]:
    features_dict = {}
    if d.contributing_features:
        try:
            features_dict = json.loads(d.contributing_features)
        except Exception:
            features_dict = {}

    return {
        "id": d.id,
        "pipeline_segment_id": d.pipeline_segment_id,
        "anomaly_score": d.anomaly_score,
        "classification": d.classification,
        "confidence": d.confidence,
        "risk_level": d.risk_level,
        "estimated_loss_lph": d.estimated_loss_lph,
        "estimated_latitude": d.estimated_latitude,
        "estimated_longitude": d.estimated_longitude,
        "localization_uncertainty_m": d.localization_uncertainty_m,
        "localization_quality": d.localization_quality,
        "status": d.status,
        "contributing_features": features_dict,
        "risk_explanation": d.risk_explanation or "",
        "model_version": d.model_version,
        "created_at": d.created_at,
        "is_simulated": True,
        "source": d.source,
    }


@router.post("/analyze", response_model=AiDetectionResponse)
def analyze_leak_single(
    req: LeakAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Executes end-to-end multi-modal AI leak detection, anomaly scoring, risk rating,
    and TDOA localization for a target pipeline segment.
    """
    detection = AiOrchestrationService.analyze_segment(db, req)
    return _format_detection(detection)


@router.post("/analyze/batch", response_model=List[AiDetectionResponse])
def analyze_leak_batch(
    batch_req: LeakAnalyzeBatchRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Batch execution of multi-modal AI leak analysis across multiple pipeline segments.
    """
    detections = AiOrchestrationService.analyze_batch(db, batch_req)
    return [_format_detection(d) for d in detections]


@router.get("/detections", response_model=List[AiDetectionResponse])
def list_ai_detections(
    segment_id: Optional[str] = Query(None, description="Filter by pipeline segment"),
    risk_level: Optional[str] = Query(None, description="Filter by risk: LOW, MODERATE, HIGH, CRITICAL"),
    status: Optional[str] = Query(None, description="Filter by status: PENDING_REVIEW, VERIFIED_BY_OPERATOR, etc."),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Lists recent AI leak detections with optional filtering by segment, severity, and review status.
    """
    detections = AiOrchestrationService.list_detections(
        db, segment_id=segment_id, risk_level=risk_level, status=status, limit=limit
    )
    return [_format_detection(d) for d in detections]


@router.get("/detections/{detection_id}", response_model=AiDetectionResponse)
def get_ai_detection_by_id(
    detection_id: str,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Inspects complete diagnostic details for a specific AI detection record.
    """
    detection = AiOrchestrationService.get_detection_by_id(db, detection_id)
    if not detection:
        raise HTTPException(status_code=404, detail=f"AI Detection '{detection_id}' not found")
    return _format_detection(detection)


@router.patch("/detections/{detection_id}/status", response_model=AiDetectionResponse)
def update_detection_review_status(
    detection_id: str,
    status_in: AiDetectionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Human-in-the-loop operator action to verify, reject, or dispatch inspection for an AI proposed detection.
    """
    detection = AiOrchestrationService.update_detection_status(
        db, detection_id, status_in.status, status_in.operator_notes
    )
    if not detection:
        raise HTTPException(status_code=404, detail=f"AI Detection '{detection_id}' not found")
    return _format_detection(detection)


@router.post("/waveform/synthesize", response_model=SyntheticWaveformResponse)
def synthesize_acoustic_waveform(
    req: SyntheticWaveformRequest,
    current_user: UserModel = Depends(require_viewer),
):
    """
    Generates synthetic acoustic waveform and FFT spectral decomposition for UI visualization.
    """
    return SignalProcessingService.analyze_synthetic_scenario(req)


@router.post("/sensors/ingest", response_model=SensorReadingResponse)
def ingest_sensor_reading(
    reading_in: SensorReadingCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    """
    Ingests multi-modal sensor telemetry reading, validates physical bounds, and computes data quality.
    """
    record = SensorIngestionService.ingest_reading(db, reading_in)
    return record


@router.get("/models")
def get_active_models(current_user: UserModel = Depends(require_viewer)):
    """
    Lists registered active machine learning models, algorithms, and versions.
    """
    return {
        "models": [
            {
                "id": "random_forest_classifier",
                "name": "Random Forest Leak Classifier",
                "algorithm": "RandomForestClassifier",
                "version": classifier_engine.model_version,
                "classes": ["NORMAL", "LOW_LEAK_PROBABILITY", "MEDIUM_LEAK_PROBABILITY", "HIGH_LEAK_PROBABILITY"],
                "features_used": 12,
                "is_active": True,
            },
            {
                "id": "isolation_forest_anomaly",
                "name": "Isolation Forest Anomaly Engine",
                "algorithm": "IsolationForest",
                "version": "v1.1.0-isoforest",
                "purpose": "Unsupervised Multi-Sensor Outlier Scoring",
                "is_active": True,
            },
            {
                "id": "logistic_regression_calibrated",
                "name": "Multinomial Logistic Regression",
                "algorithm": "LogisticRegression",
                "version": "v1.0.0-lr",
                "purpose": "Baseline Calibrated Probabilities",
                "is_active": True,
            },
            {
                "id": "tdoa_acoustic_localization",
                "name": "Cross-Correlation TDOA Localization",
                "algorithm": "Generalized Cross-Correlation (Phase Transform)",
                "version": "v1.2.0-tdoa",
                "purpose": "Acoustic Coordinate Estimation",
                "is_active": True,
            },
        ],
        "is_simulated": True,
    }


@router.get("/models/metrics")
def get_model_evaluation_metrics(current_user: UserModel = Depends(require_viewer)):
    """
    Returns actual, un-manufactured performance metrics (accuracy, precision, recall, F1)
    for models evaluated on deterministic synthetic testing sets.
    """
    return classifier_engine.get_model_metrics()


@router.get("/health", response_model=AiHealthResponse)
def get_ai_subsystem_health(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    """
    Telemetry and health status of the AI detection and signal processing subsystem.
    """
    return AiOrchestrationService.get_ai_health(db)
