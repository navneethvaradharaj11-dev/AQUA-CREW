"use client";

import React from "react";
import { Compass, Maximize2, MapPin, Eye, Layers, Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/Button";

export interface MapToolbarProps {
  onFitBounds: () => void;
  onCenterMetro: () => void;
  onResetBearing: () => void;
  basemapStyle: "dark" | "light" | "osm";
  onChangeBasemap: (style: "dark" | "light" | "osm") => void;
  isLayerPanelOpen: boolean;
  onToggleLayerPanel: () => void;
  isLegendOpen: boolean;
  onToggleLegend: () => void;
}

export function MapToolbar({
  onFitBounds,
  onCenterMetro,
  onResetBearing,
  basemapStyle,
  onChangeBasemap,
  isLayerPanelOpen,
  onToggleLayerPanel,
  isLegendOpen,
  onToggleLegend,
}: MapToolbarProps) {
  return (
    <div className="absolute top-4 left-4 z-20 flex flex-wrap items-center gap-2 rounded-xl border border-slate-800/90 bg-slate-950/85 p-2 backdrop-blur-md shadow-2xl">
      <Button
        variant="industrial"
        size="sm"
        onClick={onFitBounds}
        leftIcon={<Maximize2 className="h-3.5 w-3.5" />}
        title="Fit camera to entire pipeline network"
      >
        Fit Network
      </Button>

      <Button
        variant="secondary"
        size="sm"
        onClick={onCenterMetro}
        leftIcon={<MapPin className="h-3.5 w-3.5 text-cyan-400" />}
        title="Center camera on Sector 4 Metro Core"
      >
        Sector 4 Core
      </Button>

      <Button
        variant="ghost"
        size="sm"
        onClick={onResetBearing}
        leftIcon={<Compass className="h-3.5 w-3.5 text-slate-400" />}
        title="Reset compass heading to North"
      >
        Reset North
      </Button>

      <div className="h-4 w-px bg-slate-800 mx-1 hidden sm:block" />

      {/* Basemap Switcher */}
      <div className="flex items-center rounded-lg border border-slate-800 bg-slate-900/60 p-0.5 text-xs font-mono">
        <button
          onClick={() => onChangeBasemap("dark")}
          className={`rounded-md px-2 py-1 text-[11px] transition-colors ${
            basemapStyle === "dark" ? "bg-cyan-950 text-cyan-300 font-bold" : "text-slate-400 hover:text-white"
          }`}
          title="CartoDB Dark Matter Basemap"
        >
          Dark
        </button>
        <button
          onClick={() => onChangeBasemap("light")}
          className={`rounded-md px-2 py-1 text-[11px] transition-colors ${
            basemapStyle === "light" ? "bg-slate-700 text-white font-bold" : "text-slate-400 hover:text-white"
          }`}
          title="CartoDB Positron Basemap"
        >
          Light
        </button>
        <button
          onClick={() => onChangeBasemap("osm")}
          className={`rounded-md px-2 py-1 text-[11px] transition-colors ${
            basemapStyle === "osm" ? "bg-slate-700 text-white font-bold" : "text-slate-400 hover:text-white"
          }`}
          title="Standard OpenStreetMap Tiles"
        >
          OSM
        </button>
      </div>

      <div className="h-4 w-px bg-slate-800 mx-1 hidden sm:block" />

      <Button
        variant={isLayerPanelOpen ? "primary" : "secondary"}
        size="sm"
        onClick={onToggleLayerPanel}
        leftIcon={<Layers className="h-3.5 w-3.5" />}
      >
        Layers
      </Button>

      <Button
        variant={isLegendOpen ? "primary" : "secondary"}
        size="sm"
        onClick={onToggleLegend}
        leftIcon={<Eye className="h-3.5 w-3.5" />}
      >
        Legend
      </Button>
    </div>
  );
}

