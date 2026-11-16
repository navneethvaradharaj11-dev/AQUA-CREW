import React from "react";
import {
  LayoutDashboard,
  Map,
  Bot,
  Navigation,
  Activity,
  BrainCircuit,
  Crosshair,
  Wrench,
  CheckCircle2,
  BarChart3,
  BellRing,
  Radio,
} from "lucide-react";

interface ModuleSpec {
  id: number;
  name: string;
  category: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  status: "Architected" | "Prepared" | "Planned";
}

const MODULES: ModuleSpec[] = [
  {
    id: 1,
    name: "Command Center",
    category: "Operations",
    description: "Centralized real-time situational awareness across municipal grids.",
    icon: LayoutDashboard,
    status: "Prepared",
  },
  {
    id: 2,
    name: "Pipeline Mapping",
    category: "Geospatial",
    description: "PostGIS-backed underground pipe topology, valves, and pressure zones.",
    icon: Map,
    status: "Prepared",
  },
  {
    id: 3,
    name: "Rover Fleet Management",
    category: "Fleet",
    description: "Autonomous ground & pipe crawler registry, diagnostics, and battery status.",
    icon: Bot,
    status: "Prepared",
  },
  {
    id: 4,
    name: "Mission Control",
    category: "Operations",
    description: "Autonomous patrol dispatch, waypoint scheduling, and abort protocols.",
    icon: Navigation,
    status: "Prepared",
  },
  {
    id: 5,
    name: "Sensor Monitoring",
    category: "IoT / Telemetry",
    description: "Acoustic hydrophone, pressure transient, and flow meter telemetry streams.",
    icon: Activity,
    status: "Prepared",
  },
  {
    id: 6,
    name: "AI Leak Detection",
    category: "Machine Learning",
    description: "Spectral acoustic analysis and pressure drop anomaly classifiers.",
    icon: BrainCircuit,
    status: "Prepared",
  },
  {
    id: 7,
    name: "Leak Localization",
    category: "Signal Processing",
    description: "Time-difference-of-arrival (TDOA) pinpointing with sub-meter precision.",
    icon: Crosshair,
    status: "Prepared",
  },
  {
    id: 8,
    name: "Repair Management",
    category: "Field Operations",
    description: "Ticketing, utility work orders, and field maintenance dispatch.",
    icon: Wrench,
    status: "Prepared",
  },
  {
    id: 9,
    name: "Repair Verification",
    category: "Quality Assurance",
    description: "Post-repair acoustic verification & hydraulic pressure certification.",
    icon: CheckCircle2,
    status: "Prepared",
  },
  {
    id: 10,
    name: "Analytics & Reporting",
    category: "Executive",
    description: "Non-revenue water (NRW) reduction, water volume saved, and cost models.",
    icon: BarChart3,
    status: "Prepared",
  },
  {
    id: 11,
    name: "Alerts & Notifications",
    category: "Dispatch",
    description: "Multi-channel urgent notifications, escalations, and automated sirens.",
    icon: BellRing,
    status: "Prepared",
  },
  {
    id: 12,
    name: "Hardware Gateway",
    category: "Integration",
    description: "Hardware Abstraction Layer (HAL), MQTT, ROS2, and simulated telemetry bridges.",
    icon: Radio,
    status: "Prepared",
  },
];

export function ModuleGrid() {
  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-white">
            Architecture Blueprint & Planned Modules
          </h2>
          <p className="text-xs text-slate-400">
            Strict domain boundaries established for modular phase-by-phase implementation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center rounded-md border border-cyan-800/60 bg-cyan-950/40 px-2.5 py-1 text-xs font-medium text-cyan-300">
            12 Architectural Boundaries Configured
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {MODULES.map((mod) => {
          const Icon = mod.icon;
          return (
            <div
              key={mod.id}
              className="flex flex-col justify-between rounded-xl border border-slate-800/80 bg-slate-900/30 p-4 transition-all hover:border-slate-700 hover:bg-slate-900/60"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[11px] font-mono uppercase text-slate-500">
                    MOD-0{mod.id < 10 ? `0${mod.id}` : mod.id}
                  </span>
                  <span className="rounded bg-slate-800/80 px-2 py-0.5 text-[10px] font-medium text-cyan-400 border border-slate-700/60">
                    {mod.status}
                  </span>
                </div>
                <div className="flex items-start gap-3">
                  <div className="rounded-lg bg-slate-800/60 p-2 text-cyan-400">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">{mod.name}</h3>
                    <span className="text-[11px] font-medium text-slate-400">
                      {mod.category}
                    </span>
                  </div>
                </div>
                <p className="mt-3 text-xs leading-relaxed text-slate-400">
                  {mod.description}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
                <span>Contract Ready</span>
                <span className="text-slate-400 font-mono">Software-First</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

