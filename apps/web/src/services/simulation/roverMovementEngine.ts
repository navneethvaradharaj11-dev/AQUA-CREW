import { getPipelineSegmentById } from "../gis/pipelineGeoService";
import {
  SimulatedRover,
  RoverOperatingState,
} from "./types";

/**
 * Standard Haversine distance in meters between two [lon, lat] coordinates.
 */
export function haversineDistanceMeters(
  coord1: [number, number],
  coord2: [number, number]
): number {
  const [lon1, lat1] = coord1;
  const [lon2, lat2] = coord2;
  const R = 6371000; // Earth radius in meters
  const toRad = (deg: number) => (deg * Math.PI) / 180;

  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * Calculates initial forward azimuth bearing in degrees (0-360) from coord1 to coord2.
 */
export function calculateBearingDeg(
  coord1: [number, number],
  coord2: [number, number]
): number {
  const [lon1, lat1] = coord1;
  const [lon2, lat2] = coord2;
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  const toDeg = (rad: number) => (rad * 180) / Math.PI;

  const phi1 = toRad(lat1);
  const phi2 = toRad(lat2);
  const deltaLambda = toRad(lon2 - lon1);

  const y = Math.sin(deltaLambda) * Math.cos(phi2);
  const x =
    Math.cos(phi1) * Math.sin(phi2) -
    Math.sin(phi1) * Math.cos(phi2) * Math.cos(deltaLambda);
  const theta = Math.atan2(y, x);
  return (toDeg(theta) + 360) % 360;
}

export interface PipelineRouteProfile {
  segmentId: string;
  name: string;
  coordinates: [number, number][]; // [lon, lat]
  subSegmentDistancesM: number[];
  cumulativeDistancesM: number[];
  totalLengthM: number;
}

/**
 * Cached route profiles to avoid recomputing geometry every tick.
 */
const ROUTE_CACHE: Map<string, PipelineRouteProfile> = new Map();

export function getRouteProfileForSegment(segmentId: string): PipelineRouteProfile | null {
  if (ROUTE_CACHE.has(segmentId)) {
    return ROUTE_CACHE.get(segmentId)!;
  }

  const segment = getPipelineSegmentById(segmentId);
  if (!segment || !segment.geometry || !segment.geometry.coordinates || segment.geometry.coordinates.length < 2) {
    return null;
  }

  const coords = segment.geometry.coordinates as [number, number][];
  const subDists: number[] = [];
  const cumDists: number[] = [0];
  let total = 0;

  for (let i = 0; i < coords.length - 1; i++) {
    const d = haversineDistanceMeters(coords[i], coords[i + 1]);
    subDists.push(d);
    total += d;
    cumDists.push(total);
  }

  const profile: PipelineRouteProfile = {
    segmentId,
    name: segment.properties.name,
    coordinates: coords,
    subSegmentDistancesM: subDists,
    cumulativeDistancesM: cumDists,
    totalLengthM: Math.max(total, 1),
  };

  ROUTE_CACHE.set(segmentId, profile);
  return profile;
}

export interface InterpolatedPosition {
  longitude: number;
  latitude: number;
  headingDeg: number;
  fractionCompleted: number;
  stationName: string;
}

/**
 * Interpolates coordinates along a pipeline route given a distance in meters from start.
 */
export function interpolateRoutePosition(
  profile: PipelineRouteProfile,
  distanceAlongRouteM: number,
  isReturning = false
): InterpolatedPosition {
  const clampedDist = Math.max(0, Math.min(profile.totalLengthM, distanceAlongRouteM));
  const fraction = clampedDist / profile.totalLengthM;

  // Find sub-segment
  let segIndex = 0;
  for (let i = 0; i < profile.cumulativeDistancesM.length - 1; i++) {
    if (clampedDist >= profile.cumulativeDistancesM[i] && clampedDist <= profile.cumulativeDistancesM[i + 1]) {
      segIndex = i;
      break;
    }
  }

  const startCoord = profile.coordinates[segIndex];
  const endCoord = profile.coordinates[Math.min(segIndex + 1, profile.coordinates.length - 1)];
  const segStartDist = profile.cumulativeDistancesM[segIndex];
  const segLength = profile.subSegmentDistancesM[segIndex] || 1;
  const t = Math.max(0, Math.min(1, (clampedDist - segStartDist) / segLength));

  const lon = startCoord[0] + t * (endCoord[0] - startCoord[0]);
  const lat = startCoord[1] + t * (endCoord[1] - startCoord[1]);

  let bearing = calculateBearingDeg(startCoord, endCoord);
  if (isReturning) {
    bearing = (bearing + 180) % 360;
  }

  const stationName = `${profile.name} — Station ${Math.round(clampedDist)}m`;

  return {
    longitude: Number(lon.toFixed(6)),
    latitude: Number(lat.toFixed(6)),
    headingDeg: Number(bearing.toFixed(1)),
    fractionCompleted: Number(fraction.toFixed(3)),
    stationName,
  };
}

/**
 * State tracking for simulated rover kinematics and telemetry between ticks.
 */
export interface RoverKinematicState {
  roverId: string;
  segmentId: string;
  currentDistanceM: number;
  direction: 1 | -1; // 1 = forward, -1 = reverse (returning)
  targetSpeedMps: number;
  totalDistanceTravelledM: number;
}

/**
 * Computes telemetry updates for one tick (deltaSeconds)
 */
export function updateRoverTelemetryTick(
  rover: SimulatedRover,
  kinematicState: RoverKinematicState,
  deltaSeconds = 1
): { updatedRover: SimulatedRover; updatedKinematics: RoverKinematicState; eventOccurred?: string } {
  const route = getRouteProfileForSegment(kinematicState.segmentId);
  const state = rover.operatingState;

  let currentDist = kinematicState.currentDistanceM;
  let direction = kinematicState.direction;
  let currentSpeed = 0;
  let targetSpeed = 0;
  let eventOccurred: string | undefined;

  // Determine target speed based on operating state
  switch (state) {
    case "MOVING":
      targetSpeed = 0.55; // Standard traverse speed
      direction = 1;
      break;
    case "INSPECTING":
      targetSpeed = 0.28; // Careful acoustic inspection speed
      direction = 1;
      break;
    case "RETURNING":
      targetSpeed = 0.85; // Rapid transit back to cradle
      direction = -1;
      break;
    case "IDLE":
    case "PAUSED":
    case "CHARGING":
    case "OFFLINE":
    case "ERROR":
    case "EMERGENCY_STOP":
    default:
      targetSpeed = 0;
      break;
  }

  // Smooth acceleration/deceleration
  const currentVel = rover.kinematics.velocityMps || 0;
  if (targetSpeed > currentVel) {
    currentSpeed = Math.min(targetSpeed, currentVel + 0.15 * deltaSeconds);
  } else if (targetSpeed < currentVel) {
    currentSpeed = Math.max(targetSpeed, currentVel - 0.25 * deltaSeconds);
  } else {
    currentSpeed = targetSpeed;
  }

  // Position interpolation along route
  let newLat = rover.currentLocation.latitude;
  let newLon = rover.currentLocation.longitude;
  let newHeading = rover.kinematics.headingDeg;
  let stationName = rover.currentLocation.stationName;
  let progressPct = rover.currentLocation.routeProgressPct || 0;

  if (route && currentSpeed > 0) {
    const deltaDist = currentSpeed * deltaSeconds;
    currentDist += direction * deltaDist;
    kinematicState.totalDistanceTravelledM += deltaDist;

    // Boundary checks along route
    if (currentDist >= route.totalLengthM) {
      currentDist = route.totalLengthM;
      eventOccurred = "ROUTE_END_REACHED";
    } else if (currentDist <= 0) {
      currentDist = 0;
      eventOccurred = "BASE_REACHED";
    }

    const interp = interpolateRoutePosition(route, currentDist, direction === -1);
    newLon = interp.longitude;
    newLat = interp.latitude;
    newHeading = interp.headingDeg;
    stationName = interp.stationName;
    progressPct = Math.round(interp.fractionCompleted * 100);
  }

  // Battery simulation
  let battery = rover.batteryPercentage;
  if (state === "CHARGING") {
    battery = Math.min(100, Number((battery + 0.4 * deltaSeconds).toFixed(1)));
  } else if (state === "MOVING") {
    battery = Math.max(0, Number((battery - 0.04 * deltaSeconds).toFixed(2)));
  } else if (state === "INSPECTING") {
    battery = Math.max(0, Number((battery - 0.06 * deltaSeconds).toFixed(2)));
  } else if (state === "RETURNING") {
    battery = Math.max(0, Number((battery - 0.05 * deltaSeconds).toFixed(2)));
  } else if (state !== "OFFLINE") {
    battery = Math.max(0, Number((battery - 0.005 * deltaSeconds).toFixed(3)));
  }

  // Thermal simulation
  let motorTemp = rover.diagnostics.motorTempC || 26.0;
  let internalTemp = rover.diagnostics.internalTempC || 28.0;
  const ambientTemp = 23.5;

  if (currentSpeed > 0) {
    motorTemp = Math.min(65.0, Number((motorTemp + 0.12 * (currentSpeed / 0.5) * deltaSeconds).toFixed(1)));
    internalTemp = Math.min(42.0, Number((internalTemp + 0.04 * deltaSeconds).toFixed(1)));
  } else {
    // Cooldown towards ambient
    motorTemp = Math.max(ambientTemp, Number((motorTemp - 0.15 * deltaSeconds).toFixed(1)));
    internalTemp = Math.max(ambientTemp, Number((internalTemp - 0.05 * deltaSeconds).toFixed(1)));
  }

  // Motor Current
  let motorCurrent = 0;
  if (currentSpeed > 0) {
    motorCurrent = Number((1.2 + currentSpeed * 1.5 + (Math.random() * 0.2 - 0.1)).toFixed(2));
  }

  // Signal RSSI (bounded -45 to -105 dBm)
  let rssi = rover.diagnostics.signalRssiDbm || -65;
  if (state !== "OFFLINE") {
    const jitter = (Math.random() * 2 - 1);
    rssi = Math.max(-105, Math.min(-45, Math.round(rssi + jitter)));
  } else {
    rssi = -115;
  }

  // Connection status derivation
  let connStatus: "ONLINE" | "DEGRADED" | "OFFLINE" = "ONLINE";
  if (state === "OFFLINE") {
    connStatus = "OFFLINE";
  } else if (rssi < -90 || battery < 10) {
    connStatus = "DEGRADED";
  }

  // Inspection payload sensor readings
  let acousticSpl = rover.payloadSensors.acousticSplDb;
  let dominantFreq = rover.payloadSensors.dominantFreqHz;
  let moisture = rover.payloadSensors.groundMoisturePct;

  if (state === "INSPECTING" || state === "MOVING") {
    acousticSpl = Number((42.0 + Math.sin(currentDist / 40) * 12.0 + Math.random() * 2).toFixed(1));
    dominantFreq = Math.round(1100 + Math.cos(currentDist / 30) * 450);
    moisture = Number((16.0 + Math.sin(currentDist / 50) * 6.0).toFixed(1));
  }

  const updatedKinematics: RoverKinematicState = {
    ...kinematicState,
    currentDistanceM: currentDist,
    direction,
    targetSpeedMps: targetSpeed,
  };

  const updatedRover: SimulatedRover = {
    ...rover,
    simulatedAt: new Date().toISOString(),
    lastHeartbeatTimestamp: new Date().toISOString(),
    lastCommunication: "1s ago",
    batteryPercentage: Math.round(battery),
    distanceTravelledKm: Number((updatedKinematics.totalDistanceTravelledM / 1000).toFixed(2)),
    connectionStatus: connStatus,
    currentLocation: {
      stationName,
      latitude: newLat,
      longitude: newLon,
      pipeSegmentId: kinematicState.segmentId,
      routeProgressPct: progressPct,
    },
    kinematics: {
      velocityMps: Number(currentSpeed.toFixed(2)),
      headingDeg: newHeading,
      targetSpeedMps: targetSpeed,
    },
    diagnostics: {
      internalTempC: internalTemp,
      motorTempC: motorTemp,
      motorCurrentAmps: motorCurrent,
      signalRssiDbm: rssi,
    },
    payloadSensors: {
      acousticSplDb: acousticSpl,
      dominantFreqHz: dominantFreq,
      groundMoisturePct: moisture,
    },
  };

  return {
    updatedRover,
    updatedKinematics,
    eventOccurred,
  };
}

