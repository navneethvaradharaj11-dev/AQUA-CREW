"use client";

import React, { useState } from "react";
import {
  BarChart3,
  TrendingDown,
  Droplets,
  ShieldCheck,
  DollarSign,
  Activity,
  Calendar,
  Download,
  Filter,
  Bot,
  Radio,
  Layers,
  ArrowUpRight,
  CheckCircle2,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";

export function AnalyticsView() {
  const [timeRange, setTimeRange] = useState<"24h" | "7d" | "30d" | "quarter">("24h");
  const [selectedSector, setSelectedSector] = useState<string>("ALL");
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  // Hourly Diurnal Loss Profile (m3/h)
  const hourlyData = [
    { hour: "00:00", actualLoss: 42.1, preventedLoss: 18.4, pressurePsi: 64.2 },
    { hour: "02:00", actualLoss: 38.5, preventedLoss: 21.0, pressurePsi: 65.8 },
    { hour: "04:00", actualLoss: 34.2, preventedLoss: 24.5, pressurePsi: 67.1 },
    { hour: "06:00", actualLoss: 48.9, preventedLoss: 31.2, pressurePsi: 62.4 },
    { hour: "08:00", actualLoss: 62.4, preventedLoss: 38.6, pressurePsi: 58.0 },
    { hour: "10:00", actualLoss: 58.1, preventedLoss: 42.3, pressurePsi: 59.5 },
    { hour: "12:00", actualLoss: 52.8, preventedLoss: 44.1, pressurePsi: 60.8 },
    { hour: "14:00", actualLoss: 55.4, preventedLoss: 41.5, pressurePsi: 59.9 },
    { hour: "16:00", actualLoss: 61.2, preventedLoss: 39.8, pressurePsi: 57.8 },
    { hour: "18:00", actualLoss: 64.8, preventedLoss: 45.2, pressurePsi: 56.4 },
    { hour: "20:00", actualLoss: 54.0, preventedLoss: 47.9, pressurePsi: 60.2 },
    { hour: "22:00", actualLoss: 46.3, preventedLoss: 38.0, pressurePsi: 63.1 },
  ];

  // Sector Breakdowns
  const sectors = [
    { id: "SEC-1", name: "Sector 1 (Industrial)", lossRateLph: 1420, activeLeaks: 2, vulnerability: "Moderate", pipeAgeYears: 24, lengthKm: 84.2 },
    { id: "SEC-2", name: "Sector 2 (South Port)", lossRateLph: 380, activeLeaks: 1, vulnerability: "Low", pipeAgeYears: 12, lengthKm: 62.5 },
    { id: "SEC-3", name: "Sector 3 (Residential)", lossRateLph: 820, activeLeaks: 1, vulnerability: "Moderate", pipeAgeYears: 31, lengthKm: 114.8 },
    { id: "SEC-4", name: "Sector 4 (Central Core)", lossRateLph: 2240, activeLeaks: 3, vulnerability: "High", pipeAgeYears: 48, lengthKm: 87.1 },
  ];

  // Rover Fleet Productivity
  const fleetUtilization = [
    { category: "Acoustic Hydrophone Survey", pct: 48, hours: 11.5, color: "bg-cyan-500", text: "text-cyan-400" },
    { category: "In-Transit Autonomous Navigation", pct: 24, hours: 5.8, color: "bg-sky-500", text: "text-sky-400" },
    { category: "Depot Wireless Dock Charging", pct: 18, hours: 4.3, color: "bg-emerald-500", text: "text-emerald-400" },
    { category: "Standby / Maintenance Bay", pct: 10, hours: 2.4, color: "bg-slate-500", text: "text-slate-400" },
  ];

  // Sensor Ingestion Health
  const sensorHealth = [
    { modality: "Acoustic Hydrophones", count: 48, uptime: 98.4, latencyMs: 142, quality: "VALID" },
    { modality: "Pressure Transducers", count: 62, uptime: 99.1, latencyMs: 88, quality: "VALID" },
    { modality: "Ultrasonic Flow Meters", count: 34, uptime: 100.0, latencyMs: 65, quality: "VALID" },
    { modality: "Thermal Infrared Probes", count: 26, uptime: 94.2, latencyMs: 210, quality: "VALID" },
    { modality: "Soil Moisture Transducers", count: 20, uptime: 96.5, latencyMs: 185, quality: "VALID" },
  ];

  const handleExportCsv = () => {
    const csvContent =
      "data:text/csv;charset=utf-8," +
      "Timestamp,Actual_Loss_m3h,Prevented_Loss_m3h,Pressure_PSI\n" +
      hourlyData.map((d) => `${d.hour},${d.actualLoss},${d.preventedLoss},${d.pressurePsi}`).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `aqua_crew_analytics_${timeRange}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setExportNotice("CSV dataset exported successfully.");
    setTimeout(() => setExportNotice(null), 4000);
  };

  const handleExportJson = () => {
    const exportBundle = {
      generatedAt: new Date().toISOString(),
      provenance: "VIRTUAL_SIMULATION_ENGINE",
      timeRange,
      hourlyTelemetry: hourlyData,
      sectorAnalytics: sectors,
      fleetUtilization,
      sensorHealth,
    };
    const jsonStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(exportBundle, null, 2));
    const link = document.createElement("a");
    link.setAttribute("href", jsonStr);
    link.setAttribute("download", `aqua_crew_analytics_${timeRange}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setExportNotice("JSON analytics payload downloaded.");
    setTimeout(() => setExportNotice(null), 4000);
  };

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <BarChart3 className="h-6 w-6 text-cyan-400" />
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
              System Telemetry & Hydraulic Analytics
            </h1>
            <span className="rounded bg-cyan-950/80 px-2.5 py-0.5 text-xs font-mono text-cyan-300 border border-cyan-800/60 font-semibold">
              TASK 19 CERTIFIED
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Diurnal demand patterns, autonomous water conservation yield, sector vulnerability scores, and fleet operational performance.
          </p>
        </div>

        {/* Range Controls & Export Actions */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center rounded-lg border border-slate-800 bg-slate-900/80 p-0.5 text-xs font-mono">
            {(["24h", "7d", "30d", "quarter"] as const).map((r) => (
              <button
                key={r}
                onClick={() => setTimeRange(r)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  timeRange === r
                    ? "bg-cyan-500 text-slate-950 font-bold"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {r === "24h" ? "24H" : r === "7d" ? "7D" : r === "30d" ? "30D" : "Q4"}
              </button>
            ))}
          </div>

          <Button variant="outline" size="sm" onClick={handleExportCsv} leftIcon={<Download className="h-3.5 w-3.5" />}>
            Export CSV
          </Button>
          <Button variant="secondary" size="sm" onClick={handleExportJson} leftIcon={<Download className="h-3.5 w-3.5" />}>
            Export JSON
          </Button>
        </div>
      </div>

      {exportNotice && (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/40 bg-emerald-950/30 px-3.5 py-2 text-xs text-emerald-300 font-mono animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
          <span>{exportNotice}</span>
        </div>
      )}

      {/* Primary KPI Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Water Loss (24h)"
          value="617.8"
          unit="m³"
          tone="rose"
          change={{ value: "14.2%", direction: "up", label: "vs baseline" }}
        />
        <MetricCard
          label="Autonomous Salvage Yield"
          value="424.5"
          unit="m³"
          tone="emerald"
          change={{ value: "28.5%", direction: "up", label: "preserved" }}
        />
        <MetricCard
          label="Network Reliability Index"
          value="96.8"
          unit="%"
          tone="cyan"
          change={{ value: "99.4%", direction: "neutral", label: "target" }}
        />
        <MetricCard
          label="Estimated Cost Conservation"
          value="$14,820"
          unit="USD"
          tone="emerald"
          change={{ value: "+$3,200", direction: "up", label: "this week" }}
        />
      </div>

      {/* Main Chart Section: Diurnal Water Loss vs Prevented Loss */}
      <Card variant="industrial" className="p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-800/80 pb-3">
          <div>
            <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
              <Activity className="h-4 w-4 text-cyan-400" />
              Diurnal Hydrodynamic Loss & Recovery Profile
            </CardTitle>
            <p className="text-xs text-slate-400">
              Hourly comparison of ongoing physical leakage vs. volume saved by autonomous rover intervention.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5 text-rose-400">
              <span className="h-2.5 w-2.5 rounded-sm bg-rose-500/80" />
              Active Leakage (m³/h)
            </span>
            <span className="flex items-center gap-1.5 text-cyan-400">
              <span className="h-2.5 w-2.5 rounded-sm bg-cyan-500/80" />
              Salvaged Yield (m³/h)
            </span>
          </div>
        </div>

        {/* Interactive SVG Bar Graph */}
        <div className="h-64 w-full pt-4">
          <svg viewBox="0 0 600 180" className="w-full h-full overflow-visible" preserveAspectRatio="none">
            {/* Horizontal Grid lines */}
            <line x1="0" y1="30" x2="600" y2="30" stroke="#1e293b" strokeDasharray="3 3" />
            <line x1="0" y1="80" x2="600" y2="80" stroke="#1e293b" strokeDasharray="3 3" />
            <line x1="0" y1="130" x2="600" y2="130" stroke="#1e293b" strokeDasharray="3 3" />
            <line x1="0" y1="160" x2="600" y2="160" stroke="#334155" strokeWidth="1" />

            {/* Bars */}
            {hourlyData.map((d, i) => {
              const x = i * 50 + 10;
              const lossHeight = (d.actualLoss / 80) * 130;
              const savedHeight = (d.preventedLoss / 80) * 130;

              return (
                <g key={d.hour} className="group cursor-pointer">
                  {/* Actual Loss Bar */}
                  <rect
                    x={x}
                    y={160 - lossHeight}
                    width="16"
                    height={lossHeight}
                    rx="2"
                    className="fill-rose-500/70 group-hover:fill-rose-400 transition-colors"
                  />
                  {/* Prevented Loss Bar */}
                  <rect
                    x={x + 18}
                    y={160 - savedHeight}
                    width="16"
                    height={savedHeight}
                    rx="2"
                    className="fill-cyan-500/70 group-hover:fill-cyan-400 transition-colors"
                  />
                  {/* Label */}
                  <text
                    x={x + 17}
                    y="174"
                    textAnchor="middle"
                    className="fill-slate-500 font-mono text-[9px]"
                  >
                    {d.hour}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </Card>

      {/* Dual Column: Sector Vulnerability & Rover Fleet Productivity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sector Vulnerability Breakdown */}
        <Card variant="industrial" className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
              <Layers className="h-4 w-4 text-cyan-400" />
              Metropolitan Sector Risk & Pipe Degradation
            </CardTitle>
            <span className="text-[11px] font-mono text-slate-400">4 Sunk Sectors</span>
          </div>

          <div className="space-y-3">
            {sectors.map((s) => (
              <div
                key={s.id}
                onClick={() => setSelectedSector(s.id)}
                className={`p-3 rounded-xl border transition-all cursor-pointer ${
                  selectedSector === s.id
                    ? "border-cyan-500 bg-cyan-950/20 shadow-cyan-glow-sm"
                    : "border-slate-800/80 bg-slate-900/40 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="text-white font-semibold text-xs">{s.name}</span>
                    <div className="text-[10px] font-mono text-slate-400">
                      Network: {s.lengthKm} km • Avg Pipe Age: {s.pipeAgeYears} yrs
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-xs font-bold text-rose-400 block">
                      {s.lossRateLph} L/h
                    </span>
                    <span
                      className={`text-[10px] font-mono uppercase px-1.5 py-0.5 rounded border ${
                        s.vulnerability === "High"
                          ? "bg-rose-950/60 text-rose-300 border-rose-800/60"
                          : "bg-cyan-950/60 text-cyan-300 border-cyan-800/60"
                      }`}
                    >
                      {s.vulnerability} Risk
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Rover Fleet Productivity */}
        <Card variant="industrial" className="p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
              <Bot className="h-4 w-4 text-emerald-400" />
              Autonomous Rover Fleet Duty Cycle (24h)
            </CardTitle>
            <span className="text-[11px] font-mono text-emerald-400">3 Active Units</span>
          </div>

          <div className="space-y-3 pt-1">
            {fleetUtilization.map((f) => (
              <div key={f.category} className="space-y-1.5">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium">{f.category}</span>
                  <span className={`font-mono font-bold ${f.text}`}>
                    {f.pct}% ({f.hours}h)
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${f.color}`}
                    style={{ width: `${f.pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-3 mt-4 text-xs space-y-1 font-mono text-slate-400">
            <div className="flex justify-between">
              <span>Survey Distance Covered:</span>
              <span className="text-white font-bold">53.4 km</span>
            </div>
            <div className="flex justify-between">
              <span>Mean Localization Convergence:</span>
              <span className="text-emerald-400 font-bold">14.2 minutes</span>
            </div>
            <div className="flex justify-between">
              <span>Autonomous Mission Accuracy:</span>
              <span className="text-cyan-300 font-bold">98.9%</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Sensor Ingestion Health Table */}
      <Card variant="industrial" className="overflow-hidden">
        <CardHeader className="border-b border-slate-800 bg-slate-900/40 py-3 px-5">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
              <Radio className="h-4 w-4 text-cyan-400" />
              Stationary Sensor Ingestion Stream Telemetry
            </CardTitle>
            <span className="text-[11px] font-mono text-slate-400">190 Total Monitored Nodes</span>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold font-mono">
                <tr>
                  <th className="py-2.5 px-4">Sensor Modality</th>
                  <th className="py-2.5 px-3">Active Transducers</th>
                  <th className="py-2.5 px-3">Telemetry Uptime</th>
                  <th className="py-2.5 px-3">Mean Latency</th>
                  <th className="py-2.5 px-4">Quality Tier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {sensorHealth.map((sh) => (
                  <tr key={sh.modality} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-semibold text-white font-sans">{sh.modality}</td>
                    <td className="py-3 px-3 text-cyan-300">{sh.count} Nodes</td>
                    <td className="py-3 px-3 text-emerald-400 font-bold">{sh.uptime}%</td>
                    <td className="py-3 px-3 text-slate-300">{sh.latencyMs} ms</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-950/60 text-emerald-300 border border-emerald-500/30">
                        {sh.quality}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
