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
  // 1. Primary Trunk Line B (Incident INC-2026-081 segment) — MG Road Central Trunk
  {
    type: "Feature",
    id: "PIPE-SEC-4B-92",
    geometry: {
      type: "LineString",
      coordinates: [
        [77.5850, 12.9690],
        [77.5900, 12.9705],
        [77.5946, 12.9716], // Incident & Rover 1 location (MG Road Central Joint)
        [77.6000, 12.9730],
        [77.6060, 12.9745],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-SEC-4B-92",
      name: "Bengaluru Central MG Road Trunk B",
      category: "primary",
      categoryLabel: "Primary Trunk Main",
      material: "Ductile Iron (Class 54)",
      diameterMm: 600,
      lengthM: 1850,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Leak Suspected",
      pressureZoneId: "PZ-01",
      pressureZoneName: "BWSSB Central High-Pressure",
      nominalPressurePsi: 65,
      installYear: 2012,
      flowDirectionDeg: 62,
      conditionGrade: "C",
    },
  },

  // 2. Primary Trunk Line A (Cubbon Park - Richmond Arterial Spine)
  {
    type: "Feature",
    id: "PIPE-SEC-4A-10",
    geometry: {
      type: "LineString",
      coordinates: [
        [77.5946, 12.9550],
        [77.5946, 12.9630],
        [77.5946, 12.9716],
        [77.5946, 12.9800],
        [77.5946, 12.9880],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-SEC-4A-10",
      name: "Cubbon - Richmond Arterial Spine A",
      category: "primary",
      categoryLabel: "Primary Trunk Main",
      material: "Pre-stressed Concrete Cylinder",
      diameterMm: 750,
      lengthM: 2100,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Inspected - Verified",
      pressureZoneId: "PZ-01",
      pressureZoneName: "BWSSB Central High-Pressure",
      nominalPressurePsi: 68,
      installYear: 2018,
      flowDirectionDeg: 0,
      conditionGrade: "A",
    },
  },

  // 3. Secondary Feeder Line 1 (Indiranagar 100ft Road Feeder)
  {
    type: "Feature",
    id: "PIPE-IND-1A-04",
    geometry: {
      type: "LineString",
      coordinates: [
        [77.5946, 12.9716],
        [77.6080, 12.9735],
        [77.6200, 12.9770], // Incident INC-2026-079 & Rover 2 location
        [77.6320, 12.9780],
        [77.6400, 12.9790],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-IND-1A-04",
      name: "Indiranagar 100ft Feeder Line 1",
      category: "secondary",
      categoryLabel: "Secondary Feeder",
      material: "High-Density Polyethylene (HDPE)",
      diameterMm: 400,
      lengthM: 820,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Rover Patrol Active",
      pressureZoneId: "PZ-02",
      pressureZoneName: "Eastern Tech Corridor Sector",
      nominalPressurePsi: 60,
      installYear: 2015,
      flowDirectionDeg: 45,
      conditionGrade: "B",
    },
  },

  // 4. Secondary Feeder Line 2 (Malleshwaram Sub-Trunk)
  {
    type: "Feature",
    id: "PIPE-RES-3C-11",
    geometry: {
      type: "LineString",
      coordinates: [
        [77.5946, 12.9880],
        [77.5840, 12.9910],
        [77.5750, 12.9940], // Rover 3 / Incident location
        [77.5680, 12.9980],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-RES-3C-11",
      name: "Malleshwaram Residential Feeder 2",
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

  // 5. Distribution Pipeline (Koramangala South Distribution)
  {
    type: "Feature",
    id: "PIPE-HRB-02-19",
    geometry: {
      type: "LineString",
      coordinates: [
        [77.5946, 12.9550],
        [77.6050, 12.9480],
        [77.6120, 12.9430], // Incident INC-2026-072 location
        [77.6220, 12.9360],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-HRB-02-19",
      name: "Koramangala South Distribution Main",
      category: "distribution",
      categoryLabel: "Distribution Main",
      material: "Cast Iron (Epoxy Lined)",
      diameterMm: 250,
      lengthM: 780,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Inspected - Verified",
      pressureZoneId: "PZ-04",
      pressureZoneName: "South Koramangala Zone",
      nominalPressurePsi: 58,
      installYear: 1998,
      flowDirectionDeg: 310,
      conditionGrade: "C",
    },
  },

  // 6. Distribution Pipeline (Commercial Street Historic District)
  {
    type: "Feature",
    id: "PIPE-OLD-01-08",
    geometry: {
      type: "LineString",
      coordinates: [
        [77.5980, 12.9780],
        [77.6040, 12.9810], // Repaired leak INC-2026-068 location
        [77.6090, 12.9835],
        [77.6150, 12.9860],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-OLD-01-08",
      name: "Commercial Street Historic Main",
      category: "distribution",
      categoryLabel: "Distribution Main",
      material: "Gray Cast Iron",
      diameterMm: 200,
      lengthM: 610,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Inspected - Verified",
      pressureZoneId: "PZ-01",
      pressureZoneName: "BWSSB Central High-Pressure",
      nominalPressurePsi: 55,
      installYear: 1974,
      flowDirectionDeg: 55,
      conditionGrade: "C",
    },
  },

  // 7. Service Connection 1 (UB City Commercial High-Rise Lateral)
  {
    type: "Feature",
    id: "PIPE-LAT-04-01",
    geometry: {
      type: "LineString",
      coordinates: [
        [77.5946, 12.9716],
        [77.5970, 12.9702],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-LAT-04-01",
      name: "UB City Commercial Service Connection",
      category: "service",
      categoryLabel: "Service Lateral",
      material: "Copper (Type K)",
      diameterMm: 100,
      lengthM: 140,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Inspected - Verified",
      pressureZoneId: "PZ-01",
      pressureZoneName: "BWSSB Central High-Pressure",
      nominalPressurePsi: 65,
      installYear: 2020,
      flowDirectionDeg: 135,
      conditionGrade: "A",
    },
  },

  // 8. Service Connection 2 (Indiranagar Metro Utility Lateral)
  {
    type: "Feature",
    id: "PIPE-LAT-01-04",
    geometry: {
      type: "LineString",
      coordinates: [
        [77.6200, 12.9770],
        [77.6230, 12.9755],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      segmentId: "PIPE-LAT-01-04",
      name: "Indiranagar Metro Terminal Lateral",
      category: "service",
      categoryLabel: "Service Lateral",
      material: "Stainless Steel 316",
      diameterMm: 150,
      lengthM: 110,
      operationalStatus: "Active - Pressurized",
      inspectionStatus: "Inspected - Verified",
      pressureZoneId: "PZ-02",
      pressureZoneName: "Eastern Tech Corridor Sector",
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
