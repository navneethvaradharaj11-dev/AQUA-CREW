"use client";

import React from "react";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Map,
  Bot,
  Navigation,
  Activity,
  BrainCircuit,
  Crosshair,
  Wrench,
  BarChart3,
  FileText,
  Sliders,
  ChevronLeft,
  ChevronRight,
  Droplets,
  Radio,
  ShieldAlert,
  Compass,
  Sparkles,
  Gauge,
  Radar,
  Cpu,
  ShieldCheck,
} from "lucide-react";

export interface NavItem {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  category?: "Core" | "Operations" | "Intelligence" | "System";
}

export const NAV_ITEMS: NavItem[] = [
  { id: "overview", name: "Overview", icon: LayoutDashboard, category: "Core" },
  { id: "city-map", name: "City Map", icon: Map, badge: "GIS", category: "Core" },
  { id: "rover-fleet", name: "Rover Fleet", icon: Bot, badge: "3 Virtual", category: "Operations" },
  { id: "dispatch", name: "Autonomous Dispatch", icon: Navigation, badge: "Task 08", category: "Operations" },
  { id: "mission-control", name: "Mission Control", icon: Radio, category: "Operations" },
  { id: "sensor-monitoring", name: "Sensor Monitoring", icon: Activity, badge: "12 Nodes", category: "Operations" },
  { id: "intelligence", name: "AI Intelligence", icon: BrainCircuit, badge: "Active ML", category: "Intelligence" },
  { id: "maintenance", name: "Predictive Maintenance", icon: Wrench, badge: "Task 09", category: "Intelligence" },
  { id: "digital-twin", name: "Digital Twin & Hydraulics", icon: Activity, badge: "Task 10", category: "Intelligence" },
  { id: "infrastructure-intelligence", name: "Infrastructure Intelligence", icon: ShieldAlert, badge: "Task 11", category: "Intelligence" },
  { id: "operational-intelligence", name: "Ops Decision Support", icon: Compass, badge: "Task 12", category: "Intelligence" },
  { id: "ai-assistant", name: "AI Decision Assistant", icon: Sparkles, badge: "Task 13", category: "Intelligence" },
  { id: "optimization", name: "Network Optimization", icon: Gauge, badge: "Task 14", category: "Intelligence" },
  { id: "inspection-intelligence", name: "Autonomous Inspection", icon: Radar, badge: "Task 15", category: "Operations" },
  { id: "leak-localization", name: "Leak Localization", icon: Crosshair, category: "Intelligence" },
  { id: "repair-management", name: "Repair Management", icon: Wrench, badge: "Task 16", category: "Operations" },
  { id: "iot-devices", name: "IoT & Hardware Gateway", icon: Cpu, badge: "Task 18", category: "Operations" },
  { id: "incidents", name: "Incident Workspace", icon: ShieldCheck, badge: "Task 19", category: "Operations" },
  { id: "analytics", name: "Analytics", icon: BarChart3, category: "Intelligence" },
  { id: "reports", name: "Reports", icon: FileText, category: "System" },
  { id: "settings", name: "Settings", icon: Sliders, category: "System" },
];

export interface SidebarProps {
  activeId: string;
  onSelect: (id: string) => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  className?: string;
}

export function Sidebar({
  activeId,
  onSelect,
  isCollapsed,
  onToggleCollapse,
  className,
}: SidebarProps) {
  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-slate-800 bg-slate-950/95 transition-all duration-300 select-none z-30 shrink-0",
        isCollapsed ? "w-16" : "w-64",
        className
      )}
    >
      {/* Sidebar Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-slate-800">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-sm">
            <Droplets className="h-5 w-5" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col truncate">
              <span className="font-bold text-sm tracking-wider text-white">AQUA CREW</span>
              <span className="text-[10px] font-mono text-cyan-400">COMMAND SHELL</span>
            </div>
          )}
        </div>

        <button
          onClick={onToggleCollapse}
          className="flex h-7 w-7 items-center justify-center rounded-md border border-slate-800 bg-slate-900 text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* Navigation List */}
      <nav className="flex-1 overflow-y-auto px-2 py-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeId === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelect(item.id)}
              title={isCollapsed ? item.name : undefined}
              className={cn(
                "group relative flex w-full items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-all duration-150",
                isActive
                  ? "bg-cyan-950/50 text-cyan-300 border border-cyan-500/30 shadow-sm shadow-cyan-500/10"
                  : "text-slate-400 hover:bg-slate-900/80 hover:text-slate-200 border border-transparent"
              )}
            >
              {isActive && (
                <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-cyan-400" />
              )}
              <Icon
                className={cn(
                  "h-4 w-4 shrink-0 transition-colors",
                  isActive ? "text-cyan-400" : "text-slate-400 group-hover:text-slate-200"
                )}
              />
              {!isCollapsed && (
                <div className="flex flex-1 items-center justify-between truncate">
                  <span className="truncate">{item.name}</span>
                  {item.badge && (
                    <span
                      className={cn(
                        "rounded px-1.5 py-0.2 text-[9px] font-mono uppercase tracking-wide",
                        isActive
                          ? "bg-cyan-900/80 text-cyan-300 border border-cyan-700/50"
                          : "bg-slate-800 text-slate-400"
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </button>
          );
        })}
      </nav>

      {/* Sidebar Footer / Telemetry Status */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-900/30">
        {!isCollapsed ? (
          <div className="rounded-lg border border-cyan-900/40 bg-cyan-950/20 p-2.5 space-y-1.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="flex items-center gap-1.5 text-cyan-400 font-medium">
                <Radio className="h-3 w-3 animate-pulse" />
                Virtual HAL
              </span>
              <span className="font-mono text-[10px] text-emerald-400">SYNCED</span>
            </div>
            <div className="text-[10px] text-slate-400 font-mono leading-tight">
              Software-First Sim v0.1
            </div>
          </div>
        ) : (
          <div className="flex justify-center" title="Virtual HAL: Synced">
            <div className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50" />
          </div>
        )}
      </div>
    </aside>
  );
}

