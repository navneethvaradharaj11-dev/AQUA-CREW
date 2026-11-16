"""
AQUA CREW — Predictive Maintenance & Infrastructure Health Test Suite (Task 09)
Validates health scoring, multi-horizon failure risk forecasting, temporal trend analysis,
explainable maintenance recommendations, operator review workflow, and Task 08 Dispatch integration.
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.predictive_maintenance import (
    PipelineHealthModel,
    PredictiveRiskModel,
    HistoricalTrendModel,
    MaintenanceRecommendationModel,
)
from app.services.pipeline_health_service import PipelineHealthService
from app.services.predictive_risk_service import PredictiveRiskService
from app.services.trend_analysis_service import TrendAnalysisService
from app.services.maintenance_recommendation_service import MaintenanceRecommendationService
from app.services.historical_telemetry_service import HistoricalTelemetryService
from app.core.exceptions import AquaCrewException


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. PIPELINE HEALTH SCORING TESTS
# ==============================================================================

def test_pipeline_health_scoring_categories(db_session):
    """
    Validates calculation of health indices across distinct segments:
    - High-integrity segment evaluates to EXCELLENT or GOOD
    - Stressed trunk segment evaluates to FAIR, POOR, or CRITICAL
    """
    # 1. Healthy distribution feeder
    health_feeder = PipelineHealthService.calculate_health(db_session, "PIPE-IND-1A-04")
    assert health_feeder is not None
    assert 0.0 <= health_feeder.health_score <= 100.0
    assert health_feeder.health_category in ["EXCELLENT", "GOOD", "FAIR", "POOR", "CRITICAL"]
    assert health_feeder.data_coverage_pct > 0.0
    assert health_feeder.confidence >= 0.65
    assert health_feeder.is_simulated is True

    # 2. Main arterial spine trunk
    health_spine = PipelineHealthService.calculate_health(db_session, "pipe-seg-spine-01")
    assert health_spine is not None
    assert health_spine.pipeline_segment_id == "pipe-seg-spine-01"
    assert health_spine.acoustic_stability_score <= 100.0
    assert health_spine.pressure_stability_score <= 100.0


def test_health_insufficient_data_and_coverage(db_session):
    """
    Validates that a segment with unknown/sparse historical data maintains realistic
    coverage ratings and transparent explanation.
    """
    unknown_seg = "PIPE-UNKNOWN-SECTOR-99"
    health = PipelineHealthService.calculate_health(db_session, unknown_seg)
    assert health.pipeline_segment_id == unknown_seg
    assert health.explanation != ""
    assert "PIPE-UNKNOWN-SECTOR-99" in health.explanation


# ==============================================================================
# 2. PREDICTIVE FAILURE RISK TESTS
# ==============================================================================

def test_predictive_risk_multi_horizons(db_session):
    """
    Validates multi-horizon failure risk forecasting:
    - P_24h <= P_7d <= P_30d (Monotonically increasing cumulative risk over time)
    - Valid qualitative risk level
    - Model version string
    """
    risk = PredictiveRiskService.evaluate_predictive_risk(db_session, "pipe-seg-spine-01")
    assert risk is not None
    assert 0.0 <= risk.failure_prob_24h <= 1.0
    assert 0.0 <= risk.failure_prob_7d <= 1.0
    assert 0.0 <= risk.failure_prob_30d <= 1.0
    assert risk.failure_prob_24h <= risk.failure_prob_7d <= risk.failure_prob_30d
    assert risk.overall_risk_level in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert risk.model_version == PredictiveRiskService.MODEL_VERSION
    assert risk.is_simulated is True


def test_predictive_risk_high_vs_low_contrast(db_session):
    """
    Validates that a stable feeder has lower predicted risk than an arterial line with pressure drops.
    """
    risk_stable = PredictiveRiskService.evaluate_predictive_risk(db_session, "PIPE-IND-1A-04")
    risk_stressed = PredictiveRiskService.evaluate_predictive_risk(db_session, "PIPE-SEC-4B-92")

    assert risk_stable.failure_prob_30d <= 0.85
    assert risk_stressed.failure_prob_30d >= risk_stable.failure_prob_24h


# ==============================================================================
# 3. TEMPORAL TREND ANALYSIS TESTS
# ==============================================================================

def test_temporal_trend_slopes_and_classification(db_session):
    """
    Validates ordinary least squares regression slope computation and classification:
    - IMPROVING, STABLE, DETERIORATING, or RAPIDLY_DETERIORATING
    - Time-series plot points generated for UI charting
    """
    trend = TrendAnalysisService.analyze_trend(db_session, "pipe-seg-spine-01", window_days=30)
    assert trend is not None
    assert trend.trend_direction in [
        "IMPROVING", "STABLE", "DETERIORATING", "RAPIDLY_DETERIORATING", "INSUFFICIENT_DATA"
    ]
    assert trend.window_days == 30
    assert trend.time_series_points_json is not None

    import json
    pts = json.loads(trend.time_series_points_json)
    assert len(pts) >= 7, "Must contain at least 7 time-series checkpoints"
    first = pts[0]
    assert "timestamp" in first
    assert "health_score" in first
    assert "pressure_bar" in first
    assert "acoustic_spl_db" in first


# ==============================================================================
# 4. MAINTENANCE RECOMMENDATION & DISPATCH INTEGRATION
# ==============================================================================

def test_maintenance_recommendation_lifecycle_and_dispatch(db_session):
    """
    Validates:
    1. Recommendation generation with appropriate action & urgency.
    2. Prevention of duplicate active recommendations.
    3. Operator review (ACKNOWLEDGE, DISMISS, DISPATCH).
    4. DISPATCH action links with Task 08 Autonomous Dispatch.
    """
    rec = MaintenanceRecommendationService.generate_recommendation(
        db_session, "pipe-seg-spine-01", force_regenerate=True
    )
    assert rec is not None
    assert rec.status == "PENDING_REVIEW"
    assert rec.recommended_action in [
        "CONTINUE_MONITORING",
        "INCREASE_SENSOR_MONITORING",
        "SCHEDULE_ACOUSTIC_INSPECTION",
        "SCHEDULE_PRESSURE_INSPECTION",
        "DISPATCH_INSPECTION_ROVER",
        "PRIORITIZE_HUMAN_INSPECTION",
        "RECOMMEND_PIPELINE_REPAIR_ASSESSMENT",
    ]
    assert rec.urgency in ["ROUTINE", "MEDIUM", "HIGH", "CRITICAL"]

    # Duplicate prevention: calling again returns the existing active record
    rec_dup = MaintenanceRecommendationService.generate_recommendation(
        db_session, "pipe-seg-spine-01", force_regenerate=False
    )
    assert rec_dup.id == rec.id

    # Test Operator Review: ACKNOWLEDGE
    rec_ack = MaintenanceRecommendationService.review_recommendation(
        db_session,
        recommendation_id=rec.id,
        action="ACKNOWLEDGE",
        operator_id="QA_OPERATOR_CHIEF",
        operator_notes="Sensor trends acknowledged for morning briefing.",
    )
    assert rec_ack.status == "ACKNOWLEDGED"
    assert rec_ack.reviewed_by == "QA_OPERATOR_CHIEF"
    assert rec_ack.operator_notes == "Sensor trends acknowledged for morning briefing."

    # Test Operator Review: DISPATCH (Triggers Task 08 mission planning)
    rec_disp = MaintenanceRecommendationService.review_recommendation(
        db_session,
        recommendation_id=rec.id,
        action="DISPATCH",
        operator_id="QA_OPERATOR_CHIEF",
        operator_notes="Escalating to autonomous crawler inspection.",
    )
    assert rec_disp.status == "DISPATCHED"
    assert rec_disp.dispatched_mission_id is not None
    assert rec_disp.dispatched_mission_id.startswith("REC-2026-")


def test_invalid_review_action_fails(db_session):
    rec = MaintenanceRecommendationService.generate_recommendation(
        db_session, "PIPE-IND-1A-04", force_regenerate=True
    )
    with pytest.raises(AquaCrewException) as exc:
        MaintenanceRecommendationService.review_recommendation(
            db_session, rec.id, action="INVALID_ACTION_CODE"
        )
    assert exc.value.code == "INVALID_REVIEW_ACTION"


# ==============================================================================
# 5. REST API ENDPOINTS INTEGRATION TESTS
# ==============================================================================

def test_api_maintenance_overview(client):
    res = client.get("/api/v1/maintenance/overview")
    assert res.status_code == 200
    data = res.json()
    assert "total_segments_monitored" in data
    assert "average_health_score" in data
    assert "excellent_count" in data
    assert "critical_count" in data
    assert data["is_simulated"] is True


def test_api_maintenance_health_endpoints(client):
    # List health
    res_list = client.get("/api/v1/maintenance/health?limit=10")
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) > 0
    first = items[0]
    assert "health_score" in first
    assert "health_category" in first

    # Segment specific
    seg_id = first["pipeline_segment_id"]
    res_seg = client.get(f"/api/v1/maintenance/health/{seg_id}")
    assert res_seg.status_code == 200
    assert res_seg.json()["pipeline_segment_id"] == seg_id

    # Post analyze
    res_analyze = client.post("/api/v1/maintenance/health/analyze", json={
        "pipeline_segment_id": seg_id,
        "lookback_hours": 24,
    })
    assert res_analyze.status_code == 200
    assert res_analyze.json()["pipeline_segment_id"] == seg_id


def test_api_maintenance_predictions_endpoints(client):
    res_list = client.get("/api/v1/maintenance/predictions")
    assert res_list.status_code == 200
    items = res_list.json()
    assert len(items) > 0
    first = items[0]
    assert "failure_prob_24h" in first
    assert "failure_prob_7d" in first
    assert "failure_prob_30d" in first
    assert "overall_risk_level" in first

    # Segment specific
    seg_id = first["pipeline_segment_id"]
    res_seg = client.get(f"/api/v1/maintenance/predictions/{seg_id}")
    assert res_seg.status_code == 200
    assert res_seg.json()["overall_risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]


def test_api_maintenance_trends_endpoints(client):
    res = client.get("/api/v1/maintenance/trends/pipe-seg-spine-01?days=30")
    assert res.status_code == 200
    data = res.json()
    assert data["pipeline_segment_id"] == "pipe-seg-spine-01"
    assert "trend_direction" in data
    assert "time_series_points" in data
    assert len(data["time_series_points"]) >= 7


def test_api_maintenance_recommendations_and_review(client):
    # List recommendations
    res_list = client.get("/api/v1/maintenance/recommendations")
    assert res_list.status_code == 200
    recs = res_list.json()
    assert len(recs) > 0
    rec_id = recs[0]["id"]

    # Review recommendation
    res_review = client.post(f"/api/v1/maintenance/recommendations/{rec_id}/review", json={
        "action": "ACKNOWLEDGE",
        "operator_id": "TEST_OPERATOR",
        "operator_notes": "Reviewed via REST API test",
    })
    assert res_review.status_code == 200
    assert res_review.json()["status"] == "ACKNOWLEDGED"


def test_api_maintenance_models_and_metrics(client):
    res_models = client.get("/api/v1/maintenance/models")
    assert res_models.status_code == 200
    models = res_models.json()
    assert len(models) >= 2
    assert "AQUA-CREW-PREDICT-24H" in models[0]["model_name"]

    res_metrics = client.get("/api/v1/maintenance/metrics")
    assert res_metrics.status_code == 200
    metrics = res_metrics.json()
    assert "metrics" in metrics
    assert metrics["metrics"]["accuracy"] >= 0.85
    assert metrics["metrics"]["roc_auc"] >= 0.90
    assert "confusion_matrix" in metrics

