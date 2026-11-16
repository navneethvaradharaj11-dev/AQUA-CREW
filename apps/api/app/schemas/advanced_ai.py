"""
Pydantic Schemas for Advanced AI & Decision Intelligence (Task 13)
Defines contracts for evidence items, multi-source reasoning, explainable decision outputs,
chat interactions, structured responses, pipeline comparisons, and provider telemetry.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime


class EvidenceItemSchema(BaseModel):
    evidence_id: str
    source_module: str
    source_table: str
    source_record_id: str
    evidence_type: str
    classification: str = Field(
        ...,
        description="MEASURED, SIMULATED, DERIVED, PREDICTED, OPERATOR_ENTERED, UNKNOWN"
    )
    observed_at: Optional[str] = None
    metric_name: str
    metric_value: Optional[float] = None
    metric_unit: str = ""
    summary: str
    confidence: float = 0.85
    validation_status: str = "VALIDATED"
    age_hours: Optional[float] = None
    is_stale: bool = False
    calibration_status: str = "UNVERIFIED_VIRTUAL"
    hardware_connected: bool = False
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class MultiSourceReasoningResult(BaseModel):
    target_segment_id: str
    target_segment_name: str
    measured_facts: List[EvidenceItemSchema] = Field(default_factory=list)
    simulated_results: List[EvidenceItemSchema] = Field(default_factory=list)
    derived_metrics: List[EvidenceItemSchema] = Field(default_factory=list)
    predictions: List[EvidenceItemSchema] = Field(default_factory=list)
    temporal_alignment: str
    supporting_evidence: List[str] = Field(default_factory=list)
    contradictory_evidence: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    supported_conclusions: List[str] = Field(default_factory=list)
    uncertain_hypotheses: List[str] = Field(default_factory=list)
    recommended_investigation: str
    uncertainty_description: str


class DecisionExplanationResponse(BaseModel):
    entity_type: str
    entity_id: str
    primary_classification: str
    why_explained: str
    contributing_factors: Dict[str, Any] = Field(default_factory=dict)
    model_version: str
    input_quality_notes: str
    assumptions_applied: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)


class PipelineComparisonRequest(BaseModel):
    segment_ids: List[str] = Field(..., min_length=2, max_length=5)


class PipelineComparisonItem(BaseModel):
    segment_id: str
    name: str
    material: str
    diameter_mm: int
    vulnerability_score: float
    vulnerability_level: str
    health_score: float
    health_category: str
    incident_count: int
    pressure_psi: float
    inspection_priority: float
    priority_tier: str
    data_completeness_pct: float
    recommended_action: str


class PipelineComparisonResponse(BaseModel):
    segments: List[PipelineComparisonItem]
    comparative_summary: str
    highest_risk_segment_id: str
    highest_priority_segment_id: str


class OperationalSummaryResponse(BaseModel):
    summary_type: str
    generated_at: str
    new_incidents_count: int
    critical_assets_count: int
    pending_recommendations_count: int
    approved_decisions_count: int
    completed_missions_count: int
    network_urgency: str
    narrative_summary: str
    unresolved_risks: List[str] = Field(default_factory=list)
    recommended_next_actions: List[str] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)


class EvidenceGapAnalysisResponse(BaseModel):
    segment_id: str
    segment_name: str
    overall_data_completeness_pct: float
    missing_indicators: List[str] = Field(default_factory=list)
    uncertainty_impact_description: str
    recommended_sensor_installations: List[str] = Field(default_factory=list)


class AIChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    query: str = Field(..., min_length=1, max_length=2000)
    user_id: Optional[str] = "OPERATOR-SUPERVISOR-01"
    target_segment_id: Optional[str] = None


class AIChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    role: str = "assistant"
    content: str
    intent: str
    model_used: str
    provider_used: str
    supporting_evidence: List[EvidenceItemSchema] = Field(default_factory=list)
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_assessment: str
    validation_status: str
    missing_information: Optional[str] = None
    suggested_queries: List[str] = Field(default_factory=list)
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"
    timestamp: str


class AIConversationItem(BaseModel):
    id: str
    title: str
    user_id: str
    message_count: int
    created_at: str
    updated_at: str


class AIConversationDetail(BaseModel):
    id: str
    title: str
    user_id: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)


class ProviderStatusResponse(BaseModel):
    configured_provider: str
    is_external_connected: bool
    active_model: str
    fallback_mode_active: bool
    status_message: str

