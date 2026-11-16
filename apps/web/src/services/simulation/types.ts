/**
 * AQUA CREW — Simulation Architecture Models & Types
 * Strictly identified as simulated data for software-first platform development.
 */

export interface SimulatedBaseRecord {
  isSimulated: true;
  source: "VIRTUAL_SIMULATION_ENGINE";
  simulatedAt: string;
}

export interface DashboardKpis extends SimulatedBaseRecord {
  totalPipelineLengthKm: number;
  detectedLeakIncidentsCount: number;
  activeRoversCount: number;
  totalRoversCount: number;
  connectedSensorsCount: number;
  totalSensorsCount: number;
  estimatedWaterLossLph: number;
  activeInspectionMissionsCount: number;
}

export interface WaterNetworkOverview extends SimulatedBaseRecord {
  totalSegments: number;
  monitoredSegments: number;
  segmentsRequiringInspection: number;
  criticalSegments: number;
  networkHealthPercentage: number;
  averagePressurePsi: number;
  activePressureZones: {
    zoneId: string;
    name: string;
    pressurePsi: number;
    status: "Nominal" | "Elevated" | "Fluctuating";
  }[];
}

export type RoverOperationalStatus = "ONLINE" | "ACTIVE" | "IDLE" | "WARNING" | "OFFLINE";

/**
 * Task 05 Autonomous Rover Operating State Machine States
 */
export type RoverOperatingState =
  | "IDLE"
  | "MOVING"
  | "INSPECTING"
  | "PAUSED"
  | "RETURNING"
  | "CHARGING"
  | "OFFLINE"
  | "ERROR"
  | "EMERGENCY_STOP";

export type RoverConnectionStatus = "ONLINE" | "DEGRADED" | "OFFLINE";

export interface RoverStateTransitionRecord {
  id: string;
  roverId: string;
  previousState: RoverOperatingState;
  newState: RoverOperatingState;
  timestamp: string;
  reason: string;
  triggeredBy: "OPERATOR" | "AUTONOMOUS_CONTROLLER" | "SAFETY_INTERLOCK" | "SIMULATION_ENGINE";
  isSimulated: true;
  source: "VIRTUAL_SIMULATION_ENGINE";
}

export interface RoverTelemetryBounds {
  batteryMinPct: number;
  batteryMaxPct: number;
  maxVelocityMps: number;
  motorTempWarningC: number;
  motorTempCriticalC: number;
  internalTempMaxC: number;
  minSignalDbm: number;
  maxSignalDbm: number;
}

export interface SimulatedRover extends SimulatedBaseRecord {
  id: string;
  name: string;
  model: string;
  status: RoverOperationalStatus;
  operatingState: RoverOperatingState;
  connectionStatus: RoverConnectionStatus;
  batteryPercentage: number;
  distanceTravelledKm: number;
  currentMission: string;
  assignedMissionId?: string | null;
  currentLocation: {
    stationName: string;
    latitude: number;
    longitude: number;
    pipeSegmentId: string;
    routeProgressPct?: number;
  };
  lastCommunication: string;
  lastHeartbeatTimestamp: string;
  kinematics: {
    velocityMps: number;
    headingDeg: number;
    targetSpeedMps?: number;
  };
  diagnostics: {
    internalTempC: number;
    motorTempC: number;
    motorCurrentAmps: number;
    signalRssiDbm: number;
  };
  payloadSensors: {
    acousticSplDb: number;
    dominantFreqHz: number;
    groundMoisturePct: number;
  };
}

export type LeakSeverity = "Critical" | "High" | "Medium" | "Low";
export type LeakIncidentStatus = "Suspected" | "Investigating" | "Confirmed" | "Repaired";

export interface SimulatedLeakIncident extends SimulatedBaseRecord {
  id: string;
  pipelineSegmentId: string;
  segmentName: string;
  severity: LeakSeverity;
  status: LeakIncidentStatus;
  detectionTimestamp: string;
  estimatedLocation: {
    latitude: number;
    longitude: number;
    depthM: number;
    zone: string;
  };
  estimatedLossRateLph: number;
  confidenceScorePct: number;
  dominantAcousticFreqHz: number;
  assignedRoverId?: string;
  notes: string;
}

export interface SimulatedSensorCategory extends SimulatedBaseRecord {
  id: string;
  name: string;
  type: "acoustic" | "pressure" | "flow" | "thermal" | "moisture";
  connectedCount: number;
  totalCount: number;
  healthPercentage: number;
  avgSampleRateHz: number;
  unit: string;
  currentAverageValue: number;
  status: "Normal" | "Nominal" | "Calibrating" | "Alert";
}

export type MissionStatus = "In Progress" | "Scheduled" | "Paused" | "Completed" | "Cancelled";

export interface SimulatedMission extends SimulatedBaseRecord {
  id: string;
  assignedRoverId: string;
  assignedRoverName: string;
  missionType: "Acoustic Pipe Survey" | "Pressure Transient Test" | "Post-Repair Verification" | "Emergency Intercept";
  progressPercentage: number;
  status: MissionStatus;
  startTime: string;
  estimatedCompletionTime: string;
  targetSegmentId: string;
  waypointCount: number;
  completedWaypoints: number;
}

export type AlertSeverity = "critical" | "warning" | "informational";

export interface SimulatedAlert extends SimulatedBaseRecord {
  id: string;
  title: string;
  message: string;
  severity: AlertSeverity;
  timestamp: string;
  incidentRef?: string;
  roverRef?: string;
  acknowledged: boolean;
}

export interface AnalyticsTrends extends SimulatedBaseRecord {
  waterLossHourly: {
    time: string;
    lossLph: number;
    preventedLossLph: number;
  }[];
  leakFrequencyBySector: {
    sector: string;
    count: number;
    volumeLph: number;
  }[];
  roverUtilization: {
    category: string;
    percentage: number;
    color: string;
  }[];
  sensorConnectivity: {
    category: string;
    uptimePct: number;
  }[];
}

