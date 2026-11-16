"""
AQUA CREW — Unified Incident Management Repository (Task 19)
Handles CRUD operations, lifecycle state transitions, workflow audit logs,
and engineering approval workflows for water infrastructure incidents.
"""
import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc, func

from app.models.incident import (
    UnifiedIncidentModel,
    IncidentWorkflowEventModel,
    IncidentApprovalModel,
)


DEFAULT_INCIDENTS = [
    {
        "id": "INC-2026-0001",
        "incident_code": "INC-2026-001",
        "title": "Acoustic Anomaly & High Pressure Drop — Metro Trunk B",
        "description": "High acoustic energy detected (88.4 dB) correlated with downstream pressure loss on 400mm ductile iron trunk.",
        "category": "ACOUSTIC_ANOMALY",
        "severity": "HIGH",
        "priority": "P1",
        "lifecycle_status": "TRIAGED",
        "pipeline_segment_id": "PIPE-SEC-4B-92",
        "dma_zone": "DMA-METRO-CENTRAL",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "detection_source": "TELEMETRY_ACOUSTIC",
        "sensor_ids": ["SNS-AC-01-A", "SNS-PR-02-A"],
        "ai_leak_probability": 0.89,
        "ai_confidence": 0.92,
        "evidence_provenance": "SIMULATED",
        "hydraulic_headloss_delta": 4.25,
        "estimated_loss_lps": 12.8,
        "risk_score": 78.5,
        "is_simulated": True,
        "created_by": "SYSTEM_AI_ENGINE",
    },
    {
        "id": "INC-2026-0002",
        "incident_code": "INC-2026-002",
        "title": "Suspected Lateral Crack — Industrial Feeder Line",
        "description": "Acoustic signature matching shear cracking detected during scheduled IoT hydrophone sweep.",
        "category": "SUSPECTED_LEAK",
        "severity": "MEDIUM",
        "priority": "P2",
        "lifecycle_status": "INSPECTION_PROPOSED",
        "pipeline_segment_id": "PIPE-002",
        "dma_zone": "DMA-HARBOR-EAST",
        "latitude": 40.7160,
        "longitude": -73.9980,
        "detection_source": "TELEMETRY_ACOUSTIC",
        "sensor_ids": ["SNS-AC-02-B"],
        "ai_leak_probability": 0.74,
        "ai_confidence": 0.85,
        "evidence_provenance": "SIMULATED",
        "hydraulic_headloss_delta": 2.10,
        "estimated_loss_lps": 6.4,
        "risk_score": 62.0,
        "inspection_mission_id": "MSN-INSP-2026-02",
        "assigned_rover_id": "ROV-001",
        "is_simulated": True,
        "created_by": "SYSTEM_AI_ENGINE",
    },
    {
        "id": "INC-2026-0003",
        "incident_code": "INC-2026-003",
        "title": "Critical Circumferential Joint Rupture — Uptown Feed",
        "description": "Major pressure drop and acoustic burst confirmed via rover video inspection.",
        "category": "BURST",
        "severity": "CRITICAL",
        "priority": "P1",
        "lifecycle_status": "AWAITING_ENGINEERING_APPROVAL",
        "pipeline_segment_id": "PIPE-003",
        "dma_zone": "DMA-UPTOWN-NORTH",
        "latitude": 40.7250,
        "longitude": -74.0120,
        "detection_source": "PRESSURE_TRANSIENT",
        "sensor_ids": ["SNS-PR-03-A", "SNS-FL-03-C"],
        "ai_leak_probability": 0.96,
        "ai_confidence": 0.95,
        "evidence_provenance": "SIMULATED",
        "hydraulic_headloss_delta": 8.70,
        "estimated_loss_lps": 34.2,
        "risk_score": 94.0,
        "inspection_mission_id": "MSN-INSP-2026-03",
        "assigned_rover_id": "ROV-002",
        "inspection_findings": {
            "visual_defect_type": "CIRCUMFERENTIAL_CRACK",
            "crack_width_mm": 4.8,
            "crack_length_mm": 180.0,
            "corrosion_observed": True,
            "inspection_score": 0.95,
        },
        "repair_plan_id": "RPR-PLAN-2026-003",
        "repair_cost_estimate": 4850.0,
        "repair_urgency": "EMERGENCY_24H",
        "is_simulated": True,
        "created_by": "SYSTEM_AI_ENGINE",
    },
    {
        "id": "INC-2026-0004",
        "incident_code": "INC-2026-004",
        "title": "Pin-Hole Orifice Leak — Metro Commercial Link",
        "description": "Small leak successfully repaired via virtual sleeve clamp; digital twin verified restoration.",
        "category": "ACOUSTIC_ANOMALY",
        "severity": "LOW",
        "priority": "P3",
        "lifecycle_status": "CLOSED",
        "pipeline_segment_id": "PIPE-001",
        "dma_zone": "DMA-METRO-CENTRAL",
        "latitude": 40.7100,
        "longitude": -74.0040,
        "detection_source": "TELEMETRY_ACOUSTIC",
        "sensor_ids": ["SNS-AC-01-B"],
        "ai_leak_probability": 0.65,
        "ai_confidence": 0.88,
        "evidence_provenance": "SIMULATED",
        "hydraulic_headloss_delta": 0.90,
        "estimated_loss_lps": 2.1,
        "risk_score": 38.0,
        "inspection_mission_id": "MSN-INSP-2026-04",
        "assigned_rover_id": "ROV-003",
        "repair_plan_id": "RPR-PLAN-2026-004",
        "repair_cost_estimate": 1200.0,
        "repair_urgency": "SCHEDULED",
        "simulation_resolution_data": {
            "post_repair_pressure_gain_bar": 0.38,
            "leak_flow_eliminated_lps": 2.1,
            "hydraulic_stability_verified": True,
        },
        "resolution_summary": "Full sleeve clamp installed in simulation. Head loss returned to nominal base curve.",
        "is_simulated": True,
        "created_by": "OPERATOR-SUPERVISOR-01",
    },
]


class IncidentRepository:

    @staticmethod
    def seed_defaults(db: Session) -> None:
        """Seed default baseline incidents if the table is empty."""
        count = db.query(UnifiedIncidentModel).count()
        if count > 0:
            return

        now = datetime.now(timezone.utc)
        for item in DEFAULT_INCIDENTS:
            findings = item.get("inspection_findings")
            sim_data = item.get("simulation_resolution_data")
            incident = UnifiedIncidentModel(
                id=item["id"],
                incident_code=item["incident_code"],
                title=item["title"],
                description=item["description"],
                category=item["category"],
                severity=item["severity"],
                priority=item["priority"],
                lifecycle_status=item["lifecycle_status"],
                pipeline_segment_id=item["pipeline_segment_id"],
                dma_zone=item["dma_zone"],
                latitude=item["latitude"],
                longitude=item["longitude"],
                detection_timestamp=now,
                detection_source=item["detection_source"],
                sensor_ids_json=json.dumps(item.get("sensor_ids", [])),
                ai_leak_probability=item["ai_leak_probability"],
                ai_confidence=item["ai_confidence"],
                evidence_provenance=item["evidence_provenance"],
                hydraulic_headloss_delta=item["hydraulic_headloss_delta"],
                estimated_loss_lps=item["estimated_loss_lps"],
                risk_score=item["risk_score"],
                inspection_mission_id=item.get("inspection_mission_id"),
                assigned_rover_id=item.get("assigned_rover_id"),
                inspection_findings_json=json.dumps(findings) if findings else None,
                repair_plan_id=item.get("repair_plan_id"),
                repair_cost_estimate=item.get("repair_cost_estimate"),
                repair_urgency=item.get("repair_urgency"),
                simulation_resolution_data_json=json.dumps(sim_data) if sim_data else None,
                resolution_summary=item.get("resolution_summary"),
                is_simulated=item.get("is_simulated", True),
                created_by=item.get("created_by", "SYSTEM_AI_ENGINE"),
                created_at=now,
                updated_at=now,
            )
            db.add(incident)
            db.flush()

            # Add initial event
            evt = IncidentWorkflowEventModel(
                id=f"IWE-{uuid.uuid4().hex[:8].upper()}",
                incident_id=incident.id,
                from_status="NONE",
                to_status=incident.lifecycle_status,
                stage_number=1,
                actor_id=incident.created_by,
                actor_role="SYSTEM" if "SYSTEM" in incident.created_by else "OPERATOR",
                action="INCIDENT_INITIALIZED",
                notes=f"Seeded incident initialized at status {incident.lifecycle_status}",
                payload_json=json.dumps({"pipeline_segment_id": incident.pipeline_segment_id}),
                timestamp=now,
            )
            db.add(evt)

            # If awaiting approval, add pending approval record
            if incident.lifecycle_status == "AWAITING_ENGINEERING_APPROVAL":
                appr = IncidentApprovalModel(
                    id=f"APV-{uuid.uuid4().hex[:8].upper()}",
                    incident_id=incident.id,
                    approval_type="REPAIR_PLAN",
                    status="PENDING",
                    requested_by="SYSTEM_REPAIR_ENGINE",
                    comments="Emergency repair plan proposed for critical circumferential pipe crack.",
                    created_at=now,
                )
                db.add(appr)

        db.commit()

    @staticmethod
    def get_by_id(db: Session, incident_id: str) -> Optional[UnifiedIncidentModel]:
        return db.query(UnifiedIncidentModel).filter(UnifiedIncidentModel.id == incident_id).first()

    @staticmethod
    def get_by_code(db: Session, incident_code: str) -> Optional[UnifiedIncidentModel]:
        return db.query(UnifiedIncidentModel).filter(UnifiedIncidentModel.incident_code == incident_code).first()

    @staticmethod
    def list_incidents(
        db: Session,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        dma_zone: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[UnifiedIncidentModel], int]:
        query = db.query(UnifiedIncidentModel)
        if status:
            query = query.filter(UnifiedIncidentModel.lifecycle_status == status)
        if severity:
            query = query.filter(UnifiedIncidentModel.severity == severity)
        if category:
            query = query.filter(UnifiedIncidentModel.category == category)
        if dma_zone:
            query = query.filter(UnifiedIncidentModel.dma_zone == dma_zone)

        total = query.count()
        records = query.order_by(desc(UnifiedIncidentModel.created_at)).offset(offset).limit(limit).all()
        return records, total

    @staticmethod
    def create_incident(
        db: Session,
        title: str,
        pipeline_segment_id: str,
        latitude: float,
        longitude: float,
        description: str = "",
        category: str = "ACOUSTIC_ANOMALY",
        severity: str = "HIGH",
        priority: str = "P1",
        dma_zone: str = "DMA-CENTRAL-01",
        detection_source: str = "TELEMETRY_ACOUSTIC",
        sensor_ids: Optional[List[str]] = None,
        ai_leak_probability: float = 0.0,
        ai_confidence: float = 0.0,
        hydraulic_headloss_delta: float = 0.0,
        estimated_loss_lps: float = 0.0,
        risk_score: float = 0.0,
        created_by: str = "SYSTEM_AI_ENGINE",
        incident_id: Optional[str] = None,
    ) -> UnifiedIncidentModel:
        now = datetime.now(timezone.utc)
        uid = incident_id or f"INC-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        code = f"INC-{now.year}-{uuid.uuid4().hex[:4].upper()}"

        incident = UnifiedIncidentModel(
            id=uid,
            incident_code=code,
            title=title,
            description=description,
            category=category,
            severity=severity,
            priority=priority,
            lifecycle_status="DETECTED",
            pipeline_segment_id=pipeline_segment_id,
            dma_zone=dma_zone,
            latitude=latitude,
            longitude=longitude,
            detection_timestamp=now,
            detection_source=detection_source,
            sensor_ids_json=json.dumps(sensor_ids or []),
            ai_leak_probability=ai_leak_probability,
            ai_confidence=ai_confidence,
            evidence_provenance="SIMULATED",
            hydraulic_headloss_delta=hydraulic_headloss_delta,
            estimated_loss_lps=estimated_loss_lps,
            risk_score=risk_score,
            is_simulated=True,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        db.add(incident)
        db.flush()

        evt = IncidentWorkflowEventModel(
            id=f"IWE-{uuid.uuid4().hex[:8].upper()}",
            incident_id=incident.id,
            from_status="NONE",
            to_status="DETECTED",
            stage_number=1,
            actor_id=created_by,
            actor_role="SYSTEM",
            action="INCIDENT_DETECTED",
            notes=f"Incident registered via {detection_source} on {pipeline_segment_id}",
            payload_json=json.dumps({"ai_leak_probability": ai_leak_probability, "risk_score": risk_score}),
            timestamp=now,
        )
        db.add(evt)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def add_workflow_event(
        db: Session,
        incident_id: str,
        from_status: str,
        to_status: str,
        stage_number: int,
        action: str,
        actor_id: str = "SYSTEM",
        actor_role: str = "SYSTEM",
        notes: str = "",
        payload: Optional[Dict[str, Any]] = None,
    ) -> IncidentWorkflowEventModel:
        now = datetime.now(timezone.utc)
        evt = IncidentWorkflowEventModel(
            id=f"IWE-{uuid.uuid4().hex[:8].upper()}",
            incident_id=incident_id,
            from_status=from_status,
            to_status=to_status,
            stage_number=stage_number,
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            notes=notes,
            payload_json=json.dumps(payload) if payload else None,
            timestamp=now,
        )
        db.add(evt)
        db.flush()
        return evt

    @staticmethod
    def create_approval_request(
        db: Session,
        incident_id: str,
        approval_type: str,
        requested_by: str = "SYSTEM",
        comments: str = "",
    ) -> IncidentApprovalModel:
        now = datetime.now(timezone.utc)
        approval = IncidentApprovalModel(
            id=f"APV-{uuid.uuid4().hex[:8].upper()}",
            incident_id=incident_id,
            approval_type=approval_type,
            status="PENDING",
            requested_by=requested_by,
            comments=comments,
            created_at=now,
        )
        db.add(approval)
        db.flush()
        return approval

    @staticmethod
    def record_approval_decision(
        db: Session,
        approval_id: str,
        status: str,
        approved_by: str,
        approver_role: str,
        comments: str = "",
    ) -> Optional[IncidentApprovalModel]:
        approval = db.query(IncidentApprovalModel).filter(IncidentApprovalModel.id == approval_id).first()
        if not approval:
            return None

        now = datetime.now(timezone.utc)
        approval.status = status
        approval.approved_by = approved_by
        approval.approver_role = approver_role
        approval.decision_timestamp = now
        approval.comments = comments
        # Generate digital signature
        sig_raw = f"{approval.id}:{approval.incident_id}:{status}:{approved_by}:{approver_role}:{now.isoformat()}"
        approval.digital_signature = hashlib.sha256(sig_raw.encode("utf-8")).hexdigest()[:32].upper()
        db.flush()
        return approval

    @staticmethod
    def get_incident_stats(db: Session) -> Dict[str, Any]:
        """Compute live overview KPIs for unified command center."""
        total = db.query(UnifiedIncidentModel).count()
        by_status = dict(
            db.query(UnifiedIncidentModel.lifecycle_status, func.count(UnifiedIncidentModel.id))
            .group_by(UnifiedIncidentModel.lifecycle_status)
            .all()
        )
        by_severity = dict(
            db.query(UnifiedIncidentModel.severity, func.count(UnifiedIncidentModel.id))
            .group_by(UnifiedIncidentModel.severity)
            .all()
        )
        by_category = dict(
            db.query(UnifiedIncidentModel.category, func.count(UnifiedIncidentModel.id))
            .group_by(UnifiedIncidentModel.category)
            .all()
        )

        active_statuses = [
            "DETECTED", "TRIAGED", "INVESTIGATING", "INSPECTION_PROPOSED",
            "APPROVED", "INSPECTION_IN_PROGRESS", "ASSESSED", "REPAIR_PLANNED",
            "AWAITING_ENGINEERING_APPROVAL", "SIMULATED_RESOLUTION"
        ]
        active_count = sum(by_status.get(s, 0) for s in active_statuses)
        closed_count = by_status.get("CLOSED", 0)
        critical_count = by_severity.get("CRITICAL", 0)
        awaiting_approval_count = by_status.get("AWAITING_ENGINEERING_APPROVAL", 0) + by_status.get("INSPECTION_PROPOSED", 0)

        # Total estimated water loss in active incidents
        total_loss_lps = db.query(func.sum(UnifiedIncidentModel.estimated_loss_lps))\
            .filter(UnifiedIncidentModel.lifecycle_status.in_(active_statuses))\
            .scalar() or 0.0

        return {
            "total_incidents": total,
            "active_incidents": active_count,
            "closed_incidents": closed_count,
            "critical_incidents": critical_count,
            "awaiting_approval_incidents": awaiting_approval_count,
            "total_estimated_water_loss_lps": round(float(total_loss_lps), 2),
            "by_status": by_status,
            "by_severity": by_severity,
            "by_category": by_category,
        }

