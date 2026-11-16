import { SimulatedAlert } from "./types";

let SIMULATED_ALERTS: SimulatedAlert[] = [
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "ALT-901",
    title: "Critical Acoustic Energy Burst",
    message: "Acoustic sensor node S-04 detected 74.2 dB amplitude at Sector 4 trunk line.",
    severity: "critical",
    timestamp: "18m ago",
    incidentRef: "INC-2026-081",
    roverRef: "ROV-AQUA-01",
    acknowledged: false,
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "ALT-902",
    title: "Hydrodynamic Pressure Transient",
    message: "Zone PZ-03 pressure dropped by 4.8 PSI within 120 seconds.",
    severity: "warning",
    timestamp: "45m ago",
    incidentRef: "INC-2026-079",
    acknowledged: false,
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "ALT-903",
    title: "Rover Battery Return-to-Dock Failsafe",
    message: "Aquila Drone SoC reached 24%. Autonomous return trajectory triggered.",
    severity: "warning",
    timestamp: "1h 10m ago",
    roverRef: "ROV-AQUA-04",
    acknowledged: true,
  },
  {
    isSimulated: true,
    source: "VIRTUAL_SIMULATION_ENGINE",
    simulatedAt: new Date().toISOString(),
    id: "ALT-904",
    title: "Acoustic Baseline Recalibration Complete",
    message: "Sub-network 4 hydrophones synchronized to ambient traffic noise profile.",
    severity: "informational",
    timestamp: "2h 30m ago",
    acknowledged: true,
  },
];

export async function fetchAlerts(): Promise<SimulatedAlert[]> {
  return [...SIMULATED_ALERTS];
}

export async function acknowledgeAlert(id: string): Promise<void> {
  SIMULATED_ALERTS = SIMULATED_ALERTS.map((a) =>
    a.id === id ? { ...a, acknowledged: true } : a
  );
}

