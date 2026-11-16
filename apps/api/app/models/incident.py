"""
SQLAlchemy Persistent Models for Unified Incident Management (Task 19)
Implements the 10-stage Master Incident Lifecycle domain entities:
- UnifiedIncidentModel: Master record tying sensor telemetry, AI acoustic detection,
  hydraulic digital twin, spatial risk, virtual rover inspection, repair planning,
  and human-approved simulated resolution.
- IncidentWorkflowEventModel: Comprehensive audit log of every lifecycle transition.
- IncidentApprovalModel: Rigorous Human-in-the-Loop engineering and operator approval records.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import json
from typing import List, Dict, Any, Optional

from app.database.session import Base


class UnifiedIncidentModel(Base):
    __tablename__ = "unified_incidents"

    id = Column(String(64), primary_key=True, index=True)
    incident_code = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(128), nullable=False)
    description = Column(Text, default="")
    category = Column(String(64), default="ACOUSTIC_ANOMALY", index=True)
    severity = Column(String(32), default="HIGH", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    priority = Column(String(32), default="P1", index=True)    # P1, P2, P3, P4
    lifecycle_status = Column(String(64), default="DETECTED", index=True)
    # Lifecycle States:
    # 1. DETECTED
    # 2. TRIAGED
    # 3. INVESTIGATING
    # 4. INSPECTION_PROPOSED
    # 5. APPROVED
    # 6. INSPECTION_IN_PROGRESS
    # 7. ASSESSED
    # 8. REPAIR_PLANNED
    # 9. AWAITING_ENGINEERING_APPROVAL
    # 10. SIMULATED_RESOLUTION
    # 11. CLOSED

    pipeline_segment_id = Column(String(64), nullable=False, index=True)
    dma_zone = Column(String(64), default="DMA-CENTRAL-01", index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    detection_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    detection_source = Column(String(64), default="TELEMETRY_ACOUSTIC")  # TELEMETRY_ACOUSTIC, PRESSURE_TRANSIENT, etc.
    sensor_ids_json = Column(Text, default="[]")

    ai_leak_probability = Column(Float, default=0.0)
    ai_confidence = Column(Float, default=0.0)
    evidence_provenance = Column(String(32), default="SIMULATED", nullable=False)

    hydraulic_headloss_delta = Column(Float, default=0.0)
    estimated_loss_lps = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)

    inspection_mission_id = Column(String(64), nullable=True, index=True)
    assigned_rover_id = Column(String(64), nullable=True, index=True)
    inspection_findings_json = Column(Text, nullable=True)

    repair_plan_id = Column(String(64), nullable=True, index=True)
    repair_cost_estimate = Column(Float, nullable=True)
    repair_urgency = Column(String(32), nullable=True)

    simulation_resolution_data_json = Column(Text, nullable=True)
    resolution_summary = Column(Text, nullable=True)

    is_simulated = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(128), default="SYSTEM_AI_ENGINE")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    workflow_events = relationship(
        "IncidentWorkflowEventModel",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentWorkflowEventModel.timestamp",
    )
    approvals = relationship(
        "IncidentApprovalModel",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentApprovalModel.created_at",
    )

    @property
    def sensor_ids(self) -> List[str]:
        if not self.sensor_ids_json:
            return []
        try:
            return json.loads(self.sensor_ids_json)
        except Exception:
            return []

    @sensor_ids.setter
    def sensor_ids(self, val: List[str]):
        self.sensor_ids_json = json.dumps(val or [])

    @property
    def inspection_findings(self) -> Optional[Dict[str, Any]]:
        if not self.inspection_findings_json:
            return None
        try:
            return json.loads(self.inspection_findings_json)
        except Exception:
            return None

    @inspection_findings.setter
    def inspection_findings(self, val: Optional[Dict[str, Any]]):
        self.inspection_findings_json = json.dumps(val) if val is not None else None

    @property
    def simulation_resolution_data(self) -> Optional[Dict[str, Any]]:
        if not self.simulation_resolution_data_json:
            return None
        try:
            return json.loads(self.simulation_resolution_data_json)
        except Exception:
            return None

    @simulation_resolution_data.setter
    def simulation_resolution_data(self, val: Optional[Dict[str, Any]]):
        self.simulation_resolution_data_json = json.dumps(val) if val is not None else None


class IncidentWorkflowEventModel(Base):
    __tablename__ = "incident_workflow_events"

    id = Column(String(64), primary_key=True, index=True)
    incident_id = Column(String(64), ForeignKey("unified_incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(64), nullable=False)
    to_status = Column(String(64), nullable=False)
    stage_number = Column(Integer, default=1)
    actor_id = Column(String(128), default="SYSTEM")
    actor_role = Column(String(64), default="SYSTEM")
    action = Column(String(128), nullable=False)
    notes = Column(Text, default="")
    payload_json = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    incident = relationship("UnifiedIncidentModel", back_populates="workflow_events")

    @property
    def payload(self) -> Optional[Dict[str, Any]]:
        if not self.payload_json:
            return None
        try:
            return json.loads(self.payload_json)
        except Exception:
            return None

    @payload.setter
    def payload(self, val: Optional[Dict[str, Any]]):
        self.payload_json = json.dumps(val) if val is not None else None


class IncidentApprovalModel(Base):
    __tablename__ = "incident_approvals"

    id = Column(String(64), primary_key=True, index=True)
    incident_id = Column(String(64), ForeignKey("unified_incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    approval_type = Column(String(64), nullable=False, index=True)  # INSPECTION_DISPATCH, REPAIR_PLAN, SIMULATED_RESOLUTION, CLOSURE
    status = Column(String(32), default="PENDING", index=True)       # PENDING, APPROVED, REJECTED
    requested_by = Column(String(128), default="SYSTEM")
    approved_by = Column(String(128), nullable=True)
    approver_role = Column(String(64), nullable=True)                # OPERATOR, ENGINEER, ADMIN
    decision_timestamp = Column(DateTime(timezone=True), nullable=True)
    comments = Column(Text, default="")
    digital_signature = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    incident = relationship("UnifiedIncidentModel", back_populates="approvals")

