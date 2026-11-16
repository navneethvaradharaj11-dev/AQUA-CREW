"use client";

import React from "react";
import {
  SimulatedRover,
  RoverStateTransitionRecord,
} from "@/services/simulation/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import {
  X,
  Bot,
  Battery,
  MapPin,
  Compass,
  Activity,
  Gauge,
  Thermometer,
  Zap,
  Radio,
  History,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";

export interface RoverSelectedPanelProps {
  rover: SimulatedRover | null;
  transitions: RoverStateTransitionRecord[];
  onClose: () => void;
  onViewOnMap: (rover: SimulatedRover) => void;
  onClearEStop?: (rover: SimulatedRover) => void;
}

export function RoverSelectedPanel({
  rover,
  transitions,
  onClose,
  onViewOnMap,
  onClearEStop,
}: RoverSelectedPanelProps) {
  if (!rover) return null;

  const roverTransitions = transitions.filter((t) => t.roverId === rover.id);
  const isEStop = rover.operatingState === "EMERGENCY_STOP";

  return (
    <Card
      variant="industrial"
      className="p-5 space-y-5 border-cyan-800/40 bg-slate-950/80 backdrop-blur-md animate-in slide-in-from-right duration-200"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-950/60 border border-cyan-800 text-cyan-400">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white tracking-tight">
                {rover.name}
              </h3>
              <StatusBadge
                status={
                  isEStop
                    ? "critical"
                    : rover.operatingState === "MOVING" || rover.operatingState === "INSPECTING"
                    ? "active"
                    : "online"
                }
                label={rover.operatingState}
                size="sm"
              />
            </div>
            <span className="text-xs font-mono text-slate-400">
              {rover.id} • {rover.model}
            </span>
          </div>
        </div>

        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Primary Telemetry Readout Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs font-mono">
        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
          <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
            <Battery className="h-3 w-3 text-cyan-400" /> Battery SoC
          </span>
          <span className="text-sm font-bold text-white block mt-0.5">
            {rover.batteryPercentage}%
          </span>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
          <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
            <Gauge className="h-3 w-3 text-cyan-400" /> Velocity
          </span>
          <span className="text-sm font-bold text-cyan-300 block mt-0.5">
            {rover.kinematics.velocityMps} m/s
          </span>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
          <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
            <Compass className="h-3 w-3 text-slate-400" /> Heading
          </span>
          <span className="text-sm font-bold text-white block mt-0.5">
            {rover.kinematics.headingDeg}°
          </span>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
          <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
            <Radio className="h-3 w-3 text-emerald-400" /> Signal RSSI
          </span>
          <span className="text-sm font-bold text-emerald-400 block mt-0.5">
            {rover.diagnostics.signalRssiDbm} dBm
          </span>
        </div>
      </div>

      {/* Detailed Diagnostics */}
      <div className="space-y-2">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block">
          Hardware Diagnostics & Thermal Status
        </span>
        <div className="grid grid-cols-3 gap-2.5 text-xs font-mono">
          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Motor Temp</span>
            <span className="text-slate-200 font-semibold">{rover.diagnostics.motorTempC}°C</span>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Internal Temp</span>
            <span className="text-slate-200 font-semibold">{rover.diagnostics.internalTempC}°C</span>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Motor Current</span>
            <span className="text-slate-200 font-semibold">{rover.diagnostics.motorCurrentAmps} A</span>
          </div>
        </div>
      </div>

      {/* Geospatial Location */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 space-y-2 text-xs">
        <div className="flex items-start gap-2">
          <MapPin className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="text-slate-400 text-[11px] block">Pipeline Station & Route Segment</span>
            <span className="text-slate-100 font-semibold block">{rover.currentLocation.stationName}</span>
            <div className="text-[10px] font-mono text-slate-500 flex flex-wrap gap-2 pt-0.5">
              <span>LAT: {rover.currentLocation.latitude.toFixed(6)}</span>
              <span>LON: {rover.currentLocation.longitude.toFixed(6)}</span>
              <span>SEG: {rover.currentLocation.pipeSegmentId}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Payload Sensors */}
      <div className="space-y-2">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400 block">
          Inspection Payload Readings
        </span>
        <div className="grid grid-cols-3 gap-2 text-xs font-mono">
          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Acoustic SPL</span>
            <span className="text-cyan-300 font-bold">{rover.payloadSensors.acousticSplDb} dB</span>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Acoustic Peak</span>
            <span className="text-white font-bold">{rover.payloadSensors.dominantFreqHz} Hz</span>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Ground Moisture</span>
            <span className="text-sky-300 font-bold">{rover.payloadSensors.groundMoisturePct}%</span>
          </div>
        </div>
      </div>

      {/* State Transitions Audit Trail */}
      <div className="space-y-2">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <History className="h-3.5 w-3.5 text-slate-500" />
          Recent State Transitions ({roverTransitions.length})
        </span>

        {roverTransitions.length === 0 ? (
          <div className="rounded-lg border border-slate-800/80 bg-slate-900/30 p-3 text-center text-xs text-slate-500 font-mono">
            No state transitions logged yet.
          </div>
        ) : (
          <div className="max-h-40 overflow-y-auto space-y-1.5 pr-1 font-mono text-[11px]">
            {roverTransitions.map((tr) => (
              <div
                key={tr.id}
                className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2 space-y-0.5"
              >
                <div className="flex items-center justify-between text-[10px]">
                  <span className="text-slate-400">
                    {tr.previousState} &rarr; <strong className="text-cyan-300">{tr.newState}</strong>
                  </span>
                  <span className="text-slate-500">
                    {new Date(tr.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <p className="text-slate-300 text-[10px] truncate">{tr.reason}</p>
                <span className="text-[9px] text-slate-500 block uppercase">
                  TRIGGER: {tr.triggeredBy}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="pt-2 flex flex-wrap items-center justify-between gap-2 border-t border-slate-800">
        <Button
          variant="primary"
          size="sm"
          onClick={() => onViewOnMap(rover)}
          leftIcon={<Compass className="h-3.5 w-3.5" />}
        >
          Locate on Pipeline GIS Map
        </Button>

        {isEStop && onClearEStop && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onClearEStop(rover)}
            className="border-emerald-700 text-emerald-400 hover:bg-emerald-950/30"
          >
            Clear E-Stop
          </Button>
        )}
      </div>
    </Card>
  );
}

