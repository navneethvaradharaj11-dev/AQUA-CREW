import React from "react";
import { MetricCard } from "@/components/ui/MetricCard";
import { DashboardKpis } from "@/services/simulation/types";
import { Activity, Bot, Droplets, MapPin, Navigation, Radio } from "lucide-react";

export interface KpiSectionProps {
  kpis: DashboardKpis;
}

export function KpiSection({ kpis }: KpiSectionProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs text-slate-400 font-mono px-1">
        <span>CORE OPERATIONAL KPIS [SIMULATED]</span>
        <span className="text-[11px] text-cyan-400">TELEMETRY STREAM: SYNTHETIC V1</span>
      </div>

      <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {/* KPI 1: Total Pipeline Length Monitored */}
        <MetricCard
          label="Pipeline Length"
          value={kpis.totalPipelineLengthKm}
          unit="KM MONITORED"
          icon={MapPin}
          change={{ value: "95.6%", direction: "up", label: "Network Coverage" }}
          tone="cyan"
          progress={96}
        />

        {/* KPI 2: Detected Leak Incidents */}
        <MetricCard
          label="Detected Incidents"
          value={kpis.detectedLeakIncidentsCount}
          unit="SIMULATED LEAKS"
          icon={Droplets}
          change={{ value: "1 Critical", direction: "neutral", label: "Active Priority" }}
          tone="rose"
          progress={65}
        />

        {/* KPI 3: Active Rovers */}
        <MetricCard
          label="Active Rovers"
          value={`${kpis.activeRoversCount} / ${kpis.totalRoversCount}`}
          unit="FLEET DEPLOYED"
          icon={Bot}
          change={{ value: "60%", direction: "up", label: "Deployment Rate" }}
          tone="cyan"
          progress={60}
        />

        {/* KPI 4: Connected Sensors */}
        <MetricCard
          label="Connected Sensors"
          value={`${kpis.connectedSensorsCount} / ${kpis.totalSensorsCount}`}
          unit="NODES REPORTING"
          icon={Radio}
          change={{ value: "96.8%", direction: "up", label: "Signal Health" }}
          tone="emerald"
          progress={97}
        />

        {/* KPI 5: Estimated Water Loss */}
        <MetricCard
          label="Estimated Loss"
          value={kpis.estimatedWaterLossLph.toLocaleString()}
          unit="LITRES / HOUR"
          icon={Activity}
          change={{ value: "-14%", direction: "down", label: "Mitigation vs 24h" }}
          tone="amber"
          progress={45}
        />

        {/* KPI 6: Active Inspection Missions */}
        <MetricCard
          label="Active Missions"
          value={kpis.activeInspectionMissionsCount}
          unit="IN PROGRESS"
          icon={Navigation}
          change={{ value: "2 Patrols", direction: "neutral", label: "1 Scheduled" }}
          tone="cyan"
          progress={75}
        />
      </div>
    </div>
  );
}

