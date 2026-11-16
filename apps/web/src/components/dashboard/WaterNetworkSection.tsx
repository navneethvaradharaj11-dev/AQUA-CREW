import React from "react";
import { WaterNetworkOverview } from "@/services/simulation/types";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Layers, AlertTriangle, ShieldCheck, Gauge } from "lucide-react";

export interface WaterNetworkSectionProps {
  network: WaterNetworkOverview;
}

export function WaterNetworkSection({ network }: WaterNetworkSectionProps) {
  return (
    <Card variant="industrial">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <CardTitle>Water Network Overview</CardTitle>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-cyan-400 border border-slate-700">
                [SIMULATED]
              </span>
            </div>
            <CardDescription>
              Municipal underground pipe topology, structural segmentation and hydraulic pressure zones.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge
              status="online"
              label={`Network Health: ${network.networkHealthPercentage}%`}
              pulse
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        {/* Metric Segment Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 space-y-1">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">Total Segments</span>
            <span className="text-xl font-bold font-mono text-white">{network.totalSegments}</span>
            <span className="text-[11px] text-slate-400 block">100% PostGIS mapped</span>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 space-y-1">
            <span className="text-[10px] uppercase font-mono text-slate-500 block">Monitored Segments</span>
            <span className="text-xl font-bold font-mono text-cyan-400">{network.monitoredSegments}</span>
            <span className="text-[11px] text-emerald-400 block font-mono">95.6% Active telemetry</span>
          </div>

          <div className="rounded-lg border border-amber-900/40 bg-amber-950/20 p-3.5 space-y-1">
            <span className="text-[10px] uppercase font-mono text-amber-400/80 block">Requires Inspection</span>
            <span className="text-xl font-bold font-mono text-amber-300">{network.segmentsRequiringInspection}</span>
            <span className="text-[11px] text-amber-400/80 block font-mono">Patrols queued</span>
          </div>

          <div className="rounded-lg border border-rose-900/40 bg-rose-950/20 p-3.5 space-y-1">
            <span className="text-[10px] uppercase font-mono text-rose-400/80 block">Critical Segments</span>
            <span className="text-xl font-bold font-mono text-rose-400">{network.criticalSegments}</span>
            <span className="text-[11px] text-rose-300 block font-mono">High priority review</span>
          </div>
        </div>

        {/* Pressure Zones Bar */}
        <div className="space-y-2 pt-2 border-t border-slate-800">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span className="flex items-center gap-1.5">
              <Gauge className="h-3.5 w-3.5 text-cyan-400" />
              ACTIVE HYDRAULIC PRESSURE ZONES
            </span>
            <span className="text-[11px] text-slate-500">
              Avg Pressure: {network.averagePressurePsi} PSI
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            {network.activePressureZones.map((zone) => (
              <div
                key={zone.zoneId}
                className="flex items-center justify-between rounded-lg border border-slate-800/80 bg-slate-900/40 px-3 py-2 text-xs"
              >
                <div>
                  <span className="font-semibold text-slate-200 block text-xs">{zone.name}</span>
                  <span className="text-[10px] font-mono text-slate-500">{zone.zoneId}</span>
                </div>
                <div className="text-right">
                  <span className="font-mono text-cyan-300 font-bold block">{zone.pressurePsi} PSI</span>
                  <span
                    className={`text-[9px] font-mono uppercase ${
                      zone.status === "Nominal" ? "text-emerald-400" : "text-amber-400"
                    }`}
                  >
                    {zone.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

