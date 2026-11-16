/**
 * AQUA CREW — Predictive Maintenance & Infrastructure Health Types (Task 09)
 */

export interface PipelineHealth {
  id: string;
  pipeline_segment_id: string;
  health_score: number;
  health_category: "EXCELLENT" | "GOOD" | "FAIR" | "POOR" | "CRITICAL";
  acoustic_stability_score: number;
  pressure_stability_score: number;
  flow_stability_score: number;
  moisture_anomaly_score: number;
  data_coverage_pct: number;
  confidence: number;
  contributing_factors: Record<string, number>;
  positive_indicators: string[];
  explanation: string;
  assessed_at: string;
  is_simulated: boolean;
  source: string;
}

export interface PredictiveRisk {
  id: string;
  pipeline_segment_id: string;
  failure_prob_24h: number;
  failure_prob_7d: number;
  failure_prob_30d: number;
  overall_risk_level: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  leak_probability: number;
  burst_rupture_risk: number;
  model_version: string;
  confidence: number;
  uncertainty_margin: number;
  contributing_factors: Record<string, number>;
  risk_explanation: string;
  assessed_at: string;
  is_simulated: boolean;
  source: string;
}

export interface TrendTimePoint {
  timestamp: string;
  day_offset: number;
  health_score: number;
  pressure_bar: number;
  flow_lps: number;
  acoustic_spl_db: number;
}

export interface HistoricalTrend {
  id: string;
  pipeline_segment_id: string;
  trend_direction: "IMPROVING" | "STABLE" | "DETERIORATING" | "RAPIDLY_DETERIORATING" | "INSUFFICIENT_DATA";
  health_slope_per_day: number;
  pressure_variance: number;
  flow_anomaly_rate: number;
  acoustic_emission_count: number;
  historical_leak_count: number;
  window_days: number;
  time_series_points: TrendTimePoint[];
  assessed_at: string;
  is_simulated: boolean;
  source: string;
}

export interface MaintenanceRecommendation {
  id: string;
  pipeline_segment_id: string;
  health_score: number;
  predicted_risk: string;
  urgency: "ROUTINE" | "MEDIUM" | "HIGH" | "CRITICAL";
  recommended_action:
    | "CONTINUE_MONITORING"
    | "INCREASE_SENSOR_MONITORING"
    | "SCHEDULE_ACOUSTIC_INSPECTION"
    | "SCHEDULE_PRESSURE_INSPECTION"
    | "DISPATCH_INSPECTION_ROVER"
    | "PRIORITIZE_HUMAN_INSPECTION"
    | "RECOMMEND_PIPELINE_REPAIR_ASSESSMENT";
  timeframe_days: number;
  status: "PENDING_REVIEW" | "ACKNOWLEDGED" | "DISMISSED" | "DISPATCHED";
  explanation: string;
  sensor_evidence: Record<string, any>;
  operator_notes?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  dispatched_mission_id?: string | null;
  created_at: string;
  is_simulated: boolean;
  source: string;
}

export interface PredictiveMaintenanceOverview {
  total_segments_monitored: number;
  excellent_count: number;
  good_count: number;
  fair_count: number;
  poor_count: number;
  critical_count: number;
  insufficient_data_count: number;
  average_health_score: number;
  high_risk_segment_count: number;
  pending_recommendation_count: number;
  timestamp: string;
  is_simulated: boolean;
}

export interface MaintenanceModelInfo {
  model_name: string;
  model_version: string;
  algorithm: string;
  training_dataset_size: number;
  features: string[];
  accuracy: number;
  f1_score: number;
  roc_auc: number;
  last_evaluated: string;
  is_simulated: boolean;
  source: string;
}
