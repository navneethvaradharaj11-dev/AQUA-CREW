/**
 * AQUA CREW — AI Leak Detection & Acoustic Intelligence Types
 * Strictly software-first simulation and explainable ML contracts.
 */

export type LeakClassification =
  | "NORMAL"
  | "LOW_LEAK_PROBABILITY"
  | "MEDIUM_LEAK_PROBABILITY"
  | "HIGH_LEAK_PROBABILITY";

export type RiskLevel =
  | "CRITICAL"
  | "HIGH"
  | "MODERATE"
  | "LOW"
  | "NEGLIGIBLE";

export type DetectionStatus =
  | "PENDING_REVIEW"
  | "INVESTIGATING"
  | "VERIFIED_BY_OPERATOR"
  | "FALSE_POSITIVE"
  | "REPAIR_SCHEDULED";

export type AcousticScenario =
  | "NORMAL_FLOW"
  | "MINOR_LEAK"
  | "MODERATE_LEAK"
  | "MAJOR_LEAK"
  | "ENVIRONMENTAL_NOISE"
  | "PRESSURE_FLUCTUATION"
  | "MECHANICAL_VIBRATION";

export interface AiDetection {
  id: string;
  pipeline_segment_id: string;
  anomaly_score: number;
  classification: LeakClassification;
  confidence: number;
  risk_level: RiskLevel;
  estimated_loss_lph: number;
  estimated_latitude?: number | null;
  estimated_longitude?: number | null;
  localization_uncertainty_m?: number | null;
  localization_quality?: string | null;
  status: DetectionStatus;
  contributing_features: Record<string, number>;
  risk_explanation: string;
  model_version: string;
  created_at: string;
  is_simulated: boolean;
  source: string;
}

export interface SyntheticWaveformResponse {
  scenario: string;
  duration_sec: number;
  sampling_rate_hz: number;
  rms_amplitude: number;
  peak_amplitude: number;
  dominant_frequency_hz: number;
  spectral_centroid_hz: number;
  spectral_bandwidth_hz: number;
  snr_db: number;
  time_series: number[];
  frequency_spectrum: { frequency_hz: number; magnitude: number }[];
  is_simulated: boolean;
  source: string;
}

export interface AiModelInfo {
  id: string;
  name: string;
  algorithm: string;
  version: string;
  classes?: string[];
  purpose?: string;
  features_used?: number;
  is_active: boolean;
}

export interface AiModelMetrics {
  model_version: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  confusion_matrix: {
    normal: { normal: number; leak: number };
    leak: { normal: number; leak: number };
  };
  training_samples: number;
  testing_samples: number;
  classes: string[];
  is_simulated: boolean;
  provenance: string;
}

export interface AiHealth {
  status: string;
  models_loaded: number;
  active_classifier: string;
  total_detections: number;
  pending_reviews: number;
  sensor_readings_ingested: number;
  is_simulated: boolean;
  provenance: string;
}

export interface LeakAnalyzeRequest {
  pipeline_segment_id: string;
  acoustic_spl_db?: number;
  dominant_freq_hz?: number;
  pressure_bar?: number;
  flow_rate_m3h?: number;
  ground_moisture_pct?: number;
  acoustic_scenario?: AcousticScenario;
}

