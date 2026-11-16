"""
AQUA CREW — End-to-End Integration, Reliability & Workflow Validation Test Suite (Task 08.5)
Validates the complete operational continuum:
Simulated Sensor Reading -> AI Leak Detection -> Risk Assessment -> Mission Prioritization
-> Rover Eligibility -> Pipeline Routing -> Mission Recommendation -> Human Operator Approval
-> Rover Dispatch -> Kinematic Simulation Execution -> Telemetry -> Mission Completion -> Audit History
"""
import pytest
import json
import asyncio
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.ai_detection import AiDetectionModel
from app.models.mission_recommendation import MissionRecommendationModel
from app.models.mission import MissionModel
from app.models.rover import RoverModel
from app.models.event import AuditEventModel
from app.schemas.ai import LeakAnalyzeRequest
from app.services.ai_orchestration_service import AiOrchestrationService
from app.services.mission_planning_service import MissionPlanningService
from app.services.mission_service import MissionService
from app.services.simulation_service import SimulationService
from app.websocket.connection_manager import ws_manager
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
# 1. COMPLETE AI-TO-ROVER WORKFLOW VALIDATION (STEPS 1 - 9)
# ==============================================================================

def test_complete_ai_to_rover_workflow(db_session):
    """
    Validates complete operational workflow:
    1. Sensor Ingestion & AI Detection
    2. Mission Priority Scoring
    3. Rover Eligibility Verification
    4. Dijkstra Pipeline Routing
    5. Mission Recommendation Generation (PENDING_APPROVAL)
    6. Human Operator Approval Gate
    7. Rover Dispatch & State Transition
    8. Kinematic Simulation Traversal & Progress
    9. Mission Completion & Audit Persistence
    """
    # Ensure ROV-AQUA-01 is IDLE and has full battery for this test
    rover = db_session.query(RoverModel).filter(RoverModel.id == "ROV-AQUA-01").first()
    assert rover is not None, "ROV-AQUA-01 must exist in test database"
    rover.operating_state = "IDLE"
    rover.status = "ONLINE"
    rover.battery_percentage = 95.0
    rover.motor_temp_c = 28.0
    rover.assigned_mission_id = None
    rover.latitude = 40.7128
    rover.longitude = -74.0060
    db_session.commit()

    # -------------------------------------------------------------------------
    # STEP 1: AI DETECTION & RISK ASSESSMENT (Task 07 Pipeline)
    # -------------------------------------------------------------------------
    req = LeakAnalyzeRequest(
        pipeline_segment_id="pipe-seg-spine-01",
        acoustic_spl_db=84.5,
        dominant_freq_hz=420.0,
        pressure_bar=2.6,
        flow_rate_lps=145.0,
        ground_moisture_pct=68.0,
        operating_pressure_bar=4.5,
    )
    detection = AiOrchestrationService.analyze_segment(db_session, req)
    assert detection is not None
    assert detection.id.startswith("DET-")
    assert detection.pipeline_segment_id == "pipe-seg-spine-01"
    assert detection.classification in ["MEDIUM_LEAK_PROBABILITY", "HIGH_LEAK_PROBABILITY"]
    assert detection.risk_level in ["HIGH", "CRITICAL"]
    assert detection.estimated_latitude is not None
    assert detection.estimated_longitude is not None
    assert detection.is_simulated is True
    assert detection.source == "VIRTUAL_SIMULATION_ENGINE"

    # Verify persisted in database
    persisted_det = db_session.query(AiDetectionModel).filter(AiDetectionModel.id == detection.id).first()
    assert persisted_det is not None

    # -------------------------------------------------------------------------
    # STEP 2 & 3: MISSION PRIORITIZATION & ROVER ELIGIBILITY (Task 08 Engine)
    # -------------------------------------------------------------------------
    rec = MissionPlanningService.plan_mission_for_detection(
        db=db_session,
        detection_id=detection.id,
    )
    assert rec is not None
    assert rec.detection_id == detection.id
    assert rec.priority_category in ["CRITICAL", "HIGH", "MEDIUM"]
    assert rec.priority_score >= 50.0
    assert rec.status == "PENDING_APPROVAL"

    # -------------------------------------------------------------------------
    # STEP 4 & 5: PIPELINE ROUTING & RECOMMENDATION GENERATION
    # -------------------------------------------------------------------------
    assert rec.route_distance_m > 0
    assert rec.estimated_duration_s > 0
    assert rec.estimated_energy_pct > 0
    assert rec.battery_reserve_after_pct >= 20.0
    waypoints = json.loads(rec.route_waypoints_json)
    assert len(waypoints) >= 2, "Route must contain at least start and destination waypoints"
    assert rec.recommended_rover_id == "ROV-AQUA-01"

    # A mission must NEVER have executed yet
    assert rec.assigned_mission_id is None

    # -------------------------------------------------------------------------
    # STEP 6: HUMAN OPERATOR APPROVAL GATE
    # -------------------------------------------------------------------------
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    approval_res = loop.run_until_complete(
        MissionPlanningService.approve_recommendation(
            db=db_session,
            recommendation_id=rec.id,
            operator_id="QA_OPERATOR_01",
            notes="Acoustic signature cross-verified. Authorized for autonomous inspection.",
        )
    )
    assert approval_res["success"] is True
    mission_id = approval_res["mission_id"]

    # -------------------------------------------------------------------------
    # STEP 7: ROVER DISPATCH & MISSION PERSISTENCE
    # -------------------------------------------------------------------------
    db_session.refresh(rec)
    db_session.refresh(rover)
    assert rec.status == "APPROVED"
    assert rec.approved_by == "QA_OPERATOR_01"
    assert rover.operating_state == "INSPECTING"
    assert rover.assigned_mission_id == mission_id

    mission = db_session.query(MissionModel).filter(MissionModel.id == mission_id).first()
    assert mission is not None
    assert mission.assigned_rover_id == rover.id
    assert mission.status == "In Progress"
    assert mission.progress_percentage == 0
    assert mission.inspected_distance_m == 0.0

    # Verify audit event
    audit = db_session.query(AuditEventModel).filter(
        AuditEventModel.mission_id == mission_id,
        AuditEventModel.event_type == "MISSION_APPROVED_AND_DISPATCHED"
    ).first()
    assert audit is not None
    assert "QA_OPERATOR_01" in audit.details

    # -------------------------------------------------------------------------
    # STEP 8: SIMULATED EXECUTION (SimulationService Kinematics)
    # -------------------------------------------------------------------------
    sim = SimulationService.get_instance()
    sim.initialize_kinematics(db_session)

    # Advance discrete simulation tick
    loop.run_until_complete(sim.execute_tick())
    db_session.refresh(rover)
    db_session.refresh(mission)

    # Rover velocity should ramp up for INSPECTING
    assert rover.velocity_mps > 0
    assert rover.battery_percentage < 95.0, "Battery should discharge during traversal"
    assert rover.motor_temp_c >= 28.0

    # -------------------------------------------------------------------------
    # STEP 9: MISSION COMPLETION SIMULATION
    # -------------------------------------------------------------------------
    # Simulate completion by setting route progress to 100%
    rover.route_progress_pct = 100
    db_session.commit()

    loop.run_until_complete(sim.execute_tick())
    db_session.refresh(mission)
    assert mission.status == "Completed"
    assert mission.progress_percentage == 100
    assert mission.completed_waypoints == mission.waypoint_count

    # Cleanup event loop
    loop.close()


# ==============================================================================
# 2. CONCURRENT DISPATCH & DATABASE TRANSACTION INTEGRITY
# ==============================================================================

def test_concurrent_approval_protection(db_session):
    """
    Validates that:
    1. A recommendation cannot be approved twice.
    2. Two concurrent approvals cannot assign the same rover to conflicting missions.
    """
    rover = db_session.query(RoverModel).filter(RoverModel.id == "ROV-AQUA-02").first()
    assert rover is not None
    rover.operating_state = "IDLE"
    rover.battery_percentage = 90.0
    rover.assigned_mission_id = None
    db_session.commit()

    # Create recommendation 1
    req1 = LeakAnalyzeRequest(
        pipeline_segment_id="pipe-seg-trunk-b",
        acoustic_spl_db=79.0,
        pressure_bar=3.1,
    )
    det1 = AiOrchestrationService.analyze_segment(db_session, req1)
    rec1 = MissionPlanningService.plan_mission_for_detection(
        db_session, det1.id, preferred_rover_id="ROV-AQUA-02"
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # First approval must succeed
    res1 = loop.run_until_complete(
        MissionPlanningService.approve_recommendation(db_session, rec1.id, "OPERATOR_A")
    )
    assert res1["success"] is True

    # Repeated approval on the SAME recommendation must fail
    with pytest.raises(AquaCrewException) as exc_info:
        loop.run_until_complete(
            MissionPlanningService.approve_recommendation(db_session, rec1.id, "OPERATOR_B")
        )
    assert exc_info.value.code == "INVALID_RECOMMENDATION_STATE"

    # Now create recommendation 2 for a different leak that also wants ROV-AQUA-02
    req2 = LeakAnalyzeRequest(
        pipeline_segment_id="pipe-seg-ind-01",
        acoustic_spl_db=72.0,
        pressure_bar=3.4,
    )
    det2 = AiOrchestrationService.analyze_segment(db_session, req2)
    rec2 = MissionPlanningService.plan_mission_for_detection(
        db_session, det2.id, preferred_rover_id="ROV-AQUA-02"
    )

    # Approval of rec2 must FAIL because ROV-AQUA-02 is now INSPECTING
    with pytest.raises(AquaCrewException) as exc_info2:
        loop.run_until_complete(
            MissionPlanningService.approve_recommendation(db_session, rec2.id, "OPERATOR_C")
        )
    assert exc_info2.value.code in ["ROVER_NOT_IDLE", "ROVER_ALREADY_ASSIGNED"]

    loop.close()


# ==============================================================================
# 3. OPERATOR REJECTION & RECALCULATION
# ==============================================================================

def test_operator_rejection_and_recalculation(db_session):
    """
    Validates:
    1. Operator rejection with mandatory reason.
    2. Recalculation updating route, priority, and rover suitability.
    """
    req = LeakAnalyzeRequest(
        pipeline_segment_id="pipe-seg-feeder-w2",
        acoustic_spl_db=68.0,
        pressure_bar=3.6,
    )
    det = AiOrchestrationService.analyze_segment(db_session, req)
    rec = MissionPlanningService.plan_mission_for_detection(db_session, det.id)
    assert rec.status == "PENDING_APPROVAL"

    # Test Recalculation
    recalc = MissionPlanningService.recalculate_recommendation(db_session, rec.id)
    assert recalc.id == rec.id
    assert recalc.status == "PENDING_APPROVAL"
    assert "Recalculated" in recalc.explanation

    # Test Rejection
    rejected = MissionPlanningService.reject_recommendation(
        db_session,
        recommendation_id=rec.id,
        reason="Scheduled physical trench inspection already planned by utility crew.",
        operator_notes="Work order #WO-9918",
    )
    assert rejected.status == "REJECTED"
    assert rejected.rejection_reason == "Scheduled physical trench inspection already planned by utility crew."
    assert rejected.operator_notes == "Work order #WO-9918"

    # Cannot recalculate or approve a REJECTED recommendation
    with pytest.raises(AquaCrewException) as exc_recalc:
        MissionPlanningService.recalculate_recommendation(db_session, rec.id)
    assert exc_recalc.value.code == "INVALID_RECOMMENDATION_STATE"


# ==============================================================================
# 4. FAILURE AND RECOVERY SCENARIOS
# ==============================================================================

def test_failure_insufficient_battery_blocks_dispatch(db_session):
    """
    Scenario: Rover battery drops below mission requirement + 15% safety reserve.
    Must reject dispatch.
    """
    rover = db_session.query(RoverModel).filter(RoverModel.id == "ROV-AQUA-04").first()
    assert rover is not None
    rover.operating_state = "IDLE"
    rover.battery_percentage = 18.0  # Depleted
    rover.assigned_mission_id = None
    db_session.commit()

    req = LeakAnalyzeRequest(
        pipeline_segment_id="pipe-seg-spine-01",
        acoustic_spl_db=88.0,
        pressure_bar=2.4,
    )
    det = AiOrchestrationService.analyze_segment(db_session, req)
    rec = MissionPlanningService.plan_mission_for_detection(
        db_session, det.id, preferred_rover_id="ROV-AQUA-04"
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with pytest.raises(AquaCrewException) as exc:
        loop.run_until_complete(
            MissionPlanningService.approve_recommendation(db_session, rec.id, "OPERATOR_SAFE")
        )
    assert exc.value.code == "INSUFFICIENT_BATTERY"
    loop.close()


def test_failure_rover_offline_blocks_dispatch(db_session):
    """
    Scenario: Rover becomes OFFLINE or enters ERROR before operator approval.
    """
    rover = db_session.query(RoverModel).filter(RoverModel.id == "ROV-AQUA-04").first()
    assert rover is not None
    rover.operating_state = "ERROR"
    db_session.commit()

    req = LeakAnalyzeRequest(
        pipeline_segment_id="pipe-seg-spine-01",
        acoustic_spl_db=76.0,
        pressure_bar=3.2,
    )
    det = AiOrchestrationService.analyze_segment(db_session, req)
    rec = MissionPlanningService.plan_mission_for_detection(
        db_session, det.id, preferred_rover_id="ROV-AQUA-04"
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with pytest.raises(AquaCrewException) as exc:
        loop.run_until_complete(
            MissionPlanningService.approve_recommendation(db_session, rec.id, "OPERATOR_SAFE")
        )
    assert exc.value.code == "ROVER_NOT_IDLE"
    loop.close()


def test_failure_mission_interruption_cancellation(db_session):
    """
    Scenario: Operator cancels an active in-progress mission.
    Rover must transition to IDLE and mission status set to Cancelled.
    """
    rover = db_session.query(RoverModel).filter(RoverModel.id == "ROV-AQUA-01").first()
    rover.operating_state = "IDLE"
    rover.battery_percentage = 90.0
    rover.assigned_mission_id = None
    db_session.commit()

    # Create dummy active mission
    import uuid
    mission_id = f"MSN-CANCEL-{uuid.uuid4().hex[:6]}"
    mission = MissionModel(
        id=mission_id,
        assigned_rover_id=rover.id,
        assigned_rover_name=rover.name,
        mission_type="Emergency Inspection",
        status="In Progress",
        target_segment_id="pipe-seg-spine-01",
        is_simulated=True,
    )
    db_session.add(mission)
    rover.assigned_mission_id = mission_id
    rover.operating_state = "INSPECTING"
    db_session.commit()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res = loop.run_until_complete(
        MissionService.update_mission_status(
            db=db_session,
            mission_id=mission_id,
            new_status="Cancelled",
            reason="Aborted due to sudden water main pressure surge upstream.",
        )
    )
    assert res["success"] is True

    db_session.refresh(mission)
    db_session.refresh(rover)
    assert mission.status == "Cancelled"
    assert rover.operating_state == "IDLE"
    assert rover.assigned_mission_id is None
    loop.close()


# ==============================================================================
# 5. WEBSOCKET BROADCASTING & LIFECYCLE
# ==============================================================================

def test_websocket_connection_and_broadcast():
    """
    Validates WebSocket subscriber connection, handshake packet, and broadcasting.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        # Handshake packet
        data = ws.receive_json()
        assert data["type"] == "CONNECTION_ESTABLISHED"
        assert data["is_simulated"] is True
        assert data["provenance"] == "VIRTUAL_SIMULATION_BACKEND"

        # Broadcast test message via connection manager
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        test_payload = {
            "type": "INTEGRATION_TEST_EVENT",
            "message": "Task 08.5 WebSocket reliability verified.",
            "is_simulated": True,
        }
        loop.run_until_complete(ws_manager.broadcast(test_payload))

        received = ws.receive_json()
        assert received["type"] == "INTEGRATION_TEST_EVENT"
        assert received["message"] == "Task 08.5 WebSocket reliability verified."
        loop.close()
