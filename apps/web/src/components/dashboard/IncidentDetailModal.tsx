"use client";

import React from "react";
import { SimulatedLeakIncident } from "@/services/simulation/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Droplets, MapPin, Activity, ShieldAlert, Waves, FileText } from "lucide-react";

export interface IncidentDetailModalProps {
  incident: SimulatedLeakIncident | null;
  onClose: () => void;
}

export function IncidentDetailModal({ incident, onClose }: IncidentDetailModalProps) {
  if (!incident) return null;

  return (
    <Modal
      isOpen={!!incident}
      onClose={onClose}
      title={`Incident Investigation: ${incident.id}`}
      description={`Segment: ${incident.segmentName} (${incident.pipelineSegmentId})`}
      size="lg"
      footer={
        <Button variant="secondary" size="sm" onClick={onClose}>
          Close Incident Report
        </Button>
      }
    >
      <div className="space-y-4">
        {/* Simulation Notice Stamp */}
        <div className="flex items-center justify-between rounded-lg border border-amber-900/40 bg-amber-950/20 px-3 py-2 text-xs">
          <span className="font-mono text-amber-300 font-medium">
            SIMULATED INCIDENT — NOT REAL-WORLD LEAKAGE
          </span>
          <StatusBadge
            status={incident.severity === "Critical" ? "critical" : incident.severity === "High" ? "warning" : "active"}
            label={`Severity: ${incident.severity}`}
            size="sm"
          />
        </div>

        {/* Key Incident Statistics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Incident Status</span>
            <span className="text-white font-bold block">{incident.status}</span>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Est. Loss Rate</span>
            <span className="text-rose-400 font-bold block">{incident.estimatedLossRateLph} L/h</span>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">AI Confidence</span>
            <span className="text-cyan-400 font-bold block">{incident.confidenceScorePct}%</span>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Acoustic Peak</span>
            <span className="text-teal-300 font-bold block">{incident.dominantAcousticFreqHz} Hz</span>
          </div>
        </div>

        {/* Location & GIS Details */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 space-y-2 text-xs">
          <div className="flex items-start gap-2">
            <MapPin className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
            <div>
              <span className="text-slate-400 text-[11px] block">Estimated GIS Coordinates</span>
              <span className="text-slate-100 font-semibold">{incident.estimatedLocation?.zone || "Metro Inspection Zone"}</span>
              <span className="font-mono text-[11px] text-slate-400 block">
                Latitude: {incident.estimatedLocation?.latitude != null ? incident.estimatedLocation.latitude.toFixed(5) : "—"} • Longitude:{" "}
                {incident.estimatedLocation?.longitude != null ? incident.estimatedLocation.longitude.toFixed(5) : "—"} • Pipe Depth:{" "}
                {incident.estimatedLocation?.depthM ?? "—"}m
              </span>
            </div>
          </div>
        </div>

        {/* Analysis Notes */}
        <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3.5 space-y-1.5 text-xs">
          <div className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px]">
            <FileText className="h-3.5 w-3.5 text-cyan-400" />
            DIAGNOSTIC TRACE & RECOMMENDATIONS
          </div>
          <p className="text-slate-300 leading-relaxed font-sans">{incident.notes}</p>
          <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono text-slate-500">
            <span>Detection: {incident.detectionTimestamp}</span>
            {incident.assignedRoverId && (
              <span className="text-cyan-400">Assigned: {incident.assignedRoverId}</span>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}

