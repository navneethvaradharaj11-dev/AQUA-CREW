"use client";

import React from "react";
import { SimulatedRover, RoverOperatingState } from "@/services/simulation/types";
import { Card } from "@/components/ui/Card";

export interface FleetStatusDistributionProps {
  rovers: SimulatedRover[];
  selectedFilter: RoverOperatingState | "ALL";
  onSelectFilter: (filter: RoverOperatingState | "ALL") => void;
}

interface StateStyleConfig {
  label: string;
  color: string;
  bgColor: string;
  barColor: string;
}

const STATE_CONFIGS: Record<RoverOperatingState, StateStyleConfig> = {
  INSPECTING: {
    label: "Inspecting",
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/10 border-cyan-500/30",
    barColor: "bg-cyan-400",
  },
  MOVING: {
    label: "Moving",
    color: "text-sky-400",
    bgColor: "bg-sky-500/10 border-sky-500/30",
    barColor: "bg-sky-400",
  },
  IDLE: {
    label: "Idle / Standby",
    color: "text-slate-300",
    bgColor: "bg-slate-500/10 border-slate-500/30",
    barColor: "bg-slate-400",
  },
  PAUSED: {
    label: "Paused",
    color: "text-amber-300",
    bgColor: "bg-amber-500/10 border-amber-500/30",
    barColor: "bg-amber-400",
  },
  RETURNING: {
    label: "Returning",
    color: "text-indigo-400",
    bgColor: "bg-indigo-500/10 border-indigo-500/30",
    barColor: "bg-indigo-400",
  },
  CHARGING: {
    label: "Charging",
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10 border-emerald-500/30",
    barColor: "bg-emerald-400",
  },
  OFFLINE: {
    label: "Offline",
    color: "text-slate-500",
    bgColor: "bg-slate-800/40 border-slate-700/30",
    barColor: "bg-slate-600",
  },
  ERROR: {
    label: "Error",
    color: "text-rose-400",
    bgColor: "bg-rose-500/10 border-rose-500/30",
    barColor: "bg-rose-500",
  },
  EMERGENCY_STOP: {
    label: "Emergency Stop",
    color: "text-red-400",
    bgColor: "bg-red-500/20 border-red-500/40",
    barColor: "bg-red-500",
  },
};

export function FleetStatusDistribution({
  rovers,
  selectedFilter,
  onSelectFilter,
}: FleetStatusDistributionProps) {
  const total = rovers.length || 1;

  // Tally states
  const counts: Record<RoverOperatingState, number> = {
    IDLE: 0,
    MOVING: 0,
    INSPECTING: 0,
    PAUSED: 0,
    RETURNING: 0,
    CHARGING: 0,
    OFFLINE: 0,
    ERROR: 0,
    EMERGENCY_STOP: 0,
  };

  rovers.forEach((r) => {
    if (counts[r.operatingState] !== undefined) {
      counts[r.operatingState]++;
    }
  });

  const activeStates = (Object.keys(counts) as RoverOperatingState[]).filter(
    (st) => counts[st] > 0
  );

  return (
    <Card variant="default" className="p-4 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="space-y-0.5">
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
            Autonomous State Distribution
          </span>
          <p className="text-xs text-slate-500">
            Filter fleet cards by clicking a discrete state category below
          </p>
        </div>

        <button
          onClick={() => onSelectFilter("ALL")}
          className={`px-2.5 py-1 text-xs rounded-md font-mono border transition-colors ${
            selectedFilter === "ALL"
              ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/50"
              : "bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200"
          }`}
        >
          View All ({rovers.length})
        </button>
      </div>

      {/* Multi-segment Distribution Bar */}
      <div className="h-2.5 w-full bg-slate-900 rounded-full overflow-hidden flex border border-slate-800">
        {activeStates.map((st) => {
          const widthPct = (counts[st] / total) * 100;
          return (
            <div
              key={st}
              style={{ width: `${widthPct}%` }}
              className={`${STATE_CONFIGS[st].barColor} h-full transition-all duration-300`}
              title={`${STATE_CONFIGS[st].label}: ${counts[st]} (${Math.round(widthPct)}%)`}
            />
          );
        })}
      </div>

      {/* State Filter Chips */}
      <div className="flex flex-wrap gap-2 pt-1">
        {(Object.keys(counts) as RoverOperatingState[]).map((st) => {
          const count = counts[st];
          const cfg = STATE_CONFIGS[st];
          const isSelected = selectedFilter === st;

          return (
            <button
              key={st}
              onClick={() => onSelectFilter(isSelected ? "ALL" : st)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono border transition-all ${
                isSelected
                  ? `${cfg.bgColor} ${cfg.color} ring-1 ring-cyan-400 font-semibold shadow-sm`
                  : count > 0
                  ? "bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700"
                  : "bg-slate-950/40 border-slate-900 text-slate-600 opacity-60"
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${cfg.barColor}`} />
              <span>{cfg.label}</span>
              <span className="text-[10px] bg-slate-800/80 px-1.5 py-0.2 rounded text-slate-300">
                {count}
              </span>
            </button>
          );
        })}
      </div>
    </Card>
  );
}

