import { fetchRovers, SimulatedRover } from "../simulation/roverService";
import { fetchIncidents, SimulatedLeakIncident } from "../simulation/incidentService";
import {
  RoverMarkerProperties,
  LeakIncidentProperties,
  SensorStationProperties,
  GeoJsonPointGeometry,
  SensorModality,
} from "./types";

export interface GeoJsonFeature<P> {
  type: "Feature";
  id: string;
  geometry: GeoJsonPointGeometry;
  properties: P;
}

export interface GeoJsonFeatureCollection<P> {
  type: "FeatureCollection";
  features: GeoJsonFeature<P>[];
}

/**
 * Transforms Simulated Rovers from roverService into GeoJSON Point Features
 */
export async function getRoversGeoJson(): Promise<GeoJsonFeatureCollection<RoverMarkerProperties>> {
  const rovers = await fetchRovers();
  const features: GeoJsonFeature<RoverMarkerProperties>[] = rovers.map((r) => ({
    type: "Feature",
    id: r.id,
    geometry: {
      type: "Point",
      coordinates: [r.currentLocation.longitude, r.currentLocation.latitude],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      roverId: r.id,
      name: r.name,
      model: r.model,
      status: r.status,
      batteryPercentage: r.batteryPercentage,
      currentMission: r.currentMission,
      stationName: r.currentLocation.stationName,
      velocityMps: r.kinematics.velocityMps,
      headingDeg: r.kinematics.headingDeg,
      lastPing: r.lastCommunication,
    },
  }));

  return {
    type: "FeatureCollection",
    features,
  };
}

/**
 * Transforms Simulated Incidents from incidentService into GeoJSON Point Features
 */
export async function getIncidentsGeoJson(): Promise<GeoJsonFeatureCollection<LeakIncidentProperties>> {
  const incidents = await fetchIncidents();
  const features: GeoJsonFeature<LeakIncidentProperties>[] = incidents.map((inc) => ({
    type: "Feature",
    id: inc.id,
    geometry: {
      type: "Point",
      coordinates: [inc.estimatedLocation.longitude, inc.estimatedLocation.latitude],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      incidentId: inc.id,
      segmentId: inc.pipelineSegmentId,
      segmentName: inc.segmentName,
      severity: inc.severity,
      status: inc.status,
      detectionTimestamp: inc.detectionTimestamp,
      estimatedLossRateLph: inc.estimatedLossRateLph,
      confidenceScorePct: inc.confidenceScorePct,
      dominantFreqHz: inc.dominantAcousticFreqHz,
      depthM: inc.estimatedLocation.depthM,
      assignedRoverId: inc.assignedRoverId,
      zone: inc.estimatedLocation.zone,
    },
  }));

  return {
    type: "FeatureCollection",
    features,
  };
}

/**
 * Generates stationary sensor stations along pipeline network segments
 */
export function getSensorsGeoJson(): GeoJsonFeatureCollection<SensorStationProperties> {
  const SENSOR_STATIONS: GeoJsonFeature<SensorStationProperties>[] = [
    // Acoustic Hydrophones
    {
      type: "Feature",
      id: "SNS-AC-01",
      geometry: { type: "Point", coordinates: [-74.0110, 40.7115] },
      properties: {
        isSimulated: true,
        provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
        stationId: "SNS-AC-01",
        name: "Acoustic Hydrophone Array Alpha",
        modality: "acoustic",
        modalityLabel: "Acoustic Hydrophone",
        currentValue: 46.2,
        unit: "dB SPL",
        sampleRateHz: 48000,
        status: "Alert",
        pipeSegmentId: "PIPE-SEC-4B-92",
        batteryPct: 94,
      },
    },
    {
      type: "Feature",
      id: "SNS-AC-02",
      geometry: { type: "Point", coordinates: [-74.0010, 40.7140] },
      properties: {
        isSimulated: true,
        provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
        stationId: "SNS-AC-02",
        name: "Acoustic Hydrophone Beta",
        modality: "acoustic",
        modalityLabel: "Acoustic Hydrophone",
        currentValue: 38.5,
        unit: "dB SPL",
        sampleRateHz: 48000,
        status: "Normal",
        pipeSegmentId: "PIPE-SEC-4B-92",
        batteryPct: 91,
      },
    },

    // Pressure Transducers
    {
      type: "Feature",
      id: "SNS-PR-01",
      geometry: { type: "Point", coordinates: [-74.0060, 40.7080] },
      properties: {
        isSimulated: true,
        provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
        stationId: "SNS-PR-01",
        name: "High-Speed Pressure Transducer PZ-01",
        modality: "pressure",
        modalityLabel: "Pressure Transducer",
        currentValue: 64.2,
        unit: "PSI",
        sampleRateHz: 1000,
        status: "Nominal",
        pipeSegmentId: "PIPE-SEC-4A-10",
        batteryPct: 98,
      },
    },
    {
      type: "Feature",
      id: "SNS-PR-02",
      geometry: { type: "Point", coordinates: [-74.0035, 40.7135] },
      properties: {
        isSimulated: true,
        provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
        stationId: "SNS-PR-02",
        name: "Pressure Transient Logger PZ-02",
        modality: "pressure",
        modalityLabel: "Pressure Transducer",
        currentValue: 59.8,
        unit: "PSI",
        sampleRateHz: 1000,
        status: "Nominal",
        pipeSegmentId: "PIPE-IND-1A-04",
        batteryPct: 88,
      },
    },

    // Ultrasonic Flow Meters
    {
      type: "Feature",
      id: "SNS-FL-01",
      geometry: { type: "Point", coordinates: [-74.0060, 40.7170] },
      properties: {
        isSimulated: true,
        provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
        stationId: "SNS-FL-01",
        name: "Magnetic Ultrasonic Flow Meter FM-1",
        modality: "flow",
        modalityLabel: "Flow Meter",
        currentValue: 124.5,
        unit: "m³/h",
        sampleRateHz: 100,
        status: "Nominal",
        pipeSegmentId: "PIPE-SEC-4A-10",
        batteryPct: 99,
      },
    },

    // Thermal Soil Probes
    {
      type: "Feature",
      id: "SNS-TH-01",
      geometry: { type: "Point", coordinates: [-74.0130, 40.7180] },
      properties: {
        isSimulated: true,
        provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
        stationId: "SNS-TH-01",
        name: "Subsurface Thermal Probe TP-04",
        modality: "thermal",
        modalityLabel: "Thermal Probe",
        currentValue: 18.2,
        unit: "°C",
        sampleRateHz: 10,
        status: "Nominal",
        pipeSegmentId: "PIPE-RES-3C-11",
        batteryPct: 85,
      },
    },

    // Moisture Impedance Sensor
    {
      type: "Feature",
      id: "SNS-MS-01",
      geometry: { type: "Point", coordinates: [-74.0100, 40.7065] },
      properties: {
        isSimulated: true,
        provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
        stationId: "SNS-MS-01",
        name: "Ground Moisture Impedance Sensor M-02",
        modality: "moisture",
        modalityLabel: "Soil Moisture",
        currentValue: 16.4,
        unit: "% Vol",
        sampleRateHz: 1,
        status: "Normal",
        pipeSegmentId: "PIPE-HRB-02-19",
        batteryPct: 90,
      },
    },
  ];

  return {
    type: "FeatureCollection",
    features: SENSOR_STATIONS,
  };
}

