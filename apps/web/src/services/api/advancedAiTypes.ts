/**
 * TypeScript Definitions for Advanced AI & Decision Intelligence (Task 13)
 */

export type EvidenceClassification =
  | 'MEASURED'
  | 'SIMULATED'
  | 'DERIVED'
  | 'PREDICTED'
  | 'OPERATOR_ENTERED'
  | 'UNKNOWN';

export interface EvidenceItem {
  evidence_id: string;
  source_module: string;
  source_table: string;
  source_record_id: string;
  evidence_type: string;
  classification: EvidenceClassification;
  observed_at?: string | null;
  metric_name: string;
  metric_value?: number | null;
  metric_unit: string;
  summary: string;
  confidence: number;
  validation_status: string;
  age_hours?: number | null;
  is_stale?: boolean;
  calibration_status?: string;
  hardware_connected?: boolean;
  is_simulated: boolean;
  source: string;
}

export interface AIChatRequest {
  conversation_id?: string;
  query: string;
  user_id?: string;
  target_segment_id?: string;
}

export interface AIChatResponse {
  conversation_id: string;
  message_id: string;
  role: string;
  content: string;
  intent: string;
  model_used: string;
  provider_used: string;
  supporting_evidence: EvidenceItem[];
  claims: Array<{ claim: string; verified: boolean }>;
  confidence_assessment: string;
  validation_status: string;
  missing_information?: string | null;
  suggested_queries: string[];
  is_simulated: boolean;
  source: string;
  timestamp: string;
}

export interface AIConversationItem {
  id: string;
  title: string;
  user_id: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  intent?: string;
  model_used: string;
  provider_used: string;
  validation_status: string;
  timestamp: string;
  evidence_references: string[];
  supporting_evidence?: EvidenceItem[];
  claims?: Array<{ claim: string; verified: boolean }>;
}

export interface AIConversationDetail {
  id: string;
  title: string;
  user_id: string;
  messages: ChatMessage[];
}

export interface ProviderStatus {
  configured_provider: string;
  active_provider: string;
  active_model: string;
  is_available: boolean;
  is_fallback: boolean;
  is_live_verified: boolean;
  live_verification_status: string;
  base_url?: string | null;
  api_key_configured: boolean;
  api_key_status: string;
  timeout_seconds: number;
  max_tokens: number;
  temperature: number;
  supported_models: string[];
}

export interface DecisionExplanation {
  entity_type: string;
  entity_id: string;
  primary_classification: string;
  why_explained: string;
  contributing_factors: Record<string, any>;
  model_version: string;
  input_quality_notes: string;
  assumptions_applied: string[];
  limitations: string[];
  supporting_evidence_ids: string[];
}

export interface PipelineComparisonItem {
  segment_id: string;
  name: string;
  material: string;
  diameter_mm: number;
  vulnerability_score: number;
  vulnerability_level: string;
  health_score: number;
  health_category: string;
  incident_count: number;
  pressure_psi: number;
  inspection_priority: number;
  priority_tier: string;
  data_completeness_pct: number;
  recommended_action: string;
}

export interface PipelineComparisonResponse {
  segments: PipelineComparisonItem[];
  comparative_summary: string;
  highest_risk_segment_id: string;
  highest_priority_segment_id: string;
}

export interface OperationalSummaryResponse {
  summary_type: string;
  generated_at: string;
  new_incidents_count: number;
  critical_assets_count: number;
  pending_recommendations_count: number;
  approved_decisions_count: number;
  completed_missions_count: number;
  network_urgency: string;
  narrative_summary: string;
  unresolved_risks: string[];
  recommended_next_actions: string[];
  supporting_evidence_ids: string[];
}

export interface EvidenceGapAnalysis {
  segment_id: string;
  segment_name: string;
  overall_data_completeness_pct: number;
  missing_indicators: string[];
  uncertainty_impact_description: string;
  recommended_sensor_installations: string[];
}

export interface MultiSourceReasoningResult {
  target_segment_id: string;
  target_segment_name: string;
  measured_facts: EvidenceItem[];
  simulated_results: EvidenceItem[];
  derived_metrics: EvidenceItem[];
  predictions: EvidenceItem[];
  temporal_alignment: string;
  supporting_evidence: string[];
  contradictory_evidence: string[];
  missing_evidence: string[];
  supported_conclusions: string[];
  uncertain_hypotheses: string[];
  recommended_investigation: string;
  uncertainty_description: string;
}

