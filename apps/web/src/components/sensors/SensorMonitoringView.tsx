"use client";

import React, { useState } from "react";
import {
  Activity,
  Radio,
  Gauge,
  Droplets,
  Thermometer,
  Waves,
  Search,
  Battery,
  AlertTriangle,
  CheckCircle2,
  Filter,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";

export function SensorMonitoringView() {
  const [selectedModality, setSelectedModality] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const sensors = [
    {
      id: "SNS-AC-01-A",
      name: "Metro Trunk B Hydrophone Alpha",
      modality: "acoustic",
      pipeSegmentId: "PIPE-SEC-4B-92",
      currentValue: 88.4,
      unit: "dB",
      frequencyHz: 1420,
      status: "ANOMALY",
      batteryPct: 94,
      sampleRateHz: 4000,
      zone: "Sector 4 (Metro Core)",
    },
    {
      id: "SNS-AC-02-B",
      name: "Industrial Lateral Acoustic Node",
      modality: "acoustic",
      pipeSegmentId: "PIPE-IND-1A-04",
      currentValue: 46.2,
      unit: "dB",
      frequencyHz: 980,
      status: "ONLINE",
      batteryPct: 88,
      sampleRateHz: 4000,
      zone: "Sector 1 (Industrial)",
    },
    {
      id: "SNS-PR-02-A",
      name: "Central Core Pressure Transducer 1",
      modality: "pressure",
      pipeSegmentId: "PIPE-SEC-4B-92",
      currentValue: 56.4,
      unit: "PSI",
      frequencyHz: 10,
      status: "ONLINE",
      batteryPct: 98,
      sampleRateHz: 50,
      zone: "Sector 4 (Metro Core)",
    },
    {
      id: "SNS-PR-03-A",
      name: "Uptown Feeder Pressure Transducer",
      modality: "pressure",
      pipeSegmentId: "PIPE-003",
      currentValue: 26.4,
      unit: "PSI",
      frequencyHz: 10,
      status: "ANOMALY",
      batteryPct: 91,
      sampleRateHz: 50,
      zone: "Sector 3 (North Residential)",
    },
    {
      id: "SNS-FL-01-M",
      name: "Primary Trunk Ultrasonic Flow Meter",
      modality: "flow",
      pipeSegmentId: "PIPE-TRK-01",
      currentValue: 342.5,
      unit: "L/s",
      frequencyHz: 5,
      status: "ONLINE",
      batteryPct: 100,
      sampleRateHz: 20,
      zone: "Sector 4 (Metro Core)",
    },
    {
      id: "SNS-FL-03-C",
      name: "Uptown Feeder Ultrasonic Flow Meter",
      modality: "flow",
      pipeSegmentId: "PIPE-003",
      currentValue: 188.0,
      unit: "L/s",
      frequencyHz: 5,
      status: "ANOMALY",
      batteryPct: 82,
      sampleRateHz: 20,
      zone: "Sector 3 (North Residential)",
    },
    {
      id: "SNS-TM-04-A",
      name: "Subsurface Temperature Probe 4",
      modality: "thermal",
      pipeSegmentId: "PIPE-HRB-02-19",
      currentValue: 14.8,
      unit: "°C",
      frequencyHz: 1,
      status: "ONLINE",
      batteryPct: 95,
      sampleRateHz: 1,
      zone: "Sector 2 (South Port)",
    },
    {
      id: "SNS-MS-02-D",
      name: "Perimeter Soil Moisture Transducer",
      modality: "moisture",
      pipeSegmentId: "PIPE-RES-3C-11",
      currentValue: 42.6,
      unit: "%",
      frequencyHz: 1,
      status: "ONLINE",
      batteryPct: 89,
      sampleRateHz: 2,
      zone: "Sector 3 (North Residential)",
    },
  ];

  const filteredSensors = sensors.filter((s) => {
    if (selectedModality !== "ALL" && s.modality !== selectedModality) return false;
    if (
      searchQuery &&
      !s.id.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !s.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
      !s.pipeSegmentId.toLowerCase().includes(searchQuery.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <Radio className="h-6 w-6 text-cyan-400" />
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
              Stationary Sensor Network Monitoring
            </h1>
            <span className="rounded bg-cyan-950/80 px-2.5 py-0.5 text-xs font-mono text-cyan-300 border border-cyan-800/60 font-semibold">
              190 DISTRIBUTED STATIONS
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Live telemetry stream from permanent hydrophones, piezoresistive pressure transducers, electromagnetic flowmeters, and subsurface probes.
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search sensor ID or pipe..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-slate-800 bg-slate-900/80 pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:border-cyan-500 focus:outline-none font-mono"
          />
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <MetricCard label="Active Stationary Nodes" value="184 / 190" unit="STATIONS" tone="cyan" />
        <MetricCard label="Acoustic Anomalies" value="2" unit="CRITICAL ALERTS" tone="rose" />
        <MetricCard label="Sampling Cadence" value="4,000" unit="Hz PEAK" tone="emerald" />
        <MetricCard label="Battery Health Index" value="94.6" unit="% MEAN" tone="slate" />
      </div>

      {/* Modality Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
        {[
          { id: "ALL", label: "All Modalities" },
          { id: "acoustic", label: "Acoustic Hydrophones" },
          { id: "pressure", label: "Pressure Transducers" },
          { id: "flow", label: "Flow Meters" },
          { id: "thermal", label: "Thermal Probes" },
          { id: "moisture", label: "Soil Moisture" },
        ].map((m) => (
          <button
            key={m.id}
            onClick={() => setSelectedModality(m.id)}
            className={`px-3 py-1.5 rounded-lg border transition-colors ${
              selectedModality === m.id
                ? "bg-cyan-500 text-slate-950 font-bold border-cyan-400"
                : "bg-slate-900/60 border-slate-800 text-slate-400 hover:text-white"
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>

      {/* Sensor Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {filteredSensors.map((s) => (
          <Card
            key={s.id}
            variant="industrial"
            className={`p-4 space-y-3 transition-all ${
              s.status === "ANOMALY" ? "border-rose-500/50 bg-rose-950/10 shadow-rose-glow-sm" : ""
            }`}
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="font-mono text-[10px] text-cyan-400 font-bold block">{s.id}</span>
                <h3 className="font-semibold text-white text-xs leading-tight line-clamp-1">{s.name}</h3>
              </div>
              <StatusBadge
                status={s.status === "ANOMALY" ? "critical" : "online"}
                label={s.status}
                pulse={s.status === "ANOMALY"}
                size="sm"
              />
            </div>

            {/* Reading Highlight */}
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 flex items-center justify-between">
              <div>
                <span className="text-[10px] text-slate-400 font-mono uppercase block">Live Reading</span>
                <span
                  className={`text-xl font-bold font-mono ${
                    s.status === "ANOMALY" ? "text-rose-400" : "text-white"
                  }`}
                >
                  {s.currentValue} {s.unit}
                </span>
              </div>
              <div className="text-right text-[10px] font-mono text-slate-500">
                <div>Rate: {s.sampleRateHz} Hz</div>
                <div>{s.modality.toUpperCase()}</div>
              </div>
            </div>

            {/* Pipe & Zone Info */}
            <div className="text-[11px] font-mono text-slate-400 space-y-1 pt-1">
              <div className="flex justify-between">
                <span>Segment:</span>
                <span className="text-slate-200">{s.pipeSegmentId}</span>
              </div>
              <div className="flex justify-between">
                <span>Zone:</span>
                <span className="text-slate-300">{s.zone}</span>
              </div>
              <div className="flex justify-between pt-1 border-t border-slate-800/80">
                <span className="flex items-center gap-1 text-slate-400">
                  <Battery className="h-3.5 w-3.5" /> Battery
                </span>
                <span className="text-emerald-400 font-bold">{s.batteryPct}%</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
