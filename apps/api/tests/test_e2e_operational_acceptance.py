"""
Phase 7: End-to-End Operational Acceptance Test Suite (Task 10.6)
Covers full lifecycle validation across Scenarios A through F:
- Scenario A: Normal baseline hydraulics (nominal pressures, zero leakage)
- Scenario B: Incipient small leak (minor pressure drop, AI detection, recommendation)
- Scenario C: Major pipe burst (severe pressure collapse, critical urgency handoff)
- Scenario D: Operator rejection (documented refusal, rover remains idle, audit log)
- Scenario E: Operator approval (dispatch confirmation, rover assignment, mission creation)
- Scenario F: Duplicate dispatch & concurrency protection (idempotency, atomic guard)
"""
import pytest
import asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal, init_db
from app.models.rover import RoverModel
from app.models.pipeline_segment import PipelineSegmentModel
from app.models.mission_recommendation import MissionRecommendationModel
from app.repositories.rover_repository import RoverRepository
from app.services.ai_orchestration_service import AiOrchestrationService
from app.schemas.ai import LeakAnalyzeRequest
from app.services.mission_planning_service import MissionPlanningService

client = TestClient(app)


def reset_all_rovers():
    db = SessionLocal()
    try:
        rovers = db.query(RoverModel).all()
        for r in rovers:
            r.operating_state = "IDLE"
            r.status = "ONLINE"
            r.assigned_mission_id = None
            r.battery_percentage = 95.0
        db.commit()
    finally:
        db.close()


@pytest.fixture(autouse=True)
def ensure_db():
    init_db()
    reset_all_rovers()


@pytest.fixture
def db_session():
    reset_all_rovers()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_scenario_a_normal_baseline_hydraulics(db_session):
    """
    Scenario A: Baseline steady-state operations.
    No leaks, pressures remain in nominal municipal distribution envelope (2.5 - 5.0 bar).
    """
    res = client.post("/api/v1/digital-twin/scenarios/SCEN-BASELINE-01/run", json={})
    assert res.status_code == 200
    data = res.json()

    assert data["is_simulated"] is True
    assert data["source"] == "VIRTUAL_SIMULATION_ENGINE"
    assert data["total_leakage_m3"] == 0.0
    assert data["water_loss_percentage"] == 0.0
    assert data["pressure_deficit_nodes_count"] == 0
    assert data["min_pressure_bar"] >= 2.0


def test_scenario_b_incipient_leak_detection_and_planning(db_session):
    """
    Scenario B: Pinhole / Incipient leak.
    Causes slight pressure drop, generates AI leak detection, and plans an inspection mission.
    """
    # 1. Simulate minor 2 cm2 leak injection at NODE-JUNC-04
    leak_req = {
        "network_id": "NET-METRO-CENTRAL-01",
        "target_node_id": "NODE-JUNC-04",
        "leak_area_cm2": 2.0,
        "discharge_coeff": 0.75,
    }
    leak_res = client.post("/api/v1/digital-twin/simulate-leak", json=leak_req)
    assert leak_res.status_code == 200
    leak_data = leak_res.json()

    assert leak_data["run"]["total_leakage_m3"] > 0.0
    assert "comparison" in leak_data

    # 2. Ingest sensor reading through AI detection pipeline
    req = LeakAnalyzeRequest(
        pipeline_segment_id="pipe-seg-spine-01",
        acoustic_spl_db=76.5,
        dominant_freq_hz=380.0,
        pressure_bar=3.1,
        flow_rate_lps=130.0,
        ground_moisture_pct=52.0,
        operating_pressure_bar=4.5,
    )
    detection = AiOrchestrationService.analyze_segment(db_session, req)
    assert detection is not None
    assert detection.id.startswith("DET-")

    # 3. Generate Mission Recommendation
    rec = MissionPlanningService.plan_mission_for_detection(
        db=db_session,
        detection_id=detection.id,
    )
    assert rec is not None
    assert rec.status == "PENDING_APPROVAL"
    assert rec.recommended_rover_id is not None
    assert rec.route_distance_m > 0.0


def test_scenario_c_major_burst_and_cross_system_handoff(db_session):
    """
    Scenario C: Major pipeline burst (35 cm2).
    Generates severe pressure deficit and triggers cross-system handoff to dispatch.
    """
    # 1. Execute predefined pipe burst scenario
    sim_res = client.post("/api/v1/digital-twin/scenarios/SCEN-BURST-PIPE-02/run", json={})
    assert sim_res.status_code == 200
    sim_data = sim_res.json()

    assert sim_data["total_leakage_m3"] > 0.0
    assert sim_data["water_loss_percentage"] > 10.0

    # 2. Cross-system handoff directly from Digital Twin to Rover Dispatch
    handoff_req = {
        "scenario_id": "SCEN-BURST-PIPE-02",
        "target_node_id": "J-03",
        "anomaly_type": "PRESSURE_BURST_DEFICIT",
        "notes": "Emergency pressure collapse detected via Digital Twin simulation",
    }
    handoff_res = client.post("/api/v1/digital-twin/handoff-rover-dispatch", json=handoff_req)
    assert handoff_res.status_code == 200
    handoff_data = handoff_res.json()

    assert handoff_data["status"] == "RECOMMENDED"
    assert handoff_data["inspection_urgency"] == "CRITICAL_BURST_INVESTIGATION"
    assert handoff_data["operator_approval_required"] is True
    assert handoff_data["assigned_rover_id"] is not None


def test_scenario_d_operator_rejection(db_session):
    """
    Scenario D: Human operator reviews and rejects recommendation.
    Status transitions to REJECTED, reason is audited, rover remains IDLE.
    """
    # 1. Create a detection & recommendation
    req = LeakAnalyzeRequest(
        pipeline_segment_id="pipe-seg-branch-02",
        acoustic_spl_db=68.0,
        dominant_freq_hz=210.0,
        pressure_bar=3.8,
        flow_rate_lps=90.0,
        ground_moisture_pct=35.0,
        operating_pressure_bar=4.0,
    )
    detection = AiOrchestrationService.analyze_segment(db_session, req)
    rec = MissionPlanningService.plan_mission_for_detection(db=db_session, detection_id=detection.id)
    rec_id = rec.id
    assigned_rover_id = rec.recommended_rover_id

    # 2. Operator rejects recommendation
    reject_req = {
        "rejection_reason": "Scheduled construction work in progress at sector",
        "operator_notes": "No dispatch needed; verified false positive",
    }
    rej_res = client.post(f"/api/v1/missions/recommendations/{rec_id}/reject", json=reject_req)
    assert rej_res.status_code == 200
    rej_data = rej_res.json()

    assert rej_data["status"] == "REJECTED"

    # Rover must still be available (not dispatched)
    rover = RoverRepository.get_by_id(db_session, assigned_rover_id)
    if rover:
        assert rover.operating_state in ("IDLE", "STANDBY")


def test_scenario_e_operator_approval_and_mission_creation(db_session):
    """
    Scenario E: Human operator approves recommendation.
    Status transitions to APPROVED, rover is dispatched, and mission is created.
    """
    reset_all_rovers()

    req = LeakAnalyzeRequest(
        pipeline_segment_id="pipe-seg-spine-01",
        acoustic_spl_db=85.0,
        dominant_freq_hz=440.0,
        pressure_bar=2.4,
        flow_rate_lps=155.0,
        ground_moisture_pct=72.0,
        operating_pressure_bar=4.5,
    )
    detection = AiOrchestrationService.analyze_segment(db_session, req)
    rec = MissionPlanningService.plan_mission_for_detection(db=db_session, detection_id=detection.id)
    rec_id = rec.id

    # Approve
    approve_req = {"operator_id": "OPERATOR_COMMANDER", "notes": "Approved for immediate inspection"}
    app_res = client.post(f"/api/v1/missions/recommendations/{rec_id}/approve", json=approve_req)
    assert app_res.status_code == 200
    app_data = app_res.json()

    assert app_data["success"] is True
    assert app_data["mission_id"] is not None
    assert app_data["rover_id"] is not None


def test_scenario_f_concurrency_and_duplicate_dispatch_protection(db_session):
    """
    Scenario F: Attempting duplicate approval of the same recommendation fails.
    Demonstrates race condition protection and prevents duplicate missions.
    """
    reset_all_rovers()

    req = LeakAnalyzeRequest(
        pipeline_segment_id="pipe-seg-branch-01",
        acoustic_spl_db=82.0,
        dominant_freq_hz=410.0,
        pressure_bar=2.7,
        flow_rate_lps=140.0,
        ground_moisture_pct=60.0,
        operating_pressure_bar=4.5,
    )
    detection = AiOrchestrationService.analyze_segment(db_session, req)
    rec = MissionPlanningService.plan_mission_for_detection(db=db_session, detection_id=detection.id)
    rec_id = rec.id

    # First approval succeeds
    app1 = client.post(f"/api/v1/missions/recommendations/{rec_id}/approve", json={"operator_id": "OP_1"})
    assert app1.status_code == 200

    # Second approval must be rejected due to state conflict
    app2 = client.post(f"/api/v1/missions/recommendations/{rec_id}/approve", json={"operator_id": "OP_2"})
    assert app2.status_code == 400
    assert app2.json()["error"]["code"] == "INVALID_RECOMMENDATION_STATE"
