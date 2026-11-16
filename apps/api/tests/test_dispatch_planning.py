"""
AQUA CREW — Autonomous Mission Planning & Intelligent Rover Dispatch Tests (Task 08)
Verifies Priority Engine, Pipeline Routing, Rover Selection, Operator Approval, and Execution.
"""
import pytest
from app.models.ai_detection import AiDetectionModel
from app.models.rover import RoverModel
from app.services.mission_priority_service import MissionPriorityService
from app.services.pipeline_routing_service import PipelineRoutingService, haversine_distance_m
from app.services.rover_selection_service import RoverSelectionService
from app.repositories.pipeline_repository import DEFAULT_PIPELINES


def test_mission_priority_scoring_critical_vs_low():
    # 1. Critical Scenario
    crit_detection = AiDetectionModel(
        id="DET-TEST-CRIT",
        pipeline_segment_id="PIPE-SEC-4B-92",
        risk_level="CRITICAL",
        classification="HIGH_LEAK_PROBABILITY",
        confidence=0.95,
        estimated_loss_lph=2800.0,
        localization_uncertainty_m=12.0,
    )
    pipe_meta = {"category": "primary", "diameter_mm": 600}
    p_crit = MissionPriorityService.calculate_priority(crit_detection, pipe_meta)

    assert p_crit.priority_score >= 90.0
    assert p_crit.priority_category == "CRITICAL"
    assert "risk_severity" in p_crit.contributing_factors
    assert p_crit.contributing_factors["risk_severity"] == 35.0
    assert "Immediate autonomous rover dispatch" in p_crit.recommended_response

    # 2. Low / Negligible Scenario
    low_detection = AiDetectionModel(
        id="DET-TEST-LOW",
        pipeline_segment_id="PIPE-RES-3C-11",
        risk_level="LOW",
        classification="LOW_LEAK_PROBABILITY",
        confidence=0.60,
        estimated_loss_lph=50.0,
        localization_uncertainty_m=40.0,
    )
    p_low = MissionPriorityService.calculate_priority(low_detection, {"category": "distribution"})
    assert p_low.priority_score < 40.0
    assert p_low.priority_category == "LOW"
    assert p_low.uncertainty_warning is not None


def test_pipeline_routing_connected_shortest_path():
    # Rover at station [-74.0089, 40.7198], Target on PIPE-SEC-4B-92 at [-74.0060, 40.7128]
    start_c = [-74.0089, 40.7198]
    dest_c = [-74.0060, 40.7128]

    route = PipelineRoutingService.calculate_route(
        start_coord=start_c,
        target_coord=dest_c,
        pipeline_records=DEFAULT_PIPELINES,
        target_segment_id="PIPE-SEC-4B-92",
        rover_speed_mps=0.55,
        uncertainty_radius_m=14.0,
    )

    assert route.is_connected is True
    assert route.total_distance_m > 0.0
    assert len(route.waypoints) >= 2
    assert route.estimated_travel_time_s > 0.0
    assert route.uncertainty_radius_m == 14.0


def test_pipeline_routing_disconnected_segment_failure():
    # Waypoint in middle of ocean / remote coords not on pipeline graph
    start_c = [-74.0089, 40.7198]
    isolated_dest = [-70.0000, 30.0000]

    route = PipelineRoutingService.calculate_route(
        start_coord=start_c,
        target_coord=isolated_dest,
        pipeline_records=[],
    )
    assert route.is_connected is False


def test_rover_selection_eligibility_and_battery():
    # Rover 1: IDLE, 90% battery, cold motor
    r_eligible = RoverModel(
        id="ROV-IDLE-GOOD",
        name="Good Rover",
        model="Acoustic Crawler MK-IV",
        operating_state="IDLE",
        connection_status="ONLINE",
        battery_percentage=90.0,
        latitude=40.7198,
        longitude=-74.0089,
        motor_temp_c=28.0,
    )

    # Rover 2: IDLE, but critically low battery (18%)
    r_low_batt = RoverModel(
        id="ROV-LOW-BATT",
        name="Dying Rover",
        model="Acoustic Crawler MK-IV",
        operating_state="IDLE",
        connection_status="ONLINE",
        battery_percentage=18.0,
        latitude=40.7198,
        longitude=-74.0089,
        motor_temp_c=28.0,
    )

    # Rover 3: Busy INSPECTING
    r_busy = RoverModel(
        id="ROV-BUSY",
        name="Busy Rover",
        model="Acoustic Crawler MK-IV",
        operating_state="INSPECTING",
        connection_status="ONLINE",
        battery_percentage=85.0,
        latitude=40.7198,
        longitude=-74.0089,
        motor_temp_c=28.0,
    )

    rovers = [r_eligible, r_low_batt, r_busy]
    eligible, ineligible = RoverSelectionService.rank_rovers_for_target(
        rovers, target_lat=40.7128, target_lng=-74.0060
    )

    assert len(eligible) == 1
    assert eligible[0].rover_id == "ROV-IDLE-GOOD"
    assert eligible[0].suitability_score > 60.0

    assert len(ineligible) == 2
    ineligible_ids = [r.rover_id for r in ineligible]
    assert "ROV-LOW-BATT" in ineligible_ids
    assert "ROV-BUSY" in ineligible_ids


def test_rover_selection_motor_temp_disqualification():
    r_hot = RoverModel(
        id="ROV-HOT",
        name="Hot Rover",
        model="Crawler",
        operating_state="IDLE",
        connection_status="ONLINE",
        battery_percentage=95.0,
        latitude=40.7198,
        longitude=-74.0089,
        motor_temp_c=54.0,  # >= 50 threshold
    )
    suit = RoverSelectionService.evaluate_rover(r_hot, target_lat=40.7128, target_lng=-74.0060)
    assert suit.is_eligible is False
    assert "motor temperature" in suit.disqualification_reason.lower()


def test_api_mission_plan_and_recommendation_lifecycle(client):
    # 1. Create AI Detection to plan for
    det_res = client.post("/api/v1/ai/analyze", json={
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "pressure_bar": 2.8,
        "acoustic_spl_db": 86.0,
        "dominant_freq_hz": 1500.0,
        "acoustic_scenario": "MAJOR_LEAK",
    })
    assert det_res.status_code == 200
    det_id = det_res.json()["id"]

    # 2. Plan mission
    plan_res = client.post("/api/v1/missions/plan", json={"detection_id": det_id})
    assert plan_res.status_code == 200
    rec = plan_res.json()

    assert rec["id"].startswith("REC-2026-")
    assert rec["detection_id"] == det_id
    assert rec["pipeline_segment_id"] == "PIPE-SEC-4B-92"
    assert rec["status"] == "PENDING_APPROVAL"
    assert rec["priority_score"] > 0.0
    assert rec["priority_category"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert len(rec["waypoints"]) >= 2
    rec_id = rec["id"]

    # 3. Duplicate protection test: re-calling plan should return the same recommendation
    plan_dup = client.post("/api/v1/missions/plan", json={"detection_id": det_id})
    assert plan_dup.status_code == 200
    assert plan_dup.json()["id"] == rec_id

    # 4. List recommendations
    list_res = client.get("/api/v1/missions/recommendations")
    assert list_res.status_code == 200
    assert any(r["id"] == rec_id for r in list_res.json())

    # 5. Get recommendation by ID
    get_res = client.get(f"/api/v1/missions/recommendations/{rec_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == rec_id


def test_api_operator_reject_recommendation(client):
    # Create detection and recommendation
    det_res = client.post("/api/v1/ai/analyze", json={
        "pipeline_segment_id": "PIPE-RES-3C-11",
        "pressure_bar": 4.5,
        "acoustic_scenario": "MINOR_LEAK",
    })
    det_id = det_res.json()["id"]
    rec = client.post("/api/v1/missions/plan", json={"detection_id": det_id}).json()
    rec_id = rec["id"]

    # Operator rejects recommendation
    reject_res = client.post(
        f"/api/v1/missions/recommendations/{rec_id}/reject",
        json={
            "rejection_reason": "Low priority micro-fissure; scheduled for next maintenance window",
            "operator_notes": "Consulted with water distribution supervisor."
        }
    )
    assert reject_res.status_code == 200
    data = reject_res.json()
    assert data["status"] == "REJECTED"
    assert "Low priority micro-fissure" in data["rejection_reason"]


def test_api_operator_approve_and_dispatch(client):
    # Ensure ROV-AQUA-03 is IDLE before dispatch
    client.post("/api/v1/rovers/ROV-AQUA-03/commands", json={
        "command": "SET_STATE",
        "targetState": "IDLE",
        "reason": "Test setup reset to IDLE",
        "triggeredBy": "TEST"
    })

    # Create detection and recommendation specifically selecting ROV-AQUA-03
    det_res = client.post("/api/v1/ai/analyze", json={
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "pressure_bar": 2.9,
        "acoustic_scenario": "MAJOR_LEAK",
    })
    det_id = det_res.json()["id"]
    rec = client.post("/api/v1/missions/plan", json={
        "detection_id": det_id,
        "preferred_rover_id": "ROV-AQUA-03",
    }).json()
    rec_id = rec["id"]

    # Operator approves recommendation
    approve_res = client.post(
        f"/api/v1/missions/recommendations/{rec_id}/approve",
        json={
            "operator_id": "CHIEF_OPERATOR_ALICE",
            "notes": "Approved for emergency crawler acoustic localization scan."
        }
    )
    assert approve_res.status_code == 200
    res_data = approve_res.json()
    assert res_data["status"] == "APPROVED"
    assert res_data["rover_id"] == "ROV-AQUA-03"
    mission_id = res_data["mission_id"]

    # Verify mission route & progress endpoints
    route_res = client.get(f"/api/v1/missions/{mission_id}/route")
    assert route_res.status_code == 200
    assert route_res.json()["mission_id"] == mission_id
    assert len(route_res.json()["waypoints"]) >= 2

    prog_res = client.get(f"/api/v1/missions/{mission_id}/progress")
    assert prog_res.status_code == 200
    assert prog_res.json()["mission_id"] == mission_id
    assert prog_res.json()["status"] == "In Progress"

    ev_res = client.get(f"/api/v1/missions/{mission_id}/events")
    assert ev_res.status_code == 200
    assert ev_res.json()["mission_id"] == mission_id


def test_api_dispatch_fleet_suitability_endpoints(client):
    # Test GET /api/v1/dispatch/eligible-rovers
    res = client.get("/api/v1/dispatch/eligible-rovers?target_segment_id=PIPE-SEC-4B-92")
    assert res.status_code == 200
    rovers = res.json()
    assert isinstance(rovers, list)
    assert len(rovers) >= 3
    assert any("battery_reserve_after_pct" in r for r in rovers)

    # Test POST /api/v1/dispatch/evaluate
    eval_res = client.post("/api/v1/dispatch/evaluate", json={
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "target_lat": 40.7128,
        "target_lng": -74.0060,
    })
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["pipeline_segment_id"] == "PIPE-SEC-4B-92"
    assert "eligible_rovers" in eval_data
    assert "ineligible_rovers" in eval_data
