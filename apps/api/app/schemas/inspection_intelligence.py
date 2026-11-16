"""
AQUA CREW — Autonomous Inspection Intelligence Pydantic Schemas (Task 15)
Defines data contracts for unified inspection urgency scoring, adaptive multi-rover allocation,
intelligent pipeline route planning, simulated execution, and evidence-grounded reports.
"""
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# Strict 6-Tier Evidence Classification (inherited from Task 13)
EvidenceClassification = Literal[
    "MEASURED",
    "SIMULATED",
    "DERIVED",
    "PREDICTED",
    "OPERATOR_ENTERED",
    "UNKNOWN",
]

PriorityCategory = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]

InspectionMethod = Literal[
    "ACOUSTIC_CORRELATION",
    "VISUAL_CCTV",
    "THERMAL_INFRARED",
    "MULTI_SENSOR_CRAWLER",
    "ULTRASONIC_THICKNESS",
]

HumanApprovalStatus = Literal[
    "PENDING_APPROVAL",
    "APPROVING",
    "APPROVED",
    "REJECTED",
    "EXPIRED",
]

ExecutionStatus = Literal[
    "SCHEDULED",
    "IN_PROGRESS",
    "ADAPTED",
    "COMPLETED",
    "ABORTED_LOW_BATTERY",
    "ABORTED_SENSOR_FAULT",
    "ABORTED_COMMS_LOSS",
    "EMERGENCY_STOP",
]


class SupportingEvidenceItem(BaseModel):
    evidence_id: str
    source_subsystem: str = Field(..., description="E.g. TASK_07_AI_LEAKS, TASK_09_PRED_MAINT, TASK_10_HYDRAULICS, TASK_11_INFRA_INTEL")
    classification: EvidenceClassification
    metric_name: str
    metric_value: Any
    description: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    observed_at: Optional[str] = None


class InspectionRecommendationSchema(BaseModel):
    id: str = Field(..., description="Unique recommendation ID (INSP-REC-xxx)")
    pipeline_segment_id: str
    segment_name: str
    priority_score: float = Field(..., ge=0.0, le=100.0, description="Urgency priority score (0-100)")
    priority_category: PriorityCategory
    urgency_factors: Dict[str, float] = Field(default_factory=dict, description="Factor breakdown scores")
    supporting_evidence: List[SupportingEvidenceItem] = Field(default_factory=list)
    primary_classification: EvidenceClassification = Field("DERIVED", description="Classification of the composite score")
    confidence: float = Field(..., ge=0.0, le=1.0)
    uncertainty_radius_m: float = Field(20.0, ge=1.0)
    recommended_method: InspectionMethod
    estimated_duration_minutes: int = Field(30, ge=5)
    required_rover_capabilities: List[str] = Field(default_factory=list)
    recommended_action: str
    human_approval_status: HumanApprovalStatus = Field("PENDING_APPROVAL")
    rejection_reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: str
    is_simulated: bool = Field(True, description="Strict simulation provenance flag")


class RoverSuitabilitySchema(BaseModel):
    rover_id: str
    rover_name: str
    is_eligible: bool
    suitability_score: float = Field(..., ge=0.0, le=100.0)
    battery_percentage: float
    projected_battery_drain_pct: float
    projected_battery_reserve_pct: float
    has_safe_return_reserve: bool = Field(True, description="True if projected reserve >= 20%")
    motor_temperature_c: float
    sensor_capabilities: List[str]
    capability_match: bool
    operating_state: str
    connection_status: str
    distance_to_target_m: float
    estimated_travel_time_s: float
    disqualification_reasons: List[str] = Field(default_factory=list)


class InspectionPlanTargetSchema(BaseModel):
    target_id: str
    pipeline_segment_id: str
    target_coordinates: List[float] = Field(..., description="[lng, lat]")
    inspection_method: InspectionMethod
    priority_score: float
    estimated_duration_minutes: int


class MultiRoverAllocationItemSchema(BaseModel):
    rover_id: str
    rover_name: str
    assigned_targets: List[InspectionPlanTargetSchema]
    route_waypoints: List[List[float]] = Field(default_factory=list, description="Ordered [[lng, lat], ...]")
    segments_traversed: List[str] = Field(default_factory=list)
    total_route_distance_m: float
    estimated_mission_duration_s: float
    estimated_battery_drain_pct: float
    projected_reserve_after_return_pct: float
    return_to_base_feasible: bool
    route_selection_reason: str


class InspectionPlanSchema(BaseModel):
    id: str = Field(..., description="Unique plan ID (INSP-PLAN-xxx)")
    plan_name: str
    allocations: List[MultiRoverAllocationItemSchema] = Field(default_factory=list)
    unreachable_targets: List[str] = Field(default_factory=list, description="Target segment IDs disconnected in pipe graph")
    conflict_checks_passed: bool = Field(True)
    total_rovers_assigned: int
    total_targets_covered: int
    human_approval_status: HumanApprovalStatus = Field("PENDING_APPROVAL")
    rejection_reason: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: str
    is_simulated: bool = Field(True)


class GeneratePlanRequest(BaseModel):
    plan_name: Optional[str] = Field(None, description="Optional custom name for inspection plan")
    recommendation_ids: Optional[List[str]] = Field(None, description="Optional subset of recommendation IDs; if omitted, top urgent targets are used")
    preferred_rover_ids: Optional[List[str]] = Field(None, description="Optional pool of rovers to allocate from")
    max_targets_per_rover: int = Field(3, ge=1, le=10)
    battery_safety_reserve_pct: float = Field(20.0, ge=15.0, le=50.0)


class PlanApprovalRequest(BaseModel):
    operator_notes: Optional[str] = Field(None, description="Optional sign-off notes from certified operator")


class PlanRejectionRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=3, description="Mandatory reason for rejecting inspection plan")


class RouteAdaptationRequest(BaseModel):
    new_anomaly_coordinates: Optional[List[float]] = Field(None, description="[lng, lat] of detected acoustic surge/leak")
    new_target_segment_id: Optional[str] = None
    adaptation_reason: str = Field(..., min_length=5, description="Engineering justification for mid-mission rerouting")


class SimulatedSensorObservation(BaseModel):
    observation_id: str
    timestamp: str
    rover_id: str
    segment_id: str
    distance_along_pipe_m: float
    sensor_type: str # "ACOUSTIC", "PRESSURE", "MOISTURE", "CCTV", "THERMAL"
    reading_value: float
    unit: str
    anomaly_detected: bool
    classification: EvidenceClassification = Field("SIMULATED")


class InspectionExecutionProgressSchema(BaseModel):
    mission_id: str
    rover_id: str
    plan_id: str
    status: ExecutionStatus
    current_step: int
    total_steps: int
    progress_percentage: float
    current_coordinates: List[float] # [lng, lat]
    distance_traversed_m: float
    remaining_distance_m: float
    battery_percentage: float
    motor_temp_c: float
    active_anomalies_detected: int
    route_adapted: bool
    adaptation_history: List[Dict[str, Any]] = Field(default_factory=list)
    recent_observations: List[SimulatedSensorObservation] = Field(default_factory=list)
    last_updated: str
    is_simulated: bool = Field(True)


class InspectionReportSchema(BaseModel):
    id: str = Field(..., description="Unique report ID (INSP-REP-xxx)")
    plan_id: str
    mission_id: str
    rover_id: str
    pipeline_segment_id: str
    segment_name: str
    inspection_method: InspectionMethod
    start_time: str
    completion_time: str
    route_distance_m: float
    inspected_distance_m: float
    sensor_observations_count: int
    detected_anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_provenance: EvidenceClassification = Field("SIMULATED")
    ai_classification: Optional[Dict[str, Any]] = None
    updated_infrastructure_risk: float
    inspection_outcome: Literal["SUCCESS", "PARTIAL", "ABORTED"]
    unresolved_uncertainties: List[str] = Field(default_factory=list)
    recommended_next_action: str
    operator_review_status: Literal["PENDING_REVIEW", "REVIEWED", "ACTION_APPROVED"] = Field("PENDING_REVIEW")
    reviewed_by: Optional[str] = None
    operator_notes: Optional[str] = None
    created_at: str
    is_simulated: bool = Field(True)

