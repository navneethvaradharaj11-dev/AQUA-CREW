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
  // Sector 4: Bengaluru CBD & Vidhana Soudha (Highest density, central hub)
  {
    type: "Feature",
    id: "ZONE-SEC-04",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [77.5800, 12.9620],
          [77.6100, 12.9620],
          [77.6100, 12.9820],
          [77.5800, 12.9820],
          [77.5800, 12.9620],
        ],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      zoneId: "ZONE-SEC-04",
      name: "Sector 4 — Bengaluru CBD & Vidhana Soudha",
      sectorCode: "SEC-04",
      riskScorePct: 84.5,
      areaSqKm: 2.25,
      totalSegmentsCount: 420,
      activeRoversCount: 1,
      nominalPressurePsi: 65,
      fillColor: "#06b6d4",
    },
  },

  // Sector 1: Indiranagar & HAL Tech Corridor
  {
    type: "Feature",
    id: "ZONE-SEC-01",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [77.6100, 12.9620],
          [77.6500, 12.9620],
          [77.6500, 12.9900],
          [77.6100, 12.9900],
          [77.6100, 12.9620],
        ],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      zoneId: "ZONE-SEC-01",
      name: "Sector 1 — Indiranagar & HAL Tech Corridor",
      sectorCode: "SEC-01",
      riskScorePct: 62.0,
      areaSqKm: 3.10,
      totalSegmentsCount: 310,
      activeRoversCount: 1,
      nominalPressurePsi: 60,
      fillColor: "#38bdf8",
    },
  },

  // Sector 3: Malleshwaram & Sadashivanagar
  {
    type: "Feature",
    id: "ZONE-SEC-03",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [77.5600, 12.9820],
          [77.6100, 12.9820],
          [77.6100, 13.0150],
          [77.5600, 13.0150],
          [77.5600, 12.9820],
        ],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      zoneId: "ZONE-SEC-03",
      name: "Sector 3 — Malleshwaram & Sadashivanagar",
      sectorCode: "SEC-03",
      riskScorePct: 41.2,
      areaSqKm: 2.85,
      totalSegmentsCount: 295,
      activeRoversCount: 1,
      nominalPressurePsi: 52,
      fillColor: "#10b981",
    },
  },

  // Sector 2: Koramangala & South Distribution
  {
    type: "Feature",
    id: "ZONE-SEC-02",
    geometry: {
      type: "Polygon",
      coordinates: [
        [
          [77.5800, 12.9250],
          [77.6400, 12.9250],
          [77.6400, 12.9620],
          [77.5800, 12.9620],
          [77.5800, 12.9250],
        ],
      ],
    },
    properties: {
      isSimulated: true,
      provenance: "VIRTUAL_METROPOLITAN_DEMO_GRID",
      zoneId: "ZONE-SEC-02",
      name: "Sector 2 — Koramangala & South Distribution",
      sectorCode: "SEC-02",
      riskScorePct: 48.0,
      areaSqKm: 3.40,
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
