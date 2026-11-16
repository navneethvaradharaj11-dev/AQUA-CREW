"use client";

import React, { useEffect, useRef, useImperativeHandle, forwardRef, useState } from "react";
import {
  Map as MapLibreMap,
  NavigationControl,
  AttributionControl,
  type StyleSpecification,
  type MapLayerMouseEvent,
  type RasterTileSource,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import {
  MapLayerVisibilityState,
  SelectedMapFeature,
} from "@/services/gis/types";
import { getPipelineGeoJson } from "@/services/gis/pipelineGeoService";
import { getZonesGeoJson } from "@/services/gis/zonesGeoService";
import {
  getRoversGeoJson,
  getIncidentsGeoJson,
  getSensorsGeoJson,
} from "@/services/gis/gisSimulationAdapter";
import { roverEventBus } from "@/services/simulation/roverEventBus";

export interface MapContainerHandle {
  flyTo: (coords: [number, number], zoom?: number) => void;
  fitBounds: () => void;
  resetBearing: () => void;
}

export interface MapContainerProps {
  layers: MapLayerVisibilityState;
  basemapStyle: "dark" | "light" | "osm";
  onSelectFeature: (feature: SelectedMapFeature) => void;
  onMouseMoveCoords: (coords: { lng: number; lat: number }) => void;
  onZoomChange: (zoom: number) => void;
}

export const MapContainer = forwardRef<MapContainerHandle, MapContainerProps>(
  (
    {
      layers,
      basemapStyle,
      onSelectFeature,
      onMouseMoveCoords,
      onZoomChange,
    },
    ref
  ) => {
    const mapContainerRef = useRef<HTMLDivElement>(null);
    const mapRef = useRef<MapLibreMap | null>(null);
    const [isMapLoaded, setIsMapLoaded] = useState(false);

    // Demonstration Area Bounding Box around Lower Manhattan / Metro Simulation Grid
    const NETWORK_BOUNDS: [[number, number], [number, number]] = [
      [-74.020, 40.702], // Southwest
      [-73.990, 40.728], // Northeast
    ];

    const getBasemapStyle = (style: "dark" | "light" | "osm"): StyleSpecification => {
      const tileUrls = {
        dark: [
          "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
          "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
          "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
        ],
        light: [
          "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
          "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
          "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
        ],
        osm: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
      }[style];

      return {
        version: 8,
        sources: {
          "basemap-tiles": {
            type: "raster",
            tiles: tileUrls,
            tileSize: 256,
            attribution:
              style === "osm"
                ? '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
          },
        },
        layers: [
          {
            id: "basemap-layer",
            type: "raster",
            source: "basemap-tiles",
            minzoom: 0,
            maxzoom: 20,
          },
        ],
      };
    };

    // Imperative Camera Controls
    useImperativeHandle(ref, () => ({
      flyTo: (coords: [number, number], zoom = 15) => {
        mapRef.current?.flyTo({
          center: coords,
          zoom,
          essential: true,
          speed: 1.2,
        });
      },
      fitBounds: () => {
        mapRef.current?.fitBounds(NETWORK_BOUNDS, {
          padding: 60,
          essential: true,
        });
      },
      resetBearing: () => {
        mapRef.current?.resetNorthPitch({ duration: 800 });
      },
    }));

    // Initialize Map on mount
    useEffect(() => {
      if (!mapContainerRef.current) return;

      const map = new MapLibreMap({
        container: mapContainerRef.current,
        style: getBasemapStyle(basemapStyle),
        center: [-74.0060, 40.7128],
        zoom: 14.2,
        pitch: 30, // Subtle SCADA 3D tilt
        attributionControl: false,
      });

      map.addControl(
        new AttributionControl({ compact: true }),
        "bottom-right"
      );
      map.addControl(
        new NavigationControl({ showCompass: true, showZoom: true }),
        "top-right"
      );

      map.on("load", async () => {
        // 1. Add Inspection Zones (Polygons)
        const zonesGeoJson = getZonesGeoJson();
        map.addSource("zones-source", {
          type: "geojson",
          data: zonesGeoJson as any,
        });

        map.addLayer({
          id: "zones-fill-layer",
          type: "fill",
          source: "zones-source",
          paint: {
            "fill-color": ["get", "fillColor"],
            "fill-opacity": 0.08,
          },
        });

        map.addLayer({
          id: "zones-outline-layer",
          type: "line",
          source: "zones-source",
          paint: {
            "line-color": ["get", "fillColor"],
            "line-width": 1.5,
            "line-dasharray": [3, 2],
            "line-opacity": 0.5,
          },
        });

        // 2. Add Pipeline Network (LineStrings)
        const pipelinesGeoJson = getPipelineGeoJson();
        map.addSource("pipelines-source", {
          type: "geojson",
          data: pipelinesGeoJson as any,
        });

        // Primary Trunk Lines
        map.addLayer({
          id: "pipelines-primary-layer",
          type: "line",
          source: "pipelines-source",
          filter: ["==", ["get", "category"], "primary"],
          paint: {
            "line-color": "#06b6d4",
            "line-width": 4.5,
            "line-opacity": 0.9,
          },
        });

        // Secondary Feeder Lines
        map.addLayer({
          id: "pipelines-secondary-layer",
          type: "line",
          source: "pipelines-source",
          filter: ["==", ["get", "category"], "secondary"],
          paint: {
            "line-color": "#38bdf8",
            "line-width": 3.2,
            "line-opacity": 0.85,
          },
        });

        // Distribution Lines
        map.addLayer({
          id: "pipelines-distribution-layer",
          type: "line",
          source: "pipelines-source",
          filter: ["==", ["get", "category"], "distribution"],
          paint: {
            "line-color": "#14b8a6",
            "line-width": 2.5,
            "line-opacity": 0.8,
          },
        });

        // Service Laterals (Dashed)
        map.addLayer({
          id: "pipelines-service-layer",
          type: "line",
          source: "pipelines-source",
          filter: ["==", ["get", "category"], "service"],
          paint: {
            "line-color": "#94a3b8",
            "line-width": 1.8,
            "line-dasharray": [2, 2],
            "line-opacity": 0.75,
          },
        });

        // 3. Add Stationary Sensor Stations (Points)
        const sensorsGeoJson = getSensorsGeoJson();
        map.addSource("sensors-source", {
          type: "geojson",
          data: sensorsGeoJson as any,
        });

        map.addLayer({
          id: "sensors-point-layer",
          type: "circle",
          source: "sensors-source",
          paint: {
            "circle-radius": 5.5,
            "circle-color": "#38bdf8",
            "circle-stroke-width": 1.5,
            "circle-stroke-color": "#02060e",
          },
        });

        // 4. Add Leak Incidents (Points)
        const incidentsGeoJson = await getIncidentsGeoJson();
        map.addSource("incidents-source", {
          type: "geojson",
          data: incidentsGeoJson as any,
        });

        // Incident Pulsing Aura
        map.addLayer({
          id: "incidents-glow-layer",
          type: "circle",
          source: "incidents-source",
          paint: {
            "circle-radius": 14,
            "circle-color": [
              "match",
              ["get", "severity"],
              "Critical",
              "rgba(239, 68, 68, 0.35)",
              "High",
              "rgba(245, 158, 11, 0.35)",
              "Medium",
              "rgba(6, 182, 212, 0.3)",
              "rgba(100, 116, 139, 0.25)",
            ],
            "circle-blur": 0.8,
          },
        });

        // Incident Core Marker
        map.addLayer({
          id: "incidents-point-layer",
          type: "circle",
          source: "incidents-source",
          paint: {
            "circle-radius": 7,
            "circle-color": [
              "match",
              ["get", "severity"],
              "Critical",
              "#ef4444",
              "High",
              "#f59e0b",
              "Medium",
              "#06b6d4",
              "#94a3b8",
            ],
            "circle-stroke-width": 2,
            "circle-stroke-color": "#ffffff",
          },
        });

        // 5. Add Rover Fleet (Points)
        const roversGeoJson = await getRoversGeoJson();
        map.addSource("rovers-source", {
          type: "geojson",
          data: roversGeoJson as any,
        });

        // Rover Glow Aura
        map.addLayer({
          id: "rovers-glow-layer",
          type: "circle",
          source: "rovers-source",
          paint: {
            "circle-radius": 16,
            "circle-color": "rgba(16, 185, 129, 0.3)",
            "circle-blur": 0.6,
          },
        });

        // Rover Core Marker
        map.addLayer({
          id: "rovers-point-layer",
          type: "circle",
          source: "rovers-source",
          paint: {
            "circle-radius": 8.5,
            "circle-color": [
              "match",
              ["get", "status"],
              "ACTIVE",
              "#10b981",
              "ONLINE",
              "#06b6d4",
              "WARNING",
              "#f59e0b",
              "#64748b",
            ],
            "circle-stroke-width": 2.5,
            "circle-stroke-color": "#ffffff",
          },
        });

        setIsMapLoaded(true);
      });

      // Cursor & Coordinate Tracking
      map.on("mousemove", (e: MapLayerMouseEvent) => {
        onMouseMoveCoords({ lng: e.lngLat.lng, lat: e.lngLat.lat });
      });

      map.on("zoom", () => {
        onZoomChange(map.getZoom());
      });

      // Feature Click Handlers
      const interactiveLayers = [
        "pipelines-primary-layer",
        "pipelines-secondary-layer",
        "pipelines-distribution-layer",
        "pipelines-service-layer",
        "incidents-point-layer",
        "rovers-point-layer",
        "sensors-point-layer",
        "zones-fill-layer",
      ];

      interactiveLayers.forEach((layerId) => {
        map.on("mouseenter", layerId, () => {
          map.getCanvas().style.cursor = "pointer";
        });
        map.on("mouseleave", layerId, () => {
          map.getCanvas().style.cursor = "";
        });
      });

      // Pipeline Click
      [
        "pipelines-primary-layer",
        "pipelines-secondary-layer",
        "pipelines-distribution-layer",
        "pipelines-service-layer",
      ].forEach((layerId) => {
        map.on("click", layerId, (e: MapLayerMouseEvent) => {
          const feature = e.features?.[0];
          if (!feature) return;
          const props = feature.properties || {};
          onSelectFeature({
            type: "pipeline",
            id: String(props.segmentId || feature.id),
            title: String(props.name || "Pipeline Segment"),
            properties: props,
          });
        });
      });

      // Incident Click
      map.on("click", "incidents-point-layer", (e: MapLayerMouseEvent) => {
        const feature = e.features?.[0];
        if (!feature) return;
        const props = feature.properties || {};
        onSelectFeature({
          type: "incident",
          id: String(props.incidentId || feature.id),
          title: `Leak Alert: ${props.incidentId}`,
          properties: props,
        });
      });

      // Rover Click
      map.on("click", "rovers-point-layer", (e: MapLayerMouseEvent) => {
        const feature = e.features?.[0];
        if (!feature) return;
        const props = feature.properties || {};
        onSelectFeature({
          type: "rover",
          id: String(props.roverId || feature.id),
          title: String(props.name || "Autonomous Rover"),
          properties: props,
        });
      });

      // Sensor Click
      map.on("click", "sensors-point-layer", (e: MapLayerMouseEvent) => {
        const feature = e.features?.[0];
        if (!feature) return;
        const props = feature.properties || {};
        onSelectFeature({
          type: "sensor",
          id: String(props.stationId || feature.id),
          title: String(props.name || "Sensor Station"),
          properties: props,
        });
      });

      // Zone Click
      map.on("click", "zones-fill-layer", (e: MapLayerMouseEvent) => {
        const feature = e.features?.[0];
        if (!feature) return;
        const props = feature.properties || {};
        onSelectFeature({
          type: "zone",
          id: String(props.zoneId || feature.id),
          title: String(props.name || "Inspection Zone"),
          properties: props,
        });
      });

      mapRef.current = map;

      return () => {
        map.remove();
        mapRef.current = null;
      };
    }, []);

    // Update Basemap when basemapStyle changes
    useEffect(() => {
      if (!mapRef.current || !isMapLoaded) return;
      const source = mapRef.current.getSource("basemap-tiles") as RasterTileSource;
      if (source && source.tiles) {
        const tileUrls = {
          dark: [
            "https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
            "https://b.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
            "https://c.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
          ],
          light: [
            "https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
            "https://b.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
            "https://c.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
          ],
          osm: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        }[basemapStyle];

        // MapLibre doesn't have setTiles directly on all raster sources, so we update the source
        // Safely check and trigger repaint
        mapRef.current.triggerRepaint();
      }
    }, [basemapStyle, isMapLoaded]);

    // Update Layer Visibility dynamically without recreating the map
    useEffect(() => {
      if (!mapRef.current || !isMapLoaded) return;
      const map = mapRef.current;

      const setVisibility = (layerId: string, visible: boolean) => {
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none");
        }
      };

      // Pipelines
      setVisibility("pipelines-primary-layer", layers.pipelines.primary);
      setVisibility("pipelines-secondary-layer", layers.pipelines.secondary);
      setVisibility("pipelines-distribution-layer", layers.pipelines.distribution);
      setVisibility("pipelines-service-layer", layers.pipelines.service);

      // Incidents (by severity filter)
      const visibleSeverities = [
        ...(layers.leakIncidents.critical ? ["Critical"] : []),
        ...(layers.leakIncidents.high ? ["High"] : []),
        ...(layers.leakIncidents.medium ? ["Medium"] : []),
        ...(layers.leakIncidents.low ? ["Low"] : []),
      ];

      const anyIncidentVisible = visibleSeverities.length > 0;
      setVisibility("incidents-glow-layer", anyIncidentVisible);
      setVisibility("incidents-point-layer", anyIncidentVisible);
      if (anyIncidentVisible && map.getLayer("incidents-point-layer")) {
        map.setFilter("incidents-point-layer", ["in", ["get", "severity"], ["literal", visibleSeverities]]);
        map.setFilter("incidents-glow-layer", ["in", ["get", "severity"], ["literal", visibleSeverities]]);
      }

      // Rovers
      setVisibility("rovers-glow-layer", layers.rovers);
      setVisibility("rovers-point-layer", layers.rovers);

      // Sensors
      const visibleModalities = [
        ...(layers.sensorStations.acoustic ? ["acoustic"] : []),
        ...(layers.sensorStations.pressure ? ["pressure"] : []),
        ...(layers.sensorStations.flow ? ["flow"] : []),
        ...(layers.sensorStations.thermal ? ["thermal"] : []),
        ...(layers.sensorStations.moisture ? ["moisture"] : []),
      ];

      const anySensorVisible = visibleModalities.length > 0;
      setVisibility("sensors-point-layer", anySensorVisible);
      if (anySensorVisible && map.getLayer("sensors-point-layer")) {
        map.setFilter("sensors-point-layer", ["in", ["get", "modality"], ["literal", visibleModalities]]);
      }

      // Zones
      setVisibility("zones-fill-layer", layers.inspectionZones);
      setVisibility("zones-outline-layer", layers.inspectionZones);
    }, [layers, isMapLoaded]);

    // Dynamically update Rover positions when Simulation Engine emits telemetry updates
    useEffect(() => {
      if (!mapRef.current || !isMapLoaded) return;

      const unsubscribe = roverEventBus.subscribe("ROVER_TELEMETRY_UPDATED", async () => {
        if (!mapRef.current) return;
        const source = mapRef.current.getSource("rovers-source") as any;
        if (source && typeof source.setData === "function") {
          const updatedRovers = await getRoversGeoJson();
          source.setData(updatedRovers as any);
        }
      });

      return () => {
        unsubscribe();
      };
    }, [isMapLoaded]);

    return (
      <div className="relative w-full h-full min-h-[500px]">
        <div ref={mapContainerRef} className="absolute inset-0 w-full h-full rounded-xl overflow-hidden" />
      </div>
    );
  }
);

MapContainer.displayName = "MapContainer";
