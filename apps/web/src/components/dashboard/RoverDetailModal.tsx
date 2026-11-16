"use client";

import React from "react";
import { SimulatedRover } from "@/services/simulation/types";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Bot, Battery, Radio, Gauge, Thermometer, Zap, Compass, MapPin } from "lucide-react";

export interface RoverDetailModalProps {
  rover: SimulatedRover | null;
  onClose: () => void;
}

export function RoverDetailModal({ rover, onClose }: RoverDetailModalProps) {
  if (!rover) return null;

  return (
    <Modal
      isOpen={!!rover}
      onClose={onClose}
      title={`${rover.name} (${rover.id})`}
      description="Simulated telemetry packet and hardware diagnostics stream."
      size="lg"
      footer={
        <Button variant="secondary" size="sm" onClick={onClose}>
          Close Telemetry Panel
        </Button>
      }
    >
      <div className="space-y-4">
        {/* Banner with Simulation Stamp */}
        <div className="flex items-center justify-between rounded-lg border border-amber-900/40 bg-amber-950/20 px-3 py-2 text-xs">
          <span className="font-mono text-amber-300 font-medium">
            DATA STATUS: VIRTUAL SIMULATION MODEL
          </span>
          <StatusBadge
            status={
              rover.operatingState === "EMERGENCY_STOP"
                ? "critical"
                : rover.status === "ACTIVE"
                ? "active"
                : rover.status === "ONLINE"
                ? "online"
                : "warning"
            }
            label={rover.operatingState || rover.status}
            pulse={rover.status === "ACTIVE"}
            size="sm"
          />
        </div>

        {/* Rover Info & Model */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Model</span>
            <span className="text-slate-200 font-semibold truncate block">{rover.model || "AQUA-CRAWLER"}</span>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Battery SoC</span>
            <span className="text-cyan-400 font-semibold">{rover.batteryPercentage ?? 0}%</span>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Velocity</span>
            <span className="text-white font-semibold">{rover.kinematics?.velocityMps ?? 0} m/s</span>
          </div>
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase block">Signal RSSI</span>
            <span className="text-emerald-400 font-semibold">{rover.diagnostics?.signalRssiDbm ?? -70} dBm</span>
          </div>
        </div>

        {/* Current Location & Mission */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 space-y-2 text-xs">
          <div className="flex items-start gap-2">
            <MapPin className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
            <div>
              <span className="text-slate-400 text-[11px] block">Current Pipe Station</span>
              <span className="text-slate-100 font-semibold">{rover.currentLocation?.stationName ?? "Station Grid"}</span>
              <span className="font-mono text-[10px] text-slate-500 block">
                GPS: {rover.currentLocation?.latitude != null ? rover.currentLocation.latitude.toFixed(5) : "—"},{" "}
                {rover.currentLocation?.longitude != null ? rover.currentLocation.longitude.toFixed(5) : "—"} • Segment:{" "}
                {rover.currentLocation?.pipeSegmentId ?? "N/A"}
              </span>
            </div>
          </div>
          <div className="flex items-start gap-2 pt-2 border-t border-slate-800/80">
            <Compass className="h-4 w-4 text-slate-500 shrink-0 mt-0.5" />
            <div>
              <span className="text-slate-400 text-[11px] block">Active Mission Assignment</span>
              <span className="text-slate-200">{rover.currentMission || "Patrol Standby"}</span>
            </div>
          </div>
        </div>

        {/* Inspection Payload Sensors */}
        <div className="space-y-2">
          <span className="text-xs font-mono uppercase text-slate-400 block">
            Payload Sensor Readings
          </span>
          <div className="grid grid-cols-3 gap-3 text-xs font-mono">
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
              <span className="text-[10px] text-slate-500 uppercase block">Acoustic SPL</span>
              <span className="text-lg font-bold text-cyan-300">{rover.payloadSensors?.acousticSplDb ?? 0} dB</span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
              <span className="text-[10px] text-slate-500 uppercase block">Dominant Freq</span>
              <span className="text-lg font-bold text-white">{rover.payloadSensors?.dominantFreqHz ?? 0} Hz</span>
            </div>
            <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
              <span className="text-[10px] text-slate-500 uppercase block">Ground Moisture</span>
              <span className="text-lg font-bold text-teal-300">{rover.payloadSensors?.groundMoisturePct ?? 0}%</span>
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
}

