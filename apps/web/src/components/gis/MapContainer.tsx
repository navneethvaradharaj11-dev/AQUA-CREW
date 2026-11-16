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

    // Demonstration Area Bounding Box around Lower Manhattan / Metro Simulation Grid
    const NETWORK_BOUNDS: [[number, number], [number, number]] = [
      [-74.020, 40.702], // Southwest
      [-73.990, 40.728], // Northeast
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
          center: [-74.0060, 40.7128],
          zoom: 14.2,
          pitch: 30, // Subtle SCADA 3D tilt
          attributionControl: false,
        });
      } catch (e) {
        console.error("Failed to construct MapLibreMap:", e);
        return;
      }

      map.addControl(
        new AttributionControl({ compact: true }),
        "bottom-right"
      );
      map.addControl(
        new NavigationControl({ showCompass: true, showZoom: true }),
        "top-right"
      );

      map.on("load", async () => {
        try {
          if (!mapRef.current) return;

          // 1. Add Inspection Zones (Polygons)
          const zonesGeoJson = getZonesGeoJson();
          if (mapRef.current && !mapRef.current.getSource("zones-source")) {
            mapRef.current.addSource("zones-source", {
              type: "geojson",
              data: zonesGeoJson as any,
            });

            mapRef.current.addLayer({
              id: "zones-fill-layer",
              type: "fill",
              source: "zones-source",
              paint: {
                "fill-color": ["get", "fillColor"],
                "fill-opacity": 0.08,
              },
            });

            mapRef.current.addLayer({
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
          }

          if (!mapRef.current) return;

          // 2. Add Pipeline Network (LineStrings)
          const pipelinesGeoJson = getPipelineGeoJson();
          if (mapRef.current && !mapRef.current.getSource("pipelines-source")) {
            mapRef.current.addSource("pipelines-source", {
              type: "geojson",
              data: pipelinesGeoJson as any,
            });

            // Primary Trunk Lines
            mapRef.current.addLayer({
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
            mapRef.current.addLayer({
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
            mapRef.current.addLayer({
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
            mapRef.current.addLayer({
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
          }

          if (!mapRef.current) return;

          // 3. Add Stationary Sensor Stations (Points)
          const sensorsGeoJson = getSensorsGeoJson();
          if (mapRef.current && !mapRef.current.getSource("sensors-source")) {
            mapRef.current.addSource("sensors-source", {
              type: "geojson",
              data: sensorsGeoJson as any,
            });

            mapRef.current.addLayer({
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
          }

          if (!mapRef.current) return;

          // 4. Add Leak Incidents (Points)
          const incidentsGeoJson = await getIncidentsGeoJson();
          if (mapRef.current && !mapRef.current.getSource("incidents-source")) {
            mapRef.current.addSource("incidents-source", {
              type: "geojson",
              data: incidentsGeoJson as any,
            });

            // Incident Pulsing Aura
            mapRef.current.addLayer({
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
            mapRef.current.addLayer({
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
          }

          if (!mapRef.current) return;

          // 5. Add Rover Fleet (Points)
          const roversGeoJson = await getRoversGeoJson();
          if (mapRef.current && !mapRef.current.getSource("rovers-source")) {
            mapRef.current.addSource("rovers-source", {
              type: "geojson",
              data: roversGeoJson as any,
            });

            // Rover Glow Aura
            mapRef.current.addLayer({
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
            mapRef.current.addLayer({
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
          }

          setIsMapLoaded(true);
        } catch (err) {
          console.error("Error setting up map layers:", err);
        }
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
            if (mapRef.current) {
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

MapContainer.displayName = "MapContainer";
