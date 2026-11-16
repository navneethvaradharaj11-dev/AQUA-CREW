/**
 * AQUA CREW — Geospatial Intelligence Types & GeoJSON Schemas
 * Strictly software-first simulated demonstration pipeline network.
 */

export interface GeoJsonPointGeometry {
  type: "Point";
  coordinates: [number, number]; // [longitude, latitude]
}

export interface GeoJsonLineStringGeometry {
  type: "LineString";
  coordinates: [number, number][];
}

export interface GeoJsonPolygonGeometry {
  type: "Polygon";
  coordinates: [number, number][][];
}

export type PipelineCategory = "primary" | "secondary" | "distribution" | "service";

export interface PipelineSegmentProperties {
  isSimulated: true;
  provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID";
  segmentId: string;
  name: string;
  category: PipelineCategory;
  categoryLabel: string;
  material: string;
  diameterMm: number;
  lengthM: number;
  operationalStatus: "Active - Pressurized" | "Throttled" | "Isolated";
  inspectionStatus: "Inspected - Verified" | "Inspection Due" | "Rover Patrol Active" | "Leak Suspected";
  pressureZoneId: string;
  pressureZoneName: string;
  nominalPressurePsi: number;
  installYear: number;
  flowDirectionDeg: number;
  conditionGrade: "A" | "B" | "C" | "D";
}

export interface LeakIncidentProperties {
  isSimulated: true;
  provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID";
  incidentId: string;
  segmentId: string;
  segmentName: string;
  severity: "Critical" | "High" | "Medium" | "Low";
  status: "Suspected" | "Investigating" | "Confirmed" | "Repaired";
  detectionTimestamp: string;
  estimatedLossRateLph: number;
  confidenceScorePct: number;
  dominantFreqHz: number;
  depthM: number;
  assignedRoverId?: string;
  zone: string;
}

export interface RoverMarkerProperties {
  isSimulated: true;
  provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID";
  roverId: string;
  name: string;
  model: string;
  status: "ACTIVE" | "ONLINE" | "WARNING" | "OFFLINE" | "IDLE";
  batteryPercentage: number;
  currentMission: string;
  stationName: string;
  velocityMps: number;
  headingDeg: number;
  lastPing: string;
}

export type SensorModality = "acoustic" | "pressure" | "flow" | "thermal" | "moisture";

export interface SensorStationProperties {
  isSimulated: true;
  provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID";
  stationId: string;
  name: string;
  modality: SensorModality;
  modalityLabel: string;
  currentValue: number;
  unit: string;
  sampleRateHz: number;
  status: "Nominal" | "Normal" | "Alert" | "Calibrating";
  pipeSegmentId: string;
  batteryPct: number;
}

export interface InspectionZoneProperties {
  isSimulated: true;
  provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID";
  zoneId: string;
  name: string;
  sectorCode: string;
  riskScorePct: number;
  areaSqKm: number;
  totalSegmentsCount: number;
  activeRoversCount: number;
  nominalPressurePsi: number;
  fillColor: string;
}

export interface MapLayerVisibilityState {
  pipelines: {
    primary: boolean;
    secondary: boolean;
    distribution: boolean;
    service: boolean;
  };
  leakIncidents: {
    critical: boolean;
    high: boolean;
    medium: boolean;
    low: boolean;
  };
  rovers: boolean;
  sensorStations: {
    acoustic: boolean;
    pressure: boolean;
    flow: boolean;
    thermal: boolean;
    moisture: boolean;
  };
  inspectionZones: boolean;
}

export type SelectedMapFeatureType = "pipeline" | "incident" | "rover" | "sensor" | "zone";

export interface SelectedMapFeature {
  type: SelectedMapFeatureType;
  id: string;
  title: string;
  properties: Record<string, unknown>;
  coordinates?: [number, number];
}

