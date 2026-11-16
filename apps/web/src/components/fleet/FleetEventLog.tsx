"use client";

import React, { useState, useEffect } from "react";
import { roverEventBus, RoverSimulationEvent } from "@/services/simulation/roverEventBus";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Activity, ShieldAlert, Filter, Trash2 } from "lucide-react";

export interface FleetEventLogProps {
  selectedRoverId?: string | null;
}

export function FleetEventLog({ selectedRoverId }: FleetEventLogProps) {
  const [events, setEvents] = useState<RoverSimulationEvent[]>([]);
  const [filterType, setFilterType] = useState<string>("ALL");

  const refreshEvents = () => {
    const history = roverEventBus.getHistory(50, selectedRoverId || undefined);
    setEvents([...history]);
  };

  useEffect(() => {
    refreshEvents();

    const unsubscribe = roverEventBus.subscribe("*", () => {
      refreshEvents();
    });

    return () => {
      unsubscribe();
    };
  }, [selectedRoverId]);

  const filtered = events.filter((ev) => {
    if (filterType === "ALL") return true;
    return ev.type === filterType;
  });

  return (
    <Card variant="industrial" className="p-4 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2.5">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-cyan-400" />
          <h3 className="text-xs font-mono uppercase font-semibold text-slate-200">
            Real-Time Simulation Event Bus Audit Log
          </h3>
          <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded text-slate-400 font-mono">
            {filtered.length} EVENTS
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-300 text-xs focus:outline-none"
          >
            <option value="ALL">All Event Types</option>
            <option value="ROVER_STATE_CHANGED">State Changed</option>
            <option value="ROVER_MISSION_EVENT">Mission Events</option>
            <option value="ROVER_EMERGENCY_STOP">Emergency Stop</option>
            <option value="SIMULATION_STATUS_CHANGED">Engine Status</option>
          </select>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="py-6 text-center text-xs text-slate-500 font-mono">
          No simulation events logged yet. Trigger an action or run the simulation engine to generate events.
        </div>
      ) : (
        <div className="max-h-60 overflow-y-auto space-y-1.5 pr-1 font-mono text-[11px]">
          {filtered.map((ev) => {
            let badgeColor = "bg-cyan-500/10 text-cyan-400 border-cyan-500/30";
            let desc = "";

            if (ev.type === "ROVER_STATE_CHANGED") {
              badgeColor = "bg-sky-500/10 text-sky-400 border-sky-500/30";
              desc = `Rover ${ev.roverId}: ${ev.transition.previousState} -> ${ev.transition.newState} (${ev.transition.reason})`;
            } else if (ev.type === "ROVER_MISSION_EVENT") {
              badgeColor = "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
              desc = `Mission ${ev.missionId} [${ev.action}]: ${ev.details}`;
            } else if (ev.type === "ROVER_EMERGENCY_STOP") {
              badgeColor = "bg-rose-500/20 text-rose-400 border-rose-500/40";
              desc = `EMERGENCY STOP on ${ev.roverId}: ${ev.reason} (Triggered by: ${ev.triggeredBy})`;
            } else if (ev.type === "SIMULATION_STATUS_CHANGED") {
              badgeColor = "bg-amber-500/10 text-amber-300 border-amber-500/30";
              desc = `Simulation Engine: ${ev.isRunning ? "RUNNING" : "PAUSED"} (Interval: ${ev.intervalMs}ms)`;
            } else if (ev.type === "SIMULATION_TICK") {
              badgeColor = "bg-slate-800 text-slate-400 border-slate-700";
              desc = `Tick #${ev.tickNumber}: ${ev.activeRoverCount} active rover units`;
            } else if (ev.type === "ROVER_TELEMETRY_UPDATED") {
              badgeColor = "bg-slate-800 text-slate-400 border-slate-700";
              desc = `Telemetry pulse: ${ev.roverId} at ${ev.rover.currentLocation.stationName}`;
            }

            return (
              <div
                key={ev.id}
                className="flex items-start justify-between gap-3 p-2 rounded-lg border border-slate-800/80 bg-slate-900/40"
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-1.5 py-0.2 rounded text-[9px] uppercase border font-semibold ${badgeColor}`}
                    >
                      {ev.type.replace("ROVER_", "")}
                    </span>
                    <span className="text-slate-300 text-[10px]">{desc}</span>
                  </div>
                </div>

                <div className="text-[10px] text-slate-500 whitespace-nowrap shrink-0">
                  {new Date(ev.timestamp).toLocaleTimeString()}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}

