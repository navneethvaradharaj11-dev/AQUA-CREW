"""
AQUA CREW — Comprehensive Test Suite for Task 12
Unified Operational Intelligence & Decision Support Platform
Covers:
  - Multi-system operational assessment generation
  - Explainable recommendation categories & 10 core questions
  - Deterministic priority engine with component separation
  - Cross-system incident correlation engine (confirmed, potential, coincidence, insufficient)
  - Digital twin hydraulic impact what-if analysis
  - Virtual rover fleet suitability & safety gates (battery >= 20%, temp < 65°C)
  - Human-in-the-loop decision lifecycle (approval, rejection, duplicate protection, audit hash)
  - REST API contracts under /api/v1/operational-intelligence
"""
import pytest
import json
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal, init_db
from app.models.pipeline_segment import PipelineSegmentModel
from app.models.ai_detection import AiDetectionModel
from app.models.predictive_maintenance import PipelineHealthModel, PredictiveRiskModel
from app.models.infrastructure_intelligence import PipelineVulnerabilityProfileModel, SpatialIncidentClusterModel
from app.models.rover import RoverModel
from app.models.mission import MissionModel
from app.models.operational_intelligence import (
    OperationalAssessmentModel,
    OperationalRecommendationModel,
    OperationalDecisionModel,
    OperationalPriorityModel,
    OperationalImpactAssessmentModel,
    OperationalEvidenceReferenceModel,
    OperationalExecutionRecordModel,
)
from app.services.operational_intelligence.operational_prioritisation_service import OperationalPrioritisationService
from app.services.operational_intelligence.incident_correlation_service import IncidentCorrelationService
from app.services.operational_intelligence.operational_hydraulic_impact_service import OperationalHydraulicImpactService
from app.services.operational_intelligence.operational_resource_planning_service import OperationalResourcePlanningService
from app.services.operational_intelligence.operational_impact_service import OperationalImpactService
from app.services.operational_intelligence.operational_decision_service import OperationalDecisionService
from app.services.operational_intelligence.operational_intelligence_service import OperationalIntelligenceService
from app.core.exceptions import AquaCrewException


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


@pytest.fixture
def db_session():
    init_db()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ============================================================================
# 1. PRIORITY ENGINE TESTS (PHASE 5)
# ============================================================================

def test_priority_engine_deterministic_calculation():
    """Validates deterministic priority scoring with separate criteria components."""
    res = OperationalPrioritisationService.calculate_priority(
        incident_severity=85.0,
        vulnerability_score=75.0,
        health_score=35.0,  # deficit = 65.0
        hydraulic_impact=50.0,
        diameter_mm=600,     # crit = 100.0
        historical_incident_count=3,  # recurrence = 60.0
        confidence=0.90,
    )

    score = res["composite_priority_score"]
    assert 0.0 <= score <= 100.0
    assert res["priority_tier"] in ["CRITICAL_IMMEDIATE", "URGENT", "HIGH_PRIORITY", "ROUTINE", "DEFERRED"]
    assert res["components"]["service_criticality"] == 100.0
    assert res["components"]["asset_health_deficit"] == 65.0
    assert res["components"]["incident_severity"] == 85.0
    assert res["confidence_weight"] == 0.90


def test_priority_engine_boundary_tiers():
    """Tests exact priority tier transition thresholds."""
    # Test Tier 1: CRITICAL_IMMEDIATE (>= 80.0)
    p_crit = OperationalPrioritisationService.calculate_priority(
        incident_severity=100.0, vulnerability_score=100.0, health_score=0.0,
        hydraulic_impact=100.0, diameter_mm=600, historical_incident_count=5, confidence=1.0,
    )
    assert p_crit["composite_priority_score"] >= 80.0
    assert p_crit["priority_tier"] == "CRITICAL_IMMEDIATE"

    # Test Tier 2: ROUTINE (< 50.0, >= 30.0)
    p_routine = OperationalPrioritisationService.calculate_priority(
        incident_severity=0.0, vulnerability_score=20.0, health_score=90.0,
        hydraulic_impact=10.0, diameter_mm=200, historical_incident_count=0, confidence=1.0,
    )
    assert p_routine["composite_priority_score"] < 50.0
    assert p_routine["priority_tier"] in ["ROUTINE", "DEFERRED"]


def test_priority_ranking_monotonicity():
    """Ensures higher priority scores sort first in descending order."""
    items = [
        {"id": "A", "priority_score": 45.0, "created_at": "2026-11-16T10:00:00Z"},
        {"id": "B", "priority_score": 92.5, "created_at": "2026-11-16T10:01:00Z"},
        {"id": "C", "priority_score": 68.0, "created_at": "2026-11-16T10:02:00Z"},
    ]
    ranked = OperationalPrioritisationService.rank_recommendations(items)
    assert ranked[0]["id"] == "B"
    assert ranked[0]["rank_position"] == 1
    assert ranked[1]["id"] == "C"
    assert ranked[1]["rank_position"] == 2
    assert ranked[2]["id"] == "A"
    assert ranked[2]["rank_position"] == 3


# ============================================================================
# 2. INCIDENT CORRELATION ENGINE TESTS (PHASE 4)
# ============================================================================

def test_incident_correlation_confirmed_co_occurrence():
    """Acoustic leak + local pressure drop + moisture spike = CONFIRMED_RELATIONSHIP."""
    detections = [{
        "id": "DET-001",
        "pipeline_segment_id": "PIPE-01",
        "anomaly_score": 0.88,
        "classification": "HIGH_LEAK_PROBABILITY",
    }]
    sensors = [
        {"pipe_segment_id": "PIPE-01", "pressure_psi": 38.0, "ground_moisture_pct": 42.0}
    ]

    corrs = IncidentCorrelationService.correlate_events(
        primary_segment_id="PIPE-01",
        primary_segment_name="Grand Spine Arterial",
        detections=detections,
        sensor_readings=sensors,
    )

    assert len(corrs) >= 1
    corr = corrs[0]
    assert corr["correlation_type"] == "CONFIRMED_RELATIONSHIP"
    assert corr["correlation_strength"] >= 0.85
    assert corr["uncertainty"] <= 0.15
    assert "confirming active physical pipe orifice discharge" in corr["explanation"]


def test_incident_correlation_insufficient_evidence():
    """No active detections or pressure anomalies = INSUFFICIENT_EVIDENCE."""
    corrs = IncidentCorrelationService.correlate_events(
        primary_segment_id="PIPE-CLEAN-01",
        primary_segment_name="Clean Distribution Feeder",
        detections=[],
        sensor_readings=[],
    )

    assert len(corrs) == 1
    assert corrs[0]["correlation_type"] == "INSUFFICIENT_EVIDENCE"
    assert corrs[0]["correlation_strength"] <= 0.30


def test_incident_correlation_haversine_accuracy():
    """Verifies Haversine distance with antimeridian wrap."""
    # Two points across antimeridian
    dist = IncidentCorrelationService.haversine_distance(0.0, 179.999, 0.0, -179.999)
    # 0.002 degrees longitude at equator approx 222 meters
    assert 200.0 < dist < 250.0


# ============================================================================
# 3. HYDRAULIC WHAT-IF & IMPACT TESTS (PHASE 6 & 9)
# ============================================================================

def test_hydraulic_what_if_torricelli_discharge():
    """Validates physics-based Torricelli orifice discharge and pressure drop estimation."""
    res = OperationalHydraulicImpactService.evaluate_leak_impact(
        db=None,
        pipeline_segment_id="PIPE-SEC-4B-92",
        leak_orifice_diameter_mm=15.0,
        nominal_pressure_bar=4.2,
    )

    assert res["estimated_water_loss_m3_day"] > 50.0
    assert res["min_pressure_drop_bar"] > 0.0
    assert res["service_disruption_risk"] in ["NONE", "LOW", "MODERATE", "SEVERE"]
    assert res["cost_impact_display"] == "NOT AVAILABLE"
    assert res["is_water_loss_measured"] is False
    assert res["simulation_provenance"]["is_simulated"] is True
    assert res["simulation_provenance"]["real_world_actuators_enabled"] is False


def test_operational_impact_service_financial_rule():
    """Confirms no fabricated currency savings are returned."""
    impact = OperationalImpactService.assess_recommendation_impact(
        recommendation_id="REC-TEST-01",
        pipeline_segment_id="PIPE-01",
        diameter_mm=600,
        risk_severity="CRITICAL",
        nominal_pressure_bar=4.5,
    )
    assert impact["cost_impact_display"] == "NOT AVAILABLE"
    assert impact["is_water_loss_measured"] is False
    assert impact["assumptions"]["economic_valuation_status"] == "Omitted per governance rule (no fabricated currency)"


# ============================================================================
# 4. RESOURCE PLANNING & ROVER SAFETY GATES (PHASE 7)
# ============================================================================

def test_rover_safety_gate_battery_threshold(db_session):
    """Enforces battery >= 20.0% safety gate for subterranean inspection."""
    # Seed one healthy rover and one low battery rover
    r_healthy = RoverModel(
        id=f"ROV-HEALTHY-{uuid.uuid4().hex[:6]}",
        name="AquaRover Alpha",
        model="AquaCrawler Mk-II",
        status="ONLINE",
        operating_state="IDLE",
        battery_percentage=90.0,
        motor_temp_c=25.0,
        latitude=40.7128,
        longitude=-74.0060,
        is_simulated=True,
    )
    r_depleted = RoverModel(
        id=f"ROV-DEPLETED-{uuid.uuid4().hex[:6]}",
        name="AquaRover Depleted",
        model="AquaCrawler Mk-II",
        status="ONLINE",
        operating_state="IDLE",
        battery_percentage=14.5,  # < 20.0%
        motor_temp_c=25.0,
        latitude=40.7128,
        longitude=-74.0060,
        is_simulated=True,
    )
    db_session.add(r_healthy)
    db_session.add(r_depleted)
    db_session.commit()

    plan = OperationalResourcePlanningService.evaluate_resources_for_target(
        db=db_session,
        pipeline_segment_id="PIPE-SEC-4B-92",
        segment_name="Metro Central Main Trunk Line B",
    )

    depleted_eval = next(r for r in plan["suitable_rovers"] if r["rover_id"] == r_depleted.id)
    assert depleted_eval["is_eligible"] is False
    assert any("BATTERY_INSUFFICIENT" in reason for reason in depleted_eval["rejection_reasons"])

    healthy_eval = next(r for r in plan["suitable_rovers"] if r["rover_id"] == r_healthy.id)
    assert healthy_eval["is_eligible"] is True
    assert plan["dispatch_feasibility"] == "READY_FOR_DISPATCH"


def test_rover_safety_gate_thermal_threshold(db_session):
    """Enforces motor temperature < 65°C safety gate."""
    r_overheated = RoverModel(
        id=f"ROV-HOT-{uuid.uuid4().hex[:6]}",
        name="AquaRover Hot",
        model="AquaCrawler Mk-II",
        status="ONLINE",
        operating_state="IDLE",
        battery_percentage=85.0,
        motor_temp_c=68.5,  # >= 65.0°C
        latitude=40.7128,
        longitude=-74.0060,
        is_simulated=True,
    )
    db_session.add(r_overheated)
    db_session.commit()

    plan = OperationalResourcePlanningService.evaluate_resources_for_target(
        db=db_session,
        pipeline_segment_id="PIPE-01",
        segment_name="Test Main",
    )

    hot_eval = next(r for r in plan["suitable_rovers"] if r["rover_id"] == r_overheated.id)
    assert hot_eval["is_eligible"] is False
    assert any("MOTOR_OVERHEATED" in reason for reason in hot_eval["rejection_reasons"])


# ============================================================================
# 5. DECISION WORKFLOW & APPROVAL LIFECYCLE (PHASE 8)
# ============================================================================

def test_decision_workflow_approval_creates_mission(db_session):
    """Operator approval of an urgent recommendation schedules a Task 08 mission."""
    # Seed idle rover with sufficient battery
    rover = RoverModel(
        id=f"ROV-OPS-{uuid.uuid4().hex[:6]}",
        name="AquaRover Scout",
        model="AquaCrawler Mk-II",
        status="ONLINE",
        operating_state="IDLE",
        battery_percentage=95.0,
        motor_temp_c=24.0,
        latitude=40.7128,
        longitude=-74.0060,
        is_simulated=True,
    )
    db_session.add(rover)

    rec = OperationalRecommendationModel(
        id=f"REC-{uuid.uuid4().hex[:8]}",
        category="URGENT_LEAK_INVESTIGATION",
        pipeline_segment_id="PIPE-SEC-4B-92",
        segment_name="Metro Central Main Trunk Line B",
        risk_severity="CRITICAL",
        priority_score=88.5,
        priority_tier="CRITICAL_IMMEDIATE",
        recommended_action="Deploy crawler rover",
        why_explanation="Acoustic leak detected",
        what_missing="None",
        expected_impact="Preserves network pressure",
        status="PENDING_REVIEW",
        approval_status="PENDING",
        assigned_rover_id=rover.id,
        is_simulated=True,
    )
    db_session.add(rec)
    db_session.commit()

    # Operator approves recommendation
    res = OperationalDecisionService.process_decision(
        db=db_session,
        recommendation_id=rec.id,
        decision_type="APPROVED",
        decision_reason="Verified by chief engineer. Proceed with crawl.",
        operator_id="OPERATOR-01",
    )

    assert res["success"] is True
    assert res["decision_type"] == "APPROVED"
    assert res["resulting_mission_id"] is not None

    # Check updated recommendation state
    updated_rec = db_session.query(OperationalRecommendationModel).filter_by(id=rec.id).first()
    assert updated_rec.status == "EXECUTION_PENDING"
    assert updated_rec.approval_status == "APPROVED"

    # Check mission created in DB
    mission = db_session.query(MissionModel).filter_by(id=res["resulting_mission_id"]).first()
    assert mission is not None
    assert mission.assigned_rover_id == rover.id

    # Check audit log signature
    decision_log = db_session.query(OperationalDecisionModel).filter_by(id=res["decision_id"]).first()
    assert decision_log is not None
    assert decision_log.audit_hash is not None
    assert len(decision_log.audit_hash) == 64  # SHA-256


def test_decision_workflow_rejection_blocks_mission(db_session):
    """Operator rejection transitions status to REJECTED and NEVER creates a mission."""
    rec = OperationalRecommendationModel(
        id=f"REC-REJ-{uuid.uuid4().hex[:8]}",
        category="PREVENTIVE_MAINTENANCE",
        pipeline_segment_id="PIPE-HRB-02-19",
        segment_name="Harbor Utility Distribution Main",
        risk_severity="HIGH",
        priority_score=68.2,
        priority_tier="URGENT",
        recommended_action="Schedule pipe relining",
        why_explanation="Structural wear",
        what_missing="None",
        expected_impact="Extends life",
        status="PENDING_REVIEW",
        approval_status="PENDING",
        is_simulated=True,
    )
    db_session.add(rec)
    db_session.commit()

    res = OperationalDecisionService.process_decision(
        db=db_session,
        recommendation_id=rec.id,
        decision_type="REJECTED",
        decision_reason="Budget cycle deferred to Q3. Conduit will remain under acoustic watch.",
        operator_id="OPERATOR-01",
    )

    assert res["success"] is True
    assert res["decision_type"] == "REJECTED"
    assert res["resulting_mission_id"] is None

    # Recommendation state is REJECTED
    updated_rec = db_session.query(OperationalRecommendationModel).filter_by(id=rec.id).first()
    assert updated_rec.status == "REJECTED"
    assert updated_rec.approval_status == "REJECTED"


def test_decision_workflow_duplicate_action_rejected(db_session):
    """Enforces concurrency protection: duplicate approval/rejection is rejected with 409."""
    rec = OperationalRecommendationModel(
        id=f"REC-DUP-{uuid.uuid4().hex[:8]}",
        category="CONTINUOUS_MONITORING",
        pipeline_segment_id="PIPE-IND-1A-04",
        segment_name="Industrial Park Southern Feeder",
        risk_severity="LOW",
        priority_score=35.0,
        priority_tier="ROUTINE",
        recommended_action="Maintain logging",
        why_explanation="Normal state",
        what_missing="None",
        expected_impact="Maintains stability",
        status="APPROVED",  # Already approved!
        approval_status="APPROVED",
        is_simulated=True,
    )
    db_session.add(rec)
    db_session.commit()

    with pytest.raises(AquaCrewException) as exc:
        OperationalDecisionService.process_decision(
            db=db_session,
            recommendation_id=rec.id,
            decision_type="APPROVED",
            decision_reason="Second approval attempt",
        )
    assert exc.value.status_code == 409
    assert exc.value.code == "DUPLICATE_DECISION_REJECTED"


def test_decision_workflow_mandatory_reason(db_session):
    """Rejection or approval without adequate reason raises 400 REASON_REQUIRED."""
    rec = OperationalRecommendationModel(
        id=f"REC-BLANK-{uuid.uuid4().hex[:8]}",
        category="CONTINUOUS_MONITORING",
        pipeline_segment_id="PIPE-01",
        segment_name="Test Segment",
        risk_severity="LOW",
        priority_score=30.0,
        priority_tier="ROUTINE",
        recommended_action="Monitor",
        why_explanation="Normal",
        what_missing="None",
        expected_impact="None",
        status="PENDING_REVIEW",
        is_simulated=True,
    )
    db_session.add(rec)
    db_session.commit()

    with pytest.raises(AquaCrewException) as exc:
        OperationalDecisionService.process_decision(
            db=db_session,
            recommendation_id=rec.id,
            decision_type="APPROVED",
            decision_reason="",  # Blank reason
        )
    assert exc.value.status_code == 400
    assert exc.value.code == "REASON_REQUIRED"


# ============================================================================
# 6. REST API ENDPOINTS INTEGRATION TESTS (PHASE 12)
# ============================================================================

def test_api_overview_endpoint(client):
    """GET /api/v1/operational-intelligence/overview returns valid operational snapshot."""
    resp = client.get("/api/v1/operational-intelligence/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "network_health_score" in data
    assert "network_urgency" in data
    assert "available_rovers_count" in data
    assert data["is_simulated"] is True
    assert "REAL-WORLD PHYSICAL ACTUATORS PERMANENTLY DISABLED" in data["actuation_notice"]


def test_api_assessments_run_endpoint(client):
    """POST /api/v1/operational-intelligence/assessments/run runs full assessment."""
    resp = client.post("/api/v1/operational-intelligence/assessments/run")
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["total_recommendations"] >= 1
    assert data["is_simulated"] is True


def test_api_recommendations_list_endpoint(client):
    """GET /api/v1/operational-intelligence/recommendations lists recommendations."""
    resp = client.get("/api/v1/operational-intelligence/recommendations")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert len(data["items"]) >= 1
    rec = data["items"][0]
    assert "why_explanation" in rec
    assert "expected_impact" in rec
    assert "priority_score" in rec


def test_api_what_if_analyze_endpoint(client):
    """POST /api/v1/operational-intelligence/impact/analyze performs hydraulic what-if."""
    resp = client.post(
        "/api/v1/operational-intelligence/impact/analyze",
        json={
            "pipeline_segment_id": "PIPE-SEC-4B-92",
            "leak_orifice_diameter_mm": 20.0,
            "demand_multiplier": 1.0,
            "duration_hours": 24,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["estimated_water_loss_m3_day"] > 0
    assert data["is_water_loss_measured"] is False
    assert data["cost_impact_display"] == "NOT AVAILABLE"
    assert data["simulation_provenance"]["is_simulated"] is True


def test_api_correlations_endpoint(client):
    """GET /api/v1/operational-intelligence/correlations returns cross-system correlations."""
    resp = client.get("/api/v1/operational-intelligence/correlations")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert len(data["items"]) >= 1


def test_api_resource_planning_endpoint(client):
    """GET /api/v1/operational-intelligence/resource-planning returns rover fleet readiness."""
    resp = client.get("/api/v1/operational-intelligence/resource-planning")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_resources_evaluated" in data
    assert len(data["items"]) >= 1
    item = data["items"][0]
    assert "suitable_rovers" in item
    assert "NOT_AVAILABLE" in item["workforce_status"]
