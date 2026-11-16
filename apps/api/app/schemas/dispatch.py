"""
Pydantic Schemas for Autonomous Mission Planning & Rover Dispatch
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime


class MissionPriorityAssessment(BaseModel):
    priority_score: float = Field(..., ge=0.0, le=100.0, description="Normalized priority score (0-100)")
    priority_category: str = Field(..., description="CRITICAL, HIGH, MEDIUM, LOW")
    contributing_factors: Dict[str, float] = Field(..., description="Breakdown of points allocated per criterion")
    explanation: str = Field(..., description="Human-readable decision rationale")
    recommended_response: str = Field(..., description="Actionable response directive")
    uncertainty_warning: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_detection_id: str


class PipelineRoute(BaseModel):
    start_coordinates: List[float] = Field(..., description="[lng, lat] of rover start position")
    destination_coordinates: List[float] = Field(..., description="[lng, lat] of target leak point")
    waypoints: List[List[float]] = Field(..., description="Ordered polyline array [[lng, lat], ...]")
    segments_traversed: List[str] = Field(..., description="List of pipeline segment IDs in route sequence")
    total_distance_m: float = Field(..., ge=0.0, description="Total route length along pipeline geometry in meters")
    estimated_travel_time_s: float = Field(..., ge=0.0, description="Estimated traverse duration in seconds")
    is_connected: bool = Field(True, description="Whether continuous pipeline connection exists")
    uncertainty_radius_m: Optional[float] = None


class RoverSuitability(BaseModel):
    rover_id: str
    rover_name: str
    operating_state: str
    battery_percentage: float
    is_eligible: bool
    disqualification_reason: Optional[str] = None
    distance_to_target_m: float
    estimated_energy_consumption_pct: float
    battery_reserve_after_pct: float
    suitability_score: float = Field(..., ge=0.0, le=100.0)
    suitability_explanation: str


class MissionPlanRequest(BaseModel):
    detection_id: str = Field(..., description="Target AI leak detection record ID")
    preferred_rover_id: Optional[str] = Field(None, description="Optional operator-specified rover override")
    priority_override: Optional[str] = Field(None, description="Optional manual priority level override")


class RecommendationApprovalRequest(BaseModel):
    operator_id: Optional[str] = Field("OPERATOR_CHIEF", description="ID of authorising operator")
    notes: Optional[str] = Field(None, description="Operational notes or execution parameters")


class RecommendationRejectionRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=3, description="Mandatory documented reason for rejecting dispatch")
    operator_notes: Optional[str] = None


class MissionRecommendationResponse(BaseModel):
    id: str
    detection_id: str
    pipeline_segment_id: str
    recommended_rover_id: str
    recommended_rover_name: str
    priority_score: float
    priority_category: str
    status: str
    route_distance_m: float
    estimated_duration_s: float
    estimated_energy_pct: float
    battery_reserve_after_pct: float
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    localization_uncertainty_m: Optional[float] = None
    waypoints: List[List[float]]
    segments_traversed: List[str]
    contributing_factors: Dict[str, Any]
    explanation: str
    assigned_mission_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    operator_notes: Optional[str] = None
    created_at: datetime
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"

    model_config = ConfigDict(from_attributes=True)


class DispatchEvaluationRequest(BaseModel):
    pipeline_segment_id: str
    target_lat: Optional[float] = None
    target_lng: Optional[float] = None


class DispatchEvaluationResponse(BaseModel):
    pipeline_segment_id: str
    eligible_rovers: List[RoverSuitability]
    ineligible_rovers: List[RoverSuitability]
    is_simulated: bool = True

