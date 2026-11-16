"use client";

import React from "react";
import { Eye, X } from "lucide-react";

export interface MapLegendProps {
  onClose: () => void;
}

export function MapLegend({ onClose }: MapLegendProps) {
  return (
    <div className="absolute bottom-14 right-4 z-20 w-64 rounded-2xl border border-slate-800/90 bg-slate-950/90 p-4 backdrop-blur-xl shadow-2xl animate-in fade-in zoom-in-95 duration-150 space-y-3.5 text-xs">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center gap-1.5 font-mono text-[11px] font-bold text-white uppercase">
          <Eye className="h-3.5 w-3.5 text-cyan-400" />
          GIS Map Legend
        </div>
        <button
          onClick={onClose}
          className="text-slate-500 hover:text-white transition-colors"
          aria-label="Close legend"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Pipeline Symbology */}
      <div className="space-y-1.5">
        <span className="text-[10px] font-mono uppercase text-slate-500 block">Pipelines</span>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-5 bg-cyan-400 rounded-sm" />
            <span className="text-slate-300">Primary Trunk (600-750mm)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-5 bg-sky-400 rounded-sm" />
            <span className="text-slate-300">Secondary Feeder (350-400mm)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-5 bg-teal-400 rounded-sm" />
            <span className="text-slate-300">Distribution Main (200-250mm)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-1 w-5 border-b border-dashed border-slate-400" />
            <span className="text-slate-300">Service Lateral (100-150mm)</span>
          </div>
        </div>
      </div>

      {/* Leak Severity */}
      <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
        <span className="text-[10px] font-mono uppercase text-slate-500 block">Leak Severities</span>
        <div className="grid grid-cols-2 gap-1 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-500" />
            <span className="text-slate-300">Critical</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber-500" />
            <span className="text-slate-300">High</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-cyan-400" />
            <span className="text-slate-300">Medium</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-slate-400" />
            <span className="text-slate-300">Low</span>
          </div>
        </div>
      </div>

      {/* Fleet & Stations */}
      <div className="space-y-1.5 pt-2 border-t border-slate-800/80 text-[11px]">
        <span className="text-[10px] font-mono uppercase text-slate-500 block">Fleet & Nodes</span>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full border-2 border-emerald-400 bg-emerald-950" />
            <span className="text-slate-300">Active Rover Crawler</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-sm bg-cyan-400" />
            <span className="text-slate-300">IoT Sensor Station</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-3 rounded-sm border border-cyan-400/50 bg-cyan-950/40" />
            <span className="text-slate-300">Inspection Zone Sector</span>
          </div>
        </div>
      </div>
    </div>
  );
}

