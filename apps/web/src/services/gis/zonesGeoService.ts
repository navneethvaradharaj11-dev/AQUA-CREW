import {
  InspectionZoneProperties,
  GeoJsonPolygonGeometry,
} from "./types";

export interface ZoneFeature {
  type: "Feature";
  id: string;
  geometry: GeoJsonPolygonGeometry;
  properties: InspectionZoneProperties;
}

export interface ZoneFeatureCollection {
  type: "FeatureCollection";
  features: ZoneFeature[];
}

const ZONE_FEATURES: ZoneFeature[] = [
  // Sector 4: Metro Core (Highest density, central hub)
  {
    type: "Feature",
    id: "ZONE-SEC-04",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [-74.0150, 40.7100],
          [-74.0040, 40.7100],
          [-74.0040, 40.7180],
          [-74.0150, 40.7180],
          [-74.0150, 40.7100],
        ],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      zoneId: "ZONE-SEC-04",
      name: "Sector 4 — Metropolitan Business Core",
      sectorCode: "SEC-04",
      riskScorePct: 84.5,
      areaSqKm: 1.25,
      totalSegmentsCount: 420,
      activeRoversCount: 1,
      nominalPressurePsi: 65,
      fillColor: "#06b6d4",
    },
  },

  // Sector 1: Eastern Industrial Zone
  {
    type: "Feature",
    id: "ZONE-SEC-01",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [-74.0040, 40.7100],
          [-73.9920, 40.7100],
          [-73.9920, 40.7200],
          [-74.0040, 40.7200],
          [-74.0040, 40.7100],
        ],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      zoneId: "ZONE-SEC-01",
      name: "Sector 1 — Eastern Heavy Industrial Terminal",
      sectorCode: "SEC-01",
      riskScorePct: 62.0,
      areaSqKm: 1.68,
      totalSegmentsCount: 310,
      activeRoversCount: 1,
      nominalPressurePsi: 60,
      fillColor: "#38bdf8",
    },
  },

  // Sector 3: Northern Residential Zone
  {
    type: "Feature",
    id: "ZONE-SEC-03",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [-74.0150, 40.7180],
          [-73.9920, 40.7180],
          [-73.9920, 40.7260],
          [-74.0150, 40.7260],
          [-74.0150, 40.7180],
        ],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      zoneId: "ZONE-SEC-03",
      name: "Sector 3 — Northern Residential Enclave",
      sectorCode: "SEC-03",
      riskScorePct: 41.2,
      areaSqKm: 2.15,
      totalSegmentsCount: 295,
      activeRoversCount: 1,
      nominalPressurePsi: 52,
      fillColor: "#10b981",
    },
  },

  // Sector 2: Southern Harbor & Coastal Zone
  {
    type: "Feature",
    id: "ZONE-SEC-02",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [-74.0180, 40.7020],
          [-74.0020, 40.7020],
          [-74.0020, 40.7100],
          [-74.0180, 40.7100],
          [-74.0180, 40.7020],
        ],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      zoneId: "ZONE-SEC-02",
      name: "Sector 2 — Maritime Utility & Harbor District",
      sectorCode: "SEC-02",
      riskScorePct: 48.0,
      areaSqKm: 1.82,
      totalSegmentsCount: 215,
      activeRoversCount: 1,
      nominalPressurePsi: 58,
      fillColor: "#818cf8",
    },
  },
];

export function getZonesGeoJson(): ZoneFeatureCollection {
  return {
    type: "FeatureCollection",
    features: ZONE_FEATURES,
  };
}

