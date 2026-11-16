"""
Pydantic Schemas for Infrastructure Intelligence & Geospatial Risk Prediction (Task 11)
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime


class FactorDetail(BaseModel):
    score: float
    weight: float
    weighted_contribution: float
    reasons: List[str] = Field(default_factory=list)


class ContributingFactorsBreakdown(BaseModel):
    hydraulic: Optional[FactorDetail] = None
    structural: Optional[FactorDetail] = None
    incident: Optional[FactorDetail] = None
    environmental: Optional[FactorDetail] = None


class PipelineVulnerabilityItem(BaseModel):
    id: str
    pipeline_segment_id: str
    segment_name: str
    material: str
    diameter_mm: int
    length_m: float
    pressure_zone_id: str
    category: str
    vulnerability_score: float = Field(..., ge=0.0, le=100.0)
    vulnerability_level: str = Field(..., description="VERY_LOW, LOW, MODERATE, HIGH, CRITICAL")
    hydraulic_score: float = 0.0
    structural_score: float = 0.0
    incident_score: float = 0.0
    environmental_score: float = 0.0
    contributing_factors: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.85
    data_completeness_pct: float = 90.0
    uncertainty_margin: float = 5.0
    deterioration_rate_per_day: float = 0.0
    trend_direction: str = "STABLE"
    active_incident_count: int = 0
    midpoint_lat: Optional[float] = None
    midpoint_lng: Optional[float] = None
    assessed_at: Optional[str] = None
    is_simulated: bool = True


class PipelineVulnerabilityListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[PipelineVulnerabilityItem]


class ConfidenceInterval(BaseModel):
    lower_bound: float
    upper_bound: float


class PredictiveForecastDetail(BaseModel):
    projected_risk_24h: float
    projected_risk_7d: float
    projected_risk_30d: float
    trend_24h_delta: float
    trend_7d_delta: float
    trend_30d_delta: float
    primary_risk_drivers: List[str] = Field(default_factory=list)
    mitigation_urgency: str = "PLANNED"
    hydraulic_deficit_flag: bool = False
    cluster_proximity_m: float = 9999.0


class InspectionPriorityItem(BaseModel):
    id: str
    pipeline_segment_id: str
    segment_name: str
    priority_score: float = Field(..., ge=0.0, le=100.0)
    priority_level: str
    status: str
    target_latitude: float
    target_longitude: float
    reasons: List[str] = Field(default_factory=list)
    suggested_action: str
    assigned_rover_id: Optional[str] = None
    mission_recommendation_id: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[Union[datetime, str]] = None
    operator_notes: Optional[str] = None
    dismissal_reason: Optional[str] = None
    created_at: Optional[Union[datetime, str]] = None
    updated_at: Optional[Union[datetime, str]] = None
    is_simulated: bool = True


class SegmentDeepDiveResponse(BaseModel):
    pipeline_segment_id: str
    segment_name: str
    material: str
    diameter_mm: int
    length_m: float
    pressure_zone_id: str
    category: str
    vulnerability_score: float
    vulnerability_level: str
    hydraulic_score: float
    structural_score: float
    incident_score: float
    environmental_score: float
    contributing_factors: Dict[str, Any] = Field(default_factory=dict)
    confidence: float
    data_completeness_pct: float
    uncertainty_margin: float
    deterioration_rate_per_day: float
    trend_direction: str
    active_incident_count: int
    midpoint_lat: Optional[float] = None
    midpoint_lng: Optional[float] = None
    assessed_at: Optional[str] = None
    predictive_forecast: Optional[PredictiveForecastDetail] = None
    inspection_priority: Optional[Dict[str, Any]] = None
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class SpatialClusterItem(BaseModel):
    id: str
    cluster_name: str
    zone_id: str
    centroid_lat: float
    centroid_lng: float
    radius_m: float
    incident_count: int
    dominant_material: str
    average_severity: float
    cluster_risk_level: str
    affected_segment_ids: List[str] = Field(default_factory=list)
    hotspot_intensity: float
    is_active: bool
    identified_at: Optional[str] = None
    is_simulated: bool = True


class GeographicRiskZoneItem(BaseModel):
    id: str
    zone_code: str
    zone_name: str
    description: Optional[str] = None
    total_segments: int
    total_length_km: float
    avg_vulnerability_score: float
    dominant_risk_level: str
    critical_segment_count: int
    active_clusters_count: int
    avg_pressure_psi: float
    bounds: Optional[Dict[str, Any]] = None
    updated_at: Optional[str] = None
    is_simulated: bool = True


class HeatmapPointItem(BaseModel):
    latitude: float
    longitude: float
    weight: float
    segment_id: str
    risk_level: str
    score: float
    point_type: str


class TemporalTrendItem(BaseModel):
    pipeline_segment_id: str
    segment_name: str
    vulnerability_score: float
    trend_direction: str
    deterioration_rate_per_day: float
    trend_24h_delta: float
    trend_7d_delta: float
    trend_30d_delta: float
    rapid_degradation: bool


class PredictionItem(BaseModel):
    pipeline_segment_id: str
    segment_name: str
    current_vulnerability_score: float
    risk_level: str
    projected_risk_24h: float
    projected_risk_7d: float
    projected_risk_30d: float
    trend_24h_delta: float
    trend_7d_delta: float
    trend_30d_delta: float
    primary_risk_drivers: List[str] = Field(default_factory=list)
    mitigation_urgency: str
    hydraulic_deficit_flag: bool
    cluster_proximity_m: float


class InfrastructureOverviewResponse(BaseModel):
    total_segments_analyzed: int
    critical_segments_count: int
    high_risk_segments_count: int
    moderate_risk_segments_count: int
    low_risk_segments_count: int
    average_network_vulnerability: float
    network_deterioration_rate: float
    deteriorating_segments_count: int
    active_clusters_count: int
    pending_inspections_count: int
    highest_risk_segment: Optional[Dict[str, Any]] = None
    highest_risk_zone: Optional[Dict[str, Any]] = None
    validation_status: str = "VALIDATED"
    methodology_version: str = "v1.2.0-hybrid-physics-geodesic"
    configured_risk_weights: Dict[str, float] = Field(default_factory=lambda: {
        "hydraulic": 0.30,
        "structural": 0.25,
        "incident": 0.25,
        "environmental": 0.20,
    })
    last_updated: str
    is_fallback: bool = False
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class AcknowledgeInspectionRequest(BaseModel):
    operator_name: Optional[str] = "OPERATOR_CHIEF"
    notes: Optional[str] = None


class DismissInspectionRequest(BaseModel):
    operator_name: Optional[str] = "OPERATOR_CHIEF"
    reason: Optional[str] = None


class RequestInspectionRequest(BaseModel):
    operator_name: Optional[str] = "OPERATOR_CHIEF"
    preferred_rover_id: Optional[str] = None
    notes: Optional[str] = None


class InspectionDispatchResponse(BaseModel):
    status: str
    priority_record_id: str
    pipeline_segment_id: str
    mission_recommendation_id: str
    assigned_rover_id: str
    assigned_rover_name: str
    planned_route_distance_m: float
    operator_approval_required: bool = True
    recommendation_status: str
    message: str
