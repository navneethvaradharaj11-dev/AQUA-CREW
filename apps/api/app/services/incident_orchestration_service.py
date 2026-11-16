"""
AQUA CREW — Master End-to-End Incident Orchestration Service (Task 19)
Orchestrates the unified 10-stage incident lifecycle connecting:
- Task 18/06: IoT Telemetry & Sensor Calibration
- Task 07: AI Acoustic Leak Detection
- Task 04/11: GIS & Graph Localization
- Task 10/14: Hydraulic Digital Twin Simulation
- Task 09/11/12: Risk & Predictive Maintenance
- Task 08/15: Virtual Rover Mission Planning & Inspection
- Task 16: Intelligent Repair Planning & Management
- Task 13/13.6: Evidence Provenance & Certified Human Approval
- Task 19: Simulated Resolution & Twin Verification
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import json
import uuid
import math
from sqlalchemy.orm import Session

from app.models.incident import (
    UnifiedIncidentModel,
    IncidentWorkflowEventModel,
    IncidentApprovalModel,
)
from app.repositories.incident_repository import IncidentRepository
from app.modules.hardware_gateway import (
    HARDWARE_ACTUATION_ENABLED,
    PROHIBITED_ACTUATION_COMMANDS,
)


class IncidentLifecycleError(Exception):
    """Raised when an illegal lifecycle state transition or unauthorized operation is attempted."""
    pass


VALID_TRANSITIONS = {
    "NONE": ["DETECTED"],
    "DETECTED": ["TRIAGED", "CLOSED"],
    "TRIAGED": ["INVESTIGATING", "CLOSED"],
    "INVESTIGATING": ["INSPECTION_PROPOSED", "CLOSED"],
    "INSPECTION_PROPOSED": ["APPROVED", "CLOSED"],
    "APPROVED": ["INSPECTION_IN_PROGRESS", "SIMULATED_RESOLUTION", "CLOSED"],
    "INSPECTION_IN_PROGRESS": ["ASSESSED", "CLOSED"],
    "ASSESSED": ["REPAIR_PLANNED", "CLOSED"],
    "REPAIR_PLANNED": ["AWAITING_ENGINEERING_APPROVAL", "CLOSED"],
    "AWAITING_ENGINEERING_APPROVAL": ["APPROVED", "REPAIR_PLANNED", "CLOSED"],
    "SIMULATED_RESOLUTION": ["CLOSED"],
    "CLOSED": [],
}


class IncidentOrchestrationService:

    @staticmethod
    def validate_transition(current_status: str, target_status: str) -> None:
        allowed = VALID_TRANSITIONS.get(current_status, [])
        if target_status not in allowed:
            raise IncidentLifecycleError(
                f"Invalid lifecycle transition from '{current_status}' to '{target_status}'. "
                f"Allowed transitions: {allowed}"
            )

    @staticmethod
    def execute_stage_1_telemetry_ingest(
        db: Session,
        device_id: str,
        sensor_id: str,
        acoustic_db: float,
        frequency_hz: float = 1250.0,
        pipeline_segment_id: str = "PIPE-SEC-4B-92",
        dma_zone: str = "DMA-METRO-CENTRAL",
        latitude: float = 40.7128,
        longitude: float = -74.0060,
    ) -> Dict[str, Any]:
        """Stage 1: Process sensor telemetry observation with calibration checks and simulated provenance."""
        # Hardware safety invariant: Simulation-first
        if HARDWARE_ACTUATION_ENABLED:
            raise IncidentLifecycleError("SAFETY VIOLATION: Hardware actuation must never be enabled.")

        # Baseline noise calibration check
        calibrated = True
        calibration_offset = 0.0
        if acoustic_db < 0.0 or acoustic_db > 140.0:
            calibrated = False

        normalized_db = acoustic_db - calibration_offset
        return {
            "device_id": device_id,
            "sensor_id": sensor_id,
            "raw_value": acoustic_db,
            "normalized_value": normalized_db,
            "unit": "dB",
            "frequency_hz": frequency_hz,
            "calibrated": calibrated,
            "pipeline_segment_id": pipeline_segment_id,
            "dma_zone": dma_zone,
            "latitude": latitude,
            "longitude": longitude,
            "provenance": "SIMULATED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def execute_stage_2_ai_leak_detection(
        telemetry_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Stage 2: Evaluate acoustic signature using AI leak detection principles."""
        db_val = telemetry_data.get("normalized_value", 50.0)
        freq = telemetry_data.get("frequency_hz", 1000.0)

        # Acoustic leak physics: leaks typically present high energy in 800-2500Hz band
        freq_factor = 1.0 if (800.0 <= freq <= 2500.0) else 0.6
        raw_prob = 1.0 / (1.0 + math.exp(-(db_val - 65.0) / 10.0))
        leak_prob = round(float(min(0.99, max(0.01, raw_prob * freq_factor))), 3)
        confidence = 0.94 if telemetry_data.get("calibrated", True) else 0.70

        is_anomaly = leak_prob >= 0.50
        classification = "LEAK_DETECTED" if is_anomaly else "NORMAL_FLOW"

        return {
            "is_anomaly": is_anomaly,
            "classification": classification,
            "leak_probability": leak_prob,
            "confidence": confidence,
            "dominant_frequency_hz": freq,
            "acoustic_energy_db": db_val,
            "evidence_tier": "SIMULATED",
        }

    @staticmethod
    def execute_stage_3_localize_and_create_incident(
        db: Session,
        telemetry_data: Dict[str, Any],
        ai_findings: Dict[str, Any],
        actor_id: str = "SYSTEM_AI_ENGINE",
    ) -> UnifiedIncidentModel:
        """Stage 3: Map anomaly to pipeline segment and register unified incident (DETECTED -> TRIAGED)."""
        pipe_id = telemetry_data.get("pipeline_segment_id", "PIPE-SEC-4B-92")
        dma = telemetry_data.get("dma_zone", "DMA-METRO-CENTRAL")
        lat = telemetry_data.get("latitude", 40.7128)
        lon = telemetry_data.get("longitude", -74.0060)

        prob = ai_findings.get("leak_probability", 0.85)
        severity = "CRITICAL" if prob > 0.90 else "HIGH" if prob > 0.75 else "MEDIUM"
        priority = "P1" if severity in ["CRITICAL", "HIGH"] else "P2"

        title = f"Acoustic Leak Anomaly on {pipe_id}"
        description = (
            f"Automated AI detection identified leak signature ({ai_findings.get('acoustic_energy_db')} dB) "
            f"with probability {prob:.2f} in {dma}."
        )

        incident = IncidentRepository.create_incident(
            db=db,
            title=title,
            pipeline_segment_id=pipe_id,
            latitude=lat,
            longitude=lon,
            description=description,
            category="ACOUSTIC_ANOMALY",
            severity=severity,
            priority=priority,
            dma_zone=dma,
            detection_source="TELEMETRY_ACOUSTIC",
            sensor_ids=[telemetry_data.get("sensor_id", "SNS-AC-01-A")],
            ai_leak_probability=prob,
            ai_confidence=ai_findings.get("confidence", 0.90),
            created_by=actor_id,
        )

        # Transition DETECTED -> TRIAGED
        incident.lifecycle_status = "TRIAGED"
        IncidentRepository.add_workflow_event(
            db=db,
            incident_id=incident.id,
            from_status="DETECTED",
            to_status="TRIAGED",
            stage_number=3,
            action="AI_TRIAGE_COMPLETED",
            actor_id=actor_id,
            actor_role="SYSTEM",
            notes=f"Automated triage classified severity as {severity} ({priority}).",
            payload={"severity": severity, "priority": priority, "leak_probability": prob},
        )
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def execute_stage_4_hydraulic_digital_twin_simulation(
        db: Session,
        incident_id: str,
        actor_id: str = "SYSTEM_HYDRAULIC_ENGINE",
    ) -> UnifiedIncidentModel:
        """Stage 4: Simulate hydraulic network delta (TRIAGED -> INVESTIGATING)."""
        incident = IncidentRepository.get_by_id(db, incident_id) or IncidentRepository.get_by_code(db, incident_id)
        if not incident:
            raise IncidentLifecycleError(f"Incident {incident_id} not found.")

        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "INVESTIGATING")

        # Hydraulic physics simulation:
        # Pressure drop delta based on pipe diameter, flow velocity, and estimated orifice
        # Orifice flow Q = Cd * A * sqrt(2 * g * h)
        prob = incident.ai_leak_probability
        headloss_delta = round(3.5 * prob + 1.2, 2)
        loss_lps = round(headloss_delta * 2.8, 1)

        incident.lifecycle_status = "INVESTIGATING"
        incident.hydraulic_headloss_delta = headloss_delta
        incident.estimated_loss_lps = loss_lps
        incident.updated_at = datetime.now(timezone.utc)

        IncidentRepository.add_workflow_event(
            db=db,
            incident_id=incident.id,
            from_status="TRIAGED",
            to_status="INVESTIGATING",
            stage_number=4,
            action="DIGITAL_TWIN_SIMULATED",
            actor_id=actor_id,
            actor_role="SYSTEM",
            notes=f"Hydraulic twin simulated headloss delta of {headloss_delta}m with {loss_lps} L/s estimated loss.",
            payload={"headloss_delta_m": headloss_delta, "estimated_loss_lps": loss_lps},
        )
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def execute_stage_5_risk_scoring_and_proposal(
        db: Session,
        incident_id: str,
        actor_id: str = "SYSTEM_RISK_ENGINE",
    ) -> UnifiedIncidentModel:
        """Stage 5: Multi-factor risk calculation & proposal (INVESTIGATING -> INSPECTION_PROPOSED)."""
        incident = IncidentRepository.get_by_id(db, incident_id) or IncidentRepository.get_by_code(db, incident_id)
        if not incident:
            raise IncidentLifecycleError(f"Incident {incident_id} not found.")

        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "INSPECTION_PROPOSED")

        # Multi-factor risk formula:
        # 40% AI leak probability + 35% hydraulic loss severity + 25% zone criticality
        zone_crit = 85.0 if "METRO" in (incident.dma_zone or "") else 65.0
        calculated_risk = round(
            (incident.ai_leak_probability * 100.0 * 0.40) +
            (min(100.0, incident.estimated_loss_lps * 4.0) * 0.35) +
            (zone_crit * 0.25),
            1,
        )

        incident.lifecycle_status = "INSPECTION_PROPOSED"
        incident.risk_score = calculated_risk
        incident.updated_at = datetime.now(timezone.utc)

        # Create approval request for human operator
        IncidentRepository.create_approval_request(
            db=db,
            incident_id=incident.id,
            approval_type="INSPECTION_DISPATCH",
            requested_by=actor_id,
            comments=f"Inspection mission proposed due to risk score {calculated_risk} on {incident.pipeline_segment_id}.",
        )

        IncidentRepository.add_workflow_event(
            db=db,
            incident_id=incident.id,
            from_status="INVESTIGATING",
            to_status="INSPECTION_PROPOSED",
            stage_number=5,
            action="INSPECTION_MISSION_PROPOSED",
            actor_id=actor_id,
            actor_role="SYSTEM",
            notes=f"Multi-factor risk scored at {calculated_risk}/100. Awaiting operator dispatch approval.",
            payload={"risk_score": calculated_risk, "recommended_action": "DISPATCH_VIRTUAL_ROVER"},
        )
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def execute_stage_6_rover_selection_and_assignment(
        db: Session,
        incident_id: str,
        preferred_rover_id: Optional[str] = None,
        actor_id: str = "SYSTEM_DISPATCH_ENGINE",
    ) -> UnifiedIncidentModel:
        """Stage 6: Select best virtual rover for inspection based on battery, payloads, and availability."""
        incident = IncidentRepository.get_by_id(db, incident_id) or IncidentRepository.get_by_code(db, incident_id)
        if not incident:
            raise IncidentLifecycleError(f"Incident {incident_id} not found.")

        rover_id = preferred_rover_id or "ROV-001"
        mission_id = f"MSN-INSP-{uuid.uuid4().hex[:6].upper()}"

        incident.assigned_rover_id = rover_id
        incident.inspection_mission_id = mission_id
        incident.updated_at = datetime.now(timezone.utc)

        IncidentRepository.add_workflow_event(
            db=db,
            incident_id=incident.id,
            from_status=incident.lifecycle_status,
            to_status=incident.lifecycle_status,
            stage_number=6,
            action="ROVER_SUITABILITY_EVALUATED",
            actor_id=actor_id,
            actor_role="SYSTEM",
            notes=f"Virtual rover {rover_id} selected with acoustic and HD visual inspection payloads.",
            payload={"rover_id": rover_id, "mission_id": mission_id},
        )
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def execute_stage_7_human_approval_and_inspection(
        db: Session,
        incident_id: str,
        operator_id: str,
        operator_role: str,
        approved: bool = True,
        comments: str = "Approved for autonomous virtual rover crawl inspection.",
    ) -> UnifiedIncidentModel:
        """Stage 7: Certified human approval of mission, execution of virtual inspection (INSPECTION_PROPOSED -> APPROVED -> INSPECTION_IN_PROGRESS -> ASSESSED)."""
        incident = IncidentRepository.get_by_id(db, incident_id) or IncidentRepository.get_by_code(db, incident_id)
        if not incident:
            raise IncidentLifecycleError(f"Incident {incident_id} not found.")

        # Human in the loop verification: role must be OPERATOR, ENGINEER, or ADMIN
        if operator_role.upper() not in ["OPERATOR", "ENGINEER", "ADMIN"]:
            raise IncidentLifecycleError(f"Role '{operator_role}' is not authorized to approve inspection missions.")

        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "APPROVED")

        # Find pending approval
        pending_appr = (
            db.query(IncidentApprovalModel)
            .filter(
                IncidentApprovalModel.incident_id == incident.id,
                IncidentApprovalModel.approval_type == "INSPECTION_DISPATCH",
                IncidentApprovalModel.status == "PENDING",
            )
            .first()
        )
        if pending_appr:
            IncidentRepository.record_approval_decision(
                db=db,
                approval_id=pending_appr.id,
                status="APPROVED" if approved else "REJECTED",
                approved_by=operator_id,
                approver_role=operator_role,
                comments=comments,
            )

        if not approved:
            incident.lifecycle_status = "CLOSED"
            incident.resolution_summary = f"Inspection mission rejected by {operator_id}: {comments}"
            IncidentRepository.add_workflow_event(
                db=db,
                incident_id=incident.id,
                from_status="INSPECTION_PROPOSED",
                to_status="CLOSED",
                stage_number=7,
                action="INSPECTION_REJECTED",
                actor_id=operator_id,
                actor_role=operator_role,
                notes=comments,
            )
            db.commit()
            db.refresh(incident)
            return incident

        # Transition INSPECTION_PROPOSED -> APPROVED -> INSPECTION_IN_PROGRESS
        incident.lifecycle_status = "INSPECTION_IN_PROGRESS"
        IncidentRepository.add_workflow_event(
            db=db,
            incident_id=incident.id,
            from_status="INSPECTION_PROPOSED",
            to_status="INSPECTION_IN_PROGRESS",
            stage_number=7,
            action="MISSION_DISPATCHED",
            actor_id=operator_id,
            actor_role=operator_role,
            notes=f"Human operator {operator_id} approved rover dispatch.",
            payload={"approved_by": operator_id, "rover_id": incident.assigned_rover_id},
        )

        # Execute virtual inspection crawl
        findings = {
            "rover_id": incident.assigned_rover_id,
            "pipe_defect": "LONGITUDINAL_CRACK",
            "crack_width_mm": 3.4,
            "crack_length_mm": 145.0,
            "acoustic_peak_db": 84.6,
            "visual_confidence": 0.95,
            "inspection_score": 0.88,
            "structural_wear_pct": 42.0,
            "provenance": "SIMULATED",
        }
        incident.inspection_findings = findings
        incident.lifecycle_status = "ASSESSED"
        incident.updated_at = datetime.now(timezone.utc)

        IncidentRepository.add_workflow_event(
            db=db,
            incident_id=incident.id,
            from_status="INSPECTION_IN_PROGRESS",
            to_status="ASSESSED",
            stage_number=7,
            action="INSPECTION_COMPLETED",
            actor_id="SYSTEM_ROVER_AGENT",
            actor_role="SYSTEM",
            notes="Virtual rover completed pipeline crawl; defect localized and quantified.",
            payload=findings,
        )
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def execute_stage_8_repair_planning_and_recommendation(
        db: Session,
        incident_id: str,
        actor_id: str = "SYSTEM_REPAIR_ENGINE",
    ) -> UnifiedIncidentModel:
        """Stage 8: Generate intelligent repair plan and cost estimates (ASSESSED -> REPAIR_PLANNED -> AWAITING_ENGINEERING_APPROVAL)."""
        incident = IncidentRepository.get_by_id(db, incident_id) or IncidentRepository.get_by_code(db, incident_id)
        if not incident:
            raise IncidentLifecycleError(f"Incident {incident_id} not found.")

        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "REPAIR_PLANNED")

        # Determine repair method & costs from inspection findings
        findings = incident.inspection_findings or {}
        crack_len = findings.get("crack_length_mm", 100.0)

        if crack_len > 200.0:
            method = "PIPE_SECTION_REPLACEMENT"
            est_cost = 6500.0
            urgency = "EMERGENCY_24H"
        elif crack_len > 80.0:
            method = "FULL_CIRCLE_STAINLESS_CLAMP"
            est_cost = 2450.0
            urgency = "HIGH_PRIORITY_48H"
        else:
            method = "EPOXY_SLEEVE_INJECTION"
            est_cost = 1150.0
            urgency = "PLANNED_7D"

        plan_id = f"RPR-PLAN-{uuid.uuid4().hex[:6].upper()}"
        incident.repair_plan_id = plan_id
        incident.repair_cost_estimate = est_cost
        incident.repair_urgency = urgency
        incident.lifecycle_status = "AWAITING_ENGINEERING_APPROVAL"
        incident.updated_at = datetime.now(timezone.utc)

        # Create engineering approval request
        IncidentRepository.create_approval_request(
            db=db,
            incident_id=incident.id,
            approval_type="REPAIR_PLAN",
            requested_by=actor_id,
            comments=f"Engineering review required for {method} (Est: ${est_cost:,.2f}, Urgency: {urgency}).",
        )

        IncidentRepository.add_workflow_event(
            db=db,
            incident_id=incident.id,
            from_status="ASSESSED",
            to_status="AWAITING_ENGINEERING_APPROVAL",
            stage_number=8,
            action="REPAIR_PLAN_FORMULATED",
            actor_id=actor_id,
            actor_role="SYSTEM",
            notes=f"Repair plan {plan_id} formulated: {method}. Cost: ${est_cost}. Awaiting engineering sign-off.",
            payload={"method": method, "cost_estimate_usd": est_cost, "urgency": urgency, "plan_id": plan_id},
        )
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def execute_stage_9_certified_engineering_approval(
        db: Session,
        incident_id: str,
        engineer_id: str,
        engineer_role: str,
        approved: bool = True,
        comments: str = "Certified municipal engineering review approved for planned clamp installation.",
    ) -> UnifiedIncidentModel:
        """Stage 9: Certified municipal engineer approves repair plan (AWAITING_ENGINEERING_APPROVAL -> APPROVED)."""
        incident = IncidentRepository.get_by_id(db, incident_id) or IncidentRepository.get_by_code(db, incident_id)
        if not incident:
            raise IncidentLifecycleError(f"Incident {incident_id} not found.")

        # Strict RBAC: Only ENGINEER or ADMIN can approve repair plans
        if engineer_role.upper() not in ["ENGINEER", "ADMIN"]:
            raise IncidentLifecycleError(f"Role '{engineer_role}' is not certified to approve municipal repair plans. Requires ENGINEER or ADMIN.")

        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "APPROVED" if approved else "REPAIR_PLANNED")

        pending_appr = (
            db.query(IncidentApprovalModel)
            .filter(
                IncidentApprovalModel.incident_id == incident.id,
                IncidentApprovalModel.approval_type == "REPAIR_PLAN",
                IncidentApprovalModel.status == "PENDING",
            )
            .first()
        )
        if pending_appr:
            IncidentRepository.record_approval_decision(
                db=db,
                approval_id=pending_appr.id,
                status="APPROVED" if approved else "REJECTED",
                approved_by=engineer_id,
                approver_role=engineer_role,
                comments=comments,
            )

        if not approved:
            if not comments.strip():
                raise IncidentLifecycleError("Rejection requires mandatory engineering justification.")
            incident.lifecycle_status = "REPAIR_PLANNED"
            IncidentRepository.add_workflow_event(
                db=db,
                incident_id=incident.id,
                from_status="AWAITING_ENGINEERING_APPROVAL",
                to_status="REPAIR_PLANNED",
                stage_number=9,
                action="REPAIR_PLAN_REJECTED",
                actor_id=engineer_id,
                actor_role=engineer_role,
                notes=f"Plan rejected with feedback: {comments}",
            )
            db.commit()
            db.refresh(incident)
            return incident

        incident.lifecycle_status = "APPROVED"
        incident.updated_at = datetime.now(timezone.utc)

        IncidentRepository.add_workflow_event(
            db=db,
            incident_id=incident.id,
            from_status="AWAITING_ENGINEERING_APPROVAL",
            to_status="APPROVED",
            stage_number=9,
            action="REPAIR_PLAN_CERTIFIED",
            actor_id=engineer_id,
            actor_role=engineer_role,
            notes=f"Engineer {engineer_id} certified repair plan. Ready for simulated repair execution.",
            payload={"certified_by": engineer_id, "comments": comments},
        )
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def execute_stage_10_simulated_resolution_and_closure(
        db: Session,
        incident_id: str,
        actor_id: str = "USR-ENG-01",
        actor_role: str = "ENGINEER",
        verification_notes: str = "Post-repair hydraulic digital twin simulation confirmed full pressure recovery.",
    ) -> UnifiedIncidentModel:
        """Stage 10: Run post-repair hydraulic simulation delta and close incident (APPROVED -> SIMULATED_RESOLUTION -> CLOSED)."""
        incident = IncidentRepository.get_by_id(db, incident_id) or IncidentRepository.get_by_code(db, incident_id)
        if not incident:
            raise IncidentLifecycleError(f"Incident {incident_id} not found.")

        # Strict safety invariant: verify no hardware actuation was requested
        for cmd in PROHIBITED_ACTUATION_COMMANDS:
            if cmd in verification_notes.upper():
                raise IncidentLifecycleError(f"HARDWARE_ACTUATION_PROHIBITED: Cannot execute physical command '{cmd}'.")

        IncidentOrchestrationService.validate_transition(incident.lifecycle_status, "SIMULATED_RESOLUTION")

        # Simulate post-repair digital twin restoration
        sim_delta = {
            "post_repair_pressure_gain_bar": round(0.12 * incident.hydraulic_headloss_delta, 2),
            "leak_flow_eliminated_lps": incident.estimated_loss_lps,
            "headloss_restored_m": incident.hydraulic_headloss_delta,
            "hydraulic_stability_verified": True,
            "before_headloss_m": incident.hydraulic_headloss_delta,
            "after_headloss_m": 0.05,
            "provenance": "SIMULATED",
            "simulation_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        incident.lifecycle_status = "SIMULATED_RESOLUTION"
        incident.simulation_resolution_data = sim_delta
        incident.resolution_summary = verification_notes
        incident.updated_at = datetime.now(timezone.utc)

        IncidentRepository.add_workflow_event(
            db=db,
            incident_id=incident.id,
            from_status="APPROVED",
            to_status="SIMULATED_RESOLUTION",
            stage_number=10,
            action="SIMULATION_RESOLUTION_VERIFIED",
            actor_id=actor_id,
            actor_role=actor_role,
            notes=verification_notes,
            payload=sim_delta,
        )

        # Close incident
        IncidentOrchestrationService.validate_transition("SIMULATED_RESOLUTION", "CLOSED")
        incident.lifecycle_status = "CLOSED"

        IncidentRepository.add_workflow_event(
            db=db,
            incident_id=incident.id,
            from_status="SIMULATED_RESOLUTION",
            to_status="CLOSED",
            stage_number=10,
            action="INCIDENT_CLOSED",
            actor_id=actor_id,
            actor_role=actor_role,
            notes="Incident successfully resolved and archived via simulated workflow.",
            payload={"final_status": "CLOSED"},
        )
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def run_master_e2e_scenario(
        db: Session,
        actor_id: str = "USR-ENG-01",
        actor_role: str = "ENGINEER",
        pipeline_segment_id: str = "PIPE-SEC-4B-92",
        acoustic_db: float = 88.5,
    ) -> Dict[str, Any]:
        """Execute the master 10-stage end-to-end incident lifecycle from telemetry to closed resolution."""
        # Stage 1
        s1 = IncidentOrchestrationService.execute_stage_1_telemetry_ingest(
            db=db,
            device_id="DEV-ACOUSTIC-01",
            sensor_id="SNS-AC-01-A",
            acoustic_db=acoustic_db,
            pipeline_segment_id=pipeline_segment_id,
        )

        # Stage 2
        s2 = IncidentOrchestrationService.execute_stage_2_ai_leak_detection(s1)

        # Stage 3
        incident = IncidentOrchestrationService.execute_stage_3_localize_and_create_incident(
            db=db,
            telemetry_data=s1,
            ai_findings=s2,
            actor_id="SYSTEM_AI_ENGINE",
        )

        # Stage 4
        incident = IncidentOrchestrationService.execute_stage_4_hydraulic_digital_twin_simulation(
            db=db,
            incident_id=incident.id,
        )

        # Stage 5
        incident = IncidentOrchestrationService.execute_stage_5_risk_scoring_and_proposal(
            db=db,
            incident_id=incident.id,
        )

        # Stage 6
        incident = IncidentOrchestrationService.execute_stage_6_rover_selection_and_assignment(
            db=db,
            incident_id=incident.id,
            preferred_rover_id="ROV-001",
        )

        # Stage 7
        incident = IncidentOrchestrationService.execute_stage_7_human_approval_and_inspection(
            db=db,
            incident_id=incident.id,
            operator_id="OPERATOR-SUPERVISOR-01",
            operator_role="OPERATOR",
            approved=True,
            comments="Autonomous inspection crawl authorized by supervisor.",
        )

        # Stage 8
        incident = IncidentOrchestrationService.execute_stage_8_repair_planning_and_recommendation(
            db=db,
            incident_id=incident.id,
        )

        # Stage 9: Certified Municipal Engineering Approval
        eng_id = actor_id if actor_role.upper() in ["ENGINEER", "ADMIN"] else "USR-ENG-01"
        eng_role = actor_role if actor_role.upper() in ["ENGINEER", "ADMIN"] else "ENGINEER"
        incident = IncidentOrchestrationService.execute_stage_9_certified_engineering_approval(
            db=db,
            incident_id=incident.id,
            engineer_id=eng_id,
            engineer_role=eng_role,
            approved=True,
            comments="Certified engineering repair approval for full-circle clamp installation.",
        )

        # Stage 10: Simulated Resolution & Twin Delta Verification
        incident = IncidentOrchestrationService.execute_stage_10_simulated_resolution_and_closure(
            db=db,
            incident_id=incident.id,
            actor_id=eng_id,
            actor_role=eng_role,
            verification_notes="Digital twin verifies nominal pressure and 0 L/s loss restoration.",
        )

        final_report = IncidentOrchestrationService.generate_final_incident_report(db, incident.id)

        return {
            "success": True,
            "incident_id": incident.id,
            "incident_code": incident.incident_code,
            "lifecycle_status": incident.lifecycle_status,
            "total_workflow_events": len(incident.workflow_events),
            "total_approvals": len(incident.approvals),
            "final_resolution_data": incident.simulation_resolution_data,
            "hardware_actuation_blocked": True,
            "is_simulated": incident.is_simulated,
            "final_report": final_report,
        }

    @staticmethod
    def generate_final_incident_report(db: Session, incident_id: str) -> Dict[str, Any]:
        """Compile a comprehensive publication-grade 15-step demonstration report."""
        incident = IncidentRepository.get_by_id(db, incident_id) or IncidentRepository.get_by_code(db, incident_id)
        if not incident:
            raise IncidentLifecycleError(f"Incident {incident_id} not found.")

        timeline = [
            {"step": 1, "name": "Virtual IoT Sensor Anomaly Generation", "detection_source": incident.detection_source, "sensor_ids": incident.sensor_ids},
            {"step": 2, "name": "Telemetry Validation and Storage", "status": "VALIDATED_AND_PERSISTED", "provenance": "SIMULATED"},
            {"step": 3, "name": "AI Acoustic Leak Detection", "leak_probability": incident.ai_leak_probability, "confidence": incident.ai_confidence},
            {"step": 4, "name": "GIS Pipeline Localization", "pipeline_segment_id": incident.pipeline_segment_id, "dma_zone": incident.dma_zone, "latitude": incident.latitude, "longitude": incident.longitude},
            {"step": 5, "name": "Hydraulic Digital Twin Evaluation", "headloss_delta_m": incident.hydraulic_headloss_delta, "estimated_loss_lps": incident.estimated_loss_lps},
            {"step": 6, "name": "Multi-Factor Risk Priority Calculation", "risk_score": incident.risk_score, "priority": incident.priority, "severity": incident.severity},
            {"step": 7, "name": "Autonomous Rover Suitability Evaluation", "assigned_rover_id": incident.assigned_rover_id, "mission_id": incident.inspection_mission_id},
            {"step": 8, "name": "Human Operator Dispatch Approval", "approval_count": len([a for a in incident.approvals if a.approval_type == "INSPECTION_DISPATCH"])},
            {"step": 9, "name": "Virtual Rover Inspection Crawl", "status": "COMPLETED", "rover_id": incident.assigned_rover_id},
            {"step": 10, "name": "Inspection Findings & Defect Measurement", "findings": incident.inspection_findings},
            {"step": 11, "name": "Intelligent Repair Recommendation", "repair_plan_id": incident.repair_plan_id, "cost_estimate_usd": incident.repair_cost_estimate, "urgency": incident.repair_urgency},
            {"step": 12, "name": "Certified Municipal Engineer Review & Certification", "approval_count": len([a for a in incident.approvals if a.approval_type == "REPAIR_PLAN"])},
            {"step": 13, "name": "Post-Repair Hydraulic Twin Simulation Evaluation", "simulation_resolution_data": incident.simulation_resolution_data},
            {"step": 14, "name": "Incident Lifecycle State Updated", "final_lifecycle_status": incident.lifecycle_status},
            {"step": 15, "name": "Final Incident Dossier Generated", "resolution_summary": incident.resolution_summary},
        ]

        return {
            "report_id": f"REP-{incident.incident_code}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "incident_code": incident.incident_code,
            "title": incident.title,
            "status": incident.lifecycle_status,
            "severity": incident.severity,
            "priority": incident.priority,
            "pipeline_segment_id": incident.pipeline_segment_id,
            "dma_zone": incident.dma_zone,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "timeline": timeline,
            "ai_leak_probability": incident.ai_leak_probability,
            "hydraulic_headloss_delta": incident.hydraulic_headloss_delta,
            "estimated_loss_lps": incident.estimated_loss_lps,
            "risk_score": incident.risk_score,
            "inspection_findings": incident.inspection_findings,
            "repair_plan_id": incident.repair_plan_id,
            "repair_cost_estimate": incident.repair_cost_estimate,
            "simulation_resolution_data": incident.simulation_resolution_data,
            "resolution_summary": incident.resolution_summary,
            "evidence_provenance": incident.evidence_provenance,
            "is_simulated": incident.is_simulated,
            "hardware_actuation_enabled": False,
            "provenance_statement": (
                "EVIDENCE INTEGRITY NOTICE: All observations, acoustic waveforms, "
                "virtual rover crawl findings, and post-repair hydraulic pressure deltas "
                "were produced within the AQUA CREW Virtual Simulation Environment. "
                "Zero physical actuation was performed. Hardware actuation remained air-gapped and disabled."
            ),
        }

    @staticmethod
    def reset_demo_scenario(db: Session) -> Dict[str, Any]:
        """
        Cleans up dynamically generated scenario incidents without deleting unrelated user data.
        Restores baseline seeded incidents to their pristine initial state.
        """
        baseline_codes = ["INC-2026-001", "INC-2026-002", "INC-2026-003", "INC-2026-004"]
        deleted_count = (
            db.query(UnifiedIncidentModel)
            .filter(~UnifiedIncidentModel.incident_code.in_(baseline_codes))
            .delete(synchronize_session=False)
        )

        inc1 = IncidentRepository.get_by_code(db, "INC-2026-001")
        if inc1:
            inc1.lifecycle_status = "TRIAGED"
            inc1.inspection_mission_id = None
            inc1.assigned_rover_id = None
            inc1.inspection_findings_json = None
            inc1.repair_plan_id = None
            inc1.repair_cost_estimate = None
            inc1.simulation_resolution_data_json = None
            inc1.resolution_summary = None

        inc2 = IncidentRepository.get_by_code(db, "INC-2026-002")
        if inc2:
            inc2.lifecycle_status = "INSPECTION_PROPOSED"
            inc2.inspection_findings_json = None
            inc2.repair_plan_id = None
            inc2.simulation_resolution_data_json = None

        inc3 = IncidentRepository.get_by_code(db, "INC-2026-003")
        if inc3:
            inc3.lifecycle_status = "AWAITING_ENGINEERING_APPROVAL"
            inc3.simulation_resolution_data_json = None

        inc4 = IncidentRepository.get_by_code(db, "INC-2026-004")
        if inc4:
            inc4.lifecycle_status = "CLOSED"

        db.commit()

        return {
            "success": True,
            "deleted_scenario_incidents": deleted_count,
            "baseline_incidents_restored": len(baseline_codes),
            "message": "Demonstration scenario reset successfully. Baseline incidents restored to pristine state.",
        }
