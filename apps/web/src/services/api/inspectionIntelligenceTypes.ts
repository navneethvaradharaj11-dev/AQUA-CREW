/**
 * AQUA CREW — Autonomous Inspection Intelligence TypeScript Contracts (Task 15)
 */

export type EvidenceClassification =
  | "MEASURED"
  | "SIMULATED"
  | "DERIVED"
  | "PREDICTED"
  | "OPERATOR_ENTERED"
  | "UNKNOWN";

export type PriorityCategory = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

export type InspectionMethod =
  | "ACOUSTIC_CORRELATION"
  | "VISUAL_CCTV"
  | "THERMAL_INFRARED"
  | "MULTI_SENSOR_CRAWLER"
  | "ULTRASONIC_THICKNESS";

export type HumanApprovalStatus =
  | "PENDING_APPROVAL"
  | "APPROVING"
  | "APPROVED"
  | "REJECTED"
  | "EXPIRED";

export type ExecutionStatus =
  | "SCHEDULED"
  | "IN_PROGRESS"
  | "ADAPTED"
  | "COMPLETED"
  | "ABORTED_LOW_BATTERY"
  | "ABORTED_SENSOR_FAULT"
  | "ABORTED_COMMS_LOSS"
  | "EMERGENCY_STOP";

export interface SupportingEvidenceItem {
  evidence_id: string;
  source_subsystem: string;
  classification: EvidenceClassification;
  metric_name: string;
  metric_value: unknown;
  description: string;
  confidence: number;
  observed_at?: string | null;
}

export interface InspectionRecommendation {
  id: string;
  pipeline_segment_id: string;
  segment_name: string;
  priority_score: number;
  priority_category: PriorityCategory;
  urgency_factors: Record<string, number>;
  supporting_evidence: SupportingEvidenceItem[];
  primary_classification: EvidenceClassification;
  confidence: number;
  uncertainty_radius_m: number;
  recommended_method: InspectionMethod;
  estimated_duration_minutes: number;
  required_rover_capabilities: string[];
  recommended_action: string;
  human_approval_status: HumanApprovalStatus;
  rejection_reason?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  created_at: string;
  is_simulated: boolean;
}

export interface RoverSuitability {
  rover_id: string;
  rover_name: string;
  is_eligible: boolean;
  suitability_score: number;
  battery_percentage: number;
  projected_battery_drain_pct: number;
  projected_battery_reserve_pct: number;
  has_safe_return_reserve: boolean;
  motor_temperature_c: number;
  sensor_capabilities: string[];
  capability_match: boolean;
  operating_state: string;
  connection_status: string;
  distance_to_target_m: number;
  estimated_travel_time_s: number;
  disqualification_reasons: string[];
}

export interface InspectionPlanTarget {
  target_id: string;
  pipeline_segment_id: string;
  target_coordinates: [number, number];
  inspection_method: InspectionMethod;
  priority_score: number;
  estimated_duration_minutes: number;
}

export interface MultiRoverAllocationItem {
  rover_id: string;
  rover_name: string;
  assigned_targets: InspectionPlanTarget[];
  route_waypoints: [number, number][];
  segments_traversed: string[];
  total_route_distance_m: number;
  estimated_mission_duration_s: number;
  estimated_battery_drain_pct: number;
  projected_reserve_after_return_pct: number;
  return_to_base_feasible: boolean;
  route_selection_reason: string;
}

export interface InspectionPlan {
  id: string;
  plan_name: string;
  allocations: MultiRoverAllocationItem[];
  unreachable_targets: string[];
  conflict_checks_passed: boolean;
  total_rovers_assigned: number;
  total_targets_covered: number;
  human_approval_status: HumanApprovalStatus;
  rejection_reason?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  created_at: string;
  is_simulated: boolean;
}

export interface SimulatedSensorObservation {
  observation_id: string;
  timestamp: string;
  rover_id: string;
  segment_id: string;
  distance_along_pipe_m: number;
  sensor_type: string;
  reading_value: number;
  unit: string;
  anomaly_detected: boolean;
  classification: EvidenceClassification;
}

export interface InspectionExecutionProgress {
  mission_id: string;
  rover_id: string;
  plan_id: string;
  status: ExecutionStatus;
  current_step: number;
  total_steps: number;
  progress_percentage: number;
  current_coordinates: [number, number];
  distance_traversed_m: number;
  remaining_distance_m: number;
  battery_percentage: number;
  motor_temp_c: number;
  active_anomalies_detected: number;
  route_adapted: boolean;
  adaptation_history: Array<{
    timestamp: string;
    reason: string;
    detour_distance_m: number;
    new_target_coordinates: [number, number];
    projected_reserve_pct: number;
  }>;
  recent_observations: SimulatedSensorObservation[];
  last_updated: string;
  is_simulated: boolean;
}

export interface InspectionReport {
  id: string;
  plan_id: string;
  mission_id: string;
  rover_id: string;
  pipeline_segment_id: string;
  segment_name: string;
  inspection_method: InspectionMethod;
  start_time: string;
  completion_time: string;
  route_distance_m: number;
  inspected_distance_m: number;
  sensor_observations_count: number;
  detected_anomalies: Array<Record<string, unknown>>;
  evidence_provenance: EvidenceClassification;
  ai_classification?: {
    acoustic_leak_probability?: number;
    confidence?: number;
    estimated_leak_orifice_mm?: number;
  } | null;
  updated_infrastructure_risk: number;
  inspection_outcome: "SUCCESS" | "PARTIAL" | "ABORTED";
  unresolved_uncertainties: string[];
  recommended_next_action: string;
  operator_review_status: "PENDING_REVIEW" | "REVIEWED" | "ACTION_APPROVED";
  reviewed_by?: string | null;
  operator_notes?: string | null;
  created_at: string;
  is_simulated: boolean;
}
