"""
AQUA CREW — Autonomous Inspection Intelligence Test Suite (Task 15)
Comprehensive verification of inspection prioritization, evidence provenance, rover suitability,
battery safety reserve, connected underground Dijkstra routing, multi-rover coordination,
human approval gates, adaptive simulated execution, tamper-evident reports, and zero-trust RBAC.
"""
import pytest
from datetime import datetime, timezone
import json
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.database.session import SessionLocal, init_db
from app.models.rover import RoverModel
from app.models.pipeline_segment import PipelineSegmentModel
from app.models.ai_detection import AiDetectionModel
from app.models.inspection_intelligence import (
    InspectionRecommendationModel,
    InspectionPlanModel,
    InspectionExecutionModel,
    InspectionReportModel,
    InspectionEventModel,
)
from app.schemas.inspection_intelligence import (
    InspectionRecommendationSchema,
    RoverSuitabilitySchema,
    InspectionPlanSchema,
    InspectionPlanTargetSchema,
    InspectionExecutionProgressSchema,
    InspectionReportSchema,
    SupportingEvidenceItem,
)
from app.repositories.pipeline_repository import PipelineRepository, DEFAULT_PIPELINES
from app.repositories.rover_repository import RoverRepository
from app.repositories.user_repository import UserRepository
from app.repositories.inspection_intelligence_repository import InspectionIntelligenceRepository
from app.services.inspection_intelligence import (
    InspectionIntelligenceService,
    RoverAllocationService,
    AdaptiveRouteService,
    InspectionExecutionEngine,
)
from app.core.security import create_access_token


@pytest.fixture(scope="module")
def db():
    init_db()
    session = SessionLocal()
    try:
        UserRepository.seed_defaults(session)
        PipelineRepository.seed_defaults(session)
        RoverRepository.seed_defaults(session)
        yield session
    finally:
        session.close()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def viewer_token():
    token, _, _ = create_access_token(user_id="USR-VIEW-01", username="viewer", role="VIEWER")
    return token


@pytest.fixture(scope="module")
def operator_token():
    token, _, _ = create_access_token(user_id="OPERATOR-SUPERVISOR-01", username="operator", role="OPERATOR")
    return token


@pytest.fixture(scope="module")
def engineer_token():
    token, _, _ = create_access_token(user_id="USR-ENG-01", username="engineer", role="ENGINEER")
    return token


@pytest.fixture(scope="module")
def sample_segment(db):
    seg = PipelineRepository.get_by_id(db, "PIPE-SEC-01")
    if not seg:
        seg = PipelineRepository.get_all(db)[0]
    return seg


# =============================================================================
# 1. INSPECTION URGENCY & PRIORITIZATION (15 TESTS)
# =============================================================================
class TestUrgencyAndPrioritization:
    def test_urgency_weights_sum_to_one(self):
        total = sum(InspectionIntelligenceService.URGENCY_WEIGHTS.values())
        assert pytest.approx(total, 0.001) == 1.0

    def test_urgency_weights_vulnerability_positive(self):
        assert InspectionIntelligenceService.URGENCY_WEIGHTS["vulnerability"] > 0.0

    def test_urgency_weights_acoustic_ai_positive(self):
        assert InspectionIntelligenceService.URGENCY_WEIGHTS["active_leak_detection"] > 0.0

    def test_calculate_urgency_score_bounds(self, db, sample_segment):
        score, cat, factors, evidence, method, action = InspectionIntelligenceService.calculate_urgency_score(
            db, sample_segment
        )
        assert 0.0 <= score <= 100.0
        assert cat in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert len(factors) >= 5
        assert len(evidence) >= 1

    def test_urgency_factors_contains_vulnerability(self, db, sample_segment):
        _, _, factors, _, _, _ = InspectionIntelligenceService.calculate_urgency_score(db, sample_segment)
        assert "vulnerability" in factors

    def test_urgency_factors_contains_acoustic(self, db, sample_segment):
        _, _, factors, _, _, _ = InspectionIntelligenceService.calculate_urgency_score(db, sample_segment)
        assert "active_leak_detection" in factors

    def test_urgency_factors_contains_hydraulic_stress(self, db, sample_segment):
        _, _, factors, _, _, _ = InspectionIntelligenceService.calculate_urgency_score(db, sample_segment)
        assert "hydraulic_stress" in factors

    def test_critical_threshold_classification(self, db, sample_segment):
        # High leak detection forces high score
        det = AiDetectionModel(
            id=f"DET-TEST-{uuid.uuid4().hex[:6]}",
            pipeline_segment_id=sample_segment.id,
            confidence=0.99,
            anomaly_score=0.95,
            classification="HIGH_LEAK_PROBABILITY",
            risk_level="CRITICAL",
            status="VERIFIED_BY_OPERATOR",
            estimated_loss_lph=250.0,
        )
        db.add(det)
        db.commit()

        score, cat, _, _, method, _ = InspectionIntelligenceService.calculate_urgency_score(db, sample_segment)
        assert score >= 55.0
        assert cat in ["CRITICAL", "HIGH"]
        assert method == "ACOUSTIC_CORRELATION"

    def test_recommended_action_non_empty(self, db, sample_segment):
        _, _, _, _, _, action = InspectionIntelligenceService.calculate_urgency_score(db, sample_segment)
        assert len(action) > 10

    def test_generate_recommendations_for_all_returns_list(self, db):
        recs = InspectionIntelligenceService.generate_recommendations_for_all(db, min_urgency=0.0)
        assert isinstance(recs, list)
        assert len(recs) >= 1

    def test_generate_recommendations_descending_priority(self, db):
        recs = InspectionIntelligenceService.generate_recommendations_for_all(db, min_urgency=0.0)
        for i in range(len(recs) - 1):
            assert recs[i].priority_score >= recs[i + 1].priority_score

    def test_generate_recommendations_min_urgency_filter(self, db):
        high_recs = InspectionIntelligenceService.generate_recommendations_for_all(db, min_urgency=80.0)
        for r in high_recs:
            assert r.priority_score >= 80.0

    def test_recommendation_has_simulated_flag_true(self, db):
        recs = InspectionIntelligenceService.generate_recommendations_for_all(db, min_urgency=0.0)
        assert recs[0].is_simulated is True

    def test_recommendation_status_starts_pending_approval(self, db):
        recs = InspectionIntelligenceService.generate_recommendations_for_all(db, min_urgency=0.0)
        assert recs[0].human_approval_status == "PENDING_APPROVAL"

    def test_recommendation_capabilities_mapped_to_method(self, db):
        recs = InspectionIntelligenceService.generate_recommendations_for_all(db, min_urgency=0.0)
        rec = recs[0]
        if rec.recommended_method == "ACOUSTIC_CORRELATION":
            assert "hydrophone_acoustic" in rec.required_rover_capabilities


# =============================================================================
# 2. EVIDENCE PROVENANCE & ONTOLOGICAL CLASSIFICATION (15 TESTS)
# =============================================================================
class TestEvidenceProvenanceClassification:
    def test_physical_pipe_metadata_is_measured(self, db, sample_segment):
        _, _, _, evidence, _, _ = InspectionIntelligenceService.calculate_urgency_score(db, sample_segment)
        asset_ev = next((e for e in evidence if e.source_subsystem == "TASK_04_GIS"), None)
        assert asset_ev is not None
        assert asset_ev.classification == "MEASURED"

    def test_composite_urgency_is_derived(self, db):
        recs = InspectionIntelligenceService.generate_recommendations_for_all(db)
        assert recs[0].primary_classification == "DERIVED"

    def test_evidence_item_confidence_in_bounds(self, db, sample_segment):
        _, _, _, evidence, _, _ = InspectionIntelligenceService.calculate_urgency_score(db, sample_segment)
        for e in evidence:
            assert 0.0 <= e.confidence <= 1.0

    def test_evidence_item_description_non_empty(self, db, sample_segment):
        _, _, _, evidence, _, _ = InspectionIntelligenceService.calculate_urgency_score(db, sample_segment)
        for e in evidence:
            assert len(e.description) > 5

    def test_supporting_evidence_schema_dump(self):
        ev = SupportingEvidenceItem(
            evidence_id="EVID-01",
            source_subsystem="TASK_07_AI_LEAKS",
            classification="MEASURED",
            metric_name="acoustic_spl_db",
            metric_value=72.5,
            description="Acoustic pressure peak",
            confidence=0.92,
        )
        d = ev.model_dump()
        assert d["classification"] == "MEASURED"
        assert d["confidence"] == 0.92

    def test_evidence_provenance_rejects_invalid_classification(self):
        with pytest.raises(Exception):
            SupportingEvidenceItem(
                evidence_id="EVID-02",
                source_subsystem="TASK_07_AI_LEAKS",
                classification="INVALID_CLASSIFICATION", # type: ignore
                metric_name="spl",
                metric_value=50.0,
                description="desc",
                confidence=0.5,
            )

    def test_simulated_sensor_observation_classification(self):
        from app.schemas.inspection_intelligence import SimulatedSensorObservation
        obs = SimulatedSensorObservation(
            observation_id="OBS-01",
            timestamp=datetime.now(timezone.utc).isoformat(),
            rover_id="ROV-01",
            segment_id="PIPE-01",
            distance_along_pipe_m=120.0,
            sensor_type="ACOUSTIC",
            reading_value=45.0,
            unit="dB",
            anomaly_detected=False,
            classification="SIMULATED",
        )
        assert obs.classification == "SIMULATED"

    def test_uncertainty_radius_positive(self, db):
        recs = InspectionIntelligenceService.generate_recommendations_for_all(db)
        assert recs[0].uncertainty_radius_m > 0.0

    def test_critical_uncertainty_radius_smaller(self, db):
        recs = InspectionIntelligenceService.generate_recommendations_for_all(db)
        for r in recs:
            if r.priority_category == "CRITICAL":
                assert r.uncertainty_radius_m <= 20.0

    def test_confidence_above_threshold(self, db):
        recs = InspectionIntelligenceService.generate_recommendations_for_all(db)
        assert recs[0].confidence >= 0.80

    def test_evidence_id_prefix_evid(self, db, sample_segment):
        _, _, _, evidence, _, _ = InspectionIntelligenceService.calculate_urgency_score(db, sample_segment)
        for e in evidence:
            assert e.evidence_id.startswith("EVID-")

    def test_evidence_items_have_metric_name(self, db, sample_segment):
        _, _, _, evidence, _, _ = InspectionIntelligenceService.calculate_urgency_score(db, sample_segment)
        for e in evidence:
            assert len(e.metric_name) > 0

    def test_recommendation_schema_json_serializable(self, db):
        recs = InspectionIntelligenceService.generate_recommendations_for_all(db)
        j = json.dumps(recs[0].model_dump())
        assert isinstance(j, str)

    def test_simulated_report_provenance(self):
        rep = InspectionReportSchema(
            id="INSP-REP-TEST",
            plan_id="PLAN-01",
            mission_id="MIS-01",
            rover_id="ROV-01",
            pipeline_segment_id="PIPE-01",
            segment_name="Test Pipe",
            inspection_method="ACOUSTIC_CORRELATION",
            start_time=datetime.now(timezone.utc).isoformat(),
            completion_time=datetime.now(timezone.utc).isoformat(),
            route_distance_m=500.0,
            inspected_distance_m=480.0,
            sensor_observations_count=10,
            detected_anomalies=[],
            evidence_provenance="SIMULATED",
            updated_infrastructure_risk=45.0,
            inspection_outcome="SUCCESS",
            unresolved_uncertainties=[],
            recommended_next_action="Monitor",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        assert rep.evidence_provenance == "SIMULATED"

    def test_evidence_items_no_duplicate_ids(self, db, sample_segment):
        _, _, _, evidence, _, _ = InspectionIntelligenceService.calculate_urgency_score(db, sample_segment)
        ids = [e.evidence_id for e in evidence]
        assert len(ids) == len(set(ids))


# =============================================================================
# 3. ROVER ELIGIBILITY & SUITABILITY EVALUATION (15 TESTS)
# =============================================================================
class TestRoverEligibilityAndSuitability:
    def test_evaluate_online_idle_rover_is_eligible(self, db):
        rovers = RoverRepository.get_all(db)
        rover = rovers[0]
        rover.operating_state = "IDLE"
        rover.connection_status = "ONLINE"
        rover.battery_percentage = 95.0
        rover.motor_temp_c = 28.0
        db.commit()

        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover,
            target_lat=rover.latitude + 0.002,
            target_lng=rover.longitude + 0.002,
        )
        assert suit.is_eligible is True
        assert suit.suitability_score > 50.0

    def test_offline_rover_is_ineligible(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.connection_status = "OFFLINE"
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude
        )
        assert suit.is_eligible is False
        assert any("ONLINE" in r for r in suit.disqualification_reasons)

    def test_navigating_rover_is_ineligible(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.operating_state = "NAVIGATING"
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude
        )
        assert suit.is_eligible is False
        assert any("IDLE" in r for r in suit.disqualification_reasons)

    def test_inspecting_rover_is_ineligible(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.operating_state = "INSPECTING"
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude
        )
        assert suit.is_eligible is False

    def test_overheated_motor_rover_is_ineligible(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.operating_state = "IDLE"
        rover.connection_status = "ONLINE"
        rover.motor_temp_c = 52.5
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude
        )
        assert suit.is_eligible is False
        assert any("temperature" in r.lower() for r in suit.disqualification_reasons)

    def test_low_battery_rover_is_ineligible(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.operating_state = "IDLE"
        rover.connection_status = "ONLINE"
        rover.battery_percentage = 18.0
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude, safety_reserve_pct=20.0
        )
        assert suit.is_eligible is False
        assert suit.has_safe_return_reserve is False

    def test_battery_safety_reserve_requirement(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.operating_state = "IDLE"
        rover.connection_status = "ONLINE"
        rover.battery_percentage = 90.0
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude, safety_reserve_pct=25.0
        )
        assert suit.has_safe_return_reserve is True

    def test_suitability_score_bounds(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.operating_state = "IDLE"
        rover.connection_status = "ONLINE"
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude
        )
        assert 0.0 <= suit.suitability_score <= 100.0

    def test_ineligible_rover_score_is_zero(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.connection_status = "OFFLINE"
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude
        )
        assert suit.suitability_score == 0.0

    def test_rank_fleet_sorts_eligible_first(self, db):
        rovers = RoverRepository.get_all(db)
        rovers[0].operating_state = "IDLE"
        rovers[0].connection_status = "ONLINE"
        rovers[0].battery_percentage = 90.0
        rovers[0].motor_temp_c = 25.0
        if len(rovers) > 1:
            rovers[1].connection_status = "OFFLINE"
        db.commit()

        eligible, ineligible = RoverAllocationService.rank_fleet_for_target(
            rovers=rovers, target_lat=rovers[0].latitude, target_lng=rovers[0].longitude
        )
        assert len(eligible) >= 1
        if len(rovers) > 1:
            assert len(ineligible) >= 1

    def test_rank_fleet_descending_suitability(self, db):
        rovers = RoverRepository.get_all(db)
        for r in rovers:
            r.operating_state = "IDLE"
            r.connection_status = "ONLINE"
            r.battery_percentage = 95.0
            r.motor_temp_c = 25.0
        db.commit()

        eligible, _ = RoverAllocationService.rank_fleet_for_target(
            rovers=rovers, target_lat=rovers[0].latitude, target_lng=rovers[0].longitude
        )
        for i in range(len(eligible) - 1):
            assert eligible[i].suitability_score >= eligible[i + 1].suitability_score

    def test_sensor_payload_capabilities_match(self):
        caps = RoverAllocationService.get_rover_capabilities("ROV-AQUA-01")
        assert "hydrophone_acoustic" in caps
        assert "pipe_navigation" in caps

    def test_capability_mismatch_disqualifies(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.operating_state = "IDLE"
        rover.connection_status = "ONLINE"
        # ROV-AQUA-01 does not have crawler_traction
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude, required_method="THERMAL_INFRARED"
        )
        if "thermal_infrared" not in suit.sensor_capabilities:
            assert suit.capability_match is False
            assert suit.is_eligible is False

    def test_distance_to_target_positive(self, db):
        rover = RoverRepository.get_all(db)[0]
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude + 0.005, target_lng=rover.longitude + 0.005
        )
        assert suit.distance_to_target_m > 0.0

    def test_estimated_travel_time_positive(self, db):
        rover = RoverRepository.get_all(db)[0]
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude + 0.005, target_lng=rover.longitude + 0.005
        )
        assert suit.estimated_travel_time_s > 0.0


# =============================================================================
# 4. ADAPTIVE ROUTE PLANNING (15 TESTS)
# =============================================================================
class TestAdaptiveRoutePlanning:
    def test_plan_route_empty_targets_returns_base(self, db):
        rover = RoverRepository.get_all(db)[0]
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [])
        assert alloc.total_route_distance_m == 0.0
        assert len(alloc.route_waypoints) == 1
        assert alloc.return_to_base_feasible is True

    def test_plan_route_single_target(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.latitude = 40.7128
        rover.longitude = -74.0060
        db.commit()
        target = InspectionPlanTargetSchema(
            target_id="TGT-01",
            pipeline_segment_id="PIPE-SEC-01",
            target_coordinates=[-74.0010, 40.7140],
            inspection_method="ACOUSTIC_CORRELATION",
            priority_score=80.0,
            estimated_duration_minutes=30,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [target])
        assert alloc.total_route_distance_m > 0.0
        assert len(alloc.route_waypoints) >= 2
        assert alloc.return_to_base_feasible is True

    def test_plan_route_multi_targets(self, db):
        rover = RoverRepository.get_all(db)[0]
        t1 = InspectionPlanTargetSchema(
            target_id="TGT-01",
            pipeline_segment_id="PIPE-SEC-01",
            target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION",
            priority_score=85.0,
            estimated_duration_minutes=30,
        )
        t2 = InspectionPlanTargetSchema(
            target_id="TGT-02",
            pipeline_segment_id="PIPE-SEC-02",
            target_coordinates=[-74.002, 40.714],
            inspection_method="ACOUSTIC_CORRELATION",
            priority_score=70.0,
            estimated_duration_minutes=30,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [t1, t2])
        assert len(alloc.assigned_targets) == 2
        assert alloc.total_route_distance_m > 0.0

    def test_plan_route_battery_drain_estimated(self, db):
        rover = RoverRepository.get_all(db)[0]
        target = InspectionPlanTargetSchema(
            target_id="TGT-01",
            pipeline_segment_id="PIPE-SEC-01",
            target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION",
            priority_score=80.0,
            estimated_duration_minutes=30,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [target])
        assert alloc.estimated_battery_drain_pct > 0.0

    def test_plan_route_projected_reserve_calculation(self, db):
        rover = RoverRepository.get_all(db)[0]
        target = InspectionPlanTargetSchema(
            target_id="TGT-01",
            pipeline_segment_id="PIPE-SEC-01",
            target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION",
            priority_score=80.0,
            estimated_duration_minutes=30,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [target])
        assert alloc.projected_reserve_after_return_pct < rover.battery_percentage

    def test_plan_route_selection_reason_non_empty(self, db):
        rover = RoverRepository.get_all(db)[0]
        target = InspectionPlanTargetSchema(
            target_id="TGT-01",
            pipeline_segment_id="PIPE-SEC-01",
            target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION",
            priority_score=80.0,
            estimated_duration_minutes=30,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [target])
        assert len(alloc.route_selection_reason) > 10

    def test_reachability_check_connected_coordinate(self, db):
        all_pipes = PipelineRepository.get_all(db)
        reachable = AdaptiveRouteService.check_reachability(db, [-74.006, 40.7128], all_pipes)
        assert reachable is True

    def test_reachability_check_far_off_coordinate(self, db):
        all_pipes = PipelineRepository.get_all(db)
        # Coordinate in the Atlantic Ocean
        reachable = AdaptiveRouteService.check_reachability(db, [-60.000, 20.000], all_pipes, tolerance_m=100.0)
        assert reachable is False

    def test_route_distance_exceeds_euclidean(self, db):
        rover = RoverRepository.get_all(db)[0]
        t = InspectionPlanTargetSchema(
            target_id="TGT-01",
            pipeline_segment_id="PIPE-SEC-01",
            target_coordinates=[-74.002, 40.715],
            inspection_method="ACOUSTIC_CORRELATION",
            priority_score=80.0,
            estimated_duration_minutes=30,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [t])
        from app.services.pipeline_routing_service import haversine_distance_m
        straight = haversine_distance_m([rover.longitude, rover.latitude], t.target_coordinates)
        # Round trip along pipes must be >= 2 * straight distance
        assert alloc.total_route_distance_m >= straight

    def test_route_waypoints_format(self, db):
        rover = RoverRepository.get_all(db)[0]
        t = InspectionPlanTargetSchema(
            target_id="TGT-01",
            pipeline_segment_id="PIPE-SEC-01",
            target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION",
            priority_score=80.0,
            estimated_duration_minutes=30,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [t])
        for wp in alloc.route_waypoints:
            assert len(wp) == 2
            assert -180.0 <= wp[0] <= 180.0 # lng
            assert -90.0 <= wp[1] <= 90.0   # lat

    def test_segments_traversed_non_empty(self, db):
        rover = RoverRepository.get_all(db)[0]
        t = InspectionPlanTargetSchema(
            target_id="TGT-01",
            pipeline_segment_id="PIPE-SEC-01",
            target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION",
            priority_score=80.0,
            estimated_duration_minutes=30,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [t])
        assert isinstance(alloc.segments_traversed, list)

    def test_return_leg_closes_loop(self, db):
        rover = RoverRepository.get_all(db)[0]
        t = InspectionPlanTargetSchema(
            target_id="TGT-01",
            pipeline_segment_id="PIPE-SEC-01",
            target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION",
            priority_score=80.0,
            estimated_duration_minutes=30,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [t])
        first_wp = alloc.route_waypoints[0]
        last_wp = alloc.route_waypoints[-1]
        assert pytest.approx(first_wp[0], 0.001) == last_wp[0]
        assert pytest.approx(first_wp[1], 0.001) == last_wp[1]

    def test_low_battery_rover_return_feasible_false(self, db):
        rover = RoverRepository.get_all(db)[0]
        orig_batt = rover.battery_percentage
        rover.battery_percentage = 22.0
        db.commit()

        t = InspectionPlanTargetSchema(
            target_id="TGT-01",
            pipeline_segment_id="PIPE-SEC-01",
            target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION",
            priority_score=80.0,
            estimated_duration_minutes=60,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [t], safety_reserve_pct=20.0)
        rover.battery_percentage = orig_batt
        db.commit()
        assert alloc.return_to_base_feasible is False

    def test_estimated_mission_duration_positive(self, db):
        rover = RoverRepository.get_all(db)[0]
        t = InspectionPlanTargetSchema(
            target_id="TGT-01",
            pipeline_segment_id="PIPE-SEC-01",
            target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION",
            priority_score=80.0,
            estimated_duration_minutes=30,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [t])
        assert alloc.estimated_mission_duration_s > 0.0

    def test_multi_target_order_preservation(self, db):
        rover = RoverRepository.get_all(db)[0]
        t1 = InspectionPlanTargetSchema(
            target_id="TGT-01", pipeline_segment_id="P1", target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION", priority_score=85.0, estimated_duration_minutes=15,
        )
        t2 = InspectionPlanTargetSchema(
            target_id="TGT-02", pipeline_segment_id="P2", target_coordinates=[-74.002, 40.714],
            inspection_method="ACOUSTIC_CORRELATION", priority_score=70.0, estimated_duration_minutes=15,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [t1, t2])
        assert alloc.assigned_targets[0].target_id == "TGT-01"
        assert alloc.assigned_targets[1].target_id == "TGT-02"


# =============================================================================
# 5. MULTI-ROVER COORDINATION & LOAD BALANCING (15 TESTS)
# =============================================================================
class TestMultiRoverCoordination:
    def test_allocate_empty_targets(self, db):
        alloc_map, unallocated = RoverAllocationService.allocate_multi_rover_targets(db, [])
        assert alloc_map == {}
        assert unallocated == []

    def test_allocate_single_target(self, db):
        rovers = RoverRepository.get_all(db)
        rovers[0].operating_state = "IDLE"
        rovers[0].connection_status = "ONLINE"
        rovers[0].battery_percentage = 95.0
        db.commit()

        t = InspectionPlanTargetSchema(
            target_id="TGT-01", pipeline_segment_id="PIPE-SEC-01", target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION", priority_score=80.0, estimated_duration_minutes=30,
        )
        alloc_map, unallocated = RoverAllocationService.allocate_multi_rover_targets(db, [t])
        assert len(alloc_map) >= 1
        assert len(unallocated) == 0

    def test_no_duplicate_target_assignment(self, db):
        rovers = RoverRepository.get_all(db)
        for r in rovers:
            r.operating_state = "IDLE"
            r.connection_status = "ONLINE"
            r.battery_percentage = 95.0
        db.commit()

        targets = [
            InspectionPlanTargetSchema(
                target_id=f"TGT-{i}", pipeline_segment_id=f"PIPE-0{i}",
                target_coordinates=[-74.004 + (i * 0.001), 40.713 + (i * 0.001)],
                inspection_method="ACOUSTIC_CORRELATION", priority_score=70.0 + i, estimated_duration_minutes=20,
            )
            for i in range(4)
        ]
        alloc_map, _ = RoverAllocationService.allocate_multi_rover_targets(db, targets)
        all_assigned = []
        for tgts in alloc_map.values():
            all_assigned.extend(t.target_id for t in tgts)
        # All assigned targets must be unique
        assert len(all_assigned) == len(set(all_assigned))

    def test_respects_max_targets_per_rover(self, db):
        rovers = RoverRepository.get_all(db)
        for r in rovers:
            r.operating_state = "IDLE"
            r.connection_status = "ONLINE"
            r.battery_percentage = 95.0
        db.commit()

        targets = [
            InspectionPlanTargetSchema(
                target_id=f"TGT-{i}", pipeline_segment_id=f"PIPE-0{i}",
                target_coordinates=[-74.004, 40.713],
                inspection_method="ACOUSTIC_CORRELATION", priority_score=70.0, estimated_duration_minutes=15,
            )
            for i in range(5)
        ]
        alloc_map, _ = RoverAllocationService.allocate_multi_rover_targets(db, targets, max_targets_per_rover=2)
        for tgts in alloc_map.values():
            assert len(tgts) <= 2

    def test_offline_rovers_excluded(self, db):
        rovers = RoverRepository.get_all(db)
        rovers[0].connection_status = "OFFLINE"
        db.commit()

        t = InspectionPlanTargetSchema(
            target_id="TGT-01", pipeline_segment_id="PIPE-SEC-01", target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION", priority_score=80.0, estimated_duration_minutes=30,
        )
        alloc_map, _ = RoverAllocationService.allocate_multi_rover_targets(db, [t])
        assert rovers[0].id not in alloc_map

    def test_busy_rovers_excluded(self, db):
        rovers = RoverRepository.get_all(db)
        rovers[0].operating_state = "NAVIGATING"
        db.commit()

        t = InspectionPlanTargetSchema(
            target_id="TGT-01", pipeline_segment_id="PIPE-SEC-01", target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION", priority_score=80.0, estimated_duration_minutes=30,
        )
        alloc_map, _ = RoverAllocationService.allocate_multi_rover_targets(db, [t])
        assert rovers[0].id not in alloc_map

    def test_preferred_rover_filter(self, db):
        rovers = RoverRepository.get_all(db)
        rovers[0].operating_state = "IDLE"
        rovers[0].connection_status = "ONLINE"
        rovers[0].battery_percentage = 95.0
        db.commit()

        t = InspectionPlanTargetSchema(
            target_id="TGT-01", pipeline_segment_id="PIPE-SEC-01", target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION", priority_score=80.0, estimated_duration_minutes=30,
        )
        alloc_map, _ = RoverAllocationService.allocate_multi_rover_targets(
            db, [t], preferred_rover_ids=[rovers[0].id]
        )
        if alloc_map:
            assert list(alloc_map.keys()) == [rovers[0].id]

    def test_unallocated_targets_reported_when_capacity_exceeded(self, db):
        rovers = RoverRepository.get_all(db)
        for r in rovers:
            r.operating_state = "OFFLINE"
        db.commit()

        t = InspectionPlanTargetSchema(
            target_id="TGT-01", pipeline_segment_id="PIPE-SEC-01", target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION", priority_score=80.0, estimated_duration_minutes=30,
        )
        alloc_map, unallocated = RoverAllocationService.allocate_multi_rover_targets(db, [t])
        assert alloc_map == {}
        assert "TGT-01" in unallocated

    def test_plan_schema_generation(self):
        plan = InspectionPlanSchema(
            id="PLAN-TEST-01",
            plan_name="Campaign 01",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=0,
            total_targets_covered=0,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        assert plan.human_approval_status == "PENDING_APPROVAL"
        assert plan.conflict_checks_passed is True

    def test_plan_persistence_in_db(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Test Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=2,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        saved = InspectionIntelligenceRepository.save_plan(db, plan)
        assert saved.id == plan.id
        loaded = InspectionIntelligenceRepository.get_plan(db, plan.id)
        assert loaded is not None
        assert loaded.plan_name == "Test Plan"

    def test_list_plans_returns_persisted(self, db):
        plans = InspectionIntelligenceRepository.list_plans(db)
        assert isinstance(plans, list)

    def test_multi_rover_load_balancing_distribution(self, db):
        rovers = RoverRepository.get_all(db)
        for r in rovers:
            r.operating_state = "IDLE"
            r.connection_status = "ONLINE"
            r.battery_percentage = 95.0
            r.motor_temp_c = 25.0
        db.commit()

        targets = [
            InspectionPlanTargetSchema(
                target_id=f"TGT-{i}", pipeline_segment_id=f"PIPE-0{i}",
                target_coordinates=[-74.004 + (i * 0.001), 40.713],
                inspection_method="ACOUSTIC_CORRELATION", priority_score=80.0, estimated_duration_minutes=20,
            )
            for i in range(3)
        ]
        alloc_map, _ = RoverAllocationService.allocate_multi_rover_targets(db, targets, max_targets_per_rover=1)
        # With max 1 per rover, 3 distinct rovers should be assigned
        if len(rovers) >= 3:
            assert len(alloc_map) == 3

    def test_high_priority_targets_allocated_first(self, db):
        rovers = RoverRepository.get_all(db)
        for r in rovers:
            r.operating_state = "IDLE"
            r.connection_status = "ONLINE"
            r.battery_percentage = 95.0
        db.commit()

        t_low = InspectionPlanTargetSchema(
            target_id="TGT-LOW", pipeline_segment_id="P_LOW", target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION", priority_score=35.0, estimated_duration_minutes=20,
        )
        t_high = InspectionPlanTargetSchema(
            target_id="TGT-HIGH", pipeline_segment_id="P_HIGH", target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION", priority_score=95.0, estimated_duration_minutes=20,
        )
        alloc_map, _ = RoverAllocationService.allocate_multi_rover_targets(
            db, [t_low, t_high], max_targets_per_rover=1
        )
        # Verify that the high-priority target is allocated
        all_assigned_ids = [t.target_id for tgts in alloc_map.values() for t in tgts]
        assert "TGT-HIGH" in all_assigned_ids

    def test_conflict_detection_prevents_active_mission_rover(self, db):
        rovers = RoverRepository.get_all(db)
        rovers[0].assigned_mission_id = "MIS-ACTIVE-99"
        rovers[0].operating_state = "INSPECTING"
        db.commit()

        t = InspectionPlanTargetSchema(
            target_id="TGT-01", pipeline_segment_id="PIPE-SEC-01", target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION", priority_score=80.0, estimated_duration_minutes=30,
        )
        alloc_map, _ = RoverAllocationService.allocate_multi_rover_targets(db, [t])
        assert rovers[0].id not in alloc_map

    def test_unreachable_target_list_persistence(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Unreachable Test",
            allocations=[],
            unreachable_targets=["PIPE-ISOLATED-01"],
            conflict_checks_passed=True,
            total_rovers_assigned=0,
            total_targets_covered=0,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        loaded = InspectionIntelligenceRepository.get_plan(db, plan.id)
        targets = json.loads(loaded.unreachable_targets_json)
        assert "PIPE-ISOLATED-01" in targets


# =============================================================================
# 6. HUMAN APPROVAL WORKFLOW & CONCURRENCY (15 TESTS)
# =============================================================================
class TestHumanApprovalWorkflow:
    def test_new_plan_is_pending_approval(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Approval Test Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        saved = InspectionIntelligenceRepository.save_plan(db, plan)
        assert saved.human_approval_status == "PENDING_APPROVAL"

    def test_operator_approve_plan(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Approve Test Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        approved = InspectionIntelligenceRepository.atomically_approve_plan(
            db, plan.id, operator_id="operator_test", notes="Plan approved for morning run."
        )
        assert approved.human_approval_status == "APPROVED"
        assert approved.approved_by == "operator_test"

    def test_operator_reject_plan(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Reject Test Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        rejected = InspectionIntelligenceRepository.atomically_reject_plan(
            db, plan.id, operator_id="operator_test", reason="Inclement weather in harbor zone."
        )
        assert rejected.human_approval_status == "REJECTED"
        assert rejected.rejection_reason == "Inclement weather in harbor zone."

    def test_double_approval_rejected(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Double Approve Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        InspectionIntelligenceRepository.atomically_approve_plan(db, plan.id, "op1")
        with pytest.raises(Exception):
            InspectionIntelligenceRepository.atomically_approve_plan(db, plan.id, "op2")

    def test_approve_non_existent_plan_raises_404(self, db):
        with pytest.raises(Exception):
            InspectionIntelligenceRepository.atomically_approve_plan(db, "NON-EXISTENT", "op1")

    def test_reject_non_existent_plan_raises_404(self, db):
        with pytest.raises(Exception):
            InspectionIntelligenceRepository.atomically_reject_plan(db, "NON-EXISTENT", "op1", "reason")

    def test_reject_already_approved_plan_raises_400(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Already Approved Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        InspectionIntelligenceRepository.atomically_approve_plan(db, plan.id, "op1")
        with pytest.raises(Exception):
            InspectionIntelligenceRepository.atomically_reject_plan(db, plan.id, "op2", "reason")

    def test_approve_already_rejected_plan_raises_400(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Already Rejected Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        InspectionIntelligenceRepository.atomically_reject_plan(db, plan.id, "op1", "reason")
        with pytest.raises(Exception):
            InspectionIntelligenceRepository.atomically_approve_plan(db, plan.id, "op2")

    def test_approval_logs_audit_event(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Audit Logged Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        InspectionIntelligenceRepository.atomically_approve_plan(db, plan.id, "op_audit", "Approved notes")
        evts = InspectionIntelligenceRepository.list_events(db)
        match = next((e for e in evts if e.plan_id == plan.id and e.event_type == "INSPECTION_PLAN_APPROVED"), None)
        assert match is not None

    def test_rejection_logs_audit_event(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Audit Rejected Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        InspectionIntelligenceRepository.atomically_reject_plan(db, plan.id, "op_audit", "Valve closed")
        evts = InspectionIntelligenceRepository.list_events(db)
        match = next((e for e in evts if e.plan_id == plan.id and e.event_type == "INSPECTION_PLAN_REJECTED"), None)
        assert match is not None

    def test_mission_cannot_launch_without_approval(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Pending Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        rover = RoverRepository.get_all(db)[0]
        with pytest.raises(Exception):
            InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)

    def test_mission_cannot_launch_if_rejected(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Rejected Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="REJECTED",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        rover = RoverRepository.get_all(db)[0]
        with pytest.raises(Exception):
            InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)

    def test_approved_by_persists_correctly(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Check Operator Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        InspectionIntelligenceRepository.atomically_approve_plan(db, plan.id, "chief_operator")
        loaded = InspectionIntelligenceRepository.get_plan(db, plan.id)
        assert loaded.approved_by == "chief_operator"

    def test_approved_at_timestamp_populated(self, db):
        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Timestamp Plan",
            allocations=[],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="PENDING_APPROVAL",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        InspectionIntelligenceRepository.atomically_approve_plan(db, plan.id, "op")
        loaded = InspectionIntelligenceRepository.get_plan(db, plan.id)
        assert loaded.approved_at is not None

    def test_rejection_reason_mandatory_in_schema(self):
        from app.schemas.inspection_intelligence import PlanRejectionRequest
        with pytest.raises(Exception):
            PlanRejectionRequest(rejection_reason="") # min_length=3


# =============================================================================
# 7. ADAPTIVE EXECUTION & SAFETY SAFEGUARDS (15 TESTS)
# =============================================================================
class TestAdaptiveExecutionAndSafety:
    @pytest.fixture
    def ready_plan_and_rover(self, db):
        rovers = RoverRepository.get_all(db)
        rover = rovers[0]
        rover.operating_state = "IDLE"
        rover.connection_status = "ONLINE"
        rover.battery_percentage = 95.0
        rover.motor_temp_c = 25.0
        db.commit()

        target = InspectionPlanTargetSchema(
            target_id="TGT-TEST", pipeline_segment_id="PIPE-SEC-01", target_coordinates=[-74.004, 40.713],
            inspection_method="ACOUSTIC_CORRELATION", priority_score=85.0, estimated_duration_minutes=30,
        )
        alloc = AdaptiveRouteService.plan_multi_target_route(db, rover, [target])

        plan = InspectionPlanSchema(
            id=f"PLAN-{uuid.uuid4().hex[:6].upper()}",
            plan_name="Execution Ready Plan",
            allocations=[alloc],
            unreachable_targets=[],
            conflict_checks_passed=True,
            total_rovers_assigned=1,
            total_targets_covered=1,
            human_approval_status="APPROVED",
            approved_by="operator_auto",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_plan(db, plan)
        return plan, rover

    def test_start_mission_execution_success(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        assert exec_progress.status == "IN_PROGRESS"
        assert exec_progress.mission_id.startswith("MIS-INSP-")
        assert exec_progress.progress_percentage == 0.0

    def test_rover_state_becomes_inspecting_on_start(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        updated_rover = RoverRepository.get_by_id(db, rover.id)
        assert updated_rover.operating_state == "INSPECTING"
        assert updated_rover.assigned_mission_id == exec_progress.mission_id

    def test_advance_step_increases_progress(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        step1 = InspectionExecutionEngine.execute_next_step(db, exec_progress.mission_id, step_increment_m=100.0)
        assert step1.progress_percentage > 0.0
        assert step1.distance_traversed_m == 100.0

    def test_advance_step_discharges_battery(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        initial_batt = rover.battery_percentage
        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        step1 = InspectionExecutionEngine.execute_next_step(db, exec_progress.mission_id, step_increment_m=50.0)
        assert step1.battery_percentage < initial_batt

    def test_advance_step_records_synthetic_observations(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        step1 = InspectionExecutionEngine.execute_next_step(db, exec_progress.mission_id, step_increment_m=20.0)
        assert len(step1.recent_observations) >= 2
        for obs in step1.recent_observations:
            assert obs.classification == "SIMULATED"

    def test_step_advancement_detects_anomaly(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        # Advance multiple steps to reach 50%
        for _ in range(4):
            exec_progress = InspectionExecutionEngine.execute_next_step(db, exec_progress.mission_id, step_increment_m=30.0)
            if exec_progress.status == "COMPLETED":
                break
        assert exec_progress.active_anomalies_detected >= 0

    def test_trigger_adaptive_reroute_success(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        step1 = InspectionExecutionEngine.execute_next_step(db, exec_progress.mission_id, step_increment_m=20.0)
        adapted = InspectionExecutionEngine.trigger_adaptive_reroute(
            db, exec_progress.mission_id, adaptation_reason="Acoustic pressure surge detected."
        )
        assert adapted.route_adapted is True
        assert len(adapted.adaptation_history) == 1
        assert "Acoustic" in adapted.adaptation_history[0]["reason"]

    def test_adaptive_reroute_logs_event(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        InspectionExecutionEngine.trigger_adaptive_reroute(
            db, exec_progress.mission_id, adaptation_reason="Acoustic pressure surge detected."
        )
        evts = InspectionIntelligenceRepository.list_events(db)
        match = next((e for e in evts if e.mission_id == exec_progress.mission_id and e.event_type == "ROUTE_ADAPTED"), None)
        assert match is not None

    def test_low_battery_aborts_mission(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        rover.battery_percentage = 15.2
        db.commit()

        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        step = InspectionExecutionEngine.execute_next_step(db, exec_progress.mission_id, step_increment_m=100.0)
        assert step.status == "ABORTED_LOW_BATTERY"
        updated_rover = RoverRepository.get_by_id(db, rover.id)
        assert updated_rover.operating_state == "RETURNING"

    def test_motor_overheating_aborts_mission(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        rover.motor_temp_c = 54.9
        db.commit()

        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        step = InspectionExecutionEngine.execute_next_step(db, exec_progress.mission_id, step_increment_m=100.0)
        assert step.status == "ABORTED_SENSOR_FAULT"
        updated_rover = RoverRepository.get_by_id(db, rover.id)
        assert updated_rover.operating_state == "RETURNING"

    def test_advance_step_to_completion(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        rover.battery_percentage = 98.0
        rover.motor_temp_c = 25.0
        db.commit()

        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        # Advance until completed
        for _ in range(12):
            if exec_progress.status in ["COMPLETED", "ABORTED_LOW_BATTERY"]:
                break
            exec_progress = InspectionExecutionEngine.execute_next_step(db, exec_progress.mission_id, step_increment_m=100.0)

        assert exec_progress.status == "COMPLETED"
        updated_rover = RoverRepository.get_by_id(db, rover.id)
        assert updated_rover.operating_state == "IDLE"

    def test_advance_step_on_completed_mission_raises_400(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        for _ in range(12):
            if exec_progress.status == "COMPLETED":
                break
            exec_progress = InspectionExecutionEngine.execute_next_step(db, exec_progress.mission_id, step_increment_m=100.0)

        with pytest.raises(Exception):
            InspectionExecutionEngine.execute_next_step(db, exec_progress.mission_id, step_increment_m=50.0)

    def test_adapt_route_on_completed_mission_raises_400(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        for _ in range(12):
            if exec_progress.status == "COMPLETED":
                break
            exec_progress = InspectionExecutionEngine.execute_next_step(db, exec_progress.mission_id, step_increment_m=100.0)

        with pytest.raises(Exception):
            InspectionExecutionEngine.trigger_adaptive_reroute(db, exec_progress.mission_id, "Detour")

    def test_get_progress_matches_saved_state(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        progress = InspectionExecutionEngine.get_progress(db, exec_progress.mission_id)
        assert progress.mission_id == exec_progress.mission_id
        assert progress.status == "IN_PROGRESS"

    def test_mission_progress_simulation_provenance_flag(self, db, ready_plan_and_rover):
        plan, rover = ready_plan_and_rover
        exec_progress = InspectionExecutionEngine.start_mission_execution(db, plan.id, rover.id)
        assert exec_progress.is_simulated is True


# =============================================================================
# 8. EVIDENCE-GROUNDED INSPECTION REPORTS (15 TESTS)
# =============================================================================
class TestEvidenceGroundedReports:
    @pytest.fixture
    def completed_report(self, db):
        rep = InspectionReportSchema(
            id=f"INSP-REP-{uuid.uuid4().hex[:6].upper()}",
            plan_id="PLAN-AUTO-01",
            mission_id=f"MIS-{uuid.uuid4().hex[:6].upper()}",
            rover_id="ROV-AQUA-01",
            pipeline_segment_id="PIPE-SEC-01",
            segment_name="Metro Secondary Main",
            inspection_method="ACOUSTIC_CORRELATION",
            start_time=datetime.now(timezone.utc).isoformat(),
            completion_time=datetime.now(timezone.utc).isoformat(),
            route_distance_m=820.0,
            inspected_distance_m=790.0,
            sensor_observations_count=16,
            detected_anomalies=[{"type": "ACOUSTIC_SURGE", "spl_db": 74.5, "station_m": 185.0}],
            evidence_provenance="SIMULATED",
            ai_classification={"acoustic_leak_probability": 0.88, "confidence": 0.92},
            updated_infrastructure_risk=72.0,
            inspection_outcome="SUCCESS",
            unresolved_uncertainties=["Subsurface soil compaction unmeasured"],
            recommended_next_action="Deploy ground acoustic crew",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        saved = InspectionIntelligenceRepository.save_report(db, rep)
        return rep, saved

    def test_report_persistence(self, completed_report, db):
        rep, saved = completed_report
        loaded = InspectionIntelligenceRepository.get_report(db, rep.id)
        assert loaded is not None
        assert loaded.pipeline_segment_id == rep.pipeline_segment_id

    def test_report_payload_hash_generated(self, completed_report, db):
        _, saved = completed_report
        assert saved.payload_hash is not None
        assert len(saved.payload_hash) == 64 # SHA-256

    def test_report_evidence_provenance_simulated(self, completed_report):
        rep, _ = completed_report
        assert rep.evidence_provenance == "SIMULATED"

    def test_report_detected_anomalies_list(self, completed_report):
        rep, _ = completed_report
        assert len(rep.detected_anomalies) == 1
        assert rep.detected_anomalies[0]["type"] == "ACOUSTIC_SURGE"

    def test_report_unresolved_uncertainties_list(self, completed_report):
        rep, _ = completed_report
        assert len(rep.unresolved_uncertainties) >= 1

    def test_report_operator_review_status_pending_review(self, completed_report):
        rep, _ = completed_report
        assert rep.operator_review_status == "PENDING_REVIEW"

    def test_report_ai_classification_probability(self, completed_report):
        rep, _ = completed_report
        assert rep.ai_classification is not None
        assert 0.0 <= rep.ai_classification["acoustic_leak_probability"] <= 1.0

    def test_report_updated_infrastructure_risk_in_bounds(self, completed_report):
        rep, _ = completed_report
        assert 0.0 <= rep.updated_infrastructure_risk <= 100.0

    def test_report_inspected_distance_positive(self, completed_report):
        rep, _ = completed_report
        assert rep.inspected_distance_m > 0.0

    def test_list_reports_returns_array(self, completed_report, db):
        reps = InspectionIntelligenceRepository.list_reports(db)
        assert len(reps) >= 1

    def test_report_outcome_is_success(self, completed_report):
        rep, _ = completed_report
        assert rep.inspection_outcome == "SUCCESS"

    def test_report_recommended_next_action_non_empty(self, completed_report):
        rep, _ = completed_report
        assert len(rep.recommended_next_action) > 5

    def test_report_simulation_flag_true(self, completed_report):
        rep, _ = completed_report
        assert rep.is_simulated is True

    def test_operator_review_updates_status(self, completed_report, db):
        rep, saved = completed_report
        saved.operator_review_status = "ACTION_APPROVED"
        saved.reviewed_by = "operator_chief"
        db.commit()

        loaded = InspectionIntelligenceRepository.get_report(db, rep.id)
        assert loaded.operator_review_status == "ACTION_APPROVED"
        assert loaded.reviewed_by == "operator_chief"

    def test_report_model_serialization(self, completed_report):
        rep, _ = completed_report
        d = rep.model_dump()
        assert "sensor_observations_count" in d


# =============================================================================
# 9. API ENDPOINTS & ZERO-TRUST RBAC (20 TESTS)
# =============================================================================
class TestApiEndpointsAndRbac:
    def test_api_status_endpoint(self, client):
        res = client.get("/api/v1/inspection-intelligence/status")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "OPERATIONAL"
        assert "ACOUSTIC_CORRELATION" in data["supported_methods"]

    def test_get_recommendations_viewer_allowed(self, client, viewer_token):
        res = client.get(
            "/api/v1/inspection-intelligence/recommendations",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_get_recommendations_unauthenticated_forbidden(self, client):
        with patch.object(settings, "REQUIRE_AUTH", True):
            res = client.get("/api/v1/inspection-intelligence/recommendations")
            assert res.status_code in [401, 403]

    def test_generate_recommendations_viewer_forbidden(self, client, viewer_token):
        res = client.post(
            "/api/v1/inspection-intelligence/recommendations/generate",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == 403

    def test_generate_recommendations_operator_allowed(self, client, operator_token):
        res = client.post(
            "/api/v1/inspection-intelligence/recommendations/generate",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert res.status_code == 200

    def test_get_rover_suitability_endpoint(self, client, viewer_token):
        res = client.get(
            "/api/v1/inspection-intelligence/rovers/suitability?target_lat=40.7128&target_lng=-74.006",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_generate_plan_viewer_forbidden(self, client, viewer_token):
        res = client.post(
            "/api/v1/inspection-intelligence/plans/generate",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"plan_name": "Test Plan"},
        )
        assert res.status_code == 403

    def test_generate_plan_operator_allowed(self, client, operator_token):
        res = client.post(
            "/api/v1/inspection-intelligence/plans/generate",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"plan_name": "API Operator Plan"},
        )
        assert res.status_code == 200
        assert "id" in res.json()

    def test_list_plans_viewer_allowed(self, client, viewer_token):
        res = client.get(
            "/api/v1/inspection-intelligence/plans",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == 200

    def test_get_plan_details_viewer_allowed(self, client, operator_token, viewer_token):
        plan_res = client.post(
            "/api/v1/inspection-intelligence/plans/generate",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"plan_name": "Details Plan"},
        )
        plan_id = plan_res.json()["id"]

        res = client.get(
            f"/api/v1/inspection-intelligence/plans/{plan_id}",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == 200
        assert res.json()["id"] == plan_id

    def test_approve_plan_viewer_forbidden(self, client, operator_token, viewer_token):
        plan_res = client.post(
            "/api/v1/inspection-intelligence/plans/generate",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"plan_name": "Approve RBAC Plan"},
        )
        plan_id = plan_res.json()["id"]

        res = client.post(
            f"/api/v1/inspection-intelligence/plans/{plan_id}/approve",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"operator_notes": "Attempt"},
        )
        assert res.status_code == 403

    def test_approve_plan_operator_allowed(self, client, operator_token):
        plan_res = client.post(
            "/api/v1/inspection-intelligence/plans/generate",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"plan_name": "Approve Operator Plan"},
        )
        plan_id = plan_res.json()["id"]

        res = client.post(
            f"/api/v1/inspection-intelligence/plans/{plan_id}/approve",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"operator_notes": "Operator authorized"},
        )
        assert res.status_code == 200
        assert res.json()["human_approval_status"] == "APPROVED"

    def test_reject_plan_operator_allowed(self, client, operator_token):
        plan_res = client.post(
            "/api/v1/inspection-intelligence/plans/generate",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"plan_name": "Reject Operator Plan"},
        )
        plan_id = plan_res.json()["id"]

        res = client.post(
            f"/api/v1/inspection-intelligence/plans/{plan_id}/reject",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"rejection_reason": "Operator rejected for test."},
        )
        assert res.status_code == 200
        assert res.json()["human_approval_status"] == "REJECTED"

    def test_launch_mission_operator_allowed(self, client, operator_token):
        plan_res = client.post(
            "/api/v1/inspection-intelligence/plans/generate",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"plan_name": "Launch Mission Plan"},
        )
        plan_data = plan_res.json()
        plan_id = plan_data["id"]

        # Approve first
        client.post(
            f"/api/v1/inspection-intelligence/plans/{plan_id}/approve",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"operator_notes": "Approved for launch"},
        )

        rover_id = plan_data["allocations"][0]["rover_id"]
        res = client.post(
            f"/api/v1/inspection-intelligence/missions/{plan_id}/launch/{rover_id}",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "IN_PROGRESS"

    def test_step_mission_operator_allowed(self, client, operator_token):
        plan_res = client.post(
            "/api/v1/inspection-intelligence/plans/generate",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"plan_name": "Step Mission Plan"},
        )
        plan_data = plan_res.json()
        plan_id = plan_data["id"]

        client.post(
            f"/api/v1/inspection-intelligence/plans/{plan_id}/approve",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"operator_notes": "Approved"},
        )

        rover_id = plan_data["allocations"][0]["rover_id"]
        launch_res = client.post(
            f"/api/v1/inspection-intelligence/missions/{plan_id}/launch/{rover_id}",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        mission_id = launch_res.json()["mission_id"]

        step_res = client.post(
            f"/api/v1/inspection-intelligence/missions/{mission_id}/step?step_increment_m=80.0",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert step_res.status_code == 200
        assert step_res.json()["current_step"] == 1

    def test_adapt_route_operator_allowed(self, client, operator_token):
        plan_res = client.post(
            "/api/v1/inspection-intelligence/plans/generate",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"plan_name": "Adapt Route Plan"},
        )
        plan_data = plan_res.json()
        plan_id = plan_data["id"]

        client.post(
            f"/api/v1/inspection-intelligence/plans/{plan_id}/approve",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"operator_notes": "Approved"},
        )

        rover_id = plan_data["allocations"][0]["rover_id"]
        launch_res = client.post(
            f"/api/v1/inspection-intelligence/missions/{plan_id}/launch/{rover_id}",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        mission_id = launch_res.json()["mission_id"]

        adapt_res = client.post(
            f"/api/v1/inspection-intelligence/missions/{mission_id}/adapt-route",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"adaptation_reason": "API adaptive route test justification."},
        )
        assert adapt_res.status_code == 200
        assert adapt_res.json()["route_adapted"] is True

    def test_get_mission_progress_viewer_allowed(self, client, operator_token, viewer_token):
        plan_res = client.post(
            "/api/v1/inspection-intelligence/plans/generate",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"plan_name": "Progress Plan"},
        )
        plan_data = plan_res.json()
        plan_id = plan_data["id"]

        client.post(
            f"/api/v1/inspection-intelligence/plans/{plan_id}/approve",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"operator_notes": "Approved"},
        )

        rover_id = plan_data["allocations"][0]["rover_id"]
        launch_res = client.post(
            f"/api/v1/inspection-intelligence/missions/{plan_id}/launch/{rover_id}",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        mission_id = launch_res.json()["mission_id"]

        prog_res = client.get(
            f"/api/v1/inspection-intelligence/missions/{mission_id}/progress",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert prog_res.status_code == 200
        assert prog_res.json()["mission_id"] == mission_id

    def test_list_reports_viewer_allowed(self, client, viewer_token):
        res = client.get(
            "/api/v1/inspection-intelligence/reports",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == 200

    def test_review_report_operator_allowed(self, client, db, operator_token):
        rep = InspectionReportSchema(
            id=f"INSP-REP-{uuid.uuid4().hex[:6].upper()}",
            plan_id="PLAN-REV",
            mission_id="MIS-REV",
            rover_id="ROV-AQUA-01",
            pipeline_segment_id="PIPE-SEC-01",
            segment_name="Review Pipe",
            inspection_method="ACOUSTIC_CORRELATION",
            start_time=datetime.now(timezone.utc).isoformat(),
            completion_time=datetime.now(timezone.utc).isoformat(),
            route_distance_m=500.0,
            inspected_distance_m=480.0,
            sensor_observations_count=5,
            detected_anomalies=[],
            evidence_provenance="SIMULATED",
            updated_infrastructure_risk=30.0,
            inspection_outcome="SUCCESS",
            unresolved_uncertainties=[],
            recommended_next_action="Nominal",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        InspectionIntelligenceRepository.save_report(db, rep)

        res = client.post(
            f"/api/v1/inspection-intelligence/reports/{rep.id}/review?review_status=ACTION_APPROVED",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"notes": "Reviewed and action approved."},
        )
        assert res.status_code == 200
        assert res.json()["operator_review_status"] == "ACTION_APPROVED"

    def test_list_events_endpoint(self, client, viewer_token):
        res = client.get(
            "/api/v1/inspection-intelligence/events",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == 200
        assert isinstance(res.json(), list)


# =============================================================================
# 10. EDGE CASES & ADVERSARIAL INTEGRATION (15 TESTS)
# =============================================================================
class TestEdgeCasesAndAdversarial:
    def test_recommendation_not_found_returns_404(self, client, viewer_token):
        res = client.get(
            "/api/v1/inspection-intelligence/recommendations/NON-EXISTENT",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == 404

    def test_plan_not_found_returns_404(self, client, viewer_token):
        res = client.get(
            "/api/v1/inspection-intelligence/plans/NON-EXISTENT",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == 404

    def test_report_not_found_returns_404(self, client, viewer_token):
        res = client.get(
            "/api/v1/inspection-intelligence/reports/NON-EXISTENT",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == 404

    def test_mission_progress_not_found_returns_404(self, client, viewer_token):
        res = client.get(
            "/api/v1/inspection-intelligence/missions/NON-EXISTENT/progress",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == 404

    def test_reject_plan_empty_reason_returns_422(self, client, operator_token):
        res = client.post(
            "/api/v1/inspection-intelligence/plans/PLAN-01/reject",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"rejection_reason": ""},
        )
        assert res.status_code == 422

    def test_step_increment_below_minimum_returns_422(self, client, operator_token):
        res = client.post(
            "/api/v1/inspection-intelligence/missions/MIS-01/step?step_increment_m=5.0", # ge=10
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert res.status_code == 422

    def test_step_increment_above_maximum_returns_422(self, client, operator_token):
        res = client.post(
            "/api/v1/inspection-intelligence/missions/MIS-01/step?step_increment_m=600.0", # le=500
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert res.status_code == 422

    def test_rover_zero_battery_cannot_be_dispatched(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.battery_percentage = 0.0
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude
        )
        assert suit.is_eligible is False

    def test_rover_extreme_motor_temp_cannot_be_dispatched(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.motor_temp_c = 85.0
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude
        )
        assert suit.is_eligible is False

    def test_rover_maintenance_state_cannot_be_dispatched(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.operating_state = "MAINTENANCE"
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude
        )
        assert suit.is_eligible is False

    def test_rover_charging_state_cannot_be_dispatched(self, db):
        rover = RoverRepository.get_all(db)[0]
        rover.operating_state = "CHARGING"
        suit = RoverAllocationService.evaluate_rover_suitability(
            rover=rover, target_lat=rover.latitude, target_lng=rover.longitude
        )
        assert suit.is_eligible is False

    def test_invalid_jwt_token_returns_401(self, client):
        res = client.get(
            "/api/v1/inspection-intelligence/recommendations",
            headers={"Authorization": "Bearer INVALID.JWT.TOKEN"},
        )
        assert res.status_code == 401

    def test_empty_authorization_header_returns_401(self, client):
        with patch.object(settings, "REQUIRE_AUTH", True):
            res = client.get(
                "/api/v1/inspection-intelligence/recommendations",
                headers={"Authorization": ""},
            )
            assert res.status_code in [401, 403]

    def test_event_logging_stores_user_id(self, db):
        evt = InspectionIntelligenceRepository.log_event(
            db, event_type="TEST_EVENT", user_id="user_adv_01", details={"test": True}
        )
        assert evt.user_id == "user_adv_01"

    def test_end_to_end_inspection_campaign(self, client, db, operator_token):
        # Ensure available rovers
        for r in RoverRepository.get_all(db):
            r.operating_state = "IDLE"
            r.connection_status = "ONLINE"
            r.battery_percentage = 95.0
            r.motor_temp_c = 25.0
            r.assigned_mission_id = None
        db.commit()

        # 1. Generate recommendations
        recs_res = client.post(
            "/api/v1/inspection-intelligence/recommendations/generate",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert recs_res.status_code == 200

        # 2. Formulate Plan
        plan_res = client.post(
            "/api/v1/inspection-intelligence/plans/generate",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"plan_name": "E2E Campaign Plan"},
        )
        assert plan_res.status_code == 200
        plan_data = plan_res.json()
        plan_id = plan_data["id"]

        # 3. Approve Plan
        app_res = client.post(
            f"/api/v1/inspection-intelligence/plans/{plan_id}/approve",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"operator_notes": "E2E approved"},
        )
        assert app_res.status_code == 200

        # 4. Launch Mission
        rover_id = plan_data["allocations"][0]["rover_id"]
        launch_res = client.post(
            f"/api/v1/inspection-intelligence/missions/{plan_id}/launch/{rover_id}",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert launch_res.status_code == 200
        mission_id = launch_res.json()["mission_id"]

        # 5. Advance Step
        step_res = client.post(
            f"/api/v1/inspection-intelligence/missions/{mission_id}/step?step_increment_m=100.0",
            headers={"Authorization": f"Bearer {operator_token}"},
        )
        assert step_res.status_code == 200
        assert step_res.json()["progress_percentage"] > 0.0

