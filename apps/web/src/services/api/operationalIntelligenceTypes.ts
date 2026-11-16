/**
 * TypeScript Interfaces for Unified Operational Intelligence & Decision Support Platform (Task 12)
 */

export interface OperationalOverview {
  active_incidents_count: number;
  critical_segments_count: number;
  pending_recommendations_count: number;
  approved_actions_count: number;
  active_missions_count: number;
  available_rovers_count: number;
  network_health_score: number;
  network_urgency: "STABLE" | "ROUTINE" | "ELEVATED" | "CRITICAL";
  recommendations_by_category: Record<string, number>;
  latest_assessment: OperationalAssessment | null;
  validation_status: string;
  methodology_version: string;
  is_simulated: boolean;
  source: string;
  actuation_notice: string;
}

export interface OperationalAssessment {
  id: string;
  assessment_name: string;
  total_recommendations: number;
  immediate_action_count: number;
  urgent_leak_count: number;
  preventive_count: number;
  critical_segments_analyzed: number;
  overall_network_urgency: string;
  summary: Record<string, unknown>;
  assessed_at: string | null;
  is_simulated: boolean;
  source: string;
}

export interface OperationalRecommendation {
  id: string;
  assessment_id?: string;
  category: string;
  pipeline_segment_id: string;
  segment_name: string;
  associated_incident_id?: string | null;
  associated_cluster_id?: string | null;
  risk_severity: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  priority_score: number;
  priority_tier: "CRITICAL_IMMEDIATE" | "URGENT" | "HIGH_PRIORITY" | "ROUTINE" | "DEFERRED";
  recommended_action: string;
  action_details?: string | null;
  why_explanation: string;
  what_missing: string;
  expected_impact: string;
  contributing_factors: Record<string, number>;
  evidence_sources: string[];
  resource_requirements: Record<string, unknown>;
  confidence: number;
  data_completeness_pct: number;
  uncertainty_margin: number;
  status: "GENERATED" | "PENDING_REVIEW" | "APPROVED" | "REJECTED" | "EXECUTION_PENDING" | "IN_PROGRESS" | "COMPLETED" | "FAILED" | "CANCELLED";
  approval_status: "PENDING" | "APPROVED" | "REJECTED";
  assigned_rover_id?: string | null;
  dispatched_mission_id?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  expires_at?: string | null;
  is_simulated: boolean;
  source: string;
}

export interface OperationalEvidence {
  id: string;
  recommendation_id: string;
  evidence_type: string;
  source_module: string;
  source_table: string;
  source_record_id: string;
  metric_name: string;
  metric_value?: number | null;
  metric_unit: string;
  confidence_score: number;
  evidence_summary: string;
  payload: Record<string, unknown>;
  recorded_at?: string | null;
  is_simulated: boolean;
  source: string;
}

export interface OperationalImpact {
  id: string;
  recommendation_id: string;
  pipeline_segment_id: string;
  scenario_id?: string | null;
  estimated_water_loss_m3_day: number;
  is_water_loss_measured: boolean;
  service_disruption_risk: "NONE" | "LOW" | "MODERATE" | "SEVERE" | "EXTREME";
  affected_nodes_count: number;
  affected_population_estimate: number;
  hydraulic_headloss_delta_m: number;
  min_pressure_drop_bar: number;
  estimated_inspection_distance_m: number;
  estimated_mission_energy_pct: number;
  estimated_inspection_duration_min: number;
  cost_impact_display: string;
  data_quality_rating: string;
  assumptions: Record<string, unknown>;
  uncertainty_margin_pct: number;
  assessed_at?: string | null;
  is_simulated: boolean;
  source: string;
}

export interface IncidentCorrelation {
  id: string;
  primary_segment_id: string;
  primary_segment_name: string;
  related_segment_id?: string | null;
  incident_ids: string[];
  correlation_type: "CONFIRMED_RELATIONSHIP" | "POTENTIAL_RELATIONSHIP" | "GEOGRAPHIC_COINCIDENCE" | "INSUFFICIENT_EVIDENCE";
  correlation_strength: number;
  uncertainty: number;
  geographic_distance_m?: number | null;
  temporal_delta_hours?: number | null;
  shared_pressure_zone: boolean;
  supporting_evidence: string[];
  explanation: string;
  is_simulated: boolean;
  source: string;
}

export interface RoverSuitability {
  rover_id: string;
  rover_name: string;
  status: string;
  operating_state: string;
  battery_percentage: number;
  motor_temp_c: number;
  distance_to_target_m: number;
  suitability_score: number;
  is_eligible: boolean;
  rejection_reasons: string[];
}

export interface ResourcePlanning {
  recommendation_id: string;
  pipeline_segment_id: string;
  segment_name: string;
  required_capability: string;
  estimated_distance_m: number;
  estimated_energy_pct: number;
  estimated_duration_min: number;
  suitable_rovers: RoverSuitability[];
  best_rover_id?: string | null;
  best_rover_name?: string | null;
  dispatch_feasibility: "READY_FOR_DISPATCH" | "NO_ROVER_AVAILABLE" | "RESOURCE_CONFLICT" | "LOW_BATTERY_WARNING";
  workforce_status: string;
  inventory_status: string;
}

export interface OperationalDecisionRecord {
  id: string;
  recommendation_id: string;
  decision_type: "APPROVED" | "REJECTED";
  decision_reason: string;
  operator_id: string;
  operator_name: string;
  override_priority?: number | null;
  allocated_resource_id?: string | null;
  resulting_mission_id?: string | null;
  decision_timestamp: string;
  audit_hash?: string | null;
  is_simulated: boolean;
  source: string;
}

export interface OperationalExecutionRecord {
  id: string;
  recommendation_id: string;
  decision_id?: string | null;
  mission_id?: string | null;
  assigned_rover_id?: string | null;
  execution_stage: string;
  start_time?: string | null;
  end_time?: string | null;
  distance_inspected_m: number;
  energy_consumed_pct: number;
  findings_summary?: string | null;
  leak_confirmed?: boolean | null;
  last_updated_at?: string | null;
}

