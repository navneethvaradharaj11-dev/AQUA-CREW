import React from "react";
import { SimulatedSensorCategory } from "@/services/simulation/types";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Radio, Activity, Waves, Gauge, Thermometer, Droplet } from "lucide-react";

export interface SensorNetworkSectionProps {
  sensors: SimulatedSensorCategory[];
}

export function SensorNetworkSection({ sensors }: SensorNetworkSectionProps) {
  const getSensorIcon = (type: SimulatedSensorCategory["type"]) => {
    switch (type) {
      case "acoustic":
        return <Waves className="h-4 w-4 text-cyan-400" />;
      case "pressure":
        return <Gauge className="h-4 w-4 text-emerald-400" />;
      case "flow":
        return <Activity className="h-4 w-4 text-sky-400" />;
      case "thermal":
        return <Thermometer className="h-4 w-4 text-amber-400" />;
      case "moisture":
      default:
        return <Droplet className="h-4 w-4 text-teal-400" />;
    }
  };

  return (
    <Card variant="default">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <Radio className="h-5 w-5 text-cyan-400" />
              <CardTitle>Stationary Sensor Network</CardTitle>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-cyan-400 border border-slate-700">
                [SIMULATED IoT]
              </span>
            </div>
            <CardDescription>
              Distributed municipal IoT nodes monitoring acoustic waveforms, pressure spikes, and flow rates.
            </CardDescription>
          </div>
          <span className="text-xs font-mono text-slate-400">
            5 Diagnostic Sensor Modalities
          </span>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {sensors.map((s) => {
            const connectivityPct = Math.round((s.connectedCount / s.totalCount) * 100);
            return (
              <div
                key={s.id}
                className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-800/60 border border-slate-700/60">
                    {getSensorIcon(s.type)}
                  </div>
                  <span className="rounded bg-slate-800/80 px-1.5 py-0.5 text-[10px] font-mono text-emerald-400">
                    {s.status}
                  </span>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-white leading-tight">{s.name}</h4>
                  <span className="text-[10px] font-mono text-slate-500 uppercase">{s.id}</span>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-slate-800/80 text-xs font-mono">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Connected</span>
                    <span className="text-slate-200">
                      {s.connectedCount}/{s.totalCount} ({connectivityPct}%)
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-slate-400">
                    <span>Mean Value</span>
                    <span className="text-cyan-300 font-bold">
                      {s.currentAverageValue} {s.unit}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-slate-400">
                    <span>Sampling</span>
                    <span className="text-slate-300">{s.avgSampleRateHz} Hz</span>
                  </div>
                </div>

                {/* Connectivity Bar */}
                <div className="h-1 w-full overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-cyan-400 transition-all duration-500"
                    style={{ width: `${connectivityPct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

