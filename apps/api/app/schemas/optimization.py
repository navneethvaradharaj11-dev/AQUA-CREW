"""
Pydantic Schemas for Network Optimization & Decision Engine (Task 14)
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime, timezone


class DecisionVariableSchema(BaseModel):
    name: str = Field(..., description="Variable identifier (e.g. pump_speed_P1, prv_setting_PRV01)")
    variable_type: Literal["CONTINUOUS", "DISCRETE", "BINARY"] = Field("CONTINUOUS")
    component_id: str = Field(..., description="Target link or node ID")
    parameter_name: str = Field(..., description="Parameter being adjusted (speed, setting, status)")
    min_value: float = Field(..., description="Lower bound")
    max_value: float = Field(..., description="Upper bound")
    baseline_value: float = Field(..., description="Nominal baseline value")
    current_value: Optional[float] = Field(None, description="Candidate value")
    unit: str = Field(..., description="Physical unit of variable (ratio, bar, etc.)")


class ObjectiveWeightsSchema(BaseModel):
    water_loss_weight: float = Field(0.25, ge=0.0, le=1.0)
    energy_weight: float = Field(0.25, ge=0.0, le=1.0)
    pressure_quality_weight: float = Field(0.25, ge=0.0, le=1.0)
    demand_satisfaction_weight: float = Field(0.25, ge=0.0, le=1.0)
    cost_weight: float = Field(0.0, ge=0.0, le=1.0)


class OptimizationConstraintsSchema(BaseModel):
    min_service_pressure_bar: float = Field(1.5, description="Minimum acceptable service pressure at junctions")
    max_allowable_pressure_bar: float = Field(5.5, description="Maximum structural pressure limit")
    min_demand_satisfaction_ratio: float = Field(0.99, description="Minimum demand fulfillment (e.g. 99%)")
    max_pipe_velocity_mps: float = Field(2.5, description="Maximum pipe velocity threshold")
    min_tank_level_m: float = Field(1.5, description="Minimum tank reserve level")
    max_tank_level_m: float = Field(12.0, description="Maximum tank storage level")
    max_pump_switching_count: Optional[int] = Field(4, description="Maximum pump status toggles per 24 hours")


class OptimizationTriggerRequest(BaseModel):
    network_id: str = Field("NET-METRO-01", description="Hydraulic network ID")
    scenario_id: str = Field("SCEN-BASELINE-01", description="Baseline or operating scenario ID")
    objective_profile: Literal["BALANCED_OPERATION", "ENERGY_EFFICIENCY", "LEAKAGE_REDUCTION", "PRESSURE_STABILITY", "CUSTOM"] = Field("BALANCED_OPERATION")
    custom_weights: Optional[ObjectiveWeightsSchema] = None
    constraints: Optional[OptimizationConstraintsSchema] = None
    algorithm: Literal["DIFFERENTIAL_EVOLUTION", "MULTI_OBJECTIVE_PARETO", "SEQUENTIAL_LOCAL", "GRID_EXPLORATION"] = Field("DIFFERENTIAL_EVOLUTION")
    max_evaluations: int = Field(50, ge=5, le=500, description="Evaluation budget")
    random_seed: Optional[int] = Field(42, description="Random seed for deterministic reproducibility")
    electricity_tariff_usd_per_kwh: Optional[float] = Field(None, description="Optional tariff for cost objective")


class OptimizationCandidateSchema(BaseModel):
    candidate_id: str
    rank: int = Field(1, description="Pareto or objective rank")
    is_pareto_optimal: bool = Field(False)
    decision_variables: Dict[str, float] = Field(default_factory=dict, description="Variable assignments")
    objective_score: float = Field(..., description="Weighted objective function value (lower is better)")
    water_loss_score: float = Field(..., description="Total leakage volume in m3")
    energy_score: float = Field(..., description="Total electrical energy in kWh")
    pressure_penalty: float = Field(..., description="Pressure deviation penalty")
    demand_satisfaction_ratio: float = Field(..., description="Delivered demand / requested demand")
    estimated_cost_usd: Optional[float] = Field(None)
    is_hydraulically_verified: bool = Field(True)
    constraint_violations: List[str] = Field(default_factory=list)
    rejection_reason: Optional[str] = Field(None)


class BaselineComparisonSchema(BaseModel):
    baseline_leakage_m3: float
    optimized_leakage_m3: float
    leakage_reduction_m3: float
    leakage_reduction_pct: float

    baseline_energy_kwh: float
    optimized_energy_kwh: float
    energy_saved_kwh: float
    energy_saved_pct: float

    baseline_min_pressure_bar: float
    optimized_min_pressure_bar: float
    pressure_deficit_nodes_reduced: int

    baseline_demand_satisfaction: float
    optimized_demand_satisfaction: float

    baseline_cost_usd: Optional[float] = None
    optimized_cost_usd: Optional[float] = None
    cost_savings_usd: Optional[float] = None


class OptimizationJobDetailResponse(BaseModel):
    job_id: str
    user_id: str
    network_id: str
    scenario_id: str
    scenario_name: str
    status: Literal["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]
    objective_profile: str
    algorithm: str
    weights: ObjectiveWeightsSchema
    constraints: OptimizationConstraintsSchema
    evaluation_count: int
    execution_time_ms: float
    best_candidate: Optional[OptimizationCandidateSchema] = None
    candidates: List[OptimizationCandidateSchema] = Field(default_factory=list)
    comparison_with_baseline: Optional[BaselineComparisonSchema] = None
    pareto_frontier: List[OptimizationCandidateSchema] = Field(default_factory=list)
    created_at: str
    completed_at: Optional[str] = None
    is_simulated: bool = Field(True)
    source: str = Field("VIRTUAL_SIMULATION_ENGINE")


class OptimizationRecommendRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Operator notes for turning candidate into a recommendation")
    target_candidate_id: Optional[str] = Field(None, description="Specific candidate ID to recommend; defaults to best")

