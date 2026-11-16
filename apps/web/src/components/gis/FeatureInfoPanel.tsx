"use client";

import React from "react";
import { SelectedMapFeature } from "@/services/gis/types";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import {
  Layers,
  Droplets,
  Bot,
  Radio,
  MapPin,
  X,
  Gauge,
  ArrowUpRight,
  Battery,
  Compass,
} from "lucide-react";

export interface FeatureInfoPanelProps {
  feature: SelectedMapFeature | null;
  onClose: () => void;
  onOpenRoverModal?: (roverId: string) => void;
  onOpenIncidentModal?: (incidentId: string) => void;
}

export function FeatureInfoPanel({
  feature,
  onClose,
  onOpenRoverModal,
  onOpenIncidentModal,
}: FeatureInfoPanelProps) {
  if (!feature) return null;

  const { type, id, title, properties } = feature;

  const getHeaderIcon = () => {
    switch (type) {
      case "pipeline":
        return <Layers className="h-5 w-5 text-cyan-400" />;
      case "incident":
        return <Droplets className="h-5 w-5 text-rose-400" />;
      case "rover":
        return <Bot className="h-5 w-5 text-emerald-400" />;
      case "sensor":
        return <Radio className="h-5 w-5 text-sky-400" />;
      case "zone":
      default:
        return <MapPin className="h-5 w-5 text-amber-400" />;
    }
  };

  return (
    <div className="absolute top-20 left-4 z-20 w-80 sm:w-96 rounded-2xl border border-slate-800/90 bg-slate-950/95 p-4 backdrop-blur-xl shadow-2xl animate-in slide-in-from-left duration-200 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between pb-3 border-b border-slate-800">
        <div className="flex items-start gap-2.5">
          <div className="p-2 rounded-xl bg-slate-900 border border-slate-800 shrink-0 mt-0.5">
            {getHeaderIcon()}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] text-cyan-400 uppercase font-bold">
                {type} RECORD
              </span>
              <span className="rounded bg-amber-950/80 px-1.5 py-0.2 text-[9px] font-mono text-amber-300">
                SIMULATED
              </span>
            </div>
            <h3 className="text-sm font-bold text-white leading-tight">{title}</h3>
            <span className="font-mono text-[10px] text-slate-500">{id}</span>
          </div>
        </div>

        <button
          onClick={onClose}
          className="text-slate-500 hover:text-white transition-colors p-1"
          aria-label="Close feature info"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Feature Content based on type */}
      <div className="space-y-3 text-xs">
        {type === "pipeline" && (
          <div className="space-y-2.5">
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Category</span>
                <span className="text-cyan-300 font-semibold">{String(properties.categoryLabel || properties.category)}</span>
              </div>
              <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Diameter</span>
                <span className="text-white font-semibold">{String(properties.diameterMm)} mm</span>
              </div>
              <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Material</span>
                <span className="text-slate-200 truncate block">{String(properties.material)}</span>
              </div>
              <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Length</span>
                <span className="text-white font-semibold">{String(properties.lengthM)} m</span>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 space-y-1.5 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Pressure Zone</span>
                <span className="font-mono text-cyan-300 font-medium">{String(properties.pressureZoneName)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Nominal Pressure</span>
                <span className="font-mono text-white font-bold">{String(properties.nominalPressurePsi)} PSI</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Inspection Status</span>
                <span className="font-mono text-amber-400">{String(properties.inspectionStatus)}</span>
              </div>
            </div>
          </div>
        )}

        {type === "incident" && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="rounded-lg border border-rose-900/40 bg-rose-950/20 p-2">
                <span className="text-[10px] text-rose-400/80 uppercase block">Severity</span>
                <span className="text-rose-400 font-bold">{String(properties.severity)}</span>
              </div>
              <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Status</span>
                <span className="text-white font-bold">{String(properties.status)}</span>
              </div>
              <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Loss Rate</span>
                <span className="text-rose-300 font-bold">{String(properties.estimatedLossRateLph)} L/h</span>
              </div>
              <div className="rounded-lg border border-slate-800/80 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">AI Confidence</span>
                <span className="text-cyan-400 font-bold">{String(properties.confidenceScorePct)}%</span>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 space-y-1 text-xs">
              <span className="text-[10px] font-mono text-slate-500 block">PIPELINE SEGMENT</span>
              <span className="text-slate-200 font-semibold block">{String(properties.segmentName)}</span>
              <span className="font-mono text-[10px] text-cyan-400 block">{String(properties.segmentId)}</span>
            </div>

            {onOpenIncidentModal && (
              <Button
                variant="primary"
                size="sm"
                className="w-full"
                onClick={() => onOpenIncidentModal(id)}
                rightIcon={<ArrowUpRight className="h-3.5 w-3.5" />}
              >
                Inspect Full Incident Dossier
              </Button>
            )}
          </div>
        )}

        {type === "rover" && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Operational Status</span>
                <span className="text-emerald-400 font-bold">{String(properties.status)}</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Battery SoC</span>
                <span className="text-cyan-300 font-bold">{String(properties.batteryPercentage)}%</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Current Speed</span>
                <span className="text-white font-bold">{String(properties.velocityMps)} m/s</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Heading</span>
                <span className="text-slate-300 font-bold">{String(properties.headingDeg)}°</span>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 space-y-1 text-xs">
              <span className="text-[10px] font-mono text-slate-500 block">CURRENT MISSION</span>
              <span className="text-slate-200 font-medium">{String(properties.currentMission)}</span>
              <span className="font-mono text-[10px] text-slate-400 block pt-1">
                Station: {String(properties.stationName)}
              </span>
            </div>

            {onOpenRoverModal && (
              <Button
                variant="primary"
                size="sm"
                className="w-full"
                onClick={() => onOpenRoverModal(id)}
                rightIcon={<ArrowUpRight className="h-3.5 w-3.5" />}
              >
                Open Rover Telemetry Console
              </Button>
            )}
          </div>
        )}

        {type === "sensor" && (
          <div className="space-y-2.5">
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Modality</span>
                <span className="text-sky-300 font-semibold">{String(properties.modalityLabel)}</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Reading</span>
                <span className="text-cyan-300 font-bold">
                  {String(properties.currentValue)} {String(properties.unit)}
                </span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Sampling Rate</span>
                <span className="text-white font-bold">{String(properties.sampleRateHz)} Hz</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Battery</span>
                <span className="text-emerald-400 font-bold">{String(properties.batteryPct)}%</span>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-xs font-mono">
              <span className="text-[10px] text-slate-500 block">AFFILIATED SEGMENT</span>
              <span className="text-slate-200">{String(properties.pipeSegmentId)}</span>
            </div>
          </div>
        )}

        {type === "zone" && (
          <div className="space-y-2.5">
            <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Sector Code</span>
                <span className="text-amber-400 font-bold">{String(properties.sectorCode)}</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Risk Score</span>
                <span className="text-rose-400 font-bold">{String(properties.riskScorePct)}%</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Area Coverage</span>
                <span className="text-white font-bold">{String(properties.areaSqKm)} km²</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2">
                <span className="text-[10px] text-slate-500 uppercase block">Total Segments</span>
                <span className="text-cyan-300 font-bold">{String(properties.totalSegmentsCount)}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

