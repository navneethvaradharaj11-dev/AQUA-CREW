"""
AQUA CREW — Pydantic Schemas for Repair Planning & Management System (Task 16)
Defines strict validation contracts, enums, evidence provenance bindings,
material resources, transparent cost calculations, workflow states, and verification models.
"""
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone


DamageCategory = Literal[
    "PIPE_LEAK",
    "PIPE_BURST",
    "JOINT_FAILURE",
    "CORROSION",
    "STRUCTURAL_CRACK",
    "PRESSURE_DAMAGE",
    "VALVE_FAILURE",
    "UNKNOWN_DAMAGE",
]

DamageSeverity = Literal[
    "LOW",
    "MODERATE",
    "HIGH",
    "CRITICAL",
    "UNDETERMINED",
]

RepairMethodType = Literal[
    "CLAMP_REPAIR",
    "JOINT_REPAIR_REPLACEMENT",
    "PIPE_SECTION_REPLACEMENT",
    "INTERNAL_LINING_REHABILITATION",
    "CORROSION_PROTECTION",
    "VALVE_REPLACEMENT",
    "PRESSURE_MANAGEMENT",
    "FURTHER_INSPECTION_REQUIRED",
]

RepairWorkflowStatus = Literal[
    "INSPECTION_COMPLETED",
    "DAMAGE_ASSESSED",
    "REPAIR_RECOMMENDED",
    "ENGINEERING_REVIEW_PENDING",
    "APPROVED",
    "RESOURCE_PLANNED",
    "SCHEDULED",
    "REPAIR_IN_PROGRESS",
    "REPAIR_COMPLETED",
    "VERIFICATION_PENDING",
    "VERIFIED",
    "CLOSED",
    "REJECTED",
    "ON_HOLD",
    "FAILED",
    "REQUIRES_REINSPECTION",
]

VerificationOutcome = Literal[
    "VERIFIED_SUCCESS",
    "PARTIALLY_VERIFIED",
    "VERIFICATION_FAILED",
    "REQUIRES_REINSPECTION",
    "INSUFFICIENT_EVIDENCE",
]

EvidenceClassification = Literal[
    "MEASURED",
    "SIMULATED",
    "DERIVED",
    "PREDICTED",
    "OPERATOR_ENTERED",
    "UNKNOWN",
]

ResourceCategory = Literal[
    "MATERIALS",
    "EQUIPMENT",
    "TOOLS",
    "SAFETY",
    "COATINGS",
    "VALVES",
    "JOINTS_COUPLINGS",
]


class SupportingEvidenceItem(BaseModel):
    evidence_id: str
    source_subsystem: str
    classification: EvidenceClassification
    metric_name: str
    metric_value: Any
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    observed_at: Optional[str] = None


class DamageAssessmentSchema(BaseModel):
    id: str
    pipeline_segment_id: str
    segment_name: str
    source_inspection_report_id: Optional[str] = None
    damage_category: DamageCategory
    severity: DamageSeverity
    pipe_material: str
    pipe_diameter_mm: float
    pipe_age_years: Optional[float] = None
    nominal_pressure_psi: float
    estimated_water_loss_lph: float = Field(ge=0.0)
    structural_vulnerability_score: float = Field(ge=0.0, le=100.0)
    previous_repair_count: int = Field(ge=0, default=0)
    inspection_confidence: float = Field(ge=0.0, le=1.0, default=0.85)
    evidence_completeness_pct: float = Field(ge=0.0, le=100.0, default=80.0)
    missing_information: List[str] = Field(default_factory=list)
    engineering_review_required: bool = True
    supporting_evidence: List[SupportingEvidenceItem] = Field(default_factory=list)
    assessment_notes: str = ""
    assessed_by: str = "SYSTEM_REPAIR_ENGINE"
    assessed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_simulated: bool = True


class DamageAssessmentCreateRequest(BaseModel):
    pipeline_segment_id: str
    source_inspection_report_id: Optional[str] = None
    notes: Optional[str] = None


class RepairMethodOptionSchema(BaseModel):
    method: RepairMethodType
    method_name: str
    is_recommended: bool
    feasibility_score: float = Field(ge=0.0, le=100.0)
    rationale: str
    applicable_damage_types: List[DamageCategory]
    material_compatibility: List[str]
    min_diameter_mm: float
    max_diameter_mm: float
    max_pressure_psi: float
    operational_constraints: List[str]
    advantages: List[str]
    limitations: List[str]
    required_equipment: List[str]
    estimated_duration_hours: float = Field(gt=0.0)
    risks_and_uncertainties: List[str]
    standards_references: List[str]
    required_professional_approvals: List[str]


class RepairRecommendationSchema(BaseModel):
    id: str
    damage_assessment_id: str
    pipeline_segment_id: str
    primary_recommended_method: RepairMethodType
    secondary_alternative_method: Optional[RepairMethodType] = None
    all_evaluated_options: List[RepairMethodOptionSchema] = Field(default_factory=list)
    engineering_rationale: str
    urgency_tier: Literal["IMMEDIATE", "URGENT", "PLANNED", "ROUTINE", "FURTHER_MONITORING"]
    requires_isolation: bool = True
    bypass_pumping_needed: bool = False
    traffic_disruption_level: Literal["NONE", "LOW", "MODERATE", "SEVERE"] = "LOW"
    status: Literal["PROPOSED", "ACCEPTED", "MODIFIED", "REJECTED"] = "PROPOSED"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_simulated: bool = True


class RepairResourceItemSchema(BaseModel):
    resource_id: str
    name: str
    category: ResourceCategory
    unit: str
    estimated_quantity: float = Field(ge=0.0)
    compatibility_requirements: str
    availability_status: Literal["IN_STOCK", "SHORT_LEAD_TIME", "EXTENDED_LEAD_TIME", "UNKNOWN"]
    estimated_unit_cost_usd: float = Field(ge=0.0)
    total_cost_usd: float = Field(ge=0.0)
    supplier_info: str = "MUNICIPAL_SUPPLY_DEPOT"
    cost_data_source: EvidenceClassification = "DERIVED"
    cost_data_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ResourcePlanSchema(BaseModel):
    id: str
    repair_plan_id: str
    items: List[RepairResourceItemSchema] = Field(default_factory=list)
    total_materials_cost_usd: float = Field(ge=0.0)
    total_equipment_cost_usd: float = Field(ge=0.0)
    all_resources_available: bool
    procurement_lead_time_days: int = Field(ge=0)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CostComponentSchema(BaseModel):
    component_name: str
    amount_usd: float = Field(ge=0.0)
    formula: str
    input_values: Dict[str, Any] = Field(default_factory=dict)
    units: str
    assumptions: str
    uncertainty_range_pct: float = Field(ge=0.0, le=100.0, default=15.0)
    provenance: EvidenceClassification = "DERIVED"


class RepairCostEstimateSchema(BaseModel):
    id: str
    damage_assessment_id: str
    pipeline_segment_id: str
    components: List[CostComponentSchema] = Field(default_factory=list)
    total_material_cost_usd: float = Field(ge=0.0)
    total_equipment_cost_usd: float = Field(ge=0.0)
    total_labour_cost_usd: float = Field(ge=0.0)
    inspection_cost_usd: float = Field(ge=0.0)
    estimated_water_loss_cost_usd: float = Field(ge=0.0)
    restoration_cost_usd: float = Field(ge=0.0)
    contingency_cost_usd: float = Field(ge=0.0)
    total_estimated_cost_usd: float = Field(ge=0.0)
    estimated_downtime_hours: float = Field(ge=0.0)
    cost_uncertainty_lower_bound_usd: float = Field(ge=0.0)
    cost_uncertainty_upper_bound_usd: float = Field(ge=0.0)
    financial_disclaimer: str = (
        "Synthetic engineering estimate for operational planning. Not an active commercial quotation or guaranteed expenditure."
    )
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_simulated: bool = True


class RepairPrioritySchema(BaseModel):
    pipeline_segment_id: str
    repair_priority_score: float = Field(ge=0.0, le=100.0)
    priority_category: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    contributing_factors: Dict[str, float] = Field(default_factory=dict)
    uncertainty_margin: float = Field(ge=0.0, default=5.0)
    recommended_response_time_hours: int = Field(gt=0)
    escalation_requirements: List[str] = Field(default_factory=list)
    calculated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RepairCrewMemberSchema(BaseModel):
    member_id: str
    name: str
    role: str
    certification: str
    hourly_rate_usd: float = Field(gt=0.0)


class RepairCrewSchema(BaseModel):
    crew_id: str
    crew_name: str
    specialization: str
    skills: List[str] = Field(default_factory=list)
    members: List[RepairCrewMemberSchema] = Field(default_factory=list)
    is_available: bool = True
    base_location_lat: float
    base_location_lng: float
    current_assigned_job_id: Optional[str] = None
    max_daily_hours: float = 8.0


class RepairScheduleItemSchema(BaseModel):
    schedule_id: str
    repair_plan_id: str
    crew_id: str
    crew_name: str
    scheduled_start: str
    scheduled_end: str
    estimated_duration_hours: float = Field(gt=0.0)
    travel_distance_km: float = Field(ge=0.0)
    travel_time_hours: float = Field(ge=0.0)
    has_schedule_conflicts: bool = False
    schedule_conflict_details: Optional[str] = None
    scheduling_notes: str = ""


class RepairPlanSchema(BaseModel):
    id: str
    plan_name: str
    pipeline_segment_id: str
    segment_name: str
    damage_assessment_id: str
    repair_recommendation_id: str
    selected_method: RepairMethodType
    workflow_status: RepairWorkflowStatus
    priority: RepairPrioritySchema
    resources: Optional[ResourcePlanSchema] = None
    cost_estimate: Optional[RepairCostEstimateSchema] = None
    schedule: Optional[RepairScheduleItemSchema] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    operator_notes: Optional[str] = None
    digital_twin_scenario_id: Optional[str] = None
    created_by: str = "ENGINEER_SYSTEM"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_simulated: bool = True


class RepairPlanCreateRequest(BaseModel):
    pipeline_segment_id: str
    plan_name: str
    selected_method: Optional[RepairMethodType] = None
    override_notes: Optional[str] = None


class RepairPlanApprovalRequest(BaseModel):
    engineer_notes: str = Field(min_length=3, description="Engineering review and sign-off rationale.")
    override_selected_method: Optional[RepairMethodType] = None


class RepairPlanRejectionRequest(BaseModel):
    rejection_reason: str = Field(min_length=3, description="Mandatory reason for rejecting proposed plan.")


class RepairWorkflowTransitionRequest(BaseModel):
    target_status: RepairWorkflowStatus
    reason: str = Field(min_length=3)
    notes: Optional[str] = None


class RepairWorkflowEventSchema(BaseModel):
    id: str
    repair_plan_id: str
    from_status: str
    to_status: str
    changed_by: str
    reason: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DigitalTwinRepairScenarioSchema(BaseModel):
    scenario_id: str
    repair_plan_id: str
    pipeline_segment_id: str
    baseline_pressure_bar: float
    pre_repair_pressure_bar: float
    post_repair_pressure_bar: float
    baseline_leakage_m3: float
    pre_repair_leakage_m3: float
    post_repair_leakage_m3: float
    water_loss_reduction_pct: float
    pressure_restoration_pct: float
    pump_energy_delta_kwh: float
    demand_satisfaction_pct: float
    simulation_solver: str = "WNTR_PDA"
    is_simulated: bool = True


class DigitalTwinRepairComparisonSchema(BaseModel):
    repair_plan_id: str
    scenario_comparison_id: str
    baseline_scenario_id: str
    pre_repair_scenario_id: str
    post_repair_scenario_id: str
    summary_metrics: Dict[str, float] = Field(default_factory=dict)
    link_differences: List[Dict[str, Any]] = Field(default_factory=list)
    node_differences: List[Dict[str, Any]] = Field(default_factory=list)
    hydraulic_benefit_score: float = Field(ge=0.0, le=100.0)


class RepairVerificationRequest(BaseModel):
    repair_plan_id: str
    measured_post_repair_pressure_bar: Optional[float] = None
    measured_post_repair_flow_lps: Optional[float] = None
    acoustic_sensor_reading_db: Optional[float] = None
    visual_inspection_notes: str = Field(min_length=5)
    engineer_signoff_notes: str = Field(min_length=5)


class RepairVerificationSchema(BaseModel):
    id: str
    repair_plan_id: str
    pipeline_segment_id: str
    verification_outcome: VerificationOutcome
    pre_repair_leakage_lph: float
    post_repair_leakage_lph: float
    leakage_reduction_pct: float
    acoustic_anomaly_cleared: bool
    pressure_gradient_restored: bool
    remaining_uncertainty_pct: float
    supporting_evidence: List[SupportingEvidenceItem] = Field(default_factory=list)
    verified_by: str
    verified_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tamper_proof_hash: str
    is_simulated: bool = True


class RepairOverviewSummarySchema(BaseModel):
    system_status: str = "ONLINE"
    active_assessments_count: int = 0
    pending_engineering_reviews_count: int = 0
    approved_plans_count: int = 0
    scheduled_repairs_count: int = 0
    in_progress_repairs_count: int = 0
    completed_verifications_count: int = 0
    total_water_loss_prevented_m3: float = 0.0
    total_repair_expenditure_usd: float = 0.0
    supported_damage_categories: List[str] = Field(default_factory=list)
    supported_repair_methods: List[str] = Field(default_factory=list)
    is_simulated: bool = True

