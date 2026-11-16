"use client";

import React, { useState } from "react";
import { Search, MapPin, Bot, Droplets, Layers, X } from "lucide-react";

export interface SearchResultItem {
  id: string;
  name: string;
  type: "pipeline" | "incident" | "rover" | "zone";
  coordinates: [number, number]; // [lng, lat]
  subtext: string;
}

export interface MapSearchBarProps {
  onFlyTo: (coordinates: [number, number], zoom?: number) => void;
  onSelectFeatureId: (type: "pipeline" | "incident" | "rover" | "zone", id: string) => void;
}

export function MapSearchBar({ onFlyTo, onSelectFeatureId }: MapSearchBarProps) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  // Searchable catalog of simulated assets
  const ASSETS: SearchResultItem[] = [
    {
      id: "PIPE-SEC-4B-92",
      name: "Metro Central Main Trunk Line B",
      type: "pipeline",
      coordinates: [-74.0060, 40.7128],
      subtext: "Primary Trunk • 600mm Ductile Iron",
    },
    {
      id: "PIPE-IND-1A-04",
      name: "Industrial Park Feeder Line 1",
      type: "pipeline",
      coordinates: [-74.0021, 40.7145],
      subtext: "Secondary Feeder • 400mm HDPE",
    },
    {
      id: "PIPE-RES-3C-11",
      name: "Pinecrest Residential Sub-Branch",
      type: "pipeline",
      coordinates: [-74.0089, 40.7198],
      subtext: "Secondary Feeder • 350mm Ductile Iron",
    },
    {
      id: "INC-2026-081",
      name: "Critical Acoustic Burst Incident",
      type: "incident",
      coordinates: [-74.0060, 40.7128],
      subtext: "Critical • 680 L/h • Sector 4",
    },
    {
      id: "INC-2026-079",
      name: "Industrial Park Feeder Leak",
      type: "incident",
      coordinates: [-74.0021, 40.7145],
      subtext: "High • 420 L/h • Sector 1",
    },
    {
      id: "ROV-AQUA-01",
      name: "Triton-1 Crawler",
      type: "rover",
      coordinates: [-74.0060, 40.7128],
      subtext: "Rover Active • Station 142m",
    },
    {
      id: "ROV-AQUA-02",
      name: "Nautilus Ground Scout",
      type: "rover",
      coordinates: [-74.0021, 40.7145],
      subtext: "Rover Active • East Avenue",
    },
    {
      id: "ROV-AQUA-03",
      name: "Hydra Pipe Probe",
      type: "rover",
      coordinates: [-74.0089, 40.7198],
      subtext: "Rover Online • Northern Pump Station",
    },
    {
      id: "ZONE-SEC-04",
      name: "Sector 4 — Metro Business Core",
      type: "zone",
      coordinates: [-74.0095, 40.7140],
      subtext: "Inspection Sector 4 • 420 Segments",
    },
  ];

  const results = query.trim()
    ? ASSETS.filter(
        (a) =>
          a.id.toLowerCase().includes(query.toLowerCase()) ||
          a.name.toLowerCase().includes(query.toLowerCase()) ||
          a.subtext.toLowerCase().includes(query.toLowerCase())
      )
    : [];

  const handleSelect = (item: SearchResultItem) => {
    onFlyTo(item.coordinates, 15.5);
    onSelectFeatureId(item.type, item.id);
    setQuery("");
    setIsOpen(false);
  };

  const getItemIcon = (type: SearchResultItem["type"]) => {
    switch (type) {
      case "pipeline":
        return <Layers className="h-3.5 w-3.5 text-cyan-400" />;
      case "incident":
        return <Droplets className="h-3.5 w-3.5 text-rose-400" />;
      case "rover":
        return <Bot className="h-3.5 w-3.5 text-emerald-400" />;
      case "zone":
      default:
        return <MapPin className="h-3.5 w-3.5 text-amber-400" />;
    }
  };

  return (
    <div className="absolute top-4 right-4 z-20 w-72 sm:w-80">
      <div className="relative">
        <Search className="h-4 w-4 absolute left-3 top-3 text-slate-400" />
        <input
          type="text"
          value={query}
          onFocus={() => setIsOpen(true)}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          placeholder="Search pipe ID, leak, rover..."
          className="w-full h-10 pl-9 pr-8 rounded-xl border border-slate-800 bg-slate-950/85 text-xs text-slate-100 placeholder:text-slate-500 backdrop-blur-md shadow-2xl focus:outline-none focus:border-cyan-500 font-mono"
        />
        {query && (
          <button
            onClick={() => {
              setQuery("");
              setIsOpen(false);
            }}
            className="absolute right-2.5 top-3 text-slate-500 hover:text-white"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div className="absolute left-0 right-0 mt-2 rounded-xl border border-slate-800 bg-slate-950/95 p-1.5 shadow-2xl backdrop-blur-xl z-30 max-h-64 overflow-y-auto space-y-1">
          {results.map((item) => (
            <button
              key={item.id}
              onClick={() => handleSelect(item)}
              className="flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2 text-left hover:bg-slate-900 transition-colors group"
            >
              <div className="mt-0.5 shrink-0">{getItemIcon(item.type)}</div>
              <div className="flex-1 truncate">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-semibold text-white group-hover:text-cyan-300">
                    {item.id}
                  </span>
                  <span className="text-[10px] font-mono uppercase text-slate-500">
                    {item.type}
                  </span>
                </div>
                <div className="text-[11px] text-slate-300 truncate">{item.name}</div>
                <div className="text-[10px] font-mono text-slate-500 truncate">{item.subtext}</div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

