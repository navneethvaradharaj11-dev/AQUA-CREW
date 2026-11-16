"use client";

import React from "react";
import { Compass, Crosshair } from "lucide-react";

export interface CoordinateDisplayProps {
  coords: { lng: number; lat: number } | null;
  zoom: number;
}

export function CoordinateDisplay({ coords, zoom }: CoordinateDisplayProps) {
  return (
    <div className="absolute bottom-4 left-4 z-20 flex flex-wrap items-center gap-2 rounded-lg border border-slate-800/80 bg-slate-950/85 px-3 py-1.5 text-[11px] font-mono text-slate-400 backdrop-blur-md shadow-lg">
      <div className="flex items-center gap-1.5 text-slate-300">
        <Crosshair className="h-3.5 w-3.5 text-cyan-400" />
        <span>
          LAT: {coords ? Math.abs(coords.lat).toFixed(5) : "12.97160"}° {coords ? (coords.lat >= 0 ? "N" : "S") : "N"}
        </span>
        <span className="text-slate-600">|</span>
        <span>
          LNG: {coords ? Math.abs(coords.lng).toFixed(5) : "77.59460"}° {coords ? (coords.lng >= 0 ? "E" : "W") : "E"}
        </span>
      </div>

      <span className="text-slate-600 hidden sm:inline">|</span>

      <div className="hidden sm:flex items-center gap-1 text-slate-400">
        <Compass className="h-3 w-3 text-slate-500" />
        <span>ZOOM: {zoom.toFixed(1)}x</span>
      </div>

      <span className="text-slate-600">|</span>

      <span className="rounded bg-amber-950/80 border border-amber-800/60 px-1.5 py-0.2 text-[9px] font-mono font-bold text-amber-300">
        SIMULATED GIS
      </span>
    </div>
  );
}

