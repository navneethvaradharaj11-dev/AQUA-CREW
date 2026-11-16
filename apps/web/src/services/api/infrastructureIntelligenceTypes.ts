/**
 * AQUA CREW — Infrastructure Intelligence & Geospatial Risk Prediction Types (Task 11)
 */

export interface FactorDetail {
  score: number;
  weight: number;
  weighted_contribution: number;
  reasons: string[];
}

export interface ContributingFactorsBreakdown {
  hydraulic?: FactorDetail;
  structural?: FactorDetail;
  incident?: FactorDetail;
  environmental?: FactorDetail;
}

export interface PipelineVulnerabilityItem {
  id: string;
  pipeline_segment_id: string;
  segment_name: string;
  material: string;
  diameter_mm: number;
  length_m: number;
  pressure_zone_id: string;
  category: string;
  vulnerability_score: number;
  vulnerability_level: "VERY_LOW" | "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  hydraulic_score: number;
  structural_score: number;
  incident_score: number;
  environmental_score: number;
  contributing_factors: ContributingFactorsBreakdown;
  confidence: number;
  data_completeness_pct: number;
  uncertainty_margin: number;
  deterioration_rate_per_day: number;
  trend_direction: "DETERIORATING" | "STABLE" | "IMPROVING";
  active_incident_count: number;
  midpoint_lat?: number | null;
  midpoint_lng?: number | null;
  assessed_at?: string | null;
  is_simulated: boolean;
}

export interface PipelineVulnerabilityListResponse {
  total: number;
  limit: number;
  offset: number;
  items: PipelineVulnerabilityItem[];
}

export interface ConfidenceInterval {
  lower_bound: number;
  upper_bound: number;
}

export interface PredictiveForecastDetail {
  projected_risk_24h: number;
  projected_risk_7d: number;
  projected_risk_30d: number;
  trend_24h_delta: number;
  trend_7d_delta: number;
  trend_30d_delta: number;
  primary_risk_drivers: string[];
  mitigation_urgency: "IMMEDIATE" | "SHORT_TERM" | "PLANNED" | "ROUTINE";
  hydraulic_deficit_flag: boolean;
  cluster_proximity_m: number;
}

export interface InspectionPriorityItem {
  id: string;
  pipeline_segment_id: string;
  segment_name: string;
  priority_score: number;
  priority_level: "CRITICAL_IMMEDIATE" | "HIGH_PRIORITY" | "ROUTINE_SCHEDULED" | "MONITORING_ONLY";
  status: "PENDING" | "ACKNOWLEDGED" | "DISPATCHED" | "DISMISSED";
  target_latitude: number;
  target_longitude: number;
  reasons: string[];
  suggested_action: string;
  assigned_rover_id?: string | null;
  mission_recommendation_id?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  operator_notes?: string | null;
  dismissal_reason?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  is_simulated: boolean;
}

export interface SegmentDeepDiveResponse {
  pipeline_segment_id: string;
  segment_name: string;
  material: string;
  diameter_mm: number;
  length_m: number;
  pressure_zone_id: string;
  category: string;
  vulnerability_score: number;
  vulnerability_level: "VERY_LOW" | "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  hydraulic_score: number;
  structural_score: number;
  incident_score: number;
  environmental_score: number;
  contributing_factors: ContributingFactorsBreakdown;
  confidence: number;
  data_completeness_pct: number;
  uncertainty_margin: number;
  deterioration_rate_per_day: number;
  trend_direction: "DETERIORATING" | "STABLE" | "IMPROVING";
  active_incident_count: number;
  midpoint_lat?: number | null;
  midpoint_lng?: number | null;
  assessed_at?: string | null;
  predictive_forecast?: PredictiveForecastDetail | null;
  inspection_priority?: InspectionPriorityItem | null;
  is_simulated: boolean;
  source: string;
}

export interface SpatialClusterItem {
  id: string;
  cluster_name: string;
  zone_id: string;
  centroid_lat: number;
  centroid_lng: number;
  radius_m: number;
  incident_count: number;
  dominant_material: string;
  average_severity: number;
  cluster_risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  affected_segment_ids: string[];
  hotspot_intensity: number;
  is_active: boolean;
  identified_at?: string | null;
  is_simulated: boolean;
}

export interface GeographicRiskZoneItem {
  id: string;
  zone_code: string;
  zone_name: string;
  description?: string | null;
  total_segments: number;
  total_length_km: number;
  avg_vulnerability_score: number;
  dominant_risk_level: string;
  critical_segment_count: number;
  active_clusters_count: number;
  avg_pressure_psi: number;
  bounds?: any;
  updated_at?: string | null;
  is_simulated: boolean;
}

export interface HeatmapPointItem {
  latitude: number;
  longitude: number;
  weight: number;
  segment_id: string;
  risk_level: string;
  score: number;
  point_type: string;
}

export interface TemporalTrendItem {
  pipeline_segment_id: string;
  segment_name: string;
  vulnerability_score: number;
  trend_direction: "DETERIORATING" | "STABLE" | "IMPROVING";
  deterioration_rate_per_day: number;
  trend_24h_delta: number;
  trend_7d_delta: number;
  trend_30d_delta: number;
  rapid_degradation: boolean;
}

export interface PredictionItem {
  pipeline_segment_id: string;
  segment_name: string;
  current_vulnerability_score: number;
  risk_level: string;
  projected_risk_24h: number;
  projected_risk_7d: number;
  projected_risk_30d: number;
  trend_24h_delta: number;
  trend_7d_delta: number;
  trend_30d_delta: number;
  primary_risk_drivers: string[];
  mitigation_urgency: "IMMEDIATE" | "SHORT_TERM" | "PLANNED" | "ROUTINE";
  hydraulic_deficit_flag: boolean;
  cluster_proximity_m: number;
}

export interface InfrastructureOverviewResponse {
  total_segments_analyzed: number;
  critical_segments_count: number;
  high_risk_segments_count: number;
  moderate_risk_segments_count: number;
  low_risk_segments_count: number;
  average_network_vulnerability: number;
  network_deterioration_rate: number;
  deteriorating_segments_count: number;
  active_clusters_count: number;
  pending_inspections_count: number;
  highest_risk_segment?: {
    id: string;
    name: string;
    score: number;
    level: string;
    material: string;
  } | null;
  highest_risk_zone?: {
    code: string;
    name: string;
    avg_score: number;
    critical_count: number;
  } | null;
  validation_status?: string;
  methodology_version?: string;
  configured_risk_weights?: {
    hydraulic: number;
    structural: number;
    incident: number;
    environmental: number;
  };
  last_updated: string;
  is_fallback?: boolean;
  is_simulated: boolean;
  source: string;
}

export interface InspectionDispatchResponse {
  status: string;
  priority_record_id: string;
  pipeline_segment_id: string;
  mission_recommendation_id: string;
  assigned_rover_id: string;
  assigned_rover_name: string;
  planned_route_distance_m: number;
  operator_approval_required: boolean;
  recommendation_status: string;
  message: string;
}

