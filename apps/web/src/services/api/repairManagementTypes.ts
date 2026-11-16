/**
 * AQUA CREW — TypeScript Interfaces for Repair Planning & Management System (Task 16)
 */

export type DamageCategory =
  | 'PIPE_LEAK'
  | 'PIPE_BURST'
  | 'JOINT_FAILURE'
  | 'CORROSION'
  | 'STRUCTURAL_CRACK'
  | 'PRESSURE_DAMAGE'
  | 'VALVE_FAILURE'
  | 'UNKNOWN_DAMAGE';

export type DamageSeverity = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | 'UNDETERMINED';

export type RepairMethodType =
  | 'CLAMP_REPAIR'
  | 'JOINT_REPAIR_REPLACEMENT'
  | 'PIPE_SECTION_REPLACEMENT'
  | 'INTERNAL_LINING_REHABILITATION'
  | 'CORROSION_PROTECTION'
  | 'VALVE_REPLACEMENT'
  | 'PRESSURE_MANAGEMENT'
  | 'FURTHER_INSPECTION_REQUIRED';

export type RepairWorkflowStatus =
  | 'INSPECTION_COMPLETED'
  | 'DAMAGE_ASSESSED'
  | 'REPAIR_RECOMMENDED'
  | 'ENGINEERING_REVIEW_PENDING'
  | 'APPROVED'
  | 'RESOURCE_PLANNED'
  | 'SCHEDULED'
  | 'REPAIR_IN_PROGRESS'
  | 'REPAIR_COMPLETED'
  | 'VERIFICATION_PENDING'
  | 'VERIFIED'
  | 'CLOSED'
  | 'REJECTED'
  | 'ON_HOLD'
  | 'FAILED'
  | 'REQUIRES_REINSPECTION';

export type VerificationOutcome =
  | 'VERIFIED_SUCCESS'
  | 'PARTIALLY_VERIFIED'
  | 'VERIFICATION_FAILED'
  | 'REQUIRES_REINSPECTION'
  | 'INSUFFICIENT_EVIDENCE';

export type EvidenceClassification =
  | 'MEASURED'
  | 'SIMULATED'
  | 'DERIVED'
  | 'PREDICTED'
  | 'OPERATOR_ENTERED'
  | 'UNKNOWN';

export type ResourceCategory =
  | 'MATERIALS'
  | 'EQUIPMENT'
  | 'TOOLS'
  | 'SAFETY'
  | 'COATINGS'
  | 'VALVES'
  | 'JOINTS_COUPLINGS';

export interface SupportingEvidenceItem {
  evidence_id: string;
  source_subsystem: string;
  classification: EvidenceClassification;
  metric_name: string;
  metric_value: any;
  description: string;
  confidence: number;
  observed_at?: string | null;
}

export interface DamageAssessment {
  id: string;
  pipeline_segment_id: string;
  segment_name: string;
  source_inspection_report_id?: string | null;
  damage_category: DamageCategory;
  severity: DamageSeverity;
  pipe_material: string;
  pipe_diameter_mm: number;
  pipe_age_years?: number | null;
  nominal_pressure_psi: number;
  estimated_water_loss_lph: number;
  structural_vulnerability_score: number;
  previous_repair_count: number;
  inspection_confidence: number;
  evidence_completeness_pct: number;
  missing_information: string[];
  engineering_review_required: boolean;
  supporting_evidence: SupportingEvidenceItem[];
  assessment_notes: string;
  assessed_by: string;
  assessed_at: string;
  is_simulated: boolean;
}

export interface RepairMethodOption {
  method: RepairMethodType;
  method_name: string;
  is_recommended: boolean;
  feasibility_score: number;
  rationale: string;
  applicable_damage_types: DamageCategory[];
  material_compatibility: string[];
  min_diameter_mm: number;
  max_diameter_mm: number;
  max_pressure_psi: number;
  operational_constraints: string[];
  advantages: string[];
  limitations: string[];
  required_equipment: string[];
  estimated_duration_hours: number;
  risks_and_uncertainties: string[];
  standards_references: string[];
  required_professional_approvals: string[];
}

export interface RepairRecommendation {
  id: string;
  damage_assessment_id: string;
  pipeline_segment_id: string;
  primary_recommended_method: RepairMethodType;
  secondary_alternative_method?: RepairMethodType | null;
  all_evaluated_options: RepairMethodOption[];
  engineering_rationale: string;
  urgency_tier: 'IMMEDIATE' | 'URGENT' | 'PLANNED' | 'ROUTINE' | 'FURTHER_MONITORING';
  requires_isolation: boolean;
  bypass_pumping_needed: boolean;
  traffic_disruption_level: 'NONE' | 'LOW' | 'MODERATE' | 'SEVERE';
  status: 'PROPOSED' | 'ACCEPTED' | 'MODIFIED' | 'REJECTED';
  created_at: string;
  is_simulated: boolean;
}

export interface RepairResourceItem {
  resource_id: string;
  name: string;
  category: ResourceCategory;
  unit: string;
  estimated_quantity: number;
  compatibility_requirements: string;
  availability_status: 'IN_STOCK' | 'SHORT_LEAD_TIME' | 'EXTENDED_LEAD_TIME' | 'UNKNOWN';
  estimated_unit_cost_usd: number;
  total_cost_usd: number;
  supplier_info: string;
  cost_data_source: EvidenceClassification;
  cost_data_timestamp: string;
}

export interface ResourcePlan {
  id: string;
  repair_plan_id: string;
  items: RepairResourceItem[];
  total_materials_cost_usd: number;
  total_equipment_cost_usd: number;
  all_resources_available: boolean;
  procurement_lead_time_days: number;
  created_at: string;
}

export interface CostComponent {
  component_name: string;
  amount_usd: number;
  formula: string;
  input_values: Record<string, any>;
  units: string;
  assumptions: string;
  uncertainty_range_pct: number;
  provenance: EvidenceClassification;
}

export interface RepairCostEstimate {
  id: string;
  damage_assessment_id: string;
  pipeline_segment_id: string;
  components: CostComponent[];
  total_material_cost_usd: number;
  total_equipment_cost_usd: number;
  total_labour_cost_usd: number;
  inspection_cost_usd: number;
  estimated_water_loss_cost_usd: number;
  restoration_cost_usd: number;
  contingency_cost_usd: number;
  total_estimated_cost_usd: number;
  estimated_downtime_hours: number;
  cost_uncertainty_lower_bound_usd: number;
  cost_uncertainty_upper_bound_usd: number;
  financial_disclaimer: string;
  created_at: string;
  is_simulated: boolean;
}

export interface RepairPriority {
  pipeline_segment_id: string;
  repair_priority_score: number;
  priority_category: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  contributing_factors: Record<string, number>;
  uncertainty_margin: number;
  recommended_response_time_hours: number;
  escalation_requirements: string[];
  calculated_at: string;
}

export interface RepairScheduleItem {
  schedule_id: string;
  repair_plan_id: string;
  crew_id: string;
  crew_name: string;
  scheduled_start: string;
  scheduled_end: string;
  estimated_duration_hours: number;
  travel_distance_km: number;
  travel_time_hours: number;
  has_schedule_conflicts: boolean;
  schedule_conflict_details?: string | null;
  scheduling_notes: string;
}

export interface RepairPlan {
  id: string;
  plan_name: string;
  pipeline_segment_id: string;
  segment_name: string;
  damage_assessment_id: string;
  repair_recommendation_id: string;
  selected_method: RepairMethodType;
  workflow_status: RepairWorkflowStatus;
  priority: RepairPriority;
  resources?: ResourcePlan | null;
  cost_estimate?: RepairCostEstimate | null;
  schedule?: RepairScheduleItem | null;
  approved_by?: string | null;
  approved_at?: string | null;
  rejection_reason?: string | null;
  operator_notes?: string | null;
  digital_twin_scenario_id?: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  is_simulated: boolean;
}

export interface DigitalTwinRepairScenario {
  scenario_id: string;
  repair_plan_id: string;
  pipeline_segment_id: string;
  baseline_pressure_bar: number;
  pre_repair_pressure_bar: number;
  post_repair_pressure_bar: number;
  baseline_leakage_m3: number;
  pre_repair_leakage_m3: number;
  post_repair_leakage_m3: number;
  water_loss_reduction_pct: number;
  pressure_restoration_pct: number;
  pump_energy_delta_kwh: number;
  demand_satisfaction_pct: number;
  simulation_solver: string;
  is_simulated: boolean;
}

export interface DigitalTwinRepairComparison {
  repair_plan_id: string;
  scenario_comparison_id: string;
  baseline_scenario_id: string;
  pre_repair_scenario_id: string;
  post_repair_scenario_id: string;
  summary_metrics: Record<string, number>;
  link_differences: Array<Record<string, any>>;
  node_differences: Array<Record<string, any>>;
  hydraulic_benefit_score: number;
}

export interface RepairVerification {
  id: string;
  repair_plan_id: string;
  pipeline_segment_id: string;
  verification_outcome: VerificationOutcome;
  pre_repair_leakage_lph: number;
  post_repair_leakage_lph: number;
  leakage_reduction_pct: number;
  acoustic_anomaly_cleared: boolean;
  pressure_gradient_restored: boolean;
  remaining_uncertainty_pct: number;
  supporting_evidence: SupportingEvidenceItem[];
  verified_by: string;
  verified_at: string;
  tamper_proof_hash: string;
  is_simulated: boolean;
}

export interface RepairOverviewSummary {
  system_status: string;
  active_assessments_count: number;
  pending_engineering_reviews_count: number;
  approved_plans_count: number;
  scheduled_repairs_count: number;
  in_progress_repairs_count: number;
  completed_verifications_count: number;
  total_water_loss_prevented_m3: number;
  total_repair_expenditure_usd: number;
  supported_damage_categories: string[];
  supported_repair_methods: string[];
  is_simulated: boolean;
}

export interface RepairWorkflowEvent {
  id: string;
  repair_plan_id: string;
  from_status: string;
  to_status: string;
  changed_by: string;
  reason: string;
  details: Record<string, any>;
  timestamp: string;
}

