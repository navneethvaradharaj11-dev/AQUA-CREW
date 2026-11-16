"use client";

import React from "react";
import { SimulatedRover } from "@/services/simulation/types";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Bot, Battery, Radio, MapPin, Compass, ArrowUpRight } from "lucide-react";

export interface RoverFleetSectionProps {
  rovers: SimulatedRover[];
  onSelectRover: (rover: SimulatedRover) => void;
}

export function RoverFleetSection({ rovers, onSelectRover }: RoverFleetSectionProps) {
  const getStatusVariant = (status: SimulatedRover["status"]) => {
    switch (status) {
      case "ACTIVE":
        return "active";
      case "ONLINE":
        return "online";
      case "WARNING":
        return "warning";
      case "OFFLINE":
        return "offline";
      case "IDLE":
      default:
        return "standby";
    }
  };

  const getBatteryColor = (pct: number) => {
    if (pct > 60) return "text-emerald-400 bg-emerald-400";
    if (pct > 25) return "text-amber-400 bg-amber-400";
    return "text-rose-400 bg-rose-400";
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-cyan-400" />
          <h2 className="text-lg font-bold tracking-tight text-white">Rover Fleet Overview</h2>
          <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-cyan-400 border border-slate-700">
            [SIMULATED FLEET]
          </span>
        </div>
        <div className="text-xs font-mono text-slate-400">
          Showing {rovers.length} Virtual Crawlers & Scouts
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3.5">
        {rovers.map((rover) => {
          const batteryColor = getBatteryColor(rover.batteryPercentage);
          return (
            <div
              key={rover.id}
              onClick={() => onSelectRover(rover)}
              className="group relative flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/40 p-4 transition-all duration-200 hover:border-cyan-500/50 hover:bg-slate-900/80 cursor-pointer shadow-sm hover:shadow-cyan-glow-sm"
            >
              <div className="space-y-3">
                {/* Header: ID, Name, Status */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="font-mono text-[10px] text-cyan-400 font-bold block">
                      {rover.id}
                    </span>
                    <h3 className="font-semibold text-white text-sm group-hover:text-cyan-300 transition-colors">
                      {rover.name}
                    </h3>
                    <p className="text-[11px] text-slate-400 truncate">{rover.model}</p>
                  </div>
                  <StatusBadge
                    status={getStatusVariant(rover.status)}
                    label={rover.status}
                    pulse={rover.status === "ACTIVE"}
                    size="sm"
                  />
                </div>

                {/* Battery Bar */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-[11px] font-mono">
                    <span className="flex items-center gap-1 text-slate-400">
                      <Battery className="h-3.5 w-3.5" /> SoC
                    </span>
                    <span className={batteryColor.split(" ")[0]}>{rover.batteryPercentage}%</span>
                  </div>
                  <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${batteryColor.split(" ")[1]}`}
                      style={{ width: `${rover.batteryPercentage}%` }}
                    />
                  </div>
                </div>

                {/* Location & Mission */}
                <div className="space-y-1.5 pt-2 border-t border-slate-800/80 text-xs">
                  <div className="flex items-start gap-1.5 text-slate-300">
                    <MapPin className="h-3.5 w-3.5 text-cyan-400 shrink-0 mt-0.5" />
                    <span className="text-[11px] truncate leading-tight">
                      {rover.currentLocation?.stationName || "Station Grid"}
                    </span>
                  </div>
                  <div className="flex items-start gap-1.5 text-slate-400">
                    <Compass className="h-3.5 w-3.5 text-slate-500 shrink-0 mt-0.5" />
                    <span className="text-[11px] truncate leading-tight">
                      {rover.currentMission || "Patrol Standby"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="mt-4 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                <span>PING: {rover.lastCommunication}</span>
                <span className="text-cyan-400 flex items-center gap-0.5 group-hover:underline">
                  Telemetry <ArrowUpRight className="h-3 w-3" />
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

