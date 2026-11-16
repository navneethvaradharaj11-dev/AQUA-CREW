"""
AQUA CREW — Master System Integration & Acceptance Test Suite (Task 19)
Comprehensive End-to-End Validation covering:
- 10-Stage Master Incident Lifecycle (from Sensor Telemetry to Simulated Resolution)
- Strict Hardware Safety Invariants (HARDWARE_ACTUATION_ENABLED = False, Air-gap enforcement)
- 6-Tier Evidence Provenance (SIMULATED, MEASURED, DERIVED, PREDICTED, OPERATOR_ENTERED, UNKNOWN)
- Sensor Quality & Calibration Penalties
- AI Leak Detection & Acoustic Classification Integration
- Hydraulic Digital Twin Simulation & Headloss Delta Calculations
- Multi-Factor Priority & Risk Scoring
- Autonomous Virtual Rover Fleet Inspection Crawl & Synthetic Findings
- Intelligent Repair Plan Formulation & Transparent Cost Estimation
- Zero-Trust RBAC & Certified Human-in-the-Loop Approval Signatures
- Post-Repair Digital Twin Verification & Automated Resolution Closure
- REST API Contracts & Overview KPI Aggregations
"""
import pytest
from datetime import datetime, timezone
from fastapi import status

from app.modules.hardware_gateway import (
    HARDWARE_ACTUATION_ENABLED,
    PROHIBITED_ACTUATION_COMMANDS,
)
from app.models.incident import (
    UnifiedIncidentModel,
    IncidentWorkflowEventModel,
    IncidentApprovalModel,
)
from app.repositories.incident_repository import IncidentRepository
from app.services.incident_orchestration_service import (
    IncidentOrchestrationService,
    IncidentLifecycleError,
)
from app.core.security import create_access_token


# ==============================================================================
# FIXTURES
# ==============================================================================
@pytest.fixture
def viewer_token():
    token, _, _ = create_access_token(user_id="USR-VIEW-01", username="viewer", role="VIEWER")
    return token


@pytest.fixture
def operator_token():
    token, _, _ = create_access_token(user_id="OPERATOR-SUPERVISOR-01", username="operator", role="OPERATOR")
    return token


@pytest.fixture
def engineer_token():
    token, _, _ = create_access_token(user_id="USR-ENG-01", username="engineer", role="ENGINEER")
    return token


@pytest.fixture
def admin_token():
    token, _, _ = create_access_token(user_id="USR-ADMIN-01", username="admin", role="ADMIN")
    return token


# ==============================================================================
# 1. HARDWARE SAFETY & SIMULATION BOUNDARY TESTS
# ==============================================================================
class TestHardwareSafetyAndSimulationBoundaries:

    def test_safety_01_hardware_actuation_strictly_disabled_globally(self):
        """Verify strict safety rule: physical actuation is globally disabled."""
        assert HARDWARE_ACTUATION_ENABLED is False

    def test_safety_02_status_endpoint_reports_safe_boundary(self, client, viewer_token):
        """GET /incidents/status must explicitly advertise simulation-only mode."""
        res = client.get("/api/v1/incidents/status", headers={"Authorization": f"Bearer {viewer_token}"})
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["status"] == "OPERATIONAL"
        assert data["hardware_actuation_enabled"] is False
        assert data["hardware_actuation_strictly_blocked"] is True
        assert data["is_simulated"] is True

    def test_safety_03_resolution_rejects_physical_valve_override(self, client, engineer_token):
        """Submitting a physical actuation command in resolution notes must trigger HTTP 403."""
        for prohibited_cmd in ["CLOSE_VALVE", "OVERRIDE_SCADA_PLC", "START_PUMP"]:
            res = client.post(
                "/api/v1/incidents/INC-2026-0001/simulation-resolution",
                headers={"Authorization": f"Bearer {engineer_token}"},
                json={"verification_notes": f"Simulating resolution by issuing {prohibited_cmd}."},
            )
            assert res.status_code == status.HTTP_403_FORBIDDEN
            err_msg = res.json().get("detail") or res.json().get("error", {}).get("message", "")
            assert "HARDWARE_ACTUATION_PROHIBITED" in err_msg


# ==============================================================================
# 2. INCIDENT LIFECYCLE & STATE MACHINE TRANSITION TESTS
# ==============================================================================
class TestIncidentLifecycleStateMachine:

    def test_lifecycle_01_valid_transition_sequence(self, db_session):
        """Verify allowable forward lifecycle progression."""
        incident = IncidentRepository.create_incident(
            db=db_session,
            title="Pipeline Vibration Anomaly",
            pipeline_segment_id="PIPE-001",
            latitude=40.7128,
            longitude=-74.0060,
        )
        assert incident.lifecycle_status == "DETECTED"

        # DETECTED -> TRIAGED
        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "TRIAGED")
        incident.lifecycle_status = "TRIAGED"

        # TRIAGED -> INVESTIGATING
        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "INVESTIGATING")
        incident.lifecycle_status = "INVESTIGATING"

        # INVESTIGATING -> INSPECTION_PROPOSED
        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "INSPECTION_PROPOSED")
        incident.lifecycle_status = "INSPECTION_PROPOSED"

        # INSPECTION_PROPOSED -> APPROVED
        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "APPROVED")
        incident.lifecycle_status = "APPROVED"

        # APPROVED -> INSPECTION_IN_PROGRESS
        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "INSPECTION_IN_PROGRESS")
        incident.lifecycle_status = "INSPECTION_IN_PROGRESS"

        # INSPECTION_IN_PROGRESS -> ASSESSED
        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "ASSESSED")
        incident.lifecycle_status = "ASSESSED"

        # ASSESSED -> REPAIR_PLANNED
        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "REPAIR_PLANNED")
        incident.lifecycle_status = "REPAIR_PLANNED"

        # REPAIR_PLANNED -> AWAITING_ENGINEERING_APPROVAL
        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "AWAITING_ENGINEERING_APPROVAL")
        incident.lifecycle_status = "AWAITING_ENGINEERING_APPROVAL"

        # AWAITING_ENGINEERING_APPROVAL -> APPROVED
        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "APPROVED")
        incident.lifecycle_status = "APPROVED"

        # APPROVED -> SIMULATED_RESOLUTION
        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "SIMULATED_RESOLUTION")
        incident.lifecycle_status = "SIMULATED_RESOLUTION"

        # SIMULATED_RESOLUTION -> CLOSED
        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "CLOSED")
        incident.lifecycle_status = "CLOSED"

    def test_lifecycle_02_illegal_transition_jump_rejected(self):
        """Illegal jumps directly to CLOSED or resolution must raise IncidentLifecycleError."""
        with pytest.raises(IncidentLifecycleError):
            IncidentOrchestrationService.validate_transition("DETECTED", "SIMULATED_RESOLUTION")

        with pytest.raises(IncidentLifecycleError):
            IncidentOrchestrationService.validate_transition("INSPECTION_PROPOSED", "ASSESSED")


# ==============================================================================
# 3. TELEMETRY, AI DETECTION & HYDRAULIC DIGITAL TWIN INTEGRATION
# ==============================================================================
class TestTelemetryAiAndDigitalTwinIntegration:

    def test_integration_01_telemetry_to_ai_leak_probability(self, db_session):
        """Stage 1 & 2: Sensor telemetry triggers acoustic AI leak detection."""
        t_data = IncidentOrchestrationService.execute_stage_1_telemetry_ingest(
            db=db_session,
            device_id="DEV-ACOUSTIC-01",
            sensor_id="SNS-AC-01-A",
            acoustic_db=88.5,
            frequency_hz=1400.0,
        )
        assert t_data["normalized_value"] == 88.5
        assert t_data["calibrated"] is True
        assert t_data["provenance"] == "SIMULATED"

        ai_res = IncidentOrchestrationService.execute_stage_2_ai_leak_detection(t_data)
        assert ai_res["is_anomaly"] is True
        assert ai_res["classification"] == "LEAK_DETECTED"
        assert ai_res["leak_probability"] > 0.85
        assert ai_res["confidence"] >= 0.90

    def test_integration_02_uncalibrated_sensor_confidence_penalty(self, db_session):
        """Telemetry outside valid physics range receives a confidence penalty."""
        t_data = IncidentOrchestrationService.execute_stage_1_telemetry_ingest(
            db=db_session,
            device_id="DEV-ACOUSTIC-01",
            sensor_id="SNS-AC-01-A",
            acoustic_db=155.0,  # Out of normal 0-140dB range
        )
        assert t_data["calibrated"] is False

        ai_res = IncidentOrchestrationService.execute_stage_2_ai_leak_detection(t_data)
        assert ai_res["confidence"] == 0.70  # Penalized confidence

    def test_integration_03_hydraulic_twin_headloss_simulation(self, db_session):
        """Stage 4: Digital twin calculates headloss delta and flow loss."""
        incident = IncidentRepository.create_incident(
            db=db_session,
            title="Acoustic Anomaly",
            pipeline_segment_id="PIPE-SEC-4B-92",
            latitude=40.7128,
            longitude=-74.0060,
            ai_leak_probability=0.88,
        )
        incident.lifecycle_status = "TRIAGED"
        db_session.commit()

        updated = IncidentOrchestrationService.execute_stage_4_hydraulic_digital_twin_simulation(
            db=db_session,
            incident_id=incident.id,
        )
        assert updated.lifecycle_status == "INVESTIGATING"
        assert updated.hydraulic_headloss_delta > 0.0
        assert updated.estimated_loss_lps > 0.0

    def test_integration_04_multi_factor_risk_scoring(self, db_session):
        """Stage 5: Multi-factor risk combines AI probability, hydraulic loss, and zone criticality."""
        incident = IncidentRepository.create_incident(
            db=db_session,
            title="Acoustic Anomaly",
            pipeline_segment_id="PIPE-SEC-4B-92",
            latitude=40.7128,
            longitude=-74.0060,
            ai_leak_probability=0.92,
            dma_zone="DMA-METRO-CENTRAL",
        )
        incident.lifecycle_status = "INVESTIGATING"
        incident.estimated_loss_lps = 15.0
        db_session.commit()

        updated = IncidentOrchestrationService.execute_stage_5_risk_scoring_and_proposal(
            db=db_session,
            incident_id=incident.id,
        )
        assert updated.lifecycle_status == "INSPECTION_PROPOSED"
        assert updated.risk_score > 60.0


# ==============================================================================
# 4. VIRTUAL ROVER INSPECTION & REPAIR PLANNING
# ==============================================================================
class TestVirtualInspectionAndRepairPlanning:

    def test_workflow_01_rover_selection_and_assignment(self, db_session):
        """Stage 6: Selects virtual rover and links proposed mission ID."""
        incident = IncidentRepository.create_incident(
            db=db_session,
            title="Suspected Crack",
            pipeline_segment_id="PIPE-002",
            latitude=40.7160,
            longitude=-73.9980,
        )
        updated = IncidentOrchestrationService.execute_stage_6_rover_selection_and_assignment(
            db=db_session,
            incident_id=incident.id,
            preferred_rover_id="ROV-001",
        )
        assert updated.assigned_rover_id == "ROV-001"
        assert updated.inspection_mission_id.startswith("MSN-INSP-")

    def test_workflow_02_inspection_crawl_findings(self, db_session):
        """Stage 7: Virtual crawl produces structured defect measurements."""
        incident = IncidentRepository.create_incident(
            db=db_session,
            title="Suspected Crack",
            pipeline_segment_id="PIPE-002",
            latitude=40.7160,
            longitude=-73.9980,
        )
        incident.lifecycle_status = "INSPECTION_PROPOSED"
        incident.assigned_rover_id = "ROV-001"
        db_session.commit()

        updated = IncidentOrchestrationService.execute_stage_7_human_approval_and_inspection(
            db=db_session,
            incident_id=incident.id,
            operator_id="OPERATOR-SUPERVISOR-01",
            operator_role="OPERATOR",
            approved=True,
        )
        assert updated.lifecycle_status == "ASSESSED"
        assert updated.inspection_findings is not None
        assert updated.inspection_findings["pipe_defect"] == "LONGITUDINAL_CRACK"
        assert updated.inspection_findings["crack_length_mm"] > 0.0

    def test_workflow_03_repair_plan_recommendation(self, db_session):
        """Stage 8: Formulates engineering repair plan and cost estimate."""
        incident = IncidentRepository.create_incident(
            db=db_session,
            title="Assessed Pipe Crack",
            pipeline_segment_id="PIPE-002",
            latitude=40.7160,
            longitude=-73.9980,
        )
        incident.lifecycle_status = "ASSESSED"
        incident.inspection_findings = {"crack_length_mm": 140.0}
        db_session.commit()

        updated = IncidentOrchestrationService.execute_stage_8_repair_planning_and_recommendation(
            db=db_session,
            incident_id=incident.id,
        )
        assert updated.lifecycle_status == "AWAITING_ENGINEERING_APPROVAL"
        assert updated.repair_cost_estimate == 2450.0
        assert updated.repair_urgency == "HIGH_PRIORITY_48H"


# ==============================================================================
# 5. ZERO-TRUST RBAC & CERTIFIED HUMAN APPROVALS
# ==============================================================================
class TestZeroTrustRbacAndApprovals:

    def test_rbac_01_viewer_cannot_approve_missions(self, client, viewer_token):
        """VIEWER role cannot approve inspection missions (HTTP 403 Forbidden)."""
        res = client.post(
            "/api/v1/incidents/INC-2026-0002/approve",
            headers={"Authorization": f"Bearer {viewer_token}"},
            json={"approval_type": "INSPECTION_DISPATCH", "approved": True},
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_rbac_02_operator_can_approve_inspection_dispatch(self, client, operator_token):
        """OPERATOR role is authorized to approve virtual rover inspection dispatch."""
        res = client.post(
            "/api/v1/incidents/INC-2026-0002/approve",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={
                "approval_type": "INSPECTION_DISPATCH",
                "approved": True,
                "comments": "Approved for autonomous rover crawl.",
            },
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["lifecycle_status"] == "ASSESSED"

    def test_rbac_03_operator_cannot_certify_repair_plan(self, client, operator_token):
        """OPERATOR role is not authorized to certify repair plans (Requires ENGINEER or ADMIN)."""
        res = client.post(
            "/api/v1/incidents/INC-2026-0003/approve",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"approval_type": "REPAIR_PLAN", "approved": True},
        )
        assert res.status_code == status.HTTP_403_FORBIDDEN
        err_msg = res.json().get("detail") or res.json().get("error", {}).get("message", "")
        assert "not authorized to approve repair plans" in err_msg

    def test_rbac_04_engineer_can_certify_repair_plan(self, client, engineer_token):
        """Certified municipal ENGINEER can approve repair plans with digital signature."""
        res = client.post(
            "/api/v1/incidents/INC-2026-0003/approve",
            headers={"Authorization": f"Bearer {engineer_token}"},
            json={
                "approval_type": "REPAIR_PLAN",
                "approved": True,
                "comments": "Certified engineering repair approval for full-circle clamp.",
            },
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["lifecycle_status"] == "APPROVED"
        # Check approval signature in database
        approvals = data["approvals"]
        assert len(approvals) > 0
        latest = [a for a in approvals if a["approval_type"] == "REPAIR_PLAN"][-1]
        assert latest["status"] == "APPROVED"
        assert latest["digital_signature"] is not None

    def test_rbac_05_rejection_requires_justification(self, db_session):
        """Engineering rejection requires mandatory explanatory comments."""
        incident = IncidentRepository.create_incident(
            db=db_session,
            title="Awaiting Plan",
            pipeline_segment_id="PIPE-003",
            latitude=40.7250,
            longitude=-74.0120,
        )
        incident.lifecycle_status = "AWAITING_ENGINEERING_APPROVAL"
        db_session.commit()

        with pytest.raises(IncidentLifecycleError):
            IncidentOrchestrationService.execute_stage_9_certified_engineering_approval(
                db=db_session,
                incident_id=incident.id,
                engineer_id="USR-ENG-01",
                engineer_role="ENGINEER",
                approved=False,
                comments="   ",  # Blank rejection reason rejected
            )


# ==============================================================================
# 6. SIMULATED RESOLUTION & TWIN RESTORATION
# ==============================================================================
class TestSimulatedResolutionAndTwinRestoration:

    def test_resolution_01_simulated_resolution_restores_pressure(self, client, engineer_token, db_session):
        """Stage 10: Running simulated resolution eliminates headloss and closes incident."""
        incident = IncidentRepository.get_by_id(db_session, "INC-2026-0003") or IncidentRepository.get_by_code(db_session, "INC-2026-003")
        assert incident is not None
        incident.lifecycle_status = "APPROVED"
        incident.hydraulic_headloss_delta = 8.70
        incident.estimated_loss_lps = 34.2
        db_session.commit()

        res = client.post(
            f"/api/v1/incidents/{incident.id}/simulation-resolution",
            headers={"Authorization": f"Bearer {engineer_token}"},
            json={"verification_notes": "Digital twin verifies nominal pressure and 0 L/s loss restoration."},
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["lifecycle_status"] == "CLOSED"
        sim_data = data["simulation_resolution_data"]
        assert sim_data["hydraulic_stability_verified"] is True
        assert sim_data["leak_flow_eliminated_lps"] == 34.2
        assert sim_data["post_repair_pressure_gain_bar"] > 0.0


# ==============================================================================
# 7. REST API ENDPOINT CONTRACTS & KPI OVERVIEW
# ==============================================================================
class TestRestApiEndpoints:

    def test_api_01_list_incidents_with_filters(self, client, viewer_token):
        """GET /incidents supports status and severity filtering."""
        res = client.get(
            "/api/v1/incidents?severity=CRITICAL",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "items" in data
        assert "total" in data
        for item in data["items"]:
            assert item["severity"] == "CRITICAL"

    def test_api_02_get_incident_detail(self, client, viewer_token):
        """GET /incidents/{id} returns complete workspace details and audit logs."""
        res = client.get(
            "/api/v1/incidents/INC-2026-0001",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["incident_code"] == "INC-2026-001"
        assert len(data["workflow_events"]) > 0

    def test_api_03_overview_kpis(self, client, viewer_token):
        """GET /incidents/stats/overview aggregates live system-wide KPIs."""
        res = client.get(
            "/api/v1/incidents/stats/overview",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["total_incidents"] >= 4
        assert data["active_incidents"] >= 1
        assert "by_status" in data
        assert "by_severity" in data

    def test_api_04_create_incident(self, client, operator_token):
        """POST /incidents allows operator to register an anomaly manually."""
        payload = {
            "title": "Manual Water Main Report",
            "pipeline_segment_id": "PIPE-SEC-4B-92",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "description": "Visual surface ponding reported near valve chamber.",
            "category": "SUSPECTED_LEAK",
            "severity": "HIGH",
            "priority": "P1",
            "dma_zone": "DMA-METRO-CENTRAL",
            "ai_leak_probability": 0.85,
        }
        res = client.post(
            "/api/v1/incidents",
            headers={"Authorization": f"Bearer {operator_token}"},
            json=payload,
        )
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["title"] == "Manual Water Main Report"
        assert data["lifecycle_status"] == "DETECTED"


# ==============================================================================
# 8. MASTER 10-STAGE END-TO-END ACCEPTANCE SCENARIO
# ==============================================================================
class TestMasterAcceptanceScenario:

    def test_master_e2e_01_complete_10_stage_execution(self, client, operator_token):
        """Executes full 10-stage Master Acceptance Scenario from sensor telemetry reading to closure."""
        res = client.post(
            "/api/v1/incidents/scenarios/master-e2e",
            headers={"Authorization": f"Bearer {operator_token}"},
            json={"pipeline_segment_id": "PIPE-SEC-4B-92", "acoustic_db": 89.5},
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["success"] is True
        assert data["lifecycle_status"] == "CLOSED"
        assert data["hardware_actuation_blocked"] is True
        assert data["is_simulated"] is True
        assert data["total_workflow_events"] >= 8
        assert data["total_approvals"] >= 2
        assert data["final_resolution_data"]["hydraulic_stability_verified"] is True
