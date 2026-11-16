import {
  PipelineSegmentProperties,
  GeoJsonLineStringGeometry,
} from "./types";

export interface PipelineFeature {
  type: "Feature";
  id: string;
  geometry: GeoJsonLineStringGeometry;
  properties: PipelineSegmentProperties;
}

export interface PipelineFeatureCollection {
  type: "FeatureCollection";
  features: PipelineFeature[];
}

const PIPELINE_FEATURES: PipelineFeature[] = [
  // 1. Primary Trunk Line B (Incident INC-2026-081 segment)
  {
    type: "Feature",
    id: "PIPE-SEC-4B-92",
    geometry: {
      type: "LineString",
      coordinates: [
        [-74.0150, 40.7100],
        [-74.0110, 40.7115],
        [-74.0060, 40.7128], // Incident & Rover location
        [-74.0010, 40.7140],
        [-73.9960, 40.7155],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-SEC-4B-92",
      name: "Metro Central Main Trunk Line B",
      category: "primary",
      categoryLabel: "Primary Trunk Main",
      material: "Ductile Iron (Class 54)",
      diameterMm: 600,
      lengthM: 1850,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Leak Suspected",
      pressureZoneId: "PZ-01",
      pressureZoneName: "Metro Central High-Pressure",
      nominalPressurePsi: 65,
      installYear: 2012,
      flowDirectionDeg: 62,
      conditionGrade: "C",
    },
  },

  // 2. Primary Trunk Line A (North-South Main)
  {
    type: "Feature",
    id: "PIPE-SEC-4A-10",
    geometry: {
      type: "LineString",
      coordinates: [
        [-74.0060, 40.7040],
        [-74.0060, 40.7128],
        [-74.0060, 40.7220],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-SEC-4A-10",
      name: "Grand Avenue Spine Trunk Line A",
      category: "primary",
      categoryLabel: "Primary Trunk Main",
      material: "Pre-stressed Concrete Cylinder",
      diameterMm: 750,
      lengthM: 2100,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Inspected - Verified",
      pressureZoneId: "PZ-01",
      pressureZoneName: "Metro Central High-Pressure",
      nominalPressurePsi: 68,
      installYear: 2018,
      flowDirectionDeg: 0,
      conditionGrade: "A",
    },
  },

  // 3. Secondary Feeder Line 1 (Incident INC-2026-079 segment)
  {
    type: "Feature",
    id: "PIPE-IND-1A-04",
    geometry: {
      type: "LineString",
      coordinates: [
        [-74.0060, 40.7128],
        [-74.0035, 40.7135],
        [-74.0021, 40.7145], // Incident location
        [-73.9980, 40.7160],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-IND-1A-04",
      name: "Industrial Park Feeder Line 1",
      category: "secondary",
      categoryLabel: "Secondary Feeder",
      material: "High-Density Polyethylene (HDPE)",
      diameterMm: 400,
      lengthM: 820,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Rover Patrol Active",
      pressureZoneId: "PZ-02",
      pressureZoneName: "Eastern Industrial Sector",
      nominalPressurePsi: 60,
      installYear: 2015,
      flowDirectionDeg: 45,
      conditionGrade: "B",
    },
  },

  // 4. Secondary Feeder Line 2 (North Loop Feeder)
  {
    type: "Feature",
    id: "PIPE-RES-3C-11",
    geometry: {
      type: "LineString",
      coordinates: [
        [-74.0060, 40.7220],
        [-74.0089, 40.7198], // Rover 3 / Incident location
        [-74.0130, 40.7180],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-RES-3C-11",
      name: "Pinecrest Residential Sub-Branch",
      category: "secondary",
      categoryLabel: "Secondary Feeder",
      material: "Ductile Iron",
      diameterMm: 350,
      lengthM: 940,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Inspection Due",
      pressureZoneId: "PZ-03",
      pressureZoneName: "Northern Residential Zone",
      nominalPressurePsi: 52,
      installYear: 2008,
      flowDirectionDeg: 220,
      conditionGrade: "B",
    },
  },

  // 5. Distribution Pipeline (South Harbor Branch - Incident INC-2026-072 segment)
  {
    type: "Feature",
    id: "PIPE-HRB-02-19",
    geometry: {
      type: "LineString",
      coordinates: [
        [-74.0060, 40.7040],
        [-74.0100, 40.7065],
        [-74.0115, 40.7091], // Incident location
        [-74.0140, 40.7110],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-HRB-02-19",
      name: "Harbor Marginal Service Line",
      category: "distribution",
      categoryLabel: "Distribution Main",
      material: "Cast Iron (Epoxy Lined)",
      diameterMm: 250,
      lengthM: 780,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Inspected - Verified",
      pressureZoneId: "PZ-04",
      pressureZoneName: "Harbor Utility Terminal",
      nominalPressurePsi: 58,
      installYear: 1998,
      flowDirectionDeg: 310,
      conditionGrade: "C",
    },
  },

  // 6. Distribution Pipeline (Historic District - Repaired INC-2026-068 segment)
  {
    type: "Feature",
    id: "PIPE-OLD-01-08",
    geometry: {
      type: "LineString",
      coordinates: [
        [-74.0120, 40.7140],
        [-74.0090, 40.7160], // Repaired leak location
        [-74.0060, 40.7180],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-OLD-01-08",
      name: "Old Canal Junction Cast-Iron Pipe",
      category: "distribution",
      categoryLabel: "Distribution Main",
      material: "Gray Cast Iron",
      diameterMm: 200,
      lengthM: 610,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Inspected - Verified",
      pressureZoneId: "PZ-01",
      pressureZoneName: "Metro Central High-Pressure",
      nominalPressurePsi: 55,
      installYear: 1974,
      flowDirectionDeg: 55,
      conditionGrade: "C",
    },
  },

  // 7. Service Connection 1 (Commercial High-Rise Lateral)
  {
    type: "Feature",
    id: "PIPE-LAT-04-01",
    geometry: {
      type: "LineString",
      coordinates: [
        [-74.0060, 40.7128],
        [-74.0050, 40.7118],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-LAT-04-01",
      name: "Civic Plaza Commercial Service Connection",
      category: "service",
      categoryLabel: "Service Lateral",
      material: "Copper (Type K)",
      diameterMm: 100,
      lengthM: 140,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Inspected - Verified",
      pressureZoneId: "PZ-01",
      pressureZoneName: "Metro Central High-Pressure",
      nominalPressurePsi: 65,
      installYear: 2020,
      flowDirectionDeg: 135,
      conditionGrade: "A",
    },
  },

  // 8. Service Connection 2 (Industrial Sub-Station Lateral)
  {
    type: "Feature",
    id: "PIPE-LAT-01-04",
    geometry: {
      type: "LineString",
      coordinates: [
        [-74.0021, 40.7145],
        [-74.0010, 40.7140],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-LAT-01-04",
      name: "East Chemical Depot Lateral Feed",
      category: "service",
      categoryLabel: "Service Lateral",
      material: "Stainless Steel 316",
      diameterMm: 150,
      lengthM: 110,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Inspected - Verified",
      pressureZoneId: "PZ-02",
      pressureZoneName: "Eastern Industrial Sector",
      nominalPressurePsi: 60,
      installYear: 2017,
      flowDirectionDeg: 120,
      conditionGrade: "A",
    },
  },
];

export function getPipelineGeoJson(): PipelineFeatureCollection {
  return {
    type: "FeatureCollection",
    features: PIPELINE_FEATURES,
  };
}

export function getPipelineSegmentById(id: string): PipelineFeature | undefined {
  return PIPELINE_FEATURES.find((p) => p.properties.segmentId === id);
}

