"""
Pydantic Schemas for Predictive Maintenance & Infrastructure Health Intelligence (Task 09)
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class PipelineHealthResponse(BaseModel):
    id: str
    pipeline_segment_id: str
    health_score: float = Field(..., ge=0.0, le=100.0)
    health_category: str = Field(..., description="EXCELLENT, GOOD, FAIR, POOR, or CRITICAL")
    acoustic_stability_score: float = Field(default=100.0)
    pressure_stability_score: float = Field(default=100.0)
    flow_stability_score: float = Field(default=100.0)
    moisture_anomaly_score: float = Field(default=100.0)
    data_coverage_pct: float = Field(default=100.0)
    confidence: float = Field(default=0.90)
    contributing_factors: Dict[str, float] = Field(default_factory=dict)
    positive_indicators: List[str] = Field(default_factory=list)
    explanation: str = Field(default="")
    assessed_at: datetime
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class HealthAnalyzeRequest(BaseModel):
    pipeline_segment_id: str
    lookback_hours: Optional[int] = 24


class PredictiveRiskResponse(BaseModel):
    id: str
    pipeline_segment_id: str
    failure_prob_24h: float = Field(..., ge=0.0, le=1.0)
    failure_prob_7d: float = Field(..., ge=0.0, le=1.0)
    failure_prob_30d: float = Field(..., ge=0.0, le=1.0)
    overall_risk_level: str = Field(..., description="LOW, MODERATE, HIGH, or CRITICAL")
    leak_probability: float = Field(default=0.05)
    burst_rupture_risk: float = Field(default=0.02)
    model_version: str = "v1.0.0-rf-gradient-predictive"
    confidence: float = 0.85
    uncertainty_margin: float = 0.08
    contributing_factors: Dict[str, float] = Field(default_factory=dict)
    risk_explanation: str = ""
    assessed_at: datetime
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class PredictiveRiskAnalyzeRequest(BaseModel):
    pipeline_segment_id: str
    prediction_horizons: Optional[List[str]] = ["24h", "7d", "30d"]


class HistoricalTrendResponse(BaseModel):
    id: str
    pipeline_segment_id: str
    trend_direction: str = Field(..., description="IMPROVING, STABLE, DETERIORATING, RAPIDLY_DETERIORATING, INSUFFICIENT_DATA")
    health_slope_per_day: float = 0.0
    pressure_variance: float = 0.0
    flow_anomaly_rate: float = 0.0
    acoustic_emission_count: int = 0
    historical_leak_count: int = 0
    window_days: int = 30
    time_series_points: List[Dict[str, Any]] = Field(default_factory=list)
    assessed_at: datetime
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class MaintenanceRecommendationResponse(BaseModel):
    id: str
    pipeline_segment_id: str
    health_score: float
    predicted_risk: str
    urgency: str = Field(..., description="ROUTINE, MEDIUM, HIGH, or CRITICAL")
    recommended_action: str = Field(..., description="CONTINUE_MONITORING, SCHEDULE_ACOUSTIC_INSPECTION, DISPATCH_INSPECTION_ROVER, etc.")
    timeframe_days: int = 14
    status: str = Field(default="PENDING_REVIEW")
    explanation: str = ""
    sensor_evidence: Dict[str, Any] = Field(default_factory=dict)
    operator_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    dispatched_mission_id: Optional[str] = None
    created_at: datetime
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class MaintenanceReviewRequest(BaseModel):
    action: str = Field(..., description="ACKNOWLEDGE, DISMISS, or DISPATCH")
    operator_id: str = "OPERATOR_CHIEF"
    operator_notes: Optional[str] = None


class MaintenanceModelInfo(BaseModel):
    model_name: str
    model_version: str
    algorithm: str
    training_dataset_size: int
    features: List[str]
    accuracy: float
    f1_score: float
    roc_auc: float
    last_evaluated: str
    is_simulated: bool = True
    source: str = "VIRTUAL_SIMULATION_ENGINE"


class PredictiveMaintenanceOverview(BaseModel):
    total_segments_monitored: int
    excellent_count: int
    good_count: int
    fair_count: int
    poor_count: int
    critical_count: int
    insufficient_data_count: int
    average_health_score: float
    high_risk_segment_count: int
    pending_recommendation_count: int
    timestamp: datetime
    is_simulated: bool = True

