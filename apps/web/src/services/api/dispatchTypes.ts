/**
 * AQUA CREW — Autonomous Mission Planning & Intelligent Rover Dispatch Types (Task 08)
 */

export interface MissionPriorityAssessment {
  priority_score: number;
  priority_category: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  contributing_factors: Record<string, number>;
  explanation: string;
  recommended_response: string;
  uncertainty_warning?: string | null;
  timestamp: string;
  source_detection_id: string;
}

export interface PipelineRoute {
  start_coordinates: [number, number];
  destination_coordinates: [number, number];
  waypoints: [number, number][];
  segments_traversed: string[];
  total_distance_m: number;
  estimated_travel_time_s: number;
  is_connected: boolean;
  uncertainty_radius_m?: number | null;
}

export interface RoverSuitability {
  rover_id: string;
  rover_name: string;
  operating_state: string;
  battery_percentage: number;
  is_eligible: boolean;
  disqualification_reason?: string | null;
  distance_to_target_m: number;
  estimated_energy_consumption_pct: number;
  battery_reserve_after_pct: number;
  suitability_score: number;
  suitability_explanation: string;
}

export interface MissionRecommendation {
  id: string;
  detection_id: string;
  pipeline_segment_id: string;
  recommended_rover_id: string;
  recommended_rover_name: string;
  priority_score: number;
  priority_category: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  status: "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "CANCELLED";
  route_distance_m: number;
  estimated_duration_s: number;
  estimated_energy_pct: number;
  battery_reserve_after_pct: number;
  destination_lat?: number | null;
  destination_lng?: number | null;
  localization_uncertainty_m?: number | null;
  waypoints: [number, number][];
  segments_traversed: string[];
  contributing_factors: Record<string, any>;
  explanation: string;
  assigned_mission_id?: string | null;
  approved_by?: string | null;
  approved_at?: string | null;
  rejection_reason?: string | null;
  operator_notes?: string | null;
  created_at: string;
  is_simulated: boolean;
  source: string;
}

export interface MissionProgressInfo {
  mission_id: string;
  status: string;
  progress_percentage: number;
  inspected_distance_m: number;
  total_distance_m: number;
  completed_waypoints: number;
  total_waypoints: number;
  start_time: string;
  estimated_completion_time: string;
  is_simulated: boolean;
}

export interface MissionRouteInfo {
  mission_id: string;
  target_segment_id: string;
  assigned_rover_id?: string;
  route_distance_m: number;
  waypoint_count: number;
  waypoints: [number, number][];
  is_simulated: boolean;
}
