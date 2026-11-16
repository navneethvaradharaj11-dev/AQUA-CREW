import React from "react";
import { SimulatedMission } from "@/services/simulation/types";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Navigation, Clock, Target, Bot } from "lucide-react";

export interface ActiveMissionsSectionProps {
  missions: SimulatedMission[];
}

export function ActiveMissionsSection({ missions }: ActiveMissionsSectionProps) {
  const getStatusColor = (status: SimulatedMission["status"]) => {
    switch (status) {
      case "In Progress":
        return "text-cyan-400 bg-cyan-950/60 border-cyan-800/60";
      case "Completed":
        return "text-emerald-400 bg-emerald-950/60 border-emerald-800/60";
      case "Paused":
        return "text-amber-400 bg-amber-950/60 border-amber-800/60";
      case "Scheduled":
      default:
        return "text-slate-400 bg-slate-900 border-slate-700";
    }
  };

  return (
    <Card variant="default">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <Navigation className="h-5 w-5 text-cyan-400" />
              <CardTitle>Active Inspection & Patrol Missions</CardTitle>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-cyan-400 border border-slate-700">
                [SIMULATED MISSIONS]
              </span>
            </div>
            <CardDescription>
              Autonomous waypoint survey routing and emergency intercept operations.
            </CardDescription>
          </div>
          <span className="text-xs font-mono text-cyan-400 font-semibold">
            {missions.filter((m) => m.status === "In Progress").length} Operations Active
          </span>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {missions.map((m) => (
            <div
              key={m.id}
              className="rounded-xl border border-slate-800/80 bg-slate-900/40 p-4 space-y-3.5"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="font-mono text-[10px] text-cyan-400 font-bold block">{m.id}</span>
                  <h4 className="font-semibold text-white text-sm">{m.missionType}</h4>
                </div>
                <span
                  className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-mono font-medium ${getStatusColor(
                    m.status
                  )}`}
                >
                  {m.status}
                </span>
              </div>

              {/* Rover Assignment & Target */}
              <div className="space-y-1.5 text-xs text-slate-300">
                <div className="flex items-center gap-1.5">
                  <Bot className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                  <span className="font-medium text-slate-200">{m.assignedRoverName}</span>
                  <span className="text-[10px] font-mono text-slate-500">({m.assignedRoverId})</span>
                </div>
                <div className="flex items-center gap-1.5 text-slate-400 text-[11px]">
                  <Target className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                  <span>Target: <code>{m.targetSegmentId}</code></span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1 pt-1">
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-slate-400">Waypoints: {m.completedWaypoints}/{m.waypointCount}</span>
                  <span className="text-cyan-300 font-bold">{m.progressPercentage}%</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-cyan-400 transition-all duration-500"
                    style={{ width: `${m.progressPercentage}%` }}
                  />
                </div>
              </div>

              {/* Timing */}
              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-500 font-mono">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" /> Start: {m.startTime.split(" ")[0]}
                </span>
                <span>ETA: {m.estimatedCompletionTime.split(" ")[0]}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

