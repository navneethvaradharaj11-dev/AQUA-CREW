/**
 * AQUA CREW — Hydraulic Network Optimization Types (Task 14)
 * Type definitions for multi-objective optimization, decision variables,
 * Pareto trade-off points, baseline comparisons, and human-in-the-loop approvals.
 */

export type ObjectiveProfile =
  | 'BALANCED_OPERATION'
  | 'ENERGY_EFFICIENCY'
  | 'LEAKAGE_REDUCTION'
  | 'PRESSURE_STABILITY';

export type VariableComponentType = 'PUMP' | 'PRV' | 'VALVE' | 'TANK';

export interface DecisionVariable {
  id: string;
  component_type: VariableComponentType;
  component_id: string;
  parameter_name: string;
  baseline_value: number;
  recommended_value: number;
  min_value: number;
  max_value: number;
  unit: string;
  description: string;
}

export interface ObjectiveWeights {
  water_loss_weight: number;
  pump_energy_weight: number;
  pressure_deficit_weight: number;
  operational_cost_weight: number;
}

export interface OptimizationConstraints {
  min_pressure_m: number;
  max_pressure_m: number;
  max_velocity_mps: number;
  min_demand_satisfaction_ratio: number;
  tank_min_level_m: number;
  tank_max_level_m: number;
  max_pump_switches_per_day: number;
}

export interface HydraulicCandidateMetrics {
  water_loss_lps: number;
  pump_power_kw: number;
  pressure_deficit_m: number;
  demand_satisfaction_ratio: number;
  max_velocity_mps: number;
  min_junction_pressure_m: number;
  max_junction_pressure_m: number;
  operational_cost_usd_per_day?: number | null;
}

export interface OptimizationCandidate {
  id: string;
  job_id: string;
  candidate_index: number;
  is_pareto_optimal: boolean;
  is_hydraulically_verified: boolean;
  decision_variables: DecisionVariable[];
  metrics: HydraulicCandidateMetrics;
  tradeoff_explanation: string;
  verification_status: 'VERIFIED' | 'REJECTED' | 'WARNING';
  verification_violations?: string[];
}

export interface BaselineComparison {
  baseline_water_loss_lps: number;
  optimal_water_loss_lps: number;
  water_loss_reduction_pct: number;
  water_loss_reduction_lps: number;
  baseline_pump_power_kw: number;
  optimal_pump_power_kw: number;
  energy_savings_pct: number;
  energy_savings_kw: number;
  baseline_pressure_deficit_m: number;
  optimal_pressure_deficit_m: number;
  pressure_deficit_reduction_pct: number;
  demand_satisfaction_maintained: boolean;
  cost_reduction_available: boolean;
  cost_reduction_usd_per_day?: number | null;
}

export interface OptimizationJobDetail {
  id: string;
  network_id: string;
  objective_profile: ObjectiveProfile;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  progress_pct: number;
  created_at: string;
  completed_at?: string | null;
  scenarios_evaluated: number;
  pareto_candidate_count: number;
  selected_candidate_id?: string | null;
  comparison?: BaselineComparison | null;
  candidates: OptimizationCandidate[];
  pareto_candidates: OptimizationCandidate[];
  recommended_candidate?: OptimizationCandidate | null;
}

export interface OptimizationStatusResponse {
  status: string;
  engine: string;
  active_jobs: number;
  completed_jobs: number;
  default_network: string;
  supported_profiles: string[];
  hardware_actuation_disabled: boolean;
}

export interface OptimizationTriggerRequest {
  network_id?: string;
  objective_profile?: ObjectiveProfile;
  scenario?: string;
  custom_weights?: Partial<ObjectiveWeights>;
  constraints?: Partial<OptimizationConstraints>;
}

export interface OptimizationRecommendRequest {
  candidate_id: string;
  operator_notes?: string;
}

