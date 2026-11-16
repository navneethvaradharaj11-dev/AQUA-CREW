/**
 * AQUA CREW — Unified Incident API Client (Task 19)
 * Connects frontend incident views with FastAPI backend `/api/v1/incidents` endpoints.
 * Includes graceful fallback mock data if backend is offline.
 */

import {
  UnifiedIncident,
  IncidentStatsOverview,
  MasterE2EResult,
  ApprovalType,
  IncidentLifecycleStatus,
} from "./incidentTypes";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const FALLBACK_STATS: IncidentStatsOverview = {
  total_incidents: 4,
  active_incidents: 3,
  closed_incidents: 1,
  critical_incidents: 1,
  awaiting_approval_incidents: 2,
  total_estimated_water_loss_lps: 53.4,
  by_status: {
    TRIAGED: 1,
    INSPECTION_PROPOSED: 1,
    AWAITING_ENGINEERING_APPROVAL: 1,
    CLOSED: 1,
  },
  by_severity: {
    CRITICAL: 1,
    HIGH: 1,
    MEDIUM: 1,
    LOW: 1,
  },
  by_category: {
    ACOUSTIC_ANOMALY: 2,
    SUSPECTED_LEAK: 1,
    BURST: 1,
  },
};

const FALLBACK_INCIDENTS: UnifiedIncident[] = [
  {
    id: "INC-2026-0001",
    incident_code: "INC-2026-001",
    title: "Acoustic Anomaly & High Pressure Drop — Metro Trunk B",
    description: "High acoustic energy detected (88.4 dB) correlated with downstream pressure loss on 400mm ductile iron trunk.",
    category: "ACOUSTIC_ANOMALY",
    severity: "HIGH",
    priority: "P1",
    lifecycle_status: "TRIAGED",
    pipeline_segment_id: "PIPE-SEC-4B-92",
    dma_zone: "DMA-METRO-CENTRAL",
    latitude: 40.7128,
    longitude: -74.006,
    detection_timestamp: "2026-11-16T18:30:00Z",
    detection_source: "TELEMETRY_ACOUSTIC",
    sensor_ids: ["SNS-AC-01-A", "SNS-PR-02-A"],
    ai_leak_probability: 0.89,
    ai_confidence: 0.92,
    evidence_provenance: "SIMULATED",
    hydraulic_headloss_delta: 4.25,
    estimated_loss_lps: 12.8,
    risk_score: 78.5,
    is_simulated: true,
    created_by: "SYSTEM_AI_ENGINE",
    created_at: "2026-11-16T18:30:00Z",
    updated_at: "2026-11-16T18:35:00Z",
    workflow_events: [
      {
        id: "IWE-001",
        incident_id: "INC-2026-0001",
        from_status: "NONE",
        to_status: "DETECTED",
        stage_number: 1,
        actor_id: "SYSTEM_AI_ENGINE",
        actor_role: "SYSTEM",
        action: "INCIDENT_DETECTED",
        notes: "Acoustic anomaly detected by IoT sensor node.",
        timestamp: "2026-11-16T18:30:00Z",
      },
      {
        id: "IWE-002",
        incident_id: "INC-2026-0001",
        from_status: "DETECTED",
        to_status: "TRIAGED",
        stage_number: 2,
        actor_id: "SYSTEM_AI_ENGINE",
        actor_role: "SYSTEM",
        action: "AI_TRIAGE_COMPLETED",
        notes: "Automated triage scored high severity and P1 dispatch priority.",
        timestamp: "2026-11-16T18:32:00Z",
      },
    ],
    approvals: [],
  },
  {
    id: "INC-2026-0002",
    incident_code: "INC-2026-002",
    title: "Suspected Lateral Crack — Industrial Feeder Line",
    description: "Acoustic signature matching shear cracking detected during scheduled IoT hydrophone sweep.",
    category: "SUSPECTED_LEAK",
    severity: "MEDIUM",
    priority: "P2",
    lifecycle_status: "INSPECTION_PROPOSED",
    pipeline_segment_id: "PIPE-002",
    dma_zone: "DMA-HARBOR-EAST",
    latitude: 40.716,
    longitude: -73.998,
    detection_timestamp: "2026-11-16T17:00:00Z",
    detection_source: "TELEMETRY_ACOUSTIC",
    sensor_ids: ["SNS-AC-02-B"],
    ai_leak_probability: 0.74,
    ai_confidence: 0.85,
    evidence_provenance: "SIMULATED",
    hydraulic_headloss_delta: 2.1,
    estimated_loss_lps: 6.4,
    risk_score: 62.0,
    inspection_mission_id: "MSN-INSP-2026-02",
    assigned_rover_id: "ROV-001",
    is_simulated: true,
    created_by: "SYSTEM_AI_ENGINE",
    created_at: "2026-11-16T17:00:00Z",
    updated_at: "2026-11-16T17:15:00Z",
    workflow_events: [],
    approvals: [
      {
        id: "APV-002",
        incident_id: "INC-2026-0002",
        approval_type: "INSPECTION_DISPATCH",
        status: "PENDING",
        requested_by: "SYSTEM_DISPATCH_ENGINE",
        comments: "Proposed virtual rover crawl for lateral crack inspection.",
        created_at: "2026-11-16T17:15:00Z",
      },
    ],
  },
  {
    id: "INC-2026-0003",
    incident_code: "INC-2026-003",
    title: "Critical Circumferential Joint Rupture — Uptown Feed",
    description: "Major pressure drop and acoustic burst confirmed via rover video inspection.",
    category: "BURST",
    severity: "CRITICAL",
    priority: "P1",
    lifecycle_status: "AWAITING_ENGINEERING_APPROVAL",
    pipeline_segment_id: "PIPE-003",
    dma_zone: "DMA-UPTOWN-NORTH",
    latitude: 40.725,
    longitude: -74.012,
    detection_timestamp: "2026-11-16T15:45:00Z",
    detection_source: "PRESSURE_TRANSIENT",
    sensor_ids: ["SNS-PR-03-A", "SNS-FL-03-C"],
    ai_leak_probability: 0.96,
    ai_confidence: 0.95,
    evidence_provenance: "SIMULATED",
    hydraulic_headloss_delta: 8.7,
    estimated_loss_lps: 34.2,
    risk_score: 94.0,
    inspection_mission_id: "MSN-INSP-2026-03",
    assigned_rover_id: "ROV-002",
    inspection_findings: {
      visual_defect_type: "CIRCUMFERENTIAL_CRACK",
      crack_width_mm: 4.8,
      crack_length_mm: 180.0,
      corrosion_observed: true,
      inspection_score: 0.95,
    },
    repair_plan_id: "RPR-PLAN-2026-003",
    repair_cost_estimate: 4850.0,
    repair_urgency: "EMERGENCY_24H",
    is_simulated: true,
    created_by: "SYSTEM_AI_ENGINE",
    created_at: "2026-11-16T15:45:00Z",
    updated_at: "2026-11-16T16:20:00Z",
    workflow_events: [],
    approvals: [
      {
        id: "APV-003",
        incident_id: "INC-2026-0003",
        approval_type: "REPAIR_PLAN",
        status: "PENDING",
        requested_by: "SYSTEM_REPAIR_ENGINE",
        comments: "Emergency repair plan proposed for critical circumferential pipe crack.",
        created_at: "2026-11-16T16:20:00Z",
      },
    ],
  },
  {
    id: "INC-2026-0004",
    incident_code: "INC-2026-004",
    title: "Pin-Hole Orifice Leak — Metro Commercial Link",
    description: "Small leak successfully repaired via virtual sleeve clamp; digital twin verified restoration.",
    category: "ACOUSTIC_ANOMALY",
    severity: "LOW",
    priority: "P3",
    lifecycle_status: "CLOSED",
    pipeline_segment_id: "PIPE-001",
    dma_zone: "DMA-METRO-CENTRAL",
    latitude: 40.71,
    longitude: -74.004,
    detection_timestamp: "2026-11-16T12:00:00Z",
    detection_source: "TELEMETRY_ACOUSTIC",
    sensor_ids: ["SNS-AC-01-B"],
    ai_leak_probability: 0.65,
    ai_confidence: 0.88,
    evidence_provenance: "SIMULATED",
    hydraulic_headloss_delta: 0.9,
    estimated_loss_lps: 2.1,
    risk_score: 38.0,
    inspection_mission_id: "MSN-INSP-2026-04",
    assigned_rover_id: "ROV-003",
    repair_plan_id: "RPR-PLAN-2026-004",
    repair_cost_estimate: 1200.0,
    repair_urgency: "SCHEDULED",
    simulation_resolution_data: {
      post_repair_pressure_gain_bar: 0.38,
      leak_flow_eliminated_lps: 2.1,
      hydraulic_stability_verified: true,
    },
    resolution_summary: "Full sleeve clamp installed in simulation. Head loss returned to nominal base curve.",
    is_simulated: true,
    created_by: "OPERATOR-SUPERVISOR-01",
    created_at: "2026-11-16T12:00:00Z",
    updated_at: "2026-11-16T14:30:00Z",
    workflow_events: [],
    approvals: [],
  },
];

export const incidentApiClient = {
  getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("aqua_token") || localStorage.getItem("token");
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }
    return headers;
  },

  async getStatsOverview(): Promise<IncidentStatsOverview> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/incidents/stats/overview`, {
        headers: this.getAuthHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    } catch {
      return FALLBACK_STATS;
    }
  },

  async listIncidents(filters?: {
    status?: string;
    severity?: string;
    category?: string;
    dma_zone?: string;
  }): Promise<{ items: UnifiedIncident[]; total: number }> {
    try {
      const params = new URLSearchParams();
      if (filters?.status) params.append("status", filters.status);
      if (filters?.severity) params.append("severity", filters.severity);
      if (filters?.category) params.append("category", filters.category);
      if (filters?.dma_zone) params.append("dma_zone", filters.dma_zone);

      const url = `${API_BASE}/api/v1/incidents?${params.toString()}`;
      const res = await fetch(url, { headers: this.getAuthHeaders() });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      return { items: data.items, total: data.total };
    } catch {
      let filtered = [...FALLBACK_INCIDENTS];
      if (filters?.status) filtered = filtered.filter((i) => i.lifecycle_status === filters.status);
      if (filters?.severity) filtered = filtered.filter((i) => i.severity === filters.severity);
      if (filters?.category) filtered = filtered.filter((i) => i.category === filters.category);
      if (filters?.dma_zone) filtered = filtered.filter((i) => i.dma_zone === filters.dma_zone);
      return { items: filtered, total: filtered.length };
    }
  },

  async getIncidentById(incidentId: string): Promise<UnifiedIncident | null> {
    try {
      const res = await fetch(`${API_BASE}/api/v1/incidents/${incidentId}`, {
        headers: this.getAuthHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    } catch {
      const found = FALLBACK_INCIDENTS.find(
        (i) => i.id === incidentId || i.incident_code === incidentId
      );
      return found || null;
    }
  },

  async approveIncidentStep(
    incidentId: string,
    payload: {
      approval_type: ApprovalType;
      approved: boolean;
      comments?: string;
    }
  ): Promise<UnifiedIncident> {
    const res = await fetch(`${API_BASE}/api/v1/incidents/${incidentId}/approve`, {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Approval failed with HTTP ${res.status}`);
    }
    return await res.json();
  },

  async executeSimulatedResolution(
    incidentId: string,
    payload: { verification_notes: string }
  ): Promise<UnifiedIncident> {
    const res = await fetch(`${API_BASE}/api/v1/incidents/${incidentId}/simulation-resolution`, {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Simulation resolution failed with HTTP ${res.status}`);
    }
    return await res.json();
  },

  async runMasterE2EScenario(payload?: {
    pipeline_segment_id?: string;
    acoustic_db?: number;
  }): Promise<MasterE2EResult> {
    const res = await fetch(`${API_BASE}/api/v1/incidents/scenarios/master-e2e`, {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(payload || {}),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Master E2E scenario failed with HTTP ${res.status}`);
    }
    return await res.json();
  },

  async resetDemoScenario(): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE}/api/v1/incidents/scenarios/demo-reset`, {
      method: "POST",
      headers: this.getAuthHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Reset demo scenario failed with HTTP ${res.status}`);
    }
    return await res.json();
  },

  async getIncidentReport(incidentId: string): Promise<Record<string, any>> {
    const res = await fetch(`${API_BASE}/api/v1/incidents/${incidentId}/report`, {
      headers: this.getAuthHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to fetch incident report with HTTP ${res.status}`);
    }
    return await res.json();
  },
};

