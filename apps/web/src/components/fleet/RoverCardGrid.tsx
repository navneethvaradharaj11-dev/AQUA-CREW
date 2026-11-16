"use client";

import React from "react";
import { SimulatedRover, RoverOperatingState } from "@/services/simulation/types";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import {
  Bot,
  Battery,
  Gauge,
  Thermometer,
  Radio,
  Play,
  Pause,
  RotateCcw,
  AlertOctagon,
  ArrowRight,
  MapPin,
  ClipboardList,
} from "lucide-react";

export interface RoverCardGridProps {
  rovers: SimulatedRover[];
  selectedRoverId: string | null;
  onSelectRover: (rover: SimulatedRover) => void;
  onPauseRover: (rover: SimulatedRover) => void;
  onResumeRover: (rover: SimulatedRover) => void;
  onReturnBase: (rover: SimulatedRover) => void;
  onEmergencyStop: (rover: SimulatedRover) => void;
  onAssignMission: (rover: SimulatedRover) => void;
}

export function RoverCardGrid({
  rovers,
  selectedRoverId,
  onSelectRover,
  onPauseRover,
  onResumeRover,
  onReturnBase,
  onEmergencyStop,
  onAssignMission,
}: RoverCardGridProps) {
  if (rovers.length === 0) {
    return (
      <Card variant="default" className="p-8 text-center text-slate-400">
        No simulated rovers match the active state filter.
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {rovers.map((rover) => {
        const isSelected = selectedRoverId === rover.id;
        const state = rover.operatingState;
        const isEStop = state === "EMERGENCY_STOP";
        const isPaused = state === "PAUSED";
        const isIdle = state === "IDLE";
        const isOffline = state === "OFFLINE";
        const isActive = state === "MOVING" || state === "INSPECTING" || state === "RETURNING";

        // Battery color
        let battColor = "bg-emerald-400 text-emerald-400";
        if (rover.batteryPercentage < 20) {
          battColor = "bg-rose-500 text-rose-400";
        } else if (rover.batteryPercentage < 50) {
          battColor = "bg-amber-400 text-amber-400";
        }

        return (
          <Card
            key={rover.id}
            variant={isSelected ? "glow" : "industrial"}
            className={`p-4 space-y-4 transition-all duration-200 ${
              isEStop ? "border-red-900/60 bg-red-950/10" : ""
            }`}
          >
            {/* Header: Name, Model, Operating State */}
            <div className="flex items-start justify-between gap-2">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-900 border border-slate-800 text-cyan-400">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white tracking-tight">
                      {rover.name}
                    </h3>
                    <span className="text-[10px] font-mono text-slate-400 block">
                      {rover.id} • {rover.model}
                    </span>
                  </div>
                </div>
              </div>

              <StatusBadge
                status={
                  isEStop
                    ? "critical"
                    : isActive
                    ? "active"
                    : isPaused
                    ? "warning"
                    : isOffline
                    ? "offline"
                    : "online"
                }
                label={rover.operatingState}
                pulse={isActive}
                size="sm"
              />
            </div>

            {/* Battery SoC Gauge */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="flex items-center gap-1.5 text-slate-400 text-[11px]">
                  <Battery className="h-3.5 w-3.5 text-slate-500" />
                  Battery State of Charge
                </span>
                <span className={`font-semibold ${battColor.split(" ")[1]}`}>
                  {rover.batteryPercentage}%
                </span>
              </div>
              <div className="h-2 w-full bg-slate-900 rounded-full overflow-hidden border border-slate-800/80">
                <div
                  className={`h-full transition-all duration-300 ${battColor.split(" ")[0]}`}
                  style={{ width: `${rover.batteryPercentage}%` }}
                />
              </div>
            </div>

            {/* Telemetry Matrix (2x2) */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2 space-y-0.5">
                <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
                  <Gauge className="h-3 w-3 text-slate-400" /> Speed
                </span>
                <span className="text-slate-100 font-semibold block">
                  {rover.kinematics.velocityMps} m/s
                </span>
              </div>

              <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2 space-y-0.5">
                <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
                  <Thermometer className="h-3 w-3 text-slate-400" /> Motor Temp
                </span>
                <span className={`font-semibold block ${
                  rover.diagnostics.motorTempC > 50 ? "text-amber-400" : "text-slate-200"
                }`}>
                  {rover.diagnostics.motorTempC}°C
                </span>
              </div>

              <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2 space-y-0.5">
                <span className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
                  <Radio className="h-3 w-3 text-slate-400" /> RSSI Signal
                </span>
                <span className="text-slate-200 font-semibold block">
                  {rover.diagnostics.signalRssiDbm} dBm
                </span>
              </div>

              <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2 space-y-0.5">
                <span className="text-[10px] text-slate-500 uppercase block">
                  Distance Log
                </span>
                <span className="text-cyan-400 font-semibold block">
                  {rover.distanceTravelledKm} km
                </span>
              </div>
            </div>

            {/* Location & Mission Info */}
            <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-2.5 space-y-1.5 text-xs">
              <div className="flex items-center gap-1.5 text-slate-300">
                <MapPin className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                <span className="truncate text-[11px] font-mono">
                  {rover.currentLocation.stationName}
                </span>
              </div>

              <div className="flex items-center gap-1.5 text-slate-400 border-t border-slate-900 pt-1.5">
                <ClipboardList className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                <span className="truncate text-[11px]">
                  {rover.currentMission || "No active mission"}
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="pt-1 flex flex-wrap items-center justify-between gap-1.5">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onSelectRover(rover)}
                className="text-xs"
              >
                Inspect Telemetry
              </Button>

              <div className="flex items-center gap-1">
                {isIdle ? (
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => onAssignMission(rover)}
                    className="text-xs"
                  >
                    Assign Mission
                  </Button>
                ) : isPaused ? (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => onResumeRover(rover)}
                    className="text-xs"
                  >
                    <Play className="h-3 w-3 text-emerald-400 mr-1" /> Resume
                  </Button>
                ) : isActive ? (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => onPauseRover(rover)}
                    className="text-xs"
                  >
                    <Pause className="h-3 w-3 text-amber-400 mr-1" /> Pause
                  </Button>
                ) : null}

                {isActive && (
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => onReturnBase(rover)}
                    className="text-xs"
                    title="Recall to base docking port"
                  >
                    <RotateCcw className="h-3 w-3 text-slate-400" />
                  </Button>
                )}

                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => onEmergencyStop(rover)}
                  className="px-2"
                  title="Individual Emergency Stop"
                >
                  <AlertOctagon className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
