"use client";

import React, { useEffect, useRef, useImperativeHandle, forwardRef, useState } from "react";
import {
  Map as MapLibreMap,
  NavigationControl,
  AttributionControl,
  type StyleSpecification,
  type MapLayerMouseEvent,
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

    // Demonstration Area Bounding Box around Bengaluru (BWSSB Urban Water Supply Grid)
    const NETWORK_BOUNDS: [[number, number], [number, number]] = [
      [77.5400, 12.9100], // Southwest (South Koramangala / Dairy Circle)
      [77.6600, 13.0200], // Northeast (Indiranagar / Malleshwaram North)
    ];

    const getBasemapStyle = (style: "dark" | "light" | "osm"): StyleSpecification => {
      return {
        version: 8,
        sources: {
          "basemap-dark-tiles": {
            type: "raster",
            tiles: [
              "https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
            ],
            tileSize: 256,
            maxzoom: 16,
            attribution:
              '&copy; <a href="https://www.esri.com" target="_blank" rel="noopener">Esri</a> &mdash; SCADA Dark Gray Base',
          },
          "basemap-light-tiles": {
            type: "raster",
            tiles: [
              "https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
            ],
            tileSize: 256,
            maxzoom: 16,
            attribution:
              '&copy; <a href="https://www.esri.com" target="_blank" rel="noopener">Esri</a> &mdash; Light Gray Canvas',
          },
          "basemap-osm-tiles": {
            type: "raster",
            tiles: [
              "https://services.arcgisonline.com/arcgis/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
            ],
            tileSize: 256,
            maxzoom: 19,
            attribution:
              '&copy; <a href="https://www.esri.com" target="_blank" rel="noopener">Esri</a> &mdash; World Street Map',
          },
        },
        layers: [
          {
            id: "basemap-dark-layer",
            type: "raster",
            source: "basemap-dark-tiles",
            minzoom: 0,
            maxzoom: 22,
            layout: {
              visibility: style === "dark" ? "visible" : "none",
            },
          },
          {
            id: "basemap-light-layer",
            type: "raster",
            source: "basemap-light-tiles",
            minzoom: 0,
            maxzoom: 22,
            layout: {
              visibility: style === "light" ? "visible" : "none",
            },
          },
          {
            id: "basemap-osm-layer",
            type: "raster",
            source: "basemap-osm-tiles",
            minzoom: 0,
            maxzoom: 22,
            layout: {
              visibility: style === "osm" ? "visible" : "none",
            },
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

      // Check WebGL availability safely
      const isWebGLSupported = () => {
        try {
          const canvas = document.createElement("canvas");
          return !!(
            window.WebGLRenderingContext &&
            (canvas.getContext("webgl") || canvas.getContext("experimental-webgl"))
          );
        } catch {
          return false;
        }
      };

      if (!isWebGLSupported()) {
        console.warn("WebGL is not supported or hardware acceleration is disabled.");
        return;
      }

      let map: MapLibreMap;
      try {
        map = new MapLibreMap({
          container: mapContainerRef.current,
          style: getBasemapStyle(basemapStyle),
          center: [77.5946, 12.9716], // Bengaluru MG Road / Vidhana Soudha Central Core
          zoom: 14.2,
          pitch: 30, // Subtle SCADA 3D tilt
          attributionControl: false,
        });
      } catch (e) {
        console.error("Failed to construct MapLibreMap:", e);
        return;
      }

      // Keep ref immediately available
      mapRef.current = map;

      map.addControl(
        new AttributionControl({ compact: true }),
        "bottom-right"
      );
      map.addControl(
        new NavigationControl({ showCompass: true, showZoom: true }),
        "top-right"
      );

      const addLayers = async () => {
        try {
          if (!map) return;

          // 1. Add Inspection Zones (Polygons)
          const zonesGeoJson = getZonesGeoJson();
          if (!map.getSource("zones-source")) {
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
                "fill-opacity": 0.12,
              },
            });

            map.addLayer({
              id: "zones-outline-layer",
              type: "line",
              source: "zones-source",
              paint: {
                "line-color": ["get", "fillColor"],
                "line-width": 2.0,
                "line-dasharray": [3, 2],
                "line-opacity": 0.75,
              },
            });
          }

          // 2. Add Pipeline Network (LineStrings)
          const pipelinesGeoJson = getPipelineGeoJson();
          if (!map.getSource("pipelines-source")) {
            map.addSource("pipelines-source", {
              type: "geojson",
              data: pipelinesGeoJson as any,
            });

            // Glowing Casings for high contrast
            map.addLayer({
              id: "pipelines-casing-layer",
              type: "line",
              source: "pipelines-source",
              paint: {
                "line-color": "#0284c7",
                "line-width": 8.0,
                "line-opacity": 0.25,
                "line-blur": 2.0,
              },
            });

            // Primary Trunk Lines
            map.addLayer({
              id: "pipelines-primary-layer",
              type: "line",
              source: "pipelines-source",
              filter: ["==", ["get", "category"], "primary"],
              paint: {
                "line-color": "#00f0ff",
                "line-width": 5.5,
                "line-opacity": 0.95,
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
                "line-width": 3.8,
                "line-opacity": 0.9,
              },
            });

            // Distribution Lines
            map.addLayer({
              id: "pipelines-distribution-layer",
              type: "line",
              source: "pipelines-source",
              filter: ["==", ["get", "category"], "distribution"],
              paint: {
                "line-color": "#2dd4bf",
                "line-width": 3.0,
                "line-opacity": 0.85,
              },
            });

            // Service Laterals (Dashed)
            map.addLayer({
              id: "pipelines-service-layer",
              type: "line",
              source: "pipelines-source",
              filter: ["==", ["get", "category"], "service"],
              paint: {
                "line-color": "#e2e8f0",
                "line-width": 2.2,
                "line-dasharray": [3, 2],
                "line-opacity": 0.8,
              },
            });
          }

          // 3. Add Stationary Sensor Stations (Points)
          const sensorsGeoJson = getSensorsGeoJson();
          if (!map.getSource("sensors-source")) {
            map.addSource("sensors-source", {
              type: "geojson",
              data: sensorsGeoJson as any,
            });

            map.addLayer({
              id: "sensors-point-layer",
              type: "circle",
              source: "sensors-source",
              paint: {
                "circle-radius": 7.0,
                "circle-color": "#38bdf8",
                "circle-stroke-width": 2.0,
                "circle-stroke-color": "#020617",
              },
            });
          }

          // 4. Add Leak Incidents (Points) — Initial sync fallback
          const defaultIncidents = {
            type: "FeatureCollection",
            features: [
              {
                type: "Feature",
                id: "INC-2026-081",
                geometry: { type: "Point", coordinates: [77.5946, 12.9716] },
                properties: { severity: "Critical", incidentId: "INC-2026-081", segmentName: "MG Road Trunk B" },
              },
              {
                type: "Feature",
                id: "INC-2026-079",
                geometry: { type: "Point", coordinates: [77.6200, 12.9770] },
                properties: { severity: "High", incidentId: "INC-2026-079", segmentName: "Indiranagar Feeder" },
              },
              {
                type: "Feature",
                id: "INC-2026-076",
                geometry: { type: "Point", coordinates: [77.5750, 12.9940] },
                properties: { severity: "Medium", incidentId: "INC-2026-076", segmentName: "Malleshwaram Feeder" },
              },
              {
                type: "Feature",
                id: "INC-2026-072",
                geometry: { type: "Point", coordinates: [77.6120, 12.9430] },
                properties: { severity: "Low", incidentId: "INC-2026-072", segmentName: "Koramangala South" },
              },
            ],
          };

          if (!map.getSource("incidents-source")) {
            map.addSource("incidents-source", {
              type: "geojson",
              data: defaultIncidents as any,
            });

            // Incident Pulsing Aura
            map.addLayer({
              id: "incidents-glow-layer",
              type: "circle",
              source: "incidents-source",
              paint: {
                "circle-radius": 20,
                "circle-color": [
                  "match",
                  ["get", "severity"],
                  "Critical",
                  "rgba(239, 68, 68, 0.45)",
                  "High",
                  "rgba(245, 158, 11, 0.45)",
                  "Medium",
                  "rgba(6, 182, 212, 0.4)",
                  "rgba(100, 116, 139, 0.35)",
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
                "circle-radius": 8.5,
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
                "circle-stroke-width": 2.5,
                "circle-stroke-color": "#ffffff",
              },
            });
          }

          // 5. Add Rover Fleet (Points) — Initial sync fallback
          const defaultRovers = {
            type: "FeatureCollection",
            features: [
              {
                type: "Feature",
                id: "ROV-AQUA-01",
                geometry: { type: "Point", coordinates: [77.5946, 12.9716] },
                properties: { roverId: "ROV-AQUA-01", name: "Triton-1 Crawler", status: "ACTIVE" },
              },
              {
                type: "Feature",
                id: "ROV-AQUA-02",
                geometry: { type: "Point", coordinates: [77.6200, 12.9770] },
                properties: { roverId: "ROV-AQUA-02", name: "Nautilus Ground Scout", status: "ACTIVE" },
              },
              {
                type: "Feature",
                id: "ROV-AQUA-03",
                geometry: { type: "Point", coordinates: [77.5750, 12.9940] },
                properties: { roverId: "ROV-AQUA-03", name: "Hydra Pipe Probe", status: "ONLINE" },
              },
              {
                type: "Feature",
                id: "ROV-AQUA-04",
                geometry: { type: "Point", coordinates: [77.6120, 12.9430] },
                properties: { roverId: "ROV-AQUA-04", name: "Aquila Surface Drone", status: "ACTIVE" },
              },
            ],
          };

          if (!map.getSource("rovers-source")) {
            map.addSource("rovers-source", {
              type: "geojson",
              data: defaultRovers as any,
            });

            // Rover Glow Aura
            map.addLayer({
              id: "rovers-glow-layer",
              type: "circle",
              source: "rovers-source",
              paint: {
                "circle-radius": 22,
                "circle-color": "rgba(16, 185, 129, 0.4)",
                "circle-blur": 0.6,
              },
            });

            // Rover Core Marker
            map.addLayer({
              id: "rovers-point-layer",
              type: "circle",
              source: "rovers-source",
              paint: {
                "circle-radius": 9.5,
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
          }

          setIsMapLoaded(true);

          // Asynchronously enrich incidents and rovers with dynamic backend data
          try {
            const dynamicIncidents = await getIncidentsGeoJson();
            if (dynamicIncidents?.features?.length) {
              const incSource = map.getSource("incidents-source") as any;
              if (incSource && typeof incSource.setData === "function") {
                incSource.setData(dynamicIncidents as any);
              }
            }
          } catch (e) {
            console.warn("Using fallback incidents data:", e);
          }

          try {
            const dynamicRovers = await getRoversGeoJson();
            if (dynamicRovers?.features?.length) {
              const rovSource = map.getSource("rovers-source") as any;
              if (rovSource && typeof rovSource.setData === "function") {
                rovSource.setData(dynamicRovers as any);
              }
            }
          } catch (e) {
            console.warn("Using fallback rovers data:", e);
          }
        } catch (err) {
          console.error("Error setting up map layers:", err);
        }
      };

      if (map.loaded()) {
        addLayers();
      } else {
        map.on("load", addLayers);
      }

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

      return () => {
        map.remove();
        mapRef.current = null;
      };
    }, []);

    // Update Basemap when basemapStyle changes
    useEffect(() => {
      if (!mapRef.current || !isMapLoaded) return;
      const map = mapRef.current;
      const setVisibility = (layerId: string, visible: boolean) => {
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none");
        }
      };

      setVisibility("basemap-dark-layer", basemapStyle === "dark");
      setVisibility("basemap-light-layer", basemapStyle === "light");
      setVisibility("basemap-osm-layer", basemapStyle === "osm");
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
      setVisibility("pipelines-casing-layer", layers.pipelines.primary || layers.pipelines.secondary);
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
        const source = mapRef.current?.getSource("rovers-source") as any;
        if (source && typeof source.setData === "function") {
          try {
            const updatedRovers = await getRoversGeoJson();
            if (mapRef.current && updatedRovers?.features?.length) {
              source.setData(updatedRovers as any);
            }
          } catch (e) {
            console.warn("Failed to update dynamic rover positions:", e);
          }
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
