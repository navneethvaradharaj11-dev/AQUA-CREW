/**
 * AQUA CREW — Unified Incident Intelligence Types (Task 19)
 * Full-stack type definitions for the 10-stage Master Incident Lifecycle.
 */

export type IncidentLifecycleStatus =
  | "DETECTED"
  | "TRIAGED"
  | "INVESTIGATING"
  | "INSPECTION_PROPOSED"
  | "APPROVED"
  | "INSPECTION_IN_PROGRESS"
  | "ASSESSED"
  | "REPAIR_PLANNED"
  | "AWAITING_ENGINEERING_APPROVAL"
  | "SIMULATED_RESOLUTION"
  | "CLOSED";

export type IncidentSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type IncidentPriority = "P1" | "P2" | "P3" | "P4";
export type EvidenceProvenance = "MEASURED" | "SIMULATED" | "DERIVED" | "PREDICTED" | "OPERATOR_ENTERED" | "UNKNOWN";
export type ApprovalType = "INSPECTION_DISPATCH" | "REPAIR_PLAN" | "SIMULATED_RESOLUTION" | "CLOSURE";
export type ApprovalStatus = "PENDING" | "APPROVED" | "REJECTED";

export interface IncidentWorkflowEvent {
  id: string;
  incident_id: string;
  from_status: string;
  to_status: string;
  stage_number: number;
  actor_id: string;
  actor_role: string;
  action: string;
  notes?: string;
  payload?: Record<string, any>;
  timestamp: string;
}

export interface IncidentApproval {
  id: string;
  incident_id: string;
  approval_type: ApprovalType;
  status: ApprovalStatus;
  requested_by: string;
  approved_by?: string;
  approver_role?: string;
  decision_timestamp?: string;
  comments?: string;
  digital_signature?: string;
  created_at: string;
}

export interface UnifiedIncident {
  id: string;
  incident_code: string;
  title: string;
  description?: string;
  category: string;
  severity: IncidentSeverity;
  priority: IncidentPriority;
  lifecycle_status: IncidentLifecycleStatus;

  pipeline_segment_id: string;
  dma_zone?: string;
  latitude: number;
  longitude: number;

  detection_timestamp?: string;
  detection_source: string;
  sensor_ids: string[];

  ai_leak_probability: number;
  ai_confidence: number;
  evidence_provenance: EvidenceProvenance;

  hydraulic_headloss_delta: number;
  estimated_loss_lps: number;
  risk_score: number;

  inspection_mission_id?: string;
  assigned_rover_id?: string;
  inspection_findings?: Record<string, any>;

  repair_plan_id?: string;
  repair_cost_estimate?: number;
  repair_urgency?: string;

  simulation_resolution_data?: Record<string, any>;
  resolution_summary?: string;

  is_simulated: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;

  workflow_events: IncidentWorkflowEvent[];
  approvals: IncidentApproval[];
}

export interface IncidentStatsOverview {
  total_incidents: number;
  active_incidents: number;
  closed_incidents: number;
  critical_incidents: number;
  awaiting_approval_incidents: number;
  total_estimated_water_loss_lps: number;
  by_status: Record<string, number>;
  by_severity: Record<string, number>;
  by_category: Record<string, number>;
}

export interface MasterE2EResult {
  success: boolean;
  incident_id: string;
  incident_code: string;
  lifecycle_status: string;
  total_workflow_events: number;
  total_approvals: number;
  final_resolution_data: Record<string, any>;
  hardware_actuation_blocked: boolean;
  is_simulated: boolean;
}

