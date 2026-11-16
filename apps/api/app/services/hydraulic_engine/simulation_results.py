"""
Standardized Data Structures for Hydraulic Simulation Engine Results (Task 10)
Provides dataclasses and serialization for node results, link results,
time-series records, and overall network hydraulic performance metrics.
"""
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


@dataclass
class NodeResult:
    node_id: str
    node_type: str  # JUNCTION, RESERVOIR, TANK
    pressure_bar: float
    pressure_psi: float
    head_m: float
    elevation_m: float
    actual_demand_lps: float
    expected_demand_lps: float
    leak_flow_lps: float
    pressure_deficit: bool
    status: str  # NORMAL, DEFICIT, BURST, CRITICAL_LOW, OVERPRESSURE
    name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LinkResult:
    link_id: str
    link_type: str  # PIPE, PUMP, VALVE
    flow_lps: float
    velocity_mps: float
    headloss_m: float
    unit_headloss_m_per_km: float
    friction_factor: float
    direction: str  # FORWARD, REVERSE, ZERO
    status: str  # OPEN, CLOSED, ACTIVE, LEAKING, BURST
    name: str = ""
    pipeline_segment_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TimeStepResult:
    step_index: int
    time_offset_hours: float
    timestamp_iso: str
    demand_multiplier: float
    total_supply_lps: float
    total_demand_lps: float
    total_leakage_lps: float
    min_pressure_bar: float
    max_pressure_bar: float
    pressure_deficit_nodes: List[str] = field(default_factory=list)
    node_pressures: Dict[str, float] = field(default_factory=dict)
    link_flows: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HydraulicSimulationResult:
    scenario_id: str
    network_id: str
    converged: bool
    iterations: int
    execution_duration_ms: float
    solver_name: str
    total_supply_lps: float
    total_demand_lps: float
    total_leakage_lps: float
    water_loss_percentage: float
    min_pressure_bar: float
    max_pressure_bar: float
    avg_pressure_bar: float
    pressure_deficit_count: int
    nodes: Dict[str, NodeResult] = field(default_factory=dict)
    links: Dict[str, LinkResult] = field(default_factory=dict)
    timesteps: List[TimeStepResult] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "network_id": self.network_id,
            "converged": self.converged,
            "iterations": self.iterations,
            "execution_duration_ms": round(self.execution_duration_ms, 2),
            "solver_name": self.solver_name,
            "total_supply_lps": round(self.total_supply_lps, 3),
            "total_demand_lps": round(self.total_demand_lps, 3),
            "total_leakage_lps": round(self.total_leakage_lps, 3),
            "water_loss_percentage": round(self.water_loss_percentage, 2),
            "min_pressure_bar": round(self.min_pressure_bar, 3),
            "max_pressure_bar": round(self.max_pressure_bar, 3),
            "avg_pressure_bar": round(self.avg_pressure_bar, 3),
            "pressure_deficit_count": self.pressure_deficit_count,
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "links": {k: v.to_dict() for k, v in self.links.items()},
            "timesteps": [t.to_dict() for t in self.timesteps],
            "created_at": self.created_at,
            "is_simulated": True,
            "source": "VIRTUAL_SIMULATION_ENGINE",
        }

