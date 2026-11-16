"""
AQUA CREW — Predictive Maintenance & Infrastructure Health REST Endpoints (Task 09)
Provides versioned endpoints for pipeline health scoring, predictive failure forecasting,
temporal trend analysis, maintenance recommendations, and ML model evaluation metrics.
"""
from fastapi import APIRouter, Depends, Query, Path, Body, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json

from app.database.session import get_db
from app.schemas.predictive_maintenance import (
    PipelineHealthResponse,
    HealthAnalyzeRequest,
    PredictiveRiskResponse,
    PredictiveRiskAnalyzeRequest,
    HistoricalTrendResponse,
    MaintenanceRecommendationResponse,
    MaintenanceReviewRequest,
    MaintenanceModelInfo,
    PredictiveMaintenanceOverview,
)
from app.services.pipeline_health_service import PipelineHealthService
from app.services.predictive_risk_service import PredictiveRiskService
from app.services.trend_analysis_service import TrendAnalysisService
from app.services.maintenance_recommendation_service import MaintenanceRecommendationService
from app.services.historical_telemetry_service import HistoricalTelemetryService
from app.repositories.pipeline_repository import PipelineRepository, DEFAULT_PIPELINES
from app.models.predictive_maintenance import (
    PipelineHealthModel,
    PredictiveRiskModel,
    HistoricalTrendModel,
    MaintenanceRecommendationModel,
)
from app.core.exceptions import AquaCrewException
from app.models.user import UserModel
from app.core.auth import require_viewer, require_operator

router = APIRouter()


def _format_health(h: PipelineHealthModel) -> PipelineHealthResponse:
    factors = json.loads(h.contributing_factors) if h.contributing_factors else {}
    indicators = json.loads(h.positive_indicators) if h.positive_indicators else []
    return PipelineHealthResponse(
        id=h.id,
        pipeline_segment_id=h.pipeline_segment_id,
        health_score=h.health_score,
        health_category=h.health_category,
        acoustic_stability_score=h.acoustic_stability_score,
        pressure_stability_score=h.pressure_stability_score,
        flow_stability_score=h.flow_stability_score,
        moisture_anomaly_score=h.moisture_anomaly_score,
        data_coverage_pct=h.data_coverage_pct,
        confidence=h.confidence,
        contributing_factors=factors,
        positive_indicators=indicators,
        explanation=h.explanation or "",
        assessed_at=h.assessed_at,
        is_simulated=h.is_simulated,
        source=h.source,
    )


def _format_risk(r: PredictiveRiskModel) -> PredictiveRiskResponse:
    factors = json.loads(r.contributing_factors) if r.contributing_factors else {}
    return PredictiveRiskResponse(
        id=r.id,
        pipeline_segment_id=r.pipeline_segment_id,
        failure_prob_24h=r.failure_prob_24h,
        failure_prob_7d=r.failure_prob_7d,
        failure_prob_30d=r.failure_prob_30d,
        overall_risk_level=r.overall_risk_level,
        leak_probability=r.leak_probability,
        burst_rupture_risk=r.burst_rupture_risk,
        model_version=r.model_version,
        confidence=r.confidence,
        uncertainty_margin=r.uncertainty_margin,
        contributing_factors=factors,
        risk_explanation=r.risk_explanation or "",
        assessed_at=r.assessed_at,
        is_simulated=r.is_simulated,
        source=r.source,
    )


def _format_trend(t: HistoricalTrendModel) -> HistoricalTrendResponse:
    points = json.loads(t.time_series_points_json) if t.time_series_points_json else []
    return HistoricalTrendResponse(
        id=t.id,
        pipeline_segment_id=t.pipeline_segment_id,
        trend_direction=t.trend_direction,
        health_slope_per_day=t.health_slope_per_day,
        pressure_variance=t.pressure_variance,
        flow_anomaly_rate=t.flow_anomaly_rate,
        acoustic_emission_count=t.acoustic_emission_count,
        historical_leak_count=t.historical_leak_count,
        window_days=t.window_days,
        time_series_points=points,
        assessed_at=t.assessed_at,
        is_simulated=t.is_simulated,
        source=t.source,
    )


def _format_recommendation(m: MaintenanceRecommendationModel) -> MaintenanceRecommendationResponse:
    evidence = json.loads(m.sensor_evidence) if m.sensor_evidence else {}
    return MaintenanceRecommendationResponse(
        id=m.id,
        pipeline_segment_id=m.pipeline_segment_id,
        health_score=m.health_score,
        predicted_risk=m.predicted_risk,
        urgency=m.urgency,
        recommended_action=m.recommended_action,
        timeframe_days=m.timeframe_days,
        status=m.status,
        explanation=m.explanation or "",
        sensor_evidence=evidence,
        operator_notes=m.operator_notes,
        reviewed_by=m.reviewed_by,
        reviewed_at=m.reviewed_at,
        dispatched_mission_id=m.dispatched_mission_id,
        created_at=m.created_at,
        is_simulated=m.is_simulated,
        source=m.source,
    )


# ==============================================================================
# 1. OVERVIEW & HEALTH CHECK
# ==============================================================================

@router.get("/overview", response_model=PredictiveMaintenanceOverview, summary="Get high-level infrastructure health summary")
def get_maintenance_overview(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    pipes = PipelineRepository.get_all(db)
    if not pipes:
        pipes = DEFAULT_PIPELINES

    total_segments = len(pipes)
    counts = {"EXCELLENT": 0, "GOOD": 0, "FAIR": 0, "POOR": 0, "CRITICAL": 0, "INSUFFICIENT_DATA": 0}
    scores: List[float] = []
    high_risk_count = 0

    for p in pipes:
        seg_id = p.id if hasattr(p, "id") else p.get("id")
        h = PipelineHealthService.get_latest_health(db, seg_id)
        if not h:
            h = PipelineHealthService.calculate_health(db, seg_id)
        cat = h.health_category
        counts[cat] = counts.get(cat, 0) + 1
        scores.append(h.health_score)
        if cat in ["POOR", "CRITICAL"]:
            high_risk_count += 1

    pending_recs = db.query(MaintenanceRecommendationModel).filter(
        MaintenanceRecommendationModel.status == "PENDING_REVIEW"
    ).count()

    avg_score = round(float(sum(scores) / len(scores)), 1) if scores else 80.0

    return PredictiveMaintenanceOverview(
        total_segments_monitored=total_segments,
        excellent_count=counts["EXCELLENT"],
        good_count=counts["GOOD"],
        fair_count=counts["FAIR"],
        poor_count=counts["POOR"],
        critical_count=counts["CRITICAL"],
        insufficient_data_count=counts["INSUFFICIENT_DATA"],
        average_health_score=avg_score,
        high_risk_segment_count=high_risk_count,
        pending_recommendation_count=pending_recs,
        timestamp=datetime.now(timezone.utc),
        is_simulated=True,
    )


@router.get("/health-check", summary="Subsystem operational status")
def maintenance_health_check(current_user: UserModel = Depends(require_viewer)):
    return {
        "status": "ONLINE",
        "subsystem": "Predictive Maintenance & Infrastructure Health Engine",
        "model_version": PredictiveRiskService.MODEL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "is_simulated": True,
        "source": "VIRTUAL_SIMULATION_ENGINE",
    }


# ==============================================================================
# 2. PIPELINE HEALTH ENDPOINTS
# ==============================================================================

@router.get("/health", response_model=List[PipelineHealthResponse], summary="List latest health assessments")
def list_health_assessments(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    assessments = PipelineHealthService.list_health_assessments(db, limit)
    # If empty, pre-populate from default pipelines
    if not assessments:
        pipes = PipelineRepository.get_all(db) or DEFAULT_PIPELINES
        for p in pipes:
            seg_id = p.id if hasattr(p, "id") else p.get("id")
            PipelineHealthService.calculate_health(db, seg_id)
        assessments = PipelineHealthService.list_health_assessments(db, limit)
    return [_format_health(h) for h in assessments]


@router.get("/health/{segment_id}", response_model=PipelineHealthResponse, summary="Get pipeline health assessment")
def get_segment_health(
    segment_id: str = Path(..., description="Pipeline Segment ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    h = PipelineHealthService.get_latest_health(db, segment_id)
    if not h:
        h = PipelineHealthService.calculate_health(db, segment_id)
    return _format_health(h)


@router.post("/health/analyze", response_model=PipelineHealthResponse, summary="Trigger on-demand health analysis")
def analyze_segment_health(
    req: HealthAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    h = PipelineHealthService.calculate_health(db, req.pipeline_segment_id, req.lookback_hours or 24)
    return _format_health(h)


# ==============================================================================
# 3. PREDICTIVE RISK ENDPOINTS
# ==============================================================================

@router.get("/predictions", response_model=List[PredictiveRiskResponse], summary="List predictive failure risk assessments")
def list_predictions(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    predictions = PredictiveRiskService.list_risk_assessments(db, limit)
    if not predictions:
        pipes = PipelineRepository.get_all(db) or DEFAULT_PIPELINES
        for p in pipes:
            seg_id = p.id if hasattr(p, "id") else p.get("id")
            PredictiveRiskService.evaluate_predictive_risk(db, seg_id)
        predictions = PredictiveRiskService.list_risk_assessments(db, limit)
    return [_format_risk(r) for r in predictions]


@router.get("/predictions/{segment_id}", response_model=PredictiveRiskResponse, summary="Get predictive risk for segment")
def get_segment_prediction(
    segment_id: str = Path(..., description="Pipeline Segment ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    r = PredictiveRiskService.get_latest_risk(db, segment_id)
    if not r:
        r = PredictiveRiskService.evaluate_predictive_risk(db, segment_id)
    return _format_risk(r)


@router.post("/predictions/analyze", response_model=PredictiveRiskResponse, summary="Trigger on-demand predictive risk evaluation")
def analyze_predictive_risk(
    req: PredictiveRiskAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    r = PredictiveRiskService.evaluate_predictive_risk(db, req.pipeline_segment_id)
    return _format_risk(r)


# ==============================================================================
# 4. TEMPORAL TREND ENDPOINTS
# ==============================================================================

@router.get("/trends", response_model=List[HistoricalTrendResponse], summary="List degradation trends")
def list_trends(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    trends = TrendAnalysisService.list_trends(db, limit)
    if not trends:
        pipes = PipelineRepository.get_all(db) or DEFAULT_PIPELINES
        for p in pipes:
            seg_id = p.id if hasattr(p, "id") else p.get("id")
            TrendAnalysisService.analyze_trend(db, seg_id)
        trends = TrendAnalysisService.list_trends(db, limit)
    return [_format_trend(t) for t in trends]


@router.get("/trends/{segment_id}", response_model=HistoricalTrendResponse, summary="Get historical trend for segment")
def get_segment_trend(
    segment_id: str = Path(..., description="Pipeline Segment ID"),
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    t = TrendAnalysisService.get_latest_trend(db, segment_id)
    if not t:
        t = TrendAnalysisService.analyze_trend(db, segment_id, window_days=days)
    return _format_trend(t)


# ==============================================================================
# 5. MAINTENANCE RECOMMENDATION ENDPOINTS
# ==============================================================================

@router.get("/recommendations", response_model=List[MaintenanceRecommendationResponse], summary="List maintenance recommendations")
def list_recommendations(
    status: Optional[str] = Query(None, description="PENDING_REVIEW, ACKNOWLEDGED, DISMISSED, DISPATCHED"),
    urgency: Optional[str] = Query(None, description="ROUTINE, MEDIUM, HIGH, CRITICAL"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    recs = MaintenanceRecommendationService.list_recommendations(db, status=status, urgency=urgency, limit=limit)
    if not recs:
        pipes = PipelineRepository.get_all(db) or DEFAULT_PIPELINES
        for p in pipes:
            seg_id = p.id if hasattr(p, "id") else p.get("id")
            MaintenanceRecommendationService.generate_recommendation(db, seg_id)
        recs = MaintenanceRecommendationService.list_recommendations(db, status=status, urgency=urgency, limit=limit)
    return [_format_recommendation(m) for m in recs]


@router.get("/recommendations/{recommendation_id}", response_model=MaintenanceRecommendationResponse, summary="Get recommendation by ID")
def get_recommendation(
    recommendation_id: str = Path(..., description="Recommendation ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_viewer),
):
    rec = MaintenanceRecommendationService.get_recommendation_by_id(db, recommendation_id)
    if not rec:
        raise AquaCrewException(
            status_code=404,
            code="RECOMMENDATION_NOT_FOUND",
            message=f"Recommendation '{recommendation_id}' not found.",
        )
    return _format_recommendation(rec)


@router.post("/recommendations/{recommendation_id}/review", response_model=MaintenanceRecommendationResponse, summary="Operator review of recommendation")
def review_recommendation(
    recommendation_id: str = Path(..., description="Recommendation ID"),
    req: MaintenanceReviewRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    rec = MaintenanceRecommendationService.review_recommendation(
        db=db,
        recommendation_id=recommendation_id,
        action=req.action,
        operator_id=req.operator_id,
        operator_notes=req.operator_notes,
    )
    return _format_recommendation(rec)


@router.post("/recommendations/generate/{segment_id}", response_model=MaintenanceRecommendationResponse, summary="Force generate recommendation for segment")
def generate_recommendation_for_segment(
    segment_id: str = Path(..., description="Pipeline Segment ID"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_operator),
):
    rec = MaintenanceRecommendationService.generate_recommendation(db, segment_id, force_regenerate=True)
    return _format_recommendation(rec)


# ==============================================================================
# 6. MODEL EVALUATION & METRICS
# ==============================================================================

@router.get("/models", response_model=List[MaintenanceModelInfo], summary="Get metadata on predictive models")
def get_maintenance_models(current_user: UserModel = Depends(require_viewer)):
    return [
        MaintenanceModelInfo(
            model_name="AQUA-CREW-PREDICT-24H",
            model_version=PredictiveRiskService.MODEL_VERSION,
            algorithm="Gradient Boosted Decision Forest with Hydraulic Feature Embeddings",
            training_dataset_size=4200,
            features=[
                "acoustic_mean_spl_db", "acoustic_peak_spl_db", "pressure_drop_bar",
                "pressure_std_bar", "flow_imbalance_pct", "soil_moisture_gradient",
                "pipe_material_factor", "historical_leak_count"
            ],
            accuracy=0.912,
            f1_score=0.895,
            roc_auc=0.941,
            last_evaluated="2026-11-15T22:00:00Z",
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        ),
        MaintenanceModelInfo(
            model_name="AQUA-CREW-TREND-VELOCITY-30D",
            model_version="v1.0.0-ols-regression",
            algorithm="Ordinary Least Squares Time-Series Trend Extrapolator",
            training_dataset_size=8600,
            features=["daily_health_checkpoints", "moving_window_days", "pressure_variance"],
            accuracy=0.887,
            f1_score=0.871,
            roc_auc=0.918,
            last_evaluated="2026-11-15T22:00:00Z",
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        ),
    ]


@router.get("/metrics", summary="Model evaluation metrics and confusion matrix")
def get_maintenance_metrics(current_user: UserModel = Depends(require_viewer)):
    return {
        "model_version": PredictiveRiskService.MODEL_VERSION,
        "evaluation_dataset": "SIMULATED_METRO_HYDRAULIC_TEST_CORPUS_2026",
        "sample_count": 1250,
        "train_test_split": "80/20 Deterministic Stratified",
        "metrics": {
            "accuracy": 0.912,
            "precision": 0.884,
            "recall": 0.908,
            "f1_score": 0.895,
            "roc_auc": 0.941,
        },
        "confusion_matrix": {
            "true_positive": 412,
            "false_positive": 54,
            "true_negative": 728,
            "false_negative": 56,
        },
        "prediction_horizons": {
            "24h": {"brier_score": 0.084, "confidence_interval": "±5.8%"},
            "7d": {"brier_score": 0.112, "confidence_interval": "±6.4%"},
            "30d": {"brier_score": 0.145, "confidence_interval": "±7.9%"},
        },
        "is_simulated": True,
        "source": "VIRTUAL_SIMULATION_ENGINE",
    }

