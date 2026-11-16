"""
Pydantic Schemas for Network Performance Evaluation (Task 14)
Standardizes pressure, hydraulic, water-loss, energy, and reliability metrics.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class MetricValue(BaseModel):
    value: Optional[float] = Field(None, description="Numerical metric value, None if unavailable")
    unit: str = Field(..., description="Engineering unit of measure (e.g. bar, m3/day, kWh, L/s)")
    is_available: bool = Field(True, description="False if metric data is missing or unconfigured")
    source: str = Field("VIRTUAL_SIMULATION_ENGINE", description="Origin of metric calculation")


class PressureMetrics(BaseModel):
    min_pressure_bar: MetricValue
    max_pressure_bar: MetricValue
    avg_pressure_bar: MetricValue
    pressure_deficit_nodes_count: int = Field(0, description="Nodes below minimum regulatory pressure (1.5 bar)")
    pressure_excess_nodes_count: int = Field(0, description="Nodes exceeding maximum pressure threshold (5.5 bar)")
    deficit_node_ids: List[str] = Field(default_factory=list)
    excess_node_ids: List[str] = Field(default_factory=list)
    node_pressures_bar: Dict[str, float] = Field(default_factory=dict)


class HydraulicFlowMetrics(BaseModel):
    total_requested_demand_lps: MetricValue
    total_delivered_demand_lps: MetricValue
    demand_satisfaction_ratio: MetricValue
    max_pipe_velocity_mps: MetricValue
    avg_pipe_velocity_mps: MetricValue
    max_pipe_headloss_m: MetricValue
    total_network_headloss_m: MetricValue
    capacity_utilization_pct: MetricValue
    link_velocities_mps: Dict[str, float] = Field(default_factory=dict)
    link_flows_lps: Dict[str, float] = Field(default_factory=dict)


class WaterLossMetrics(BaseModel):
    total_simulated_leakage_lps: MetricValue
    daily_leakage_volume_m3: MetricValue
    leakage_to_supplied_ratio_pct: MetricValue
    leakage_by_segment: Dict[str, float] = Field(default_factory=dict, description="Leak flow in L/s by segment")
    leakage_by_zone: Dict[str, float] = Field(default_factory=dict, description="Leak flow in L/s by pressure zone")


class EnergyMetrics(BaseModel):
    pump_electrical_energy_kwh: MetricValue
    pump_hydraulic_energy_kwh: MetricValue
    pump_wire_to_water_efficiency_pct: MetricValue
    pump_operating_hours: MetricValue
    energy_cost_usd: MetricValue
    tariff_usd_per_kwh: Optional[float] = Field(None, description="Configured electricity tariff rate if available")
    cost_data_available: bool = Field(False, description="True if energy tariff was provided, False if unknown")


class ReliabilityMetrics(BaseModel):
    hydraulic_converged: bool = Field(True, description="True if simulation solver achieved convergence")
    iterations: int = Field(1, description="Solver iterations required for convergence")
    unserved_demand_lps: MetricValue
    mass_balance_error_lps: MetricValue
    network_connectivity: bool = Field(True, description="True if all demand nodes are hydraulically connected")
    critical_violations_count: int = Field(0, description="Count of active pressure, velocity, or tank violations")
    violations: List[str] = Field(default_factory=list)


class NetworkPerformanceReport(BaseModel):
    network_id: str
    scenario_id: str
    scenario_name: str
    evaluation_timestamp: str
    duration_hours: int
    solver_mode: str
    pressure: PressureMetrics
    hydraulic: HydraulicFlowMetrics
    water_loss: WaterLossMetrics
    energy: EnergyMetrics
    reliability: ReliabilityMetrics
    is_simulated: bool = Field(True, description="Explicit simulated provenance")
    source: str = Field("VIRTUAL_SIMULATION_ENGINE", description="Origin of simulation data")

