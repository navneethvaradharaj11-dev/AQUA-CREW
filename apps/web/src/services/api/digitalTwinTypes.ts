/**
 * TypeScript Interfaces for Digital Twin & Hydraulic Simulation Platform (Task 10 & 10.5)
 */

export interface HydraulicNetwork {
  id: string;
  name: string;
  description: string;
  headloss_formula: string;
  flow_units: string;
  demand_model: string;
  is_active: boolean;
  created_at?: string;
}

export interface NodeResult {
  node_id: string;
  name: string;
  node_type: "JUNCTION" | "RESERVOIR" | "TANK";
  pressure_bar: number;
  pressure_psi: number;
  head_m: number;
  elevation_m: number;
  actual_demand_lps: number;
  expected_demand_lps: number;
  leak_flow_lps: number;
  pressure_deficit: boolean;
  status: "NORMAL" | "DEFICIT" | "BURST" | "CRITICAL_LOW" | "OVERPRESSURE" | "LEAK";
}

export interface LinkResult {
  link_id: string;
  name: string;
  link_type: "PIPE" | "PUMP" | "VALVE";
  flow_lps: number;
  velocity_mps: number;
  headloss_m: number;
  unit_headloss_m_per_km: number;
  friction_factor: number;
  direction: "FORWARD" | "REVERSE" | "ZERO";
  status: "OPEN" | "CLOSED" | "ACTIVE" | "LEAKING" | "BURST";
  pipeline_segment_id?: string;
}

export interface TimeStepResult {
  step_index: number;
  time_offset_hours: number;
  timestamp_iso: string;
  demand_multiplier: number;
  total_supply_lps: number;
  total_demand_lps: number;
  total_leakage_lps: number;
  min_pressure_bar: number;
  max_pressure_bar: number;
  pressure_deficit_nodes: string[];
  node_pressures: Record<string, number>;
  link_flows: Record<string, number>;
}

export interface SimulationRun {
  id: string;
  scenario_id: string;
  network_id: string;
  execution_timestamp: string;
  execution_duration_ms: number;
  converged: boolean;
  iterations: number;
  total_demand_m3: number;
  total_leakage_m3: number;
  water_loss_percentage: number;
  min_pressure_bar: number;
  max_pressure_bar: number;
  pressure_deficit_nodes_count: number;
  summary: {
    solver_name?: string;
    total_supply_lps?: number;
    total_demand_lps?: number;
    total_leakage_lps?: number;
    avg_pressure_bar?: number;
    mass_continuity_residual_lps?: number;
    mass_conserved?: boolean;
    network_version?: string;
  };
  nodes: Record<string, NodeResult>;
  links: Record<string, LinkResult>;
  timesteps: TimeStepResult[];
  is_simulated: boolean;
  source: string;
}

export interface SimulationScenario {
  id: string;
  network_id: string;
  name: string;
  scenario_type: "BASELINE" | "HIGH_DEMAND" | "PIPE_BURST" | "MINOR_LEAK" | "PUMP_TRIP" | "VALVE_FAILURE" | "RECOVERY" | "WHAT_IF" | "WHAT_IF_LEAK";
  description: string;
  is_baseline: boolean;
  duration_hours: number;
  time_step_minutes: number;
  solver_mode: "PDA" | "DDA";
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
  parameters_override: {
    demand_multiplier?: number;
    leaks?: Array<{
      node_id: string;
      area_m2: number;
      discharge_coeff?: number;
      severity?: string;
      pipeline_segment_id?: string;
    }>;
    pipe_overrides?: Record<string, { status: "OPEN" | "CLOSED" }>;
    pump_overrides?: Record<string, { status: "OPEN" | "CLOSED"; speed?: number }>;
  };
  created_at?: string;
}

export interface NodeComparisonDelta {
  node_id: string;
  name: string;
  baseline_pressure_bar: number;
  comparison_pressure_bar: number;
  delta_pressure_bar: number;
  pressure_drop_pct: number;
  baseline_leak_lps: number;
  comparison_leak_lps: number;
  delta_leak_lps: number;
  deficit_introduced: boolean;
}

export interface LinkComparisonDelta {
  link_id: string;
  name: string;
  baseline_flow_lps: number;
  comparison_flow_lps: number;
  delta_flow_lps: number;
  baseline_velocity_mps: number;
  comparison_velocity_mps: number;
  delta_velocity_mps: number;
  is_high_risk: boolean;
}

export interface ScenarioComparison {
  comparison_id: string;
  baseline_scenario_id: string;
  comparison_scenario_id: string;
  baseline_run_id: string;
  comparison_run_id: string;
  delta_total_leakage_m3: number;
  delta_water_loss_pct: number;
  delta_min_pressure_bar: number;
  affected_nodes_count: number;
  high_risk_links_count: number;
  nodes: Record<string, NodeComparisonDelta>;
  links: Record<string, LinkComparisonDelta>;
  is_simulated: boolean;
  source: string;
}

export interface PumpEquipmentStatus {
  id: string;
  name: string;
  status: string;
  speed: number;
  power_kw: number;
  flow_lps: number;
  headloss_m: number;
  efficiency_pct: number;
}

export interface ValveEquipmentStatus {
  id: string;
  name: string;
  valve_type: string;
  setting_bar: number;
  status: string;
  flow_lps: number;
}

export interface TankEquipmentStatus {
  id: string;
  name: string;
  level_m: number;
  min_level_m: number;
  max_level_m: number;
  diameter_m: number;
  volume_pct: number;
  pressure_bar: number;
  status: string;
}

export interface EquipmentStatusBundle {
  network_id: string;
  pumps: PumpEquipmentStatus[];
  valves: ValveEquipmentStatus[];
  tanks: TankEquipmentStatus[];
  is_simulated: boolean;
  source: string;
}

export interface NetworkTopologyBundle {
  network: HydraulicNetwork;
  nodes_count: number;
  links_count: number;
  geojson: {
    type: "FeatureCollection";
    features: Array<{
      type: "Feature";
      id: string;
      geometry: {
        type: "Point" | "LineString";
        coordinates: any;
      };
      properties: Record<string, any>;
    }>;
  };
  solver_data: Record<string, any>;
}

export interface RoverHandoffResponse {
  recommendation_id: string;
  status: string;
  scenario_id: string;
  target_node_id: string;
  target_coordinates: [number, number];
  assigned_rover_id?: string;
  assigned_rover_name?: string;
  suitability_score: number;
  inspection_urgency: string;
  operator_approval_required: boolean;
  notes?: string;
  message: string;
  is_simulated: boolean;
  source: string;
}

export interface ValidationStatus {
  audit_version: string;
  acceptance_version?: string;
  primary_solver: {
    name: string;
    status: string;
    modes_supported: string[];
    fallback_policy: string;
  };
  secondary_solver: {
    name: string;
    status: string;
    scope: string;
  };
  benchmark_summary: {
    name: string;
    status: string;
    max_relative_pressure_error_pct: number;
    max_absolute_flow_error_m3s: number;
    mass_balance_continuity_residual_m3s: number;
    loop_headloss_closure_residual_m: number;
  };
  benchmarks?: {
    net1: {
      name: string;
      nodes_count: number;
      links_count: number;
      status: string;
      max_relative_pressure_error_pct: number;
      max_absolute_flow_error_m3s: number;
      mass_balance_continuity_residual_m3s: number;
      loop_headloss_closure_residual_m: number;
    };
    net3: {
      name: string;
      nodes_count: number;
      links_count: number;
      status: string;
      max_relative_pressure_error_pct: number;
      max_absolute_flow_error_m3s: number;
      mass_balance_continuity_residual_m3s: number;
      loop_headloss_closure_residual_m: number;
    };
  };
  reproducibility?: {
    status: string;
    iterations: number;
    max_head_standard_deviation_m: number;
    max_flow_standard_deviation_m3s: number;
    deterministic: boolean;
  };
  physical_formulations: {
    pipe_friction: string;
    orifice_leakage: string;
    pressure_dependent_demand: string;
    mass_conservation: string;
    energy_conservation: string;
  };
  operational_guardrails: {
    simulation_isolation: string;
    hardware_control_disabled: boolean;
    human_approval_required_for_dispatch: boolean;
    baseline_immutability: boolean;
  };
  is_simulated: boolean;
  source: string;
}

export interface Net1BenchmarkResult {
  benchmark_network: string;
  benchmark_file: string;
  source_provenance: string;
  nodes_count: number;
  links_count: number;
  junctions_count: number;
  tanks_count: number;
  reservoirs_count: number;
  pipes_count: number;
  pumps_count: number;
  valves_count: number;
  execution_duration_ms: number;
  validation_status: string;
  is_validated: boolean;
  loops_evaluated_count?: number;
  tolerances: Record<string, number>;
  metrics: {
    max_absolute_error_pressure_m: number;
    max_relative_error_pressure_pct: number;
    max_absolute_error_head_m: number;
    max_relative_error_head_pct: number;
    max_absolute_error_flow_m3s: number;
    max_relative_error_flow_pct: number;
    max_absolute_error_velocity_mps: number;
    total_inflow_m3s: number;
    total_outflow_m3s: number;
    mass_balance_residual_m3s: number;
    mass_balance_conserved: boolean;
    loop_headloss_closure_residual_m: number;
    energy_balance_conserved: boolean;
  };
  is_simulated: boolean;
  source: string;
}

export type Net3BenchmarkResult = Net1BenchmarkResult;

export interface ReproducibilityBenchmarkResult {
  network_name: string;
  iterations: number;
  deterministic_reproducible: boolean;
  reproducibility_status: string;
  max_head_standard_deviation_m: number;
  max_flow_standard_deviation_m3s: number;
  run_durations_ms: number[];
  mean_execution_duration_ms: number;
  min_execution_duration_ms: number;
  max_execution_duration_ms: number;
  provenance: string;
  is_simulated: boolean;
  source: string;
}
