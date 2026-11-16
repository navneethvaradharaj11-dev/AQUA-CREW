"use client";

import React from "react";
import { Button } from "@/components/ui/Button";
import { Play, Pause, RotateCcw, AlertOctagon, Activity, ShieldAlert } from "lucide-react";

export interface FleetSimulationControlsProps {
  isRunning: boolean;
  tickCount: number;
  onTogglePlay: () => void;
  onReset: () => void;
  onEmergencyStopFleet: () => void;
}

export function FleetSimulationControls({
  isRunning,
  tickCount,
  onTogglePlay,
  onReset,
  onEmergencyStopFleet,
}: FleetSimulationControlsProps) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-3">
      {/* Simulation Banner Notice */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <span className="flex h-2.5 w-2.5 relative">
            {isRunning && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
            )}
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isRunning ? "bg-cyan-500" : "bg-amber-500"
              }`}
            />
          </span>
          <span className="font-mono text-slate-300 font-semibold tracking-wide">
            SIMULATION ENGINE: {isRunning ? "ACTIVE [1000ms TICK]" : "PAUSED"}
          </span>
          <span className="text-[10px] bg-slate-800 border border-slate-700 px-2 py-0.5 rounded text-slate-400 font-mono">
            TICK #{tickCount}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-[11px] font-mono text-amber-400/90 bg-amber-950/30 border border-amber-900/40 px-2.5 py-1 rounded-md">
          <ShieldAlert className="h-3.5 w-3.5" />
          <span>VIRTUAL SIMULATION BENCH • ZERO PHYSICAL ACTUATION</span>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Button
            variant={isRunning ? "secondary" : "primary"}
            size="sm"
            onClick={onTogglePlay}
            leftIcon={
              isRunning ? (
                <Pause className="h-3.5 w-3.5 text-amber-400" />
              ) : (
                <Play className="h-3.5 w-3.5 text-cyan-400" />
              )
            }
          >
            {isRunning ? "Pause Engine" : "Resume Simulation"}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onReset}
            leftIcon={<RotateCcw className="h-3.5 w-3.5 text-slate-400" />}
          >
            Reset Engine
          </Button>
        </div>

        <div>
          <Button
            variant="destructive"
            size="sm"
            onClick={onEmergencyStopFleet}
            leftIcon={<AlertOctagon className="h-4 w-4" />}
            className="shadow-rose-glow-sm"
          >
            Fleet Emergency Stop
          </Button>
        </div>
      </div>
    </div>
  );
}
