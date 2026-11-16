import { AnalyticsTrends } from "./types";

export async function fetchAnalyticsTrends(): Promise<AnalyticsTrends> {
  return {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    waterLossHourly: [
      { time: "00:00", lossLph: 1820, preventedLossLph: 450 },
      { time: "04:00", lossLph: 1650, preventedLossLph: 680 },
      { time: "08:00", lossLph: 2100, preventedLossLph: 1100 },
      { time: "12:00", lossLph: 1780, preventedLossLph: 1450 },
      { time: "16:00", lossLph: 1420, preventedLossLph: 1720 },
      { time: "20:00", lossLph: 1310, preventedLossLph: 1850 },
    ],
    leakFrequencyBySector: [
      { sector: "Sector 1 (Industrial)", count: 5, volumeLph: 1420 },
      { sector: "Sector 2 (Harbor)", count: 2, volumeLph: 380 },
      { sector: "Sector 3 (Residential)", count: 4, volumeLph: 820 },
      { sector: "Sector 4 (Metro Core)", count: 7, volumeLph: 2240 },
    ],
    roverUtilization: [
      { category: "Acoustic Survey", percentage: 48, color: "#06b6d4" },
      { category: "En-Route Transit", percentage: 22, color: "#38bdf8" },
      { category: "Dock Charging", percentage: 20, color: "#10b981" },
      { category: "Depot Standby", percentage: 10, color: "#64748b" },
    ],
    sensorConnectivity: [
      { category: "Acoustic", uptimePct: 98.4 },
      { category: "Pressure", uptimePct: 99.1 },
      { category: "Flow", uptimePct: 100.0 },
      { category: "Thermal", uptimePct: 94.2 },
      { category: "Moisture", uptimePct: 96.5 },
    ],
  };
}

