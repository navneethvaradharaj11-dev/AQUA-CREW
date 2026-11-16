"use client";

import React, { useState } from "react";
import {
  Sliders,
  ShieldCheck,
  ShieldAlert,
  Lock,
  Cpu,
  Activity,
  UserCheck,
  Save,
  RotateCcw,
  Volume2,
  VolumeX,
  Server,
  KeyRound,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";

export function SettingsView() {
  const [simulationSpeed, setSimulationSpeed] = useState<"1x" | "2x" | "5x">("1x");
  const [tickRateHz, setTickRateHz] = useState<number>(60);
  const [noiseFloorDb, setNoiseFloorDb] = useState<number>(-70);
  const [audioAlerts, setAudioAlerts] = useState<boolean>(true);
  const [activeRole, setActiveRole] = useState<string>("PRINCIPAL_OPERATOR");
  const [apiUrl, setApiUrl] = useState<string>("http://localhost:8005/api/v1");
  const [wsUrl, setWsUrl] = useState<string>("ws://localhost:8005/api/v1/ws");
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  const handleSave = () => {
    setSavedMessage("Configuration saved. System operating in simulation-first mode.");
    setTimeout(() => setSavedMessage(null), 4000);
  };

  const handleResetDefaults = () => {
    setSimulationSpeed("1x");
    setTickRateHz(60);
    setNoiseFloorDb(-70);
    setAudioAlerts(true);
    setSavedMessage("Settings restored to factory engineering defaults.");
    setTimeout(() => setSavedMessage(null), 4000);
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <Sliders className="h-6 w-6 text-cyan-400" />
            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white">
              Platform & Simulation Settings
            </h1>
            <span className="rounded bg-cyan-950/80 px-2.5 py-0.5 text-xs font-mono text-cyan-300 border border-cyan-800/60 font-semibold">
              TASK 20 RELEASE
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Configure hydrodynamic simulation parameters, hardware safety guards, access control role bindings, and telemetry streaming endpoints.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleResetDefaults} leftIcon={<RotateCcw className="h-3.5 w-3.5" />}>
            Reset Defaults
          </Button>
          <Button variant="primary" size="sm" onClick={handleSave} leftIcon={<Save className="h-3.5 w-3.5" />}>
            Save Preferences
          </Button>
        </div>
      </div>

      {savedMessage && (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/40 bg-emerald-950/30 px-3.5 py-2 text-xs text-emerald-300 font-mono animate-in fade-in">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
          <span>{savedMessage}</span>
        </div>
      )}

      {/* 1. Critical Hardware Safety Enforcement (Task 18 Mandatory Requirement) */}
      <Card variant="industrial" className="border-amber-900/60 bg-amber-950/15 p-5 space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-950/80 border border-amber-800/80 text-amber-400">
              <Lock className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white">HARDWARE ACTUATION SAFETY INTERLOCK</h3>
                <span className="rounded bg-rose-950/90 px-2 py-0.5 text-[10px] font-mono text-rose-300 border border-rose-800/80 font-bold">
                  PERMANENTLY LOCKED
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Backend Enforced: <code>HARDWARE_ACTUATION_ENABLED = false</code>
              </p>
            </div>
          </div>

          <StatusBadge status="critical" label="ACTUATION DISABLED" size="sm" />
        </div>

        <p className="text-xs text-slate-300 leading-relaxed font-sans bg-slate-900/60 p-3 rounded-lg border border-slate-800">
          In strict compliance with the platform safety charter, AQUA CREW runs in a simulation-first sandbox. Physical pump speeds, automated valve shutoffs, and direct crawler servo triggers are rejected by backend security middleware. All operations are non-actuating telemetry reads and virtual simulations.
        </p>
      </Card>

      {/* 2. Simulation Engine Tuning */}
      <Card variant="industrial" className="p-5 space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
            <Cpu className="h-4 w-4 text-cyan-400" />
            Simulation Engine Parameters & Physics Loop
          </CardTitle>
          <p className="text-xs text-slate-400">
            Tune the real-time simulation broker execution loop and acoustic synthesizer characteristics.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
          {/* Tick Rate */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 space-y-2">
            <span className="text-slate-300 font-semibold block">Simulation Engine Tick Rate</span>
            <div className="flex items-center gap-2">
              {[30, 60, 120].map((hz) => (
                <button
                  key={hz}
                  onClick={() => setTickRateHz(hz)}
                  className={`flex-1 py-1.5 rounded-lg border text-xs font-bold transition-colors ${
                    tickRateHz === hz
                      ? "bg-cyan-500 text-slate-950 border-cyan-400"
                      : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
                  }`}
                >
                  {hz} Hz
                </button>
              ))}
            </div>
            <span className="text-[10px] text-slate-500 block">
              Determines temporal resolution for crawler movement & pressure wave decay.
            </span>
          </div>

          {/* Time Warp / Speed */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 space-y-2">
            <span className="text-slate-300 font-semibold block">Simulation Clock Speed</span>
            <div className="flex items-center gap-2">
              {(["1x", "2x", "5x"] as const).map((spd) => (
                <button
                  key={spd}
                  onClick={() => setSimulationSpeed(spd)}
                  className={`flex-1 py-1.5 rounded-lg border text-xs font-bold transition-colors ${
                    simulationSpeed === spd
                      ? "bg-emerald-500 text-slate-950 border-emerald-400"
                      : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
                  }`}
                >
                  {spd} Realtime
                </button>
              ))}
            </div>
            <span className="text-[10px] text-slate-500 block">
              Accelerate long-duration pipeline leak scenarios and crawler surveys.
            </span>
          </div>

          {/* Acoustic Sensor Noise Floor */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-300 font-semibold">Sensor Acoustic Noise Floor</span>
              <span className="text-cyan-400 font-bold">{noiseFloorDb} dB</span>
            </div>
            <input
              type="range"
              min="-100"
              max="-40"
              value={noiseFloorDb}
              onChange={(e) => setNoiseFloorDb(Number(e.target.value))}
              className="w-full accent-cyan-400 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
            />
            <span className="text-[10px] text-slate-500 block">
              Simulates environmental background vibrations in industrial zones.
            </span>
          </div>

          {/* Audio Chimes */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3.5 space-y-2 flex flex-col justify-between">
            <div className="flex justify-between items-center">
              <span className="text-slate-300 font-semibold">Critical Incident Audio Alerts</span>
              <button
                onClick={() => setAudioAlerts(!audioAlerts)}
                className={`p-1.5 rounded-lg border transition-colors ${
                  audioAlerts
                    ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/40"
                    : "bg-slate-900 text-slate-500 border-slate-800"
                }`}
              >
                {audioAlerts ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
              </button>
            </div>
            <span className="text-[10px] text-slate-500 block">
              Audible sonar ping when AI classifies an acoustic signal as Critical Burst.
            </span>
          </div>
        </div>
      </Card>

      {/* 3. Role-Based Access Control (RBAC) */}
      <Card variant="industrial" className="p-5 space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
            <UserCheck className="h-4 w-4 text-emerald-400" />
            Active Role-Based Access Control (RBAC) Profile
          </CardTitle>
          <p className="text-xs text-slate-400">
            Switch your current session clearance tier to verify authorization rules across endpoints.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs font-mono">
          {[
            { id: "ADMINISTRATOR", name: "Administrator", perms: "Full System Access" },
            { id: "HYDRAULIC_ENGINEER", name: "Hydraulic Engineer", perms: "Twin & Digital Models" },
            { id: "PRINCIPAL_OPERATOR", name: "Principal Operator", perms: "Dispatch & Approvals" },
            { id: "VIEWER", name: "Read-Only Viewer", perms: "Telemetry Observation" },
          ].map((role) => (
            <div
              key={role.id}
              onClick={() => setActiveRole(role.id)}
              className={`p-3 rounded-xl border transition-all cursor-pointer space-y-1 ${
                activeRole === role.id
                  ? "border-emerald-500 bg-emerald-950/20 shadow-emerald-glow-sm"
                  : "border-slate-800/80 bg-slate-900/40 hover:border-slate-700"
              }`}
            >
              <span className="text-white font-bold block">{role.name}</span>
              <span className="text-[10px] text-slate-400 block">{role.perms}</span>
              {activeRole === role.id && (
                <span className="text-[10px] text-emerald-400 font-bold block pt-1">
                  ✓ ACTIVE SESSION
                </span>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* 4. API & Telemetry Stream Connectivity */}
      <Card variant="industrial" className="p-5 space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <CardTitle className="text-sm font-bold text-white flex items-center gap-2">
            <Server className="h-4 w-4 text-cyan-400" />
            Backend REST & Real-Time WebSocket Endpoints
          </CardTitle>
          <p className="text-xs text-slate-400">
            Active gateway ports configured for local multi-service orchestration.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
          <div className="space-y-1.5">
            <label className="text-slate-400 font-medium">FastAPI REST Base URL</label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-2 text-slate-100 font-mono text-xs focus:border-cyan-500 focus:outline-none"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-slate-400 font-medium">WebSocket Telemetry URL</label>
            <input
              type="text"
              value={wsUrl}
              onChange={(e) => setWsUrl(e.target.value)}
              className="w-full rounded-lg border border-slate-800 bg-slate-900/80 px-3 py-2 text-slate-100 font-mono text-xs focus:border-cyan-500 focus:outline-none"
            />
          </div>
        </div>
      </Card>
    </div>
  );
}
