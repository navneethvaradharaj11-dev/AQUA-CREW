"use client";

import React from "react";
import { Radio, RefreshCw, ShieldAlert, Cpu, Activity } from "lucide-react";
import { Button } from "@/components/ui/Button";

export interface CommandCenterHeaderProps {
  lastUpdated: string;
  isRefreshing: boolean;
  onRefresh: () => void;
  unacknowledgedAlertsCount: number;
}

export function CommandCenterHeader({
  lastUpdated,
  isRefreshing,
  onRefresh,
  unacknowledgedAlertsCount,
}: CommandCenterHeaderProps) {
  return (
    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 rounded-xl border border-cyan-900/30 bg-gradient-to-r from-slate-900/90 via-slate-900/50 to-slate-950 p-5 backdrop-blur-md">
      {/* Title & Mode */}
      <div className="space-y-1.5">
        <div className="flex flex-wrap items-center gap-2.5">
          <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white flex items-center gap-2">
            AQUA CREW Command Center
          </h1>

          {/* Prominent SIMULATION Mode Badge */}
          <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-500/40 bg-amber-950/60 px-3 py-1 text-xs font-mono font-bold uppercase tracking-wider text-amber-300 shadow-sm shadow-amber-950">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-amber-400" />
            </span>
            OPERATIONAL MODE: SIMULATION
          </span>
        </div>

        <p className="text-xs text-slate-400 max-w-2xl leading-relaxed">
          Autonomous metropolitan hydro-network telemetry monitor.
          <span className="text-slate-300 font-medium ml-1">
            All telemetry and incident data are software-simulated models.
          </span>
        </p>
      </div>

      {/* Synchronization, Broker Status & Controls */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Virtual Broker Connection Status */}
        <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-xs">
          <Radio className="h-3.5 w-3.5 text-cyan-400 animate-pulse" />
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-500 font-mono uppercase">Simulation Broker</span>
            <span className="text-emerald-400 font-mono text-[11px] font-semibold">CONNECTED • 60Hz</span>
          </div>
        </div>

        {/* Sync Timestamp */}
        <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-1.5 text-xs">
          <Activity className="h-3.5 w-3.5 text-slate-400" />
          <div className="flex flex-col">
            <span className="text-[10px] text-slate-500 font-mono uppercase">Last Sync</span>
            <span className="text-slate-200 font-mono text-[11px] font-semibold">{lastUpdated}</span>
          </div>
        </div>

        {/* Interactive Refresh Button */}
        <Button
          variant="industrial"
          size="sm"
          isLoading={isRefreshing}
          onClick={onRefresh}
          leftIcon={<RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />}
        >
          {isRefreshing ? "Syncing..." : "Refresh Telemetry"}
        </Button>
      </div>
    </div>
  );
}

