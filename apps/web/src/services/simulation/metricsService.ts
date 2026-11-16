import { DashboardKpis, WaterNetworkOverview } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchDashboardKpis(): Promise<DashboardKpis> {
  const fallback: DashboardKpis = {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    totalPipelineLengthKm: 348.6,
    detectedLeakIncidentsCount: 4,
    activeRoversCount: 3,
    totalRoversCount: 5,
    connectedSensorsCount: 184,
    totalSensorsCount: 190,
    estimatedWaterLossLph: 1420,
    activeInspectionMissionsCount: 2,
  };

  try {
    const res = await fetch(`${API_BASE}/api/v1/incidents/stats/overview`, {
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
    });
    if (res.ok) {
      const stats = await res.json();
      return {
        ...fallback,
        source: "VIRTUAL_SIMULATION_ENGINE",
        simulatedAt: new Date().toISOString(),
        detectedLeakIncidentsCount: stats.active_incidents ?? fallback.detectedLeakIncidentsCount,
        estimatedWaterLossLph: Math.round((stats.total_estimated_water_loss_lps ?? 0) * 3600) || fallback.estimatedWaterLossLph,
      };
    }
  } catch {
    // Graceful fallback to simulated values if backend is unreachable
  }

  return fallback;
}

export async function fetchNetworkOverview(): Promise<WaterNetworkOverview> {
  return {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    totalSegments: 1240,
    monitoredSegments: 1185,
    segmentsRequiringInspection: 14,
    criticalSegments: 3,
    networkHealthPercentage: 96.4,
    averagePressurePsi: 58.2,
    activePressureZones: [
      { zoneId: "PZ-01", name: "Metro Central High-Pressure", pressurePsi: 64.1, status: "Nominal" },
      { zoneId: "PZ-02", name: "Eastern Industrial Sector", pressurePsi: 59.8, status: "Nominal" },
      { zoneId: "PZ-03", name: "Northern Residential Zone", pressurePsi: 51.4, status: "Fluctuating" },
      { zoneId: "PZ-04", name: "Harbor Utility Terminal", pressurePsi: 57.5, status: "Nominal" },
    ],
  };
}

