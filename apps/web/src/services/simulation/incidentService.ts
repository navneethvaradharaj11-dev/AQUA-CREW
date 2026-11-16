import { SimulatedLeakIncident, LeakSeverity, LeakIncidentStatus } from "./types";
export type { SimulatedLeakIncident };

const SIMULATED_INCIDENTS: SimulatedLeakIncident[] = [
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "INC-2026-081",
    pipelineSegmentId: "PIPE-SEC-4B-92",
    segmentName: "Metro Main Trunk Line B",
    severity: "Critical",
    status: "Investigating",
    detectionTimestamp: "18m ago (2026-11-15 15:42)",
    estimatedLocation: {
      latitude: 40.7128,
      longitude: -74.006,
      depthM: 2.4,
      zone: "Sector 4 (Central Business)",
    },
    estimatedLossRateLph: 680,
    confidenceScorePct: 98.4,
    dominantAcousticFreqHz: 1420,
    assignedRoverId: "ROV-AQUA-01",
    notes: "High acoustic resonance detected by crawler hydrophone. Pressure drop of 4.2 PSI confirmed by downstream transducer PZ-01.",
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "INC-2026-079",
    pipelineSegmentId: "PIPE-IND-1A-04",
    segmentName: "Industrial Park Feeder Line 1",
    severity: "High",
    status: "Confirmed",
    detectionTimestamp: "1h 12m ago (2026-11-15 14:48)",
    estimatedLocation: {
      latitude: 40.7145,
      longitude: -74.0021,
      depthM: 1.8,
      zone: "Sector 1 (East Industrial)",
    },
    estimatedLossRateLph: 420,
    confidenceScorePct: 94.1,
    dominantAcousticFreqHz: 980,
    assignedRoverId: "ROV-AQUA-02",
    notes: "TDOA acoustic cross-correlation locked to valve joint J-14. Repair crew dispatched.",
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "INC-2026-076",
    pipelineSegmentId: "PIPE-RES-3C-11",
    segmentName: "Pinecrest Residential Sub-Branch",
    severity: "Medium",
    status: "Suspected",
    detectionTimestamp: "3h 40m ago (2026-11-15 12:20)",
    estimatedLocation: {
      latitude: 40.7198,
      longitude: -74.0089,
      depthM: 1.2,
      zone: "Sector 3 (North Residential)",
    },
    estimatedLossRateLph: 210,
    confidenceScorePct: 82.5,
    dominantAcousticFreqHz: 620,
    notes: "Night-time minimum flow analysis indicates minor differential anomaly. Scheduled for crawler inspection.",
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "INC-2026-072",
    pipelineSegmentId: "PIPE-HRB-02-19",
    segmentName: "Harbor Marginal Service Line",
    severity: "Low",
    status: "Confirmed",
    detectionTimestamp: "6h 15m ago (2026-11-15 09:45)",
    estimatedLocation: {
      latitude: 40.7091,
      longitude: -74.0115,
      depthM: 3.1,
      zone: "Sector 2 (South Port)",
    },
    estimatedLossRateLph: 110,
    confidenceScorePct: 89.0,
    dominantAcousticFreqHz: 340,
    notes: "Minor seal weeping near flanged valve terminal. Non-urgent work order queued.",
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "INC-2026-068",
    pipelineSegmentId: "PIPE-OLD-01-08",
    segmentName: "Old Canal Junction Cast-Iron Pipe",
    severity: "Critical",
    status: "Repaired",
    detectionTimestamp: "Yesterday (2026-11-14 18:30)",
    estimatedLocation: {
      latitude: 40.716,
      longitude: -74.009,
      depthM: 2.2,
      zone: "Sector 1 (Historic District)",
    },
    estimatedLossRateLph: 950,
    confidenceScorePct: 99.1,
    dominantAcousticFreqHz: 1800,
    notes: "Structural clamp fitted by utility crew. Post-repair acoustic verification certified watertight.",
  },
];

export async function fetchIncidents(filters?: {
  severity?: string;
  status?: string;
}): Promise<SimulatedLeakIncident[]> {
  return SIMULATED_INCIDENTS.filter((item) => {
    if (filters?.severity && filters.severity !== "All" && item.severity !== filters.severity) {
      return false;
    }
    if (filters?.status && filters.status !== "All" && item.status !== filters.status) {
      return false;
    }
    return true;
  });
}

export async function fetchIncidentById(id: string): Promise<SimulatedLeakIncident | null> {
  const incident = SIMULATED_INCIDENTS.find((i) => i.id === id);
  return incident || null;
}

