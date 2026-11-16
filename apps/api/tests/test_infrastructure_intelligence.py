"""
AQUA CREW — Infrastructure Intelligence & Geospatial Risk Prediction Test Suite (Task 11)
Validates multi-factor vulnerability scoring, geospatial clustering, zone aggregation,
temporal deterioration velocity, predictive forecasting, and prioritized inspection dispatch.
"""
import pytest
from datetime import datetime, timezone
import json
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.pipeline_segment import PipelineSegmentModel
from app.models.ai_detection import AiDetectionModel
from app.models.rover import RoverModel
from app.models.infrastructure_intelligence import (
    PipelineVulnerabilityProfileModel,
    InfrastructureRiskAssessmentModel,
    SpatialIncidentClusterModel,
    GeographicRiskZoneModel,
    InspectionPriorityRecordModel,
)
from app.repositories.pipeline_repository import PipelineRepository
from app.services.infrastructure_intelligence.vulnerability_scoring_service import VulnerabilityScoringService
from app.services.infrastructure_intelligence.geospatial_clustering_service import GeospatialClusteringService
from app.services.infrastructure_intelligence.spatial_analysis_service import SpatialAnalysisService
from app.services.infrastructure_intelligence.risk_trend_service import RiskTrendService
from app.services.infrastructure_intelligence.infrastructure_prediction_service import InfrastructurePredictionService
from app.services.infrastructure_intelligence.inspection_priority_service import InspectionPriorityService
from app.services.infrastructure_intelligence.infrastructure_intelligence_service import InfrastructureIntelligenceService


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        # Reset any stuck rovers to IDLE to avoid cross-test collision
        for r in db.query(RoverModel).all():
            r.status = "IDLE"
            r.assigned_mission_id = None
        db.commit()
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. MULTI-FACTOR VULNERABILITY SCORING ENGINE TESTS
# ==============================================================================

def test_vulnerability_scoring_weights_and_bounds(db_session):
    """
    Validates vulnerability score is strictly bounded [0, 100] and
    component weights sum exactly to 1.0.
    """
    assert (
        VulnerabilityScoringService.WEIGHT_HYDRAULIC +
        VulnerabilityScoringService.WEIGHT_STRUCTURAL +
        VulnerabilityScoringService.WEIGHT_INCIDENT +
        VulnerabilityScoringService.WEIGHT_ENVIRONMENTAL
    ) == pytest.approx(1.0, 0.001)

    PipelineRepository.seed_defaults(db_session)
    segments = PipelineRepository.get_all(db_session)
    assert len(segments) > 0

    for seg in segments:
        prof = VulnerabilityScoringService.evaluate_pipeline_vulnerability(seg)
        score = prof["vulnerability_score"]
        assert 0.0 <= score <= 100.0
        assert prof["vulnerability_level"] in ["VERY_LOW", "LOW", "MODERATE", "HIGH", "CRITICAL"]
        assert 0.0 <= prof["confidence"] <= 1.0
        assert 0.0 <= prof["data_completeness_pct"] <= 100.0
        assert prof["uncertainty_margin"] > 0.0

        factors = prof["contributing_factors"]
        assert "hydraulic" in factors
        assert "structural" in factors
        assert "incident" in factors
        assert "environmental" in factors


def test_vulnerability_material_sensitivity():
    """
    Validates that Cast Iron generates higher structural risk than Ductile Iron or HDPE.
    """
    ci_seg = PipelineSegmentModel(id="test_ci", name="Cast Iron Test", material="Cast Iron", diameter_mm=300)
    di_seg = PipelineSegmentModel(id="test_di", name="Ductile Iron Test", material="Ductile Iron", diameter_mm=300)
    hdpe_seg = PipelineSegmentModel(id="test_hdpe", name="HDPE Test", material="High-Density Polyethylene (HDPE)", diameter_mm=300)

    score_ci, _ = VulnerabilityScoringService.calculate_structural_score(ci_seg)
    score_di, _ = VulnerabilityScoringService.calculate_structural_score(di_seg)
    score_hdpe, _ = VulnerabilityScoringService.calculate_structural_score(hdpe_seg)

    assert score_ci > score_di > score_hdpe


def test_vulnerability_incident_recurrence_sensitivity():
    """
    Validates that segments with multiple AI detections evaluate to substantially higher incident risk.
    """
    seg = PipelineSegmentModel(id="test_inc_seg", name="Test Inc Seg", material="Ductile Iron", diameter_mm=300)

    score_zero, _ = VulnerabilityScoringService.calculate_incident_score(seg, [])

    d1 = AiDetectionModel(id="det_1", pipeline_segment_id=seg.id, anomaly_score=0.85, status="PENDING_REVIEW")
    score_one, _ = VulnerabilityScoringService.calculate_incident_score(seg, [d1])

    d2 = AiDetectionModel(id="det_2", pipeline_segment_id=seg.id, anomaly_score=0.92, status="PENDING_REVIEW")
    score_two, _ = VulnerabilityScoringService.calculate_incident_score(seg, [d1, d2])

    assert score_two > score_one > score_zero


# ==============================================================================
# 2. GEOSPATIAL CLUSTERING & SPATIAL ANALYSIS TESTS
# ==============================================================================

def test_haversine_geodesic_distance():
    """
    Validates Haversine distance matches known earth geodesic benchmarks:
    1 degree of latitude is approx 111,000 meters.
    """
    dist = GeospatialClusteringService.haversine_distance_m(40.0, -74.0, 41.0, -74.0)
    assert 110_000.0 < dist < 112_000.0

    # Same point distance should be zero
    zero_dist = GeospatialClusteringService.haversine_distance_m(40.7128, -74.0060, 40.7128, -74.0060)
    assert zero_dist == pytest.approx(0.0, 0.1)


def test_density_based_spatial_clustering():
    """
    Validates clustering logic:
    Points within eps_m (350m) cluster together; distant point (>2000m) is separated.
    """
    # 2 close points in Lower Manhattan
    pt1 = {"id": "p1", "latitude": 40.7128, "longitude": -74.0060, "segment_id": "seg_1", "severity": 0.8, "material": "Cast Iron"}
    pt2 = {"id": "p2", "latitude": 40.7135, "longitude": -74.0050, "segment_id": "seg_1", "severity": 0.7, "material": "Cast Iron"}
    # 1 distant point in Midtown (~5 km north)
    pt3 = {"id": "p3", "latitude": 40.7550, "longitude": -73.9850, "segment_id": "seg_2", "severity": 0.4, "material": "HDPE"}

    clusters = GeospatialClusteringService.cluster_incidents([pt1, pt2, pt3], eps_m=350.0, min_samples=2)

    assert len(clusters) >= 1
    # First cluster should contain pt1 and pt2
    c1 = clusters[0]
    assert c1["incident_count"] == 2
    assert "seg_1" in c1["affected_segment_ids"]
    assert c1["radius_m"] >= 150.0  # minimum radius floor
    assert c1["dominant_material"] == "Cast Iron"
    assert c1["cluster_risk_level"] in ["MODERATE", "HIGH", "CRITICAL"]


def test_geographic_risk_zones_aggregation(db_session):
    """
    Validates aggregation of pipeline segments into geographic risk zones.
    """
    PipelineRepository.seed_defaults(db_session)
    segments = PipelineRepository.get_all(db_session)

    profiles = {}
    for s in segments:
        profiles[s.id] = VulnerabilityScoringService.evaluate_pipeline_vulnerability(s)

    clusters = GeospatialClusteringService.cluster_incidents([])
    zones = SpatialAnalysisService.aggregate_zones(segments, profiles, clusters)

    assert len(zones) >= 1
    for z in zones:
        assert z["total_segments"] > 0
        assert z["total_length_km"] > 0.0
        assert 0.0 <= z["avg_vulnerability_score"] <= 100.0
        assert z["dominant_risk_level"] in ["VERY_LOW", "LOW", "MODERATE", "HIGH", "CRITICAL"]
        assert z["is_simulated"] is True


# ==============================================================================
# 3. TEMPORAL TRENDS & PREDICTIVE FORECASTING TESTS
# ==============================================================================

def test_temporal_risk_trend_calculation():
    """
    Validates multi-horizon deterioration deltas and direction classifications.
    """
    seg = PipelineSegmentModel(id="test_seg", name="Test Seg", material="Cast Iron", diameter_mm=300)

    # 1. Normal rate
    trend_res = RiskTrendService.calculate_temporal_trends(seg, current_vulnerability=50.0)
    assert "deterioration_rate_per_day" in trend_res
    assert trend_res["trend_24h_delta"] == pytest.approx(trend_res["deterioration_rate_per_day"] * 1.0, 0.01)
    assert trend_res["trend_7d_delta"] == pytest.approx(trend_res["deterioration_rate_per_day"] * 7.0, 0.01)
    assert trend_res["trend_30d_delta"] == pytest.approx(trend_res["deterioration_rate_per_day"] * 30.0, 0.01)
    assert trend_res["trend_direction"] in ["DETERIORATING", "STABLE", "IMPROVING"]
    assert trend_res["data_sufficiency"] in ["HIGH", "MODERATE", "LOW"]


def test_predictive_risk_forecasting_bounds_and_uncertainty():
    """
    Validates predictive forecasting outputs:
    - Future scores strictly bounded within [0, 100]
    - Expanding confidence intervals over longer time horizons
    """
    seg = PipelineSegmentModel(id="test_seg", name="Test Seg", material="Cast Iron", diameter_mm=600)
    trend = {
        "trend_24h_delta": 0.2,
        "trend_7d_delta": 1.4,
        "trend_30d_delta": 6.0,
        "rapid_degradation": False,
    }

    pred = InfrastructurePredictionService.forecast_risk(seg, current_vulnerability=65.0, trend_info=trend)

    assert 0.0 <= pred["projected_risk_24h"] <= 100.0
    assert 0.0 <= pred["projected_risk_7d"] <= 100.0
    assert 0.0 <= pred["projected_risk_30d"] <= 100.0

    # Uncertainty width: 30d interval width must be greater than 24h interval width
    ci_24_width = pred["confidence_interval_24h"]["upper_bound"] - pred["confidence_interval_24h"]["lower_bound"]
    ci_30_width = pred["confidence_interval_30d"]["upper_bound"] - pred["confidence_interval_30d"]["lower_bound"]
    assert ci_30_width > ci_24_width

    assert pred["mitigation_urgency"] in ["IMMEDIATE", "SHORT_TERM", "PLANNED", "ROUTINE"]
    assert len(pred["primary_risk_drivers"]) > 0


# ==============================================================================
# 4. INSPECTION PRIORITISATION & ROVER DISPATCH TESTS
# ==============================================================================

def test_inspection_priority_scoring_and_ranking(db_session):
    """
    Validates that high-vulnerability and cluster-adjacent segments rank highest in inspection queue.
    """
    PipelineRepository.seed_defaults(db_session)
    segments = PipelineRepository.get_all(db_session)

    p_high, lvl_high, reasons_high, act_high = InspectionPriorityService.calculate_priority_score(
        vulnerability_score=85.0,
        deterioration_rate_per_day=0.35,
        cluster_distance_m=120.0,
        segment=segments[0],
    )

    p_low, lvl_low, reasons_low, act_low = InspectionPriorityService.calculate_priority_score(
        vulnerability_score=25.0,
        deterioration_rate_per_day=0.04,
        cluster_distance_m=1200.0,
        segment=segments[-1],
    )

    assert p_high > p_low
    assert lvl_high in ["CRITICAL_IMMEDIATE", "HIGH_PRIORITY"]
    assert lvl_low in ["ROUTINE_SCHEDULED", "MONITORING_ONLY"]
    assert len(reasons_high) > 0


def test_inspection_queue_operator_workflow(db_session):
    """
    Validates complete operator workflow:
    1. Synchronize inspection queue
    2. Operator acknowledges priority target
    3. Operator requests rover inspection -> generates recommendation with operator approval required
    """
    InfrastructureIntelligenceService.run_assessment(db_session)
    priorities = db_session.query(InspectionPriorityRecordModel).all()
    assert len(priorities) > 0

    target = priorities[0]

    # 1. Acknowledge
    ack_res = InspectionPriorityService.acknowledge_priority(
        db=db_session,
        priority_id=target.id,
        operator_name="TEST_OPERATOR",
        notes="Reviewed during shift handover",
    )
    assert ack_res.status == "ACKNOWLEDGED"
    assert ack_res.reviewed_by == "TEST_OPERATOR"

    # 2. Request Inspection
    dispatch_res = InspectionPriorityService.request_inspection(
        db=db_session,
        priority_id=target.id,
        operator_name="TEST_OPERATOR",
    )
    assert dispatch_res["status"] == "DISPATCHED"
    assert dispatch_res["operator_approval_required"] is True
    assert dispatch_res["mission_recommendation_id"] is not None
    assert dispatch_res["assigned_rover_id"] is not None

    # Check updated record in DB
    refreshed = db_session.query(InspectionPriorityRecordModel).filter(
        InspectionPriorityRecordModel.id == target.id
    ).first()
    assert refreshed.status == "DISPATCHED"
    assert refreshed.assigned_rover_id == dispatch_res["assigned_rover_id"]


def test_inspection_queue_dismissal(db_session):
    """
    Validates operator dismissal of a low-priority or false-positive target.
    """
    InfrastructureIntelligenceService.run_assessment(db_session)
    priorities = db_session.query(InspectionPriorityRecordModel).all()
    target = priorities[-1]

    dismiss_res = InspectionPriorityService.dismiss_priority(
        db=db_session,
        priority_id=target.id,
        operator_name="TEST_OPERATOR",
        reason="Scheduled in capital replacement program next quarter.",
    )
    assert dismiss_res.status == "DISMISSED"
    assert "capital replacement" in dismiss_res.dismissal_reason


# ==============================================================================
# 5. REST API CONTRACT & ENDPOINT INTEGRATION TESTS
# ==============================================================================

def test_api_infrastructure_overview(client):
    res = client.get("/api/v1/infrastructure-intelligence/overview")
    assert res.status_code == 200
    data = res.json()
    assert "total_segments_analyzed" in data
    assert "critical_segments_count" in data
    assert "average_network_vulnerability" in data
    assert "active_clusters_count" in data
    assert "pending_inspections_count" in data
    assert data["is_simulated"] is True


def test_api_infrastructure_segments(client):
    res = client.get("/api/v1/infrastructure-intelligence/segments?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "items" in data
    assert len(data["items"]) > 0

    first = data["items"][0]
    assert "vulnerability_score" in first
    assert "hydraulic_score" in first
    assert "structural_score" in first
    assert "incident_score" in first
    assert "environmental_score" in first
    assert "contributing_factors" in first


def test_api_segment_deep_dive(client):
    # First get a segment id
    res_list = client.get("/api/v1/infrastructure-intelligence/segments?limit=1")
    seg_id = res_list.json()["items"][0]["pipeline_segment_id"]

    res = client.get(f"/api/v1/infrastructure-intelligence/segments/{seg_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["pipeline_segment_id"] == seg_id
    assert "contributing_factors" in data
    assert "predictive_forecast" in data
    assert data["predictive_forecast"]["projected_risk_24h"] is not None
    assert data["is_simulated"] is True


def test_api_heatmap(client):
    res = client.get("/api/v1/infrastructure-intelligence/heatmap")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "latitude" in first
    assert "longitude" in first
    assert "weight" in first


def test_api_clusters(client):
    res = client.get("/api/v1/infrastructure-intelligence/clusters")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_api_zones(client):
    res = client.get("/api/v1/infrastructure-intelligence/zones")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "zone_code" in first
    assert "avg_vulnerability_score" in first


def test_api_trends_and_predictions(client):
    res_trends = client.get("/api/v1/infrastructure-intelligence/trends")
    assert res_trends.status_code == 200
    assert len(res_trends.json()) > 0

    res_preds = client.get("/api/v1/infrastructure-intelligence/predictions")
    assert res_preds.status_code == 200
    assert len(res_preds.json()) > 0


def test_api_inspection_priorities_flow(client):
    # Get priorities
    res = client.get("/api/v1/infrastructure-intelligence/inspection-priorities")
    assert res.status_code == 200
    items = res.json()
    assert len(items) > 0

    target_id = items[0]["id"]

    # Acknowledge endpoint
    ack_res = client.post(
        f"/api/v1/infrastructure-intelligence/inspection-priorities/{target_id}/acknowledge",
        json={"operator_name": "API_TEST_OPERATOR", "notes": "Handled via API test"}
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "ACKNOWLEDGED"

    # Request inspection endpoint
    req_res = client.post(
        f"/api/v1/infrastructure-intelligence/inspection-priorities/{target_id}/request-inspection",
        json={"operator_name": "API_TEST_OPERATOR"}
    )
    assert req_res.status_code == 200
    data = req_res.json()
    assert data["status"] == "DISPATCHED"
    assert data["operator_approval_required"] is True

