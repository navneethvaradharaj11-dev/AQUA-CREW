"use client";

import React from "react";
import { MapLayerVisibilityState } from "@/services/gis/types";
import { Layers, X, CheckSquare, Square, Eye, EyeOff } from "lucide-react";

export interface LayerControlPanelProps {
  layers: MapLayerVisibilityState;
  onChangeLayers: (newLayers: MapLayerVisibilityState) => void;
  onClose: () => void;
}

export function LayerControlPanel({
  layers,
  onChangeLayers,
  onClose,
}: LayerControlPanelProps) {
  const togglePipelineSub = (key: keyof MapLayerVisibilityState["pipelines"]) => {
    onChangeLayers({
      ...layers,
      pipelines: {
        ...layers.pipelines,
        [key]: !layers.pipelines[key],
      },
    });
  };

  const toggleIncidentSub = (key: keyof MapLayerVisibilityState["leakIncidents"]) => {
    onChangeLayers({
      ...layers,
      leakIncidents: {
        ...layers.leakIncidents,
        [key]: !layers.leakIncidents[key],
      },
    });
  };

  const toggleSensorSub = (key: keyof MapLayerVisibilityState["sensorStations"]) => {
    onChangeLayers({
      ...layers,
      sensorStations: {
        ...layers.sensorStations,
        [key]: !layers.sensorStations[key],
      },
    });
  };

  return (
    <div className="absolute top-20 right-4 z-20 w-72 rounded-2xl border border-slate-800/90 bg-slate-950/90 p-4 backdrop-blur-xl shadow-2xl animate-in fade-in zoom-in-95 duration-150 space-y-4 max-h-[calc(100vh-140px)] overflow-y-auto">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-cyan-400" />
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-white">
            GIS Layer Controls
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-slate-500 hover:text-white transition-colors"
          aria-label="Close layer panel"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* 1. Pipeline Network */}
      <div className="space-y-2">
        <span className="text-[10px] font-mono uppercase text-slate-400 font-semibold block">
          Water Pipeline Network
        </span>
        <div className="space-y-1.5 pl-1">
          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-3.5 bg-cyan-400 rounded-sm inline-block" />
              Primary Trunk Mains
            </span>
            <input
              type="checkbox"
              checked={layers.pipelines.primary}
              onChange={() => togglePipelineSub("primary")}
              className="rounded accent-cyan-500"
            />
          </label>

          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-3.5 bg-sky-400 rounded-sm inline-block" />
              Secondary Feeders
            </span>
            <input
              type="checkbox"
              checked={layers.pipelines.secondary}
              onChange={() => togglePipelineSub("secondary")}
              className="rounded accent-cyan-500"
            />
          </label>

          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-3.5 bg-teal-400 rounded-sm inline-block" />
              Distribution Lines
            </span>
            <input
              type="checkbox"
              checked={layers.pipelines.distribution}
              onChange={() => togglePipelineSub("distribution")}
              className="rounded accent-cyan-500"
            />
          </label>

          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span className="flex items-center gap-2">
              <span className="h-1.5 w-3.5 border-b border-dashed border-slate-400 inline-block" />
              Service Laterals
            </span>
            <input
              type="checkbox"
              checked={layers.pipelines.service}
              onChange={() => togglePipelineSub("service")}
              className="rounded accent-cyan-500"
            />
          </label>
        </div>
      </div>

      {/* 2. Leak Incidents */}
      <div className="space-y-2 pt-2 border-t border-slate-800/80">
        <span className="text-[10px] font-mono uppercase text-slate-400 font-semibold block">
          Leak Incidents (Severity)
        </span>
        <div className="space-y-1.5 pl-1">
          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-rose-500" />
              Critical Breaches
            </span>
            <input
              type="checkbox"
              checked={layers.leakIncidents.critical}
              onChange={() => toggleIncidentSub("critical")}
              className="rounded accent-rose-500"
            />
          </label>

          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-amber-500" />
              High Priority Leaks
            </span>
            <input
              type="checkbox"
              checked={layers.leakIncidents.high}
              onChange={() => toggleIncidentSub("high")}
              className="rounded accent-amber-500"
            />
          </label>

          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-cyan-400" />
              Medium Anomalies
            </span>
            <input
              type="checkbox"
              checked={layers.leakIncidents.medium}
              onChange={() => toggleIncidentSub("medium")}
              className="rounded accent-cyan-500"
            />
          </label>

          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-slate-400" />
              Low / Weeping Leaks
            </span>
            <input
              type="checkbox"
              checked={layers.leakIncidents.low}
              onChange={() => toggleIncidentSub("low")}
              className="rounded accent-slate-500"
            />
          </label>
        </div>
      </div>

      {/* 3. Rover Fleet */}
      <div className="space-y-2 pt-2 border-t border-slate-800/80">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono uppercase text-slate-400 font-semibold block">
            Rover Fleet
          </span>
          <label className="cursor-pointer">
            <input
              type="checkbox"
              checked={layers.rovers}
              onChange={() => onChangeLayers({ ...layers, rovers: !layers.rovers })}
              className="rounded accent-emerald-500"
            />
          </label>
        </div>
      </div>

      {/* 4. Sensor Stations */}
      <div className="space-y-2 pt-2 border-t border-slate-800/80">
        <span className="text-[10px] font-mono uppercase text-slate-400 font-semibold block">
          IoT Sensor Stations
        </span>
        <div className="space-y-1.5 pl-1">
          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span>Acoustic Hydrophones</span>
            <input
              type="checkbox"
              checked={layers.sensorStations.acoustic}
              onChange={() => toggleSensorSub("acoustic")}
              className="rounded accent-cyan-500"
            />
          </label>

          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span>Pressure Transducers</span>
            <input
              type="checkbox"
              checked={layers.sensorStations.pressure}
              onChange={() => toggleSensorSub("pressure")}
              className="rounded accent-emerald-500"
            />
          </label>

          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span>Ultrasonic Flow Meters</span>
            <input
              type="checkbox"
              checked={layers.sensorStations.flow}
              onChange={() => toggleSensorSub("flow")}
              className="rounded accent-sky-500"
            />
          </label>

          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span>Thermal Soil Probes</span>
            <input
              type="checkbox"
              checked={layers.sensorStations.thermal}
              onChange={() => toggleSensorSub("thermal")}
              className="rounded accent-amber-500"
            />
          </label>

          <label className="flex items-center justify-between text-xs text-slate-200 cursor-pointer">
            <span>Moisture Sensors</span>
            <input
              type="checkbox"
              checked={layers.sensorStations.moisture}
              onChange={() => toggleSensorSub("moisture")}
              className="rounded accent-teal-500"
            />
          </label>
        </div>
      </div>

      {/* 5. Inspection Zones */}
      <div className="space-y-2 pt-2 border-t border-slate-800/80">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono uppercase text-slate-400 font-semibold block">
            Inspection Zones (Polygons)
          </span>
          <label className="cursor-pointer">
            <input
              type="checkbox"
              checked={layers.inspectionZones}
              onChange={() => onChangeLayers({ ...layers, inspectionZones: !layers.inspectionZones })}
              className="rounded accent-cyan-500"
            />
          </label>
        </div>
      </div>
    </div>
  );
}

