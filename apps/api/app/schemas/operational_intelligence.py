"""
Pydantic Schemas for Unified Operational Intelligence & Decision Support Platform (Task 12)
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime


class OperationalEvidenceItem(BaseModel):
    id: str
    recommendation_id: str
    evidence_type: str
    source_module: str
    source_table: str
    source_record_id: str
    metric_name: str
    metric_value: Optional[float] = None
    metric_unit: str = ""
    confidence_score: float = 0.85
    evidence_summary: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    recorded_at: Optional[str] = None
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class OperationalEvidenceListResponse(BaseModel):
    total: int
    recommendation_id: str
    items: List[OperationalEvidenceItem]


class OperationalImpactItem(BaseModel):
    id: str
    recommendation_id: str
    pipeline_segment_id: str
    scenario_id: Optional[str] = None
    estimated_water_loss_m3_day: float = 0.0
    is_water_loss_measured: bool = False
    service_disruption_risk: str = "LOW"
    affected_nodes_count: int = 0
    affected_population_estimate: int = 0
    hydraulic_headloss_delta_m: float = 0.0
    min_pressure_drop_bar: float = 0.0
    estimated_inspection_distance_m: float = 0.0
    estimated_mission_energy_pct: float = 0.0
    estimated_inspection_duration_min: float = 0.0
    cost_impact_display: str = "NOT AVAILABLE"
    data_quality_rating: str = "ESTIMATED_SIMULATED"
    assumptions: Dict[str, Any] = Field(default_factory=dict)
    uncertainty_margin_pct: float = 15.0
    assessed_at: Optional[str] = None
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class OperationalImpactAnalysisRequest(BaseModel):
    pipeline_segment_id: str
    leak_orifice_diameter_mm: Optional[float] = 15.0
    demand_multiplier: Optional[float] = 1.0
    duration_hours: Optional[int] = 24


class OperationalRecommendationItem(BaseModel):
    id: str
    assessment_id: Optional[str] = None
    category: str
    pipeline_segment_id: str
    segment_name: str
    associated_incident_id: Optional[str] = None
    associated_cluster_id: Optional[str] = None
    risk_severity: str
    priority_score: float = Field(..., ge=0.0, le=100.0)
    priority_tier: str
    recommended_action: str
    action_details: Optional[str] = None
    why_explanation: str
    what_missing: str
    expected_impact: str
    contributing_factors: Dict[str, Any] = Field(default_factory=dict)
    evidence_sources: List[str] = Field(default_factory=list)
    resource_requirements: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(..., ge=0.0, le=1.0)
    data_completeness_pct: float = Field(..., ge=0.0, le=100.0)
    uncertainty_margin: float = 5.0
    status: str
    approval_status: str
    assigned_rover_id: Optional[str] = None
    dispatched_mission_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    expires_at: Optional[str] = None
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class OperationalRecommendationDetail(OperationalRecommendationItem):
    evidences: List[OperationalEvidenceItem] = Field(default_factory=list)
    impact_assessment: Optional[OperationalImpactItem] = None


class OperationalRecommendationListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[OperationalRecommendationItem]


class OperationalDecisionRequest(BaseModel):
    decision_type: str = Field(..., description="APPROVED or REJECTED")
    decision_reason: str = Field(..., min_length=3, description="Mandatory operator justification")
    operator_id: Optional[str] = "OPERATOR-SUPERVISOR-01"
    operator_name: Optional[str] = "Lead Operations Engineer"
    allocated_resource_id: Optional[str] = None
    override_priority: Optional[float] = None


class OperationalDecisionResponse(BaseModel):
    success: bool
    decision_id: str
    recommendation_id: str
    decision_type: str
    decision_reason: str
    operator_id: Optional[str] = None
    operator_name: Optional[str] = None
    resulting_mission_id: Optional[str] = None
    status: str
    timestamp: str
    message: str


class OperationalPriorityItem(BaseModel):
    id: str
    recommendation_id: str
    pipeline_segment_id: str
    rank_position: int
    composite_priority_score: float
    incident_severity_component: float
    vulnerability_component: float
    asset_health_component: float
    hydraulic_impact_component: float
    service_criticality_component: float
    recurrence_component: float
    confidence_weight: float
    weights_version: str
    weights_applied: Dict[str, float] = Field(default_factory=dict)
    reassessment_counter: int
    last_ranked_at: Optional[str] = None


class OperationalPriorityListResponse(BaseModel):
    total: int
    items: List[OperationalPriorityItem]


class IncidentCorrelationItem(BaseModel):
    id: str
    primary_segment_id: str
    primary_segment_name: str
    related_segment_id: Optional[str] = None
    incident_ids: List[str] = Field(default_factory=list)
    correlation_type: str  # CONFIRMED_RELATIONSHIP, POTENTIAL_RELATIONSHIP, GEOGRAPHIC_COINCIDENCE, INSUFFICIENT_EVIDENCE
    correlation_strength: float = Field(..., ge=0.0, le=1.0)
    uncertainty: float = 0.15
    geographic_distance_m: Optional[float] = None
    temporal_delta_hours: Optional[float] = None
    shared_pressure_zone: bool = True
    supporting_evidence: List[str] = Field(default_factory=list)
    explanation: str
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class IncidentCorrelationListResponse(BaseModel):
    total: int
    items: List[IncidentCorrelationItem]


class RoverSuitabilityItem(BaseModel):
    rover_id: str
    rover_name: str
    status: str
    operating_state: str
    battery_percentage: float
    motor_temp_c: float
    distance_to_target_m: float
    suitability_score: float  # 0.0 to 100.0
    is_eligible: bool
    rejection_reasons: List[str] = Field(default_factory=list)


class ResourcePlanningItem(BaseModel):
    recommendation_id: str
    pipeline_segment_id: str
    segment_name: str
    required_capability: str
    estimated_distance_m: float
    estimated_energy_pct: float
    estimated_duration_min: float
    suitable_rovers: List[RoverSuitabilityItem] = Field(default_factory=list)
    best_rover_id: Optional[str] = None
    best_rover_name: Optional[str] = None
    dispatch_feasibility: str  # READY_FOR_DISPATCH, NO_ROVER_AVAILABLE, RESOURCE_CONFLICT, LOW_BATTERY_WARNING
    workforce_status: str = "NOT_AVAILABLE (Software Simulation Mode)"
    inventory_status: str = "NOT_AVAILABLE (Software Simulation Mode)"


class ResourcePlanningResponse(BaseModel):
    total_resources_evaluated: int
    items: List[ResourcePlanningItem]


class OperationalExecutionItem(BaseModel):
    id: str
    recommendation_id: str
    decision_id: Optional[str] = None
    mission_id: Optional[str] = None
    assigned_rover_id: Optional[str] = None
    execution_stage: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    distance_inspected_m: float = 0.0
    energy_consumed_pct: float = 0.0
    findings_summary: Optional[str] = None
    leak_confirmed: Optional[bool] = None
    last_updated_at: Optional[str] = None


class OperationalExecutionHistoryResponse(BaseModel):
    total: int
    items: List[OperationalExecutionItem]


class OperationalAssessmentResponse(BaseModel):
    id: str
    assessment_name: str
    total_recommendations: int
    immediate_action_count: int
    urgent_leak_count: int
    preventive_count: int
    critical_segments_analyzed: int
    overall_network_urgency: str
    summary: Dict[str, Any] = Field(default_factory=dict)
    assessed_at: Optional[str] = None
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class OperationalOverviewResponse(BaseModel):
    active_incidents_count: int
    critical_segments_count: int
    pending_recommendations_count: int
    approved_actions_count: int
    active_missions_count: int
    available_rovers_count: int
    network_health_score: float
    network_urgency: str
    recommendations_by_category: Dict[str, int] = Field(default_factory=dict)
    latest_assessment: Optional[OperationalAssessmentResponse] = None
    validation_status: str = "VALIDATED_AND_CERTIFIED"
    methodology_version: str = "v1.0.0-unified-operational-decision"
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"
    actuation_notice: str = "REAL-WORLD PHYSICAL ACTUATORS PERMANENTLY DISABLED (SAFETY INTERLOCKED)"

