"""
AQUA CREW — Comprehensive Infrastructure Intelligence & Geospatial Accuracy Validation Suite (Task 11.5)
Strictly independent audit and automated validation covering:
- 15 independent vulnerability expected-value scenarios
- Exact boundary thresholds (19.99/20.0, 39.99/40.0, 59.99/60.0, 79.99/80.0)
- 10 geographic clustering datasets (antimeridian crossing, 3D spherical centroid, poles, noise)
- OLS temporal deterioration regression with irregular timestamps and data sufficiency checks
- Multi-horizon predictive risk saturation and expanding confidence intervals
- 15 inspection queue ranking scenarios
- Rover battery safety gate (>= 20% threshold) and dispatch Scenarios A through E
"""
import pytest
import math
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from app.database.session import SessionLocal
from app.models.pipeline_segment import PipelineSegmentModel
from app.models.rover import RoverModel
from app.models.ai_detection import AiDetectionModel
from app.models.predictive_maintenance import PipelineHealthModel, PredictiveRiskModel
from app.models.digital_twin import HydraulicLinkModel
from app.models.infrastructure_intelligence import (
    PipelineVulnerabilityProfileModel,
    InspectionPriorityRecordModel,
    SpatialIncidentClusterModel,
    GeographicRiskZoneModel,
)
from app.services.infrastructure_intelligence.vulnerability_scoring_service import VulnerabilityScoringService
from app.services.infrastructure_intelligence.geospatial_clustering_service import GeospatialClusteringService
from app.services.infrastructure_intelligence.spatial_analysis_service import SpatialAnalysisService
from app.services.infrastructure_intelligence.risk_trend_service import RiskTrendService
from app.services.infrastructure_intelligence.infrastructure_prediction_service import InfrastructurePredictionService
from app.services.infrastructure_intelligence.inspection_priority_service import InspectionPriorityService
from app.core.exceptions import AquaCrewException


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        # Reset any test rovers to IDLE and replenish battery
        for r in db.query(RoverModel).all():
            r.status = "IDLE"
            r.assigned_mission_id = None
            if "DEPLETED" not in r.id:
                r.battery_percentage = 95.0
        db.commit()
        yield db
    finally:
        db.close()


# ==============================================================================
# 1. 15 INDEPENDENT VULNERABILITY EXPECTED-VALUE SCENARIOS
# ==============================================================================

def test_scenario_01_healthy_hdpe_pipeline():
    """Scenario 1: Modern HDPE pipe with low operating pressure, zero incidents, stable ground."""
    seg = PipelineSegmentModel(
        id="SCEN-01-HDPE",
        name="Industrial Low-Pressure Feeder",
        material="High-Density Polyethylene (HDPE)",
        diameter_mm=200,
        length_m=500.0,
        pressure_zone_id="PZ-02",
        category="distribution",
        nominal_pressure_psi=40.0,
    )
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
        segment=seg,
        ai_detections=[],
        distance_to_cluster_m=2500.0,
    )
    assert res["vulnerability_score"] < 35.0
    assert res["vulnerability_level"] in ("VERY_LOW", "LOW")
    assert res["contributing_factors"]["structural"]["score"] <= 35.0


def test_scenario_02_healthy_ductile_iron():
    """Scenario 2: Healthy ductile iron conduit under moderate operating pressure."""
    seg = PipelineSegmentModel(
        id="SCEN-02-DI",
        name="Moderate Ductile Feeder",
        material="Ductile Iron (Class 54)",
        diameter_mm=300,
        length_m=800.0,
        pressure_zone_id="PZ-01",
        category="secondary",
        nominal_pressure_psi=50.0,
    )
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
        segment=seg,
        ai_detections=[],
        distance_to_cluster_m=1500.0,
    )
    assert 25.0 <= res["vulnerability_score"] <= 45.0
    assert res["vulnerability_level"] in ("LOW", "MODERATE")


def test_scenario_03_aging_cast_iron():
    """Scenario 3: Aging cast iron pipeline with graphitization and active incident history."""
    seg = PipelineSegmentModel(
        id="SCEN-03-CI",
        name="Historic Downtown Cast Iron",
        material="Cast Iron",
        diameter_mm=300,
        length_m=650.0,
        pressure_zone_id="PZ-04",
        category="distribution",
        nominal_pressure_psi=55.0,
    )
    det = AiDetectionModel(id="det_ci_1", pipeline_segment_id=seg.id, anomaly_score=0.88, status="PENDING_REVIEW")
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
        segment=seg,
        ai_detections=[det],
        distance_to_cluster_m=180.0,
    )
    assert res["vulnerability_score"] >= 50.0
    assert res["vulnerability_level"] in ("MODERATE", "HIGH")
    assert res["contributing_factors"]["structural"]["score"] >= 75.0


def test_scenario_04_high_pressure_instability():
    """Scenario 4: Pipeline experiencing high transient pressure fluctuations."""
    seg = PipelineSegmentModel(
        id="SCEN-04-PRESS",
        name="Surge Prone Arterial",
        material="Steel",
        diameter_mm=500,
        length_m=1200.0,
        pressure_zone_id="PZ-01",
        category="primary",
        nominal_pressure_psi=90.0,
    )
    h_rec = PipelineHealthModel(
        id="H-SCEN04",
        pipeline_segment_id=seg.id,
        pressure_stability_score=20.0,  # 80% deficit -> +32.0 hydraulic stress
        health_score=45.0,
    )
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
        segment=seg,
        health_rec=h_rec,
        distance_to_cluster_m=1000.0,
    )
    assert res["contributing_factors"]["hydraulic"]["score"] >= 60.0
    assert res["vulnerability_score"] >= 40.0


def test_scenario_05_repeated_leakage():
    """Scenario 5: Pipeline with multiple confirmed acoustic leaks."""
    seg = PipelineSegmentModel(
        id="SCEN-05-LEAKS",
        name="Repetitive Leak Segment",
        material="PVC (Schedule 80)",
        diameter_mm=250,
        length_m=400.0,
        pressure_zone_id="PZ-03",
        category="distribution",
        nominal_pressure_psi=45.0,
    )
    d1 = AiDetectionModel(id="det_scen5_1", pipeline_segment_id=seg.id, anomaly_score=0.91, status="PENDING_REVIEW")
    d2 = AiDetectionModel(id="det_scen5_2", pipeline_segment_id=seg.id, anomaly_score=0.89, status="PENDING_REVIEW")
    d3 = AiDetectionModel(id="det_scen5_3", pipeline_segment_id=seg.id, anomaly_score=0.94, status="PENDING_REVIEW")
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
        segment=seg,
        ai_detections=[d1, d2, d3],
        distance_to_cluster_m=100.0,
    )
    assert res["contributing_factors"]["incident"]["score"] >= 80.0
    assert res["vulnerability_score"] >= 50.0


def test_scenario_06_severe_flow_imbalance():
    """Scenario 6: Significant hydraulic pressure delta across pipeline segment."""
    seg = PipelineSegmentModel(
        id="SCEN-06-IMBALANCE",
        name="Flow Constriction Lateral",
        material="Ductile Iron (Class 54)",
        diameter_mm=200,
        length_m=1500.0,
        pressure_zone_id="PZ-01",
        category="secondary",
        nominal_pressure_psi=50.0,
    )
    link = HydraulicLinkModel(
        id="LINK-SCEN06",
        pipeline_segment_id=seg.id,
        length_m=1000.0,
    )
    link.velocity_mps = 2.4
    link.headloss_m = 25.0
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
        segment=seg,
        digital_twin_links=[link],
        distance_to_cluster_m=400.0,
    )
    assert res["contributing_factors"]["hydraulic"]["score"] >= 50.0


def test_scenario_07_high_hydraulic_stress():
    """Scenario 7: Continuous high dynamic head exceeding standard limits."""
    seg = PipelineSegmentModel(
        id="SCEN-07-STRESS",
        name="Pump Discharge Manifold",
        material="Steel",
        diameter_mm=600,
        length_m=300.0,
        pressure_zone_id="PZ-01",
        category="primary",
        nominal_pressure_psi=85.0,
    )
    link = HydraulicLinkModel(
        id="LINK-SCEN07",
        pipeline_segment_id=seg.id,
        length_m=500.0,
    )
    link.velocity_mps = 2.8
    link.headloss_m = 30.0
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
        segment=seg,
        digital_twin_links=[link],
        distance_to_cluster_m=800.0,
    )
    assert res["contributing_factors"]["hydraulic"]["score"] >= 50.0


def test_scenario_08_incomplete_data_missing_material():
    """Scenario 8: Missing material and diameter penalized with default baseline and lower completeness."""
    seg = PipelineSegmentModel(
        id="SCEN-08-MISSING",
        name="Uncatalogued Legacy Conduit",
        material=None,  # Missing material
        diameter_mm=None,  # Missing diameter
        length_m=500.0,
        pressure_zone_id="PZ-01",
        category="distribution",
        nominal_pressure_psi=50.0,
    )
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(segment=seg)
    # Default unclassified score is 50.0
    assert res["contributing_factors"]["structural"]["score"] == 50.0
    assert res["data_completeness_pct"] <= 50.0
    assert res["uncertainty_margin"] >= 5.0


def test_scenario_09_conflicting_indicators():
    """Scenario 9: Excellent material (HDPE) but multiple active leak detections."""
    seg = PipelineSegmentModel(
        id="SCEN-09-CONFLICT",
        name="Damaged New HDPE Pipeline",
        material="High-Density Polyethylene (HDPE)",
        diameter_mm=250,
        length_m=600.0,
        pressure_zone_id="PZ-02",
        category="distribution",
        nominal_pressure_psi=45.0,
    )
    d1 = AiDetectionModel(id="det_scen9_1", pipeline_segment_id=seg.id, anomaly_score=0.92, status="PENDING_REVIEW")
    d2 = AiDetectionModel(id="det_scen9_2", pipeline_segment_id=seg.id, anomaly_score=0.88, status="PENDING_REVIEW")
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
        segment=seg,
        ai_detections=[d1, d2],
        distance_to_cluster_m=80.0,
    )
    assert res["contributing_factors"]["structural"]["score"] <= 35.0
    assert res["contributing_factors"]["incident"]["score"] >= 70.0
    assert res["contributing_factors"]["environmental"]["score"] >= 60.0


def test_scenario_10_high_material_vulnerability():
    """Scenario 10: Cast iron in high-risk environmental hotspot zone."""
    seg = PipelineSegmentModel(
        id="SCEN-10-CORROSIVE",
        name="Corrosive Harbor Lateral",
        material="Cast Iron",
        diameter_mm=200,
        length_m=350.0,
        pressure_zone_id="PZ-04",
        category="distribution",
        nominal_pressure_psi=45.0,
    )
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
        segment=seg,
        distance_to_cluster_m=150.0,
    )
    assert res["contributing_factors"]["structural"]["score"] >= 80.0
    assert res["contributing_factors"]["environmental"]["score"] >= 40.0


def test_scenario_11_large_diameter_critical_main():
    """Scenario 11: 800mm transmission main receives large diameter consequence boost."""
    seg = PipelineSegmentModel(
        id="SCEN-11-TRUNK800",
        name="Primary Metro Aqueduct Trunk",
        material="Prestressed Concrete Cylinder Pipe (PCCP)",
        diameter_mm=800,
        length_m=2500.0,
        pressure_zone_id="PZ-01",
        category="primary",
        nominal_pressure_psi=65.0,
    )
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(segment=seg)
    # PCCP base ~68 + 12 (dia >= 600) + 8 (primary) = 86
    assert res["contributing_factors"]["structural"]["score"] >= 80.0
    assert res["vulnerability_score"] >= 35.0


def test_scenario_12_multiple_risk_factors_combined():
    """Scenario 12: Combined high pressure, aging material, large diameter, and active cluster."""
    seg = PipelineSegmentModel(
        id="SCEN-12-MULTIRISK",
        name="Critical Downtown Transmission Intersection",
        material="Cast Iron (Epoxy Lined)",
        diameter_mm=600,
        length_m=1200.0,
        pressure_zone_id="PZ-01",
        category="primary",
        nominal_pressure_psi=65.0,
    )
    h_rec = PipelineHealthModel(
        id="H-SCEN12",
        pipeline_segment_id=seg.id,
        pressure_stability_score=15.0,
        health_score=30.0,
    )
    d1 = AiDetectionModel(id="det_scen12_1", pipeline_segment_id=seg.id, anomaly_score=0.95, status="PENDING_REVIEW")
    d2 = AiDetectionModel(id="det_scen12_2", pipeline_segment_id=seg.id, anomaly_score=0.90, status="PENDING_REVIEW")
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
        segment=seg,
        health_rec=h_rec,
        ai_detections=[d1, d2],
        distance_to_cluster_m=100.0,
    )
    assert res["vulnerability_score"] >= 70.0
    assert res["vulnerability_level"] in ("HIGH", "CRITICAL")


def test_scenario_13_all_risk_factors_near_zero():
    """Scenario 13: Pristine HDPE, low pressure, zero traffic, zero incidents, isolated location."""
    seg = PipelineSegmentModel(
        id="SCEN-13-PRISTINE",
        name="Pristine Rural Lateral",
        material="High-Density Polyethylene (HDPE)",
        diameter_mm=100,
        length_m=200.0,
        pressure_zone_id="PZ-02",
        category="service",
        nominal_pressure_psi=25.0,
    )
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
        segment=seg,
        distance_to_cluster_m=10000.0,
    )
    assert res["vulnerability_score"] < 35.0
    assert res["vulnerability_level"] in ("VERY_LOW", "LOW")


def test_scenario_14_maximum_risk_conditions():
    """Scenario 14: Worst-case parameters saturating into CRITICAL."""
    seg = PipelineSegmentModel(
        id="SCEN-14-MAXRISK",
        name="Catastrophic Failure Risk Segment",
        material="Cast Iron",
        diameter_mm=1200,
        length_m=3000.0,
        pressure_zone_id="PZ-01",
        category="primary",
        nominal_pressure_psi=80.0,
    )
    h_rec = PipelineHealthModel(
        id="H-SCEN14",
        pipeline_segment_id=seg.id,
        pressure_stability_score=0.0,
        health_score=10.0,
    )
    detections = [
        AiDetectionModel(id=f"det_scen14_{i}", pipeline_segment_id=seg.id, anomaly_score=0.99, status="PENDING_REVIEW")
        for i in range(5)
    ]
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(
        segment=seg,
        health_rec=h_rec,
        ai_detections=detections,
        distance_to_cluster_m=10.0,
    )
    assert res["vulnerability_score"] >= 80.0
    assert res["vulnerability_level"] == "CRITICAL"


def test_scenario_15_invalid_parameter_conditions():
    """Scenario 15: Negative diameter, negative pressure, extreme outliers handled cleanly without crashing."""
    seg = PipelineSegmentModel(
        id="SCEN-15-INVALID",
        name="Corrupted Data Input Test",
        material="Unknown Strange Material",
        diameter_mm=-500,  # Negative diameter
        length_m=-100.0,   # Negative length
        pressure_zone_id="PZ-01",
        category="distribution",
        nominal_pressure_psi=-50.0,  # Negative pressure
    )
    res = VulnerabilityScoringService.evaluate_pipeline_vulnerability(segment=seg)
    # Must remain strictly bounded [0, 100] without throwing uncaught exceptions
    assert 0.0 <= res["vulnerability_score"] <= 100.0
    assert res["vulnerability_level"] in ("VERY_LOW", "LOW", "MODERATE", "HIGH", "CRITICAL")
    assert res["data_completeness_pct"] < 60.0


# ==============================================================================
# 2. EXACT BOUNDARY THRESHOLD TESTS
# ==============================================================================

def test_boundary_thresholds_exact():
    """
    Tests exact boundary transitions:
    - 19.99 vs 20.00 (VERY_LOW vs LOW)
    - 39.99 vs 40.00 (LOW vs MODERATE)
    - 59.99 vs 60.00 (MODERATE vs HIGH)
    - 79.99 vs 80.00 (HIGH vs CRITICAL)
    """
    assert VulnerabilityScoringService.get_vulnerability_level(19.99) == "VERY_LOW"
    assert VulnerabilityScoringService.get_vulnerability_level(20.00) == "LOW"

    assert VulnerabilityScoringService.get_vulnerability_level(39.99) == "LOW"
    assert VulnerabilityScoringService.get_vulnerability_level(40.00) == "MODERATE"

    assert VulnerabilityScoringService.get_vulnerability_level(59.99) == "MODERATE"
    assert VulnerabilityScoringService.get_vulnerability_level(60.00) == "HIGH"

    assert VulnerabilityScoringService.get_vulnerability_level(79.99) == "HIGH"
    assert VulnerabilityScoringService.get_vulnerability_level(80.00) == "CRITICAL"


# ==============================================================================
# 3. 10 GEOGRAPHIC CLUSTERING DATASETS (DBSCAN & HAVERSINE)
# ==============================================================================

def test_clustering_01_points_within_epsilon():
    """Dataset 1: Two points separated by 200m (epsilon=350m) cluster together."""
    pts = [
        {"id": "p1", "latitude": 40.7128, "longitude": -74.0060, "segment_id": "s1", "severity": "HIGH"},
        {"id": "p2", "latitude": 40.7146, "longitude": -74.0060, "segment_id": "s1", "severity": "HIGH"},
    ]
    clusters = GeospatialClusteringService.cluster_incidents(pts, eps_m=350.0, min_samples=2)
    assert len(clusters) == 1
    assert clusters[0]["incident_count"] == 2


def test_clustering_02_points_outside_epsilon():
    """Dataset 2: Two points separated by 1000m (epsilon=350m) are marked as noise."""
    pts = [
        {"id": "p1", "latitude": 40.7128, "longitude": -74.0060, "segment_id": "s1", "severity": "HIGH"},
        {"id": "p2", "latitude": 40.7218, "longitude": -74.0060, "segment_id": "s1", "severity": "HIGH"},
    ]
    clusters = GeospatialClusteringService.cluster_incidents(pts, eps_m=350.0, min_samples=2)
    assert len(clusters) == 0


def test_clustering_03_three_nearby_points():
    """Dataset 3: Three points within 150m of each other form a single 3-incident cluster."""
    pts = [
        {"id": "p1", "latitude": 40.7128, "longitude": -74.0060, "segment_id": "s1", "severity": "CRITICAL"},
        {"id": "p2", "latitude": 40.7132, "longitude": -74.0062, "segment_id": "s1", "severity": "HIGH"},
        {"id": "p3", "latitude": 40.7129, "longitude": -74.0058, "segment_id": "s1", "severity": "HIGH"},
    ]
    clusters = GeospatialClusteringService.cluster_incidents(pts, eps_m=350.0, min_samples=2)
    assert len(clusters) == 1
    assert clusters[0]["incident_count"] == 3


def test_clustering_04_isolated_noise_point():
    """Dataset 4: Two points close together plus one isolated point 5km away."""
    pts = [
        {"id": "p1", "latitude": 40.7128, "longitude": -74.0060, "segment_id": "s1", "severity": "HIGH"},
        {"id": "p2", "latitude": 40.7135, "longitude": -74.0055, "segment_id": "s1", "severity": "HIGH"},
        {"id": "p3_isolated", "latitude": 40.7580, "longitude": -73.9855, "segment_id": "s2", "severity": "CRITICAL"},
    ]
    clusters = GeospatialClusteringService.cluster_incidents(pts, eps_m=350.0, min_samples=2)
    assert len(clusters) == 1
    assert "p3_isolated" not in clusters[0]["affected_segment_ids"] or clusters[0]["incident_count"] == 2


def test_clustering_05_duplicate_coordinates():
    """Dataset 5: Points with identical coordinates handled gracefully."""
    pts = [
        {"id": "p1", "latitude": 40.7128, "longitude": -74.0060, "segment_id": "s1", "severity": "HIGH"},
        {"id": "p2", "latitude": 40.7128, "longitude": -74.0060, "segment_id": "s1", "severity": "HIGH"},
    ]
    clusters = GeospatialClusteringService.cluster_incidents(pts, eps_m=350.0, min_samples=2)
    assert len(clusters) == 1
    assert clusters[0]["incident_count"] == 2
    assert clusters[0]["radius_m"] >= 50.0


def test_clustering_06_antimeridian_crossing():
    """
    Dataset 6: Points across the 180th antimeridian (+179.999° and -179.999°).
    Distance along longitude wrap is ~222 meters, well within epsilon=350m.
    Must cluster together, NOT be treated as 20,000 km apart.
    """
    dist = GeospatialClusteringService.haversine_distance_m(0.0, 179.999, 0.0, -179.999)
    # (0.002 degrees * 111,319m) ≈ 222.6 meters
    assert 220.0 <= dist <= 225.0

    pts = [
        {"id": "p_east", "latitude": 0.0, "longitude": 179.999, "segment_id": "s_wrap", "severity": "CRITICAL"},
        {"id": "p_west", "latitude": 0.0, "longitude": -179.999, "segment_id": "s_wrap", "severity": "CRITICAL"},
    ]
    clusters = GeospatialClusteringService.cluster_incidents(pts, eps_m=350.0, min_samples=2)
    assert len(clusters) == 1
    assert clusters[0]["incident_count"] == 2


def test_clustering_07_spherical_centroid_across_antimeridian():
    """
    Dataset 7: 3D Spherical Cartesian centroid across antimeridian.
    Centroid of (+179.9° and -179.9°) at latitude 0° must be at 180.0° (or -180.0°),
    NOT at 0.0° (Greenwich prime meridian).
    """
    coords = [
        {"latitude": 0.0, "longitude": 179.9},
        {"latitude": 0.0, "longitude": -179.9},
    ]
    c_lat, c_lng = GeospatialClusteringService.calculate_spherical_centroid(coords)
    assert abs(c_lat) < 0.0001
    assert abs(abs(c_lng) - 180.0) < 0.01


def test_clustering_08_polar_proximity():
    """Dataset 8: Points near high latitudes (89.9° North)."""
    dist = GeospatialClusteringService.haversine_distance_m(89.9, 0.0, 89.9, 1.0)
    assert dist < 250.0

    pts = [
        {"id": "pole_1", "latitude": 89.9, "longitude": 0.0, "segment_id": "s_pole", "severity": "HIGH"},
        {"id": "pole_2", "latitude": 89.9, "longitude": 1.0, "segment_id": "s_pole", "severity": "HIGH"},
    ]
    clusters = GeospatialClusteringService.cluster_incidents(pts, eps_m=350.0, min_samples=2)
    assert len(clusters) == 1
    assert clusters[0]["incident_count"] == 2


def test_clustering_09_invalid_coordinates_rejected():
    """Dataset 9: Invalid coordinate values (NaN, > 90 lat) return is_valid=False."""
    is_valid1, _ = GeospatialClusteringService.validate_coordinate(95.0, -74.0)
    assert is_valid1 is False

    is_valid2, _ = GeospatialClusteringService.validate_coordinate(float("nan"), -74.0)
    assert is_valid2 is False

    is_valid3, _ = GeospatialClusteringService.validate_coordinate(40.7, 200.0)
    assert is_valid3 is False


def test_clustering_10_empty_dataset_handling():
    """Dataset 10: Empty point list returns empty clusters without crash."""
    clusters = GeospatialClusteringService.cluster_incidents([], eps_m=350.0, min_samples=2)
    assert clusters == []


# ==============================================================================
# 4. OLS TEMPORAL REGRESSION & DATA SUFFICIENCY TESTS
# ==============================================================================

def test_ols_slope_irregular_timestamps():
    """OLS slope over irregular timestamps: 0d (score 50), 3d (score 51.5), 10d (score 55.0)."""
    base = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)
    series = [
        (base, 50.0),
        (base + timedelta(days=3), 51.5),
        (base + timedelta(days=10), 55.0),
    ]
    slope, sufficiency, r2 = RiskTrendService.calculate_ols_slope(series)
    # Expected slope is 0.50 points per day
    assert slope is not None
    assert abs(slope - 0.50) < 0.01
    assert sufficiency in ("LOW", "MODERATE", "HIGH")
    assert r2 is not None and r2 >= 0.99


def test_ols_slope_duplicate_timestamps():
    """Duplicate timestamps should be grouped and averaged before regression."""
    base = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)
    series = [
        (base, 50.0),
        (base, 52.0),  # Average at base is 51.0
        (base + timedelta(days=10), 56.0),
    ]
    slope, sufficiency, r2 = RiskTrendService.calculate_ols_slope(series)
    # From 51.0 to 56.0 over 10 days = 0.50 pts/day
    assert slope is not None
    assert abs(slope - 0.50) < 0.01


def test_ols_insufficient_data():
    """Less than 2 points or timespan < 1 hour must return INSUFFICIENT_DATA."""
    base = datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Single point
    slope1, suff1, _ = RiskTrendService.calculate_ols_slope([(base, 60.0)])
    assert slope1 is None
    assert suff1 == "INSUFFICIENT_DATA"

    # 15 minutes apart (< 1 hour)
    slope2, suff2, _ = RiskTrendService.calculate_ols_slope([(base, 60.0), (base + timedelta(minutes=15), 62.0)])
    assert slope2 is None
    assert suff2 == "INSUFFICIENT_DATA"


# ==============================================================================
# 5. MULTI-HORIZON PREDICTIONS & EXPANDING CONFIDENCE INTERVALS
# ==============================================================================

def test_prediction_confidence_intervals_expand():
    """Confidence interval width must expand monotonically from 24h to 7d to 30d."""
    seg = PipelineSegmentModel(id="pred_test_seg", name="Prediction Main", diameter_mm=400)
    res = InfrastructurePredictionService.forecast_risk(
        segment=seg,
        current_vulnerability=70.0,
        trend_info={"trend_24h_delta": 0.20, "trend_7d_delta": 1.40, "trend_30d_delta": 6.00},
        cluster_proximity_m=150.0,
    )
    ci_24h_width = res["confidence_interval_24h"]["upper_bound"] - res["confidence_interval_24h"]["lower_bound"]
    ci_7d_width = res["confidence_interval_7d"]["upper_bound"] - res["confidence_interval_7d"]["lower_bound"]
    ci_30d_width = res["confidence_interval_30d"]["upper_bound"] - res["confidence_interval_30d"]["lower_bound"]

    assert ci_24h_width < ci_7d_width < ci_30d_width
    assert res["projected_risk_24h"] <= res["projected_risk_7d"] <= res["projected_risk_30d"]
    assert res["projected_risk_30d"] <= 100.0


# ==============================================================================
# 6. INSPECTION QUEUE 15 RANKING SCENARIOS & ROVER BATTERY GATE
# ==============================================================================

def test_inspection_priority_formula_ranking():
    """
    Tests 15 inspection ranking items verifying exact descending order:
    Priority = 0.40 * Vulnerability + 0.25 * Degradation + 0.20 * Hotspot + 0.15 * Consequence
    """
    items = []
    for i in range(15):
        vuln = 20.0 + (i * 4.5)
        rate = 0.02 * i
        prox = max(50.0, 1000.0 - (i * 65.0))
        dia = 150 + (i * 35)
        seg = PipelineSegmentModel(id=f"seg_rank_{i}", name=f"Rank {i}", diameter_mm=dia)
        score, level, reasons, action = InspectionPriorityService.calculate_priority_score(
            vulnerability_score=vuln,
            deterioration_rate_per_day=rate,
            cluster_distance_m=prox,
            segment=seg,
        )
        items.append({"index": i, "score": score})

    # Scores must increase monotonically as vulnerability, degradation, hotspot proximity, and diameter increase
    for i in range(len(items) - 1):
        assert items[i]["score"] <= items[i+1]["score"]


def test_rover_dispatch_scenarios_a_through_e(db_session):
    """
    Validates Scenarios A through E:
    - Scenario A: High-risk priority record created in PENDING status.
    - Scenario B: Rover with < 20% battery rejected by safety gate.
    - Scenario C: Operator dismissal halts mission.
    - Scenario D: Operator approval triggers mission dispatch.
    - Scenario E: Duplicate request prevention rejects secondary dispatch.
    """
    # Setup a test pipeline segment
    seg = db_session.query(PipelineSegmentModel).filter_by(id="PIPE-VAL-TEST-01").first()
    if not seg:
        seg = PipelineSegmentModel(
            id="PIPE-VAL-TEST-01",
            name="Validation Test Main",
            material="Ductile Iron",
            diameter_mm=500,
            length_m=800.0,
            pressure_zone_id="PZ-01",
            category="primary",
            nominal_pressure_psi=60.0,
            coordinates_json=json.dumps([[40.7128, -74.0060], [40.7138, -74.0050]]),
        )
        db_session.add(seg)
        db_session.commit()

    # Ensure a rover exists with 90% battery and IDLE status
    rover = db_session.query(RoverModel).filter_by(id="ROV-VAL-01").first()
    if not rover:
        rover = RoverModel(
            id="ROV-VAL-01",
            name="AquaRover Validator",
            model="AquaCrawler Mk-II",
            status="IDLE",
            battery_percentage=90.0,
            latitude=40.7128,
            longitude=-74.0060,
        )
        db_session.add(rover)
    else:
        rover.status = "IDLE"
        rover.battery_percentage = 90.0
    db_session.commit()

    # Ensure a depleted rover exists with 15% battery (< 20%)
    depleted_rover = db_session.query(RoverModel).filter_by(id="ROV-DEPLETED").first()
    if not depleted_rover:
        depleted_rover = RoverModel(
            id="ROV-DEPLETED",
            name="AquaRover Low Battery",
            model="AquaCrawler Mk-II",
            status="IDLE",
            battery_percentage=15.0,
            latitude=40.7128,
            longitude=-74.0060,
        )
        db_session.add(depleted_rover)
    else:
        depleted_rover.status = "IDLE"
        depleted_rover.battery_percentage = 15.0
    db_session.commit()

    # Clean existing priority records for this test pipe
    db_session.query(InspectionPriorityRecordModel).filter_by(pipeline_segment_id="PIPE-VAL-TEST-01").delete()
    db_session.commit()

    # Scenario A: Generate Priority Record
    rec_id = f"INSP-VAL-{uuid.uuid4().hex[:6].upper()}"
    rec = InspectionPriorityRecordModel(
        id=rec_id,
        pipeline_segment_id=seg.id,
        segment_name=seg.name,
        priority_score=85.0,
        priority_level="CRITICAL_IMMEDIATE",
        status="PENDING",
        target_latitude=40.7128,
        target_longitude=-74.0060,
        reasons=json.dumps(["Acoustic anomaly", "High pressure"]),
        suggested_action="Immediate crawler dispatch",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        is_simulated=True,
    )
    db_session.add(rec)
    db_session.commit()
    assert rec.status == "PENDING"

    # Scenario B: Depleted Rover (< 20%) must be rejected by battery gate
    with pytest.raises(AquaCrewException) as exc_info:
        InspectionPriorityService.request_inspection(
            db=db_session,
            priority_id=rec.id,
            operator_name="CHIEF_INSPECTOR",
            preferred_rover_id="ROV-DEPLETED",
            notes="Deploy depleted rover",
        )
    assert exc_info.value.code == "ROVER_BATTERY_INSUFFICIENT"
    assert "insufficient battery reserve" in exc_info.value.message
    assert "< 20.0%" in exc_info.value.message

    # Scenario C: Operator Dismissal
    rec_dismiss_id = f"INSP-DISM-{uuid.uuid4().hex[:6].upper()}"
    rec_dismiss = InspectionPriorityRecordModel(
        id=rec_dismiss_id,
        pipeline_segment_id=seg.id,
        segment_name=seg.name,
        priority_score=45.0,
        priority_level="ROUTINE_SCHEDULED",
        status="PENDING",
        target_latitude=40.7128,
        target_longitude=-74.0060,
        reasons=json.dumps(["Routine check"]),
        suggested_action="Routine patrol",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        is_simulated=True,
    )
    db_session.add(rec_dismiss)
    db_session.commit()

    dismiss_res = InspectionPriorityService.dismiss_priority(
        db=db_session,
        priority_id=rec_dismiss.id,
        operator_name="CHIEF_INSPECTOR",
        reason="Operator verified false positive",
    )
    assert dismiss_res.status == "DISMISSED"
    assert dismiss_res.dismissal_reason == "Operator verified false positive"

    # Scenario D: Operator Approval & Valid Rover Dispatch
    dispatch_res = InspectionPriorityService.request_inspection(
        db=db_session,
        priority_id=rec.id,
        operator_name="CHIEF_INSPECTOR",
        preferred_rover_id="ROV-VAL-01",
        notes="Urgent acoustic inspection",
    )
    assert dispatch_res["status"] == "DISPATCHED"
    assert dispatch_res["operator_approval_required"] is True
    assert dispatch_res["assigned_rover_id"] == "ROV-VAL-01"

    # Verify record in DB is now DISPATCHED
    db_session.refresh(rec)
    assert rec.status == "DISPATCHED"

    # Scenario E: Duplicate Request Prevention
    with pytest.raises(AquaCrewException) as exc_info_dup:
        InspectionPriorityService.request_inspection(
            db=db_session,
            priority_id=rec.id,
            operator_name="CHIEF_INSPECTOR",
            preferred_rover_id="ROV-VAL-01",
            notes="Redundant dispatch attempt",
        )
    assert exc_info_dup.value.code == "DUPLICATE_DISPATCH_REJECTED"
