"""
SQLAlchemy Models for Digital Twin & Hydraulic Network Simulation Platform (Task 10)
Stores hydraulic network topology, physical components, simulation scenarios,
run telemetry outputs, and scenario comparison deltas.
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, ForeignKey
from datetime import datetime, timezone
import json

from app.database.session import Base


class HydraulicNetworkModel(Base):
    __tablename__ = "hydraulic_networks"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, default="")
    headloss_formula = Column(String(32), default="H-W")  # H-W (Hazen-Williams) or D-W (Darcy-Weisbach)
    flow_units = Column(String(32), default="LPS")  # LPS, GPM, M3/H
    demand_model = Column(String(32), default="PDA")  # PDA (Pressure-Driven) or DDA (Demand-Driven)
    is_active = Column(Boolean, default=True, nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


class HydraulicNodeModel(Base):
    __tablename__ = "hydraulic_nodes"

    id = Column(String(64), primary_key=True, index=True)
    network_id = Column(String(64), ForeignKey("hydraulic_networks.id"), nullable=False, index=True)
    node_type = Column(String(32), nullable=False, index=True)  # JUNCTION, RESERVOIR, TANK
    name = Column(String(256), nullable=False)
    elevation_m = Column(Float, default=15.0, nullable=False)
    base_head_m = Column(Float, nullable=True)  # For reservoirs (e.g., 85.0)
    base_demand_lps = Column(Float, default=0.0, nullable=False)
    demand_pattern_id = Column(String(64), nullable=True)
    emitter_coeff = Column(Float, default=0.0, nullable=False)  # Torricelli leak orifice coefficient
    min_pressure_bar = Column(Float, default=1.5, nullable=False)  # Min regulatory pressure
    nominal_pressure_bar = Column(Float, default=4.2, nullable=False)
    # Storage tank specific properties
    initial_level_m = Column(Float, nullable=True)
    min_level_m = Column(Float, nullable=True)
    max_level_m = Column(Float, nullable=True)
    diameter_m = Column(Float, nullable=True)
    # Geospatial location
    longitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)


class HydraulicLinkModel(Base):
    __tablename__ = "hydraulic_links"

    id = Column(String(64), primary_key=True, index=True)
    network_id = Column(String(64), ForeignKey("hydraulic_networks.id"), nullable=False, index=True)
    link_type = Column(String(32), nullable=False, index=True)  # PIPE, PUMP, VALVE
    name = Column(String(256), nullable=False)
    start_node_id = Column(String(64), nullable=False, index=True)
    end_node_id = Column(String(64), nullable=False, index=True)
    length_m = Column(Float, default=500.0, nullable=False)
    diameter_mm = Column(Float, default=300.0, nullable=False)
    roughness = Column(Float, default=140.0, nullable=False)  # Hazen-Williams C or DW roughness (mm)
    minor_loss = Column(Float, default=0.0, nullable=False)
    initial_status = Column(String(32), default="OPEN", nullable=False)  # OPEN, CLOSED, ACTIVE
    current_status = Column(String(32), default="OPEN", nullable=False)
    pipeline_segment_id = Column(String(64), nullable=True, index=True)  # Associated GIS pipeline segment
    # Pump specific properties
    pump_curve_coeffs_json = Column(Text, nullable=True)  # {"h0": 60.0, "a": 0.002, "b": 2.0}
    pump_speed = Column(Float, default=1.0, nullable=True)
    pump_power_kw = Column(Float, default=45.0, nullable=True)
    # Valve specific properties
    valve_type = Column(String(32), nullable=True)  # PRV, FCV, TCV
    valve_setting = Column(Float, nullable=True)
    # GIS coordinates serialized [[lon, lat], ...]
    coordinates_json = Column(Text, nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)


class SimulationScenarioModel(Base):
    __tablename__ = "simulation_scenarios"

    id = Column(String(64), primary_key=True, index=True)
    network_id = Column(String(64), ForeignKey("hydraulic_networks.id"), nullable=False, index=True)
    name = Column(String(256), nullable=False)
    scenario_type = Column(String(64), nullable=False, index=True)  # BASELINE, HIGH_DEMAND, PIPE_BURST, MINOR_LEAK, PUMP_TRIP, VALVE_FAILURE, RECOVERY
    description = Column(Text, default="")
    is_baseline = Column(Boolean, default=False, nullable=False)
    duration_hours = Column(Integer, default=24, nullable=False)
    time_step_minutes = Column(Integer, default=60, nullable=False)
    solver_mode = Column(String(32), default="PDA", nullable=False)  # PDA, DDA
    parameters_override_json = Column(Text, default="{}", nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)


class SimulationRunModel(Base):
    __tablename__ = "simulation_runs"

    id = Column(String(64), primary_key=True, index=True)
    scenario_id = Column(String(64), ForeignKey("simulation_scenarios.id"), nullable=False, index=True)
    network_id = Column(String(64), ForeignKey("hydraulic_networks.id"), nullable=False, index=True)
    execution_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    execution_duration_ms = Column(Float, default=0.0, nullable=False)
    converged = Column(Boolean, default=True, nullable=False)
    iterations = Column(Integer, default=1, nullable=False)
    total_demand_m3 = Column(Float, default=0.0, nullable=False)
    total_leakage_m3 = Column(Float, default=0.0, nullable=False)
    water_loss_percentage = Column(Float, default=0.0, nullable=False)
    min_pressure_bar = Column(Float, default=0.0, nullable=False)
    max_pressure_bar = Column(Float, default=0.0, nullable=False)
    pressure_deficit_nodes_count = Column(Integer, default=0, nullable=False)
    summary_json = Column(Text, default="{}", nullable=False)
    node_results_json = Column(Text, default="{}", nullable=False)
    link_results_json = Column(Text, default="{}", nullable=False)
    time_series_json = Column(Text, default="{}", nullable=True)
    is_simulated = Column(Boolean, default=True, nullable=False)


class ScenarioComparisonModel(Base):
    __tablename__ = "scenario_comparisons"

    id = Column(String(64), primary_key=True, index=True)
    baseline_scenario_id = Column(String(64), ForeignKey("simulation_scenarios.id"), nullable=False, index=True)
    comparison_scenario_id = Column(String(64), ForeignKey("simulation_scenarios.id"), nullable=False, index=True)
    delta_total_leakage_m3 = Column(Float, default=0.0, nullable=False)
    delta_water_loss_pct = Column(Float, default=0.0, nullable=False)
    delta_min_pressure_bar = Column(Float, default=0.0, nullable=False)
    affected_nodes_count = Column(Integer, default=0, nullable=False)
    high_risk_links_count = Column(Integer, default=0, nullable=False)
    comparison_matrix_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_simulated = Column(Boolean, default=True, nullable=False)

