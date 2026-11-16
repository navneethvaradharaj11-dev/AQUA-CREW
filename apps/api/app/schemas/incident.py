"""
AQUA CREW — Pydantic Validation Schemas for Unified Incidents (Task 19)
Provides strict request/response data contracts for the 10-stage Master Incident Lifecycle.
"""
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone


IncidentLifecycleStatus = Literal[
    "DETECTED",
    "TRIAGED",
    "INVESTIGATING",
    "INSPECTION_PROPOSED",
    "APPROVED",
    "INSPECTION_IN_PROGRESS",
    "ASSESSED",
    "REPAIR_PLANNED",
    "AWAITING_ENGINEERING_APPROVAL",
    "SIMULATED_RESOLUTION",
    "CLOSED",
]

IncidentSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
IncidentPriority = Literal["P1", "P2", "P3", "P4"]
EvidenceProvenance = Literal["MEASURED", "SIMULATED", "DERIVED", "PREDICTED", "OPERATOR_ENTERED", "UNKNOWN"]
ApprovalType = Literal["INSPECTION_DISPATCH", "REPAIR_PLAN", "SIMULATED_RESOLUTION", "CLOSURE"]
ApprovalStatus = Literal["PENDING", "APPROVED", "REJECTED"]


class IncidentWorkflowEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    from_status: str
    to_status: str
    stage_number: int
    actor_id: str
    actor_role: str
    action: str
    notes: Optional[str] = ""
    payload: Optional[Dict[str, Any]] = None
    timestamp: datetime


class IncidentApprovalSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    approval_type: ApprovalType
    status: ApprovalStatus
    requested_by: str
    approved_by: Optional[str] = None
    approver_role: Optional[str] = None
    decision_timestamp: Optional[datetime] = None
    comments: Optional[str] = ""
    digital_signature: Optional[str] = None
    created_at: datetime


class UnifiedIncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_code: str
    title: str
    description: Optional[str] = ""
    category: str
    severity: IncidentSeverity
    priority: IncidentPriority
    lifecycle_status: IncidentLifecycleStatus

    pipeline_segment_id: str
    dma_zone: Optional[str] = None
    latitude: float
    longitude: float

    detection_timestamp: Optional[datetime] = None
    detection_source: str
    sensor_ids: List[str] = Field(default_factory=list)

    ai_leak_probability: float
    ai_confidence: float
    evidence_provenance: EvidenceProvenance

    hydraulic_headloss_delta: float
    estimated_loss_lps: float
    risk_score: float

    inspection_mission_id: Optional[str] = None
    assigned_rover_id: Optional[str] = None
    inspection_findings: Optional[Dict[str, Any]] = None

    repair_plan_id: Optional[str] = None
    repair_cost_estimate: Optional[float] = None
    repair_urgency: Optional[str] = None

    simulation_resolution_data: Optional[Dict[str, Any]] = None
    resolution_summary: Optional[str] = None

    is_simulated: bool = True
    created_by: str
    created_at: datetime
    updated_at: datetime

    workflow_events: List[IncidentWorkflowEventSchema] = Field(default_factory=list)
    approvals: List[IncidentApprovalSchema] = Field(default_factory=list)


class IncidentListResponse(BaseModel):
    items: List[UnifiedIncidentResponse]
    total: int
    limit: int
    offset: int


class IncidentCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=128)
    pipeline_segment_id: str = Field(..., min_length=1)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    description: Optional[str] = ""
    category: str = "ACOUSTIC_ANOMALY"
    severity: IncidentSeverity = "HIGH"
    priority: IncidentPriority = "P1"
    dma_zone: str = "DMA-CENTRAL-01"
    detection_source: str = "TELEMETRY_ACOUSTIC"
    sensor_ids: List[str] = Field(default_factory=list)
    ai_leak_probability: float = Field(default=0.0, ge=0.0, le=1.0)
    ai_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    hydraulic_headloss_delta: float = Field(default=0.0, ge=0.0)
    estimated_loss_lps: float = Field(default=0.0, ge=0.0)
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)


class IncidentTransitionRequest(BaseModel):
    target_status: IncidentLifecycleStatus
    notes: Optional[str] = ""
    payload: Optional[Dict[str, Any]] = None


class IncidentApprovalDecisionRequest(BaseModel):
    approval_type: ApprovalType
    approved: bool
    comments: Optional[str] = ""


class IncidentResolutionRequest(BaseModel):
    verification_notes: str = Field(..., min_length=5)


class MasterE2ERequest(BaseModel):
    pipeline_segment_id: Optional[str] = "PIPE-SEC-4B-92"
    acoustic_db: Optional[float] = Field(default=88.5, ge=0.0, le=140.0)


class IncidentStatsOverview(BaseModel):
    total_incidents: int
    active_incidents: int
    closed_incidents: int
    critical_incidents: int
    awaiting_approval_incidents: int
    total_estimated_water_loss_lps: float
    by_status: Dict[str, int]
    by_severity: Dict[str, int]
    by_category: Dict[str, int]

