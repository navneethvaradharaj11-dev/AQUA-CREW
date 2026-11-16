"use client";

import React, { useState, useRef } from "react";
import {
  MapLayerVisibilityState,
  SelectedMapFeature,
} from "@/services/gis/types";
import { MapContainer, MapContainerHandle } from "./MapContainer";
import { MapToolbar } from "./MapToolbar";
import { MapSearchBar } from "./MapSearchBar";
import { CoordinateDisplay } from "./CoordinateDisplay";
import { LayerControlPanel } from "./LayerControlPanel";
import { MapLegend } from "./MapLegend";
import { FeatureInfoPanel } from "./FeatureInfoPanel";
import { RoverDetailModal } from "@/components/dashboard/RoverDetailModal";
import { IncidentDetailModal } from "@/components/dashboard/IncidentDetailModal";
import { fetchRoverById, SimulatedRover } from "@/services/simulation/roverService";
import { fetchIncidentById, SimulatedLeakIncident } from "@/services/simulation/incidentService";
import { getPipelineSegmentById } from "@/services/gis/pipelineGeoService";

export function MapIntelligenceView() {
  const mapHandleRef = useRef<MapContainerHandle>(null);

  // Map Controls State
  const [basemapStyle, setBasemapStyle] = useState<"dark" | "light" | "osm">("dark");
  const [isLayerPanelOpen, setIsLayerPanelOpen] = useState(false);
  const [isLegendOpen, setIsLegendOpen] = useState(true);
  const [cursorCoords, setCursorCoords] = useState<{ lng: number; lat: number } | null>(null);
  const [currentZoom, setCurrentZoom] = useState(14.2);

  // Selected Feature & Modal States
  const [selectedFeature, setSelectedFeature] = useState<SelectedMapFeature | null>(null);
  const [modalRover, setModalRover] = useState<SimulatedRover | null>(null);
  const [modalIncident, setModalIncident] = useState<SimulatedLeakIncident | null>(null);

  // Layer Visibility State
  const [layers, setLayers] = useState<MapLayerVisibilityState>({
    pipelines: {
      primary: true,
      secondary: true,
      distribution: true,
      service: true,
    },
    leakIncidents: {
      critical: true,
      high: true,
      medium: true,
      low: true,
    },
    rovers: true,
    sensorStations: {
      acoustic: true,
      pressure: true,
      flow: true,
      thermal: true,
      moisture: true,
    },
    inspectionZones: true,
  });

  const handleOpenRoverModal = async (roverId: string) => {
    const rover = await fetchRoverById(roverId);
    if (rover) setModalRover(rover);
  };

  const handleOpenIncidentModal = async (incidentId: string) => {
    const incident = await fetchIncidentById(incidentId);
    if (incident) setModalIncident(incident);
  };

  const handleSelectFeatureById = async (
    type: "pipeline" | "incident" | "rover" | "zone",
    id: string
  ) => {
    if (type === "pipeline") {
      const p = getPipelineSegmentById(id);
      if (p) {
        setSelectedFeature({
          type: "pipeline",
          id: p.properties.segmentId,
          title: p.properties.name,
          properties: p.properties as any,
        });
      }
    } else if (type === "incident") {
      const inc = await fetchIncidentById(id);
      if (inc) {
        setSelectedFeature({
          type: "incident",
          id: inc.id,
          title: `Leak Alert: ${inc.id}`,
          properties: {
            ...inc,
            incidentId: inc.id,
            segmentName: inc.segmentName,
            segmentId: inc.pipelineSegmentId,
          },
        });
      }
    } else if (type === "rover") {
      const r = await fetchRoverById(id);
      if (r) {
        setSelectedFeature({
          type: "rover",
          id: r.id,
          title: r.name,
          properties: {
            ...r,
            roverId: r.id,
            stationName: r.currentLocation.stationName,
            velocityMps: r.kinematics.velocityMps,
            headingDeg: r.kinematics.headingDeg,
          },
        });
      }
    }
  };

  return (
    <div className="relative w-full h-[calc(100vh-6rem)] min-h-[600px] rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl flex flex-col">
      {/* 1. Map Canvas with WebGL MapLibre */}
      <div className="relative flex-1 w-full h-full">
        <MapContainer
          ref={mapHandleRef}
          layers={layers}
          basemapStyle={basemapStyle}
          onSelectFeature={(feat) => setSelectedFeature(feat)}
          onMouseMoveCoords={(coords) => setCursorCoords(coords)}
          onZoomChange={(zoom) => setCurrentZoom(zoom)}
        />

        {/* 2. Map Toolbar */}
        <MapToolbar
          onFitBounds={() => mapHandleRef.current?.fitBounds()}
          onCenterMetro={() => mapHandleRef.current?.flyTo([-74.0060, 40.7128], 15)}
          onResetBearing={() => mapHandleRef.current?.resetBearing()}
          basemapStyle={basemapStyle}
          onChangeBasemap={(style) => setBasemapStyle(style)}
          isLayerPanelOpen={isLayerPanelOpen}
          onToggleLayerPanel={() => setIsLayerPanelOpen(!isLayerPanelOpen)}
          isLegendOpen={isLegendOpen}
          onToggleLegend={() => setIsLegendOpen(!isLegendOpen)}
        />

        {/* 3. Search Bar */}
        <MapSearchBar
          onFlyTo={(coords, zoom) => mapHandleRef.current?.flyTo(coords, zoom)}
          onSelectFeatureId={handleSelectFeatureById}
        />

        {/* 4. Live Coordinate & Zoom Bar */}
        <CoordinateDisplay coords={cursorCoords} zoom={currentZoom} />

        {/* 5. Layer Visibility Panel (Collapsible) */}
        {isLayerPanelOpen && (
          <LayerControlPanel
            layers={layers}
            onChangeLayers={(newLayers) => setLayers(newLayers)}
            onClose={() => setIsLayerPanelOpen(false)}
          />
        )}

        {/* 6. Map Symbology Legend (Collapsible) */}
        {isLegendOpen && (
          <MapLegend onClose={() => setIsLegendOpen(false)} />
        )}

        {/* 7. Selected Feature Information Panel */}
        {selectedFeature && (
          <FeatureInfoPanel
            feature={selectedFeature}
            onClose={() => setSelectedFeature(null)}
            onOpenRoverModal={handleOpenRoverModal}
            onOpenIncidentModal={handleOpenIncidentModal}
          />
        )}
      </div>

      {/* Reused Modals for Deep Telemetry Drilling */}
      <RoverDetailModal
        rover={modalRover}
        onClose={() => setModalRover(null)}
      />

      <IncidentDetailModal
        incident={modalIncident}
        onClose={() => setModalIncident(null)}
      />
    </div>
  );
}

