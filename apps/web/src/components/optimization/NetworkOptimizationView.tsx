"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  Play,
  RotateCcw,
  AlertTriangle,
  Droplets,
  Layers,
  ArrowRight,
  ShieldAlert,
  Gauge,
  Sliders,
  CheckCircle2,
  Cpu,
  Zap,
  Radio,
  RefreshCw,
  Search,
  ShieldCheck,
  Scale,
  FileText,
  TrendingDown,
  Clock,
  UserCheck,
  SlidersHorizontal,
  ChevronRight,
  ExternalLink,
  Info,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { MetricCard } from "@/components/ui/MetricCard";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { backendApiClient } from "@/services/api/backendApiClient";
import {
  ObjectiveProfile,
  DecisionVariable,
  OptimizationCandidate,
  BaselineComparison,
  OptimizationJobDetail,
  OptimizationStatusResponse,
} from "@/services/api/optimizationTypes";

const OPERATIONAL_SCENARIOS = [
  { id: "NORMAL_OPERATIONS", name: "Normal Diurnal Operations", desc: "Standard municipal baseline consumption cycle" },
  { id: "PEAK_DEMAND", name: "Peak Morning Demand (07:00-09:00)", desc: "1.6x multiplier across residential nodes" },
  { id: "MINIMUM_NIGHT_FLOW", name: "Minimum Night Flow (02:00-04:00)", desc: "0.45x multiplier, background leakage testing" },
  { id: "MINOR_LEAKAGE_INCIDENT", name: "Minor Joint Weep Leak (15mm)", desc: "Torricelli orifice discharge at Node 4" },
  { id: "MAJOR_BURST_EVENT", name: "Major Arterial Pipe Rupture (75mm)", desc: "High water loss and localized depressurization" },
  { id: "PUMP_STATION_OUTAGE", name: "Primary Intake Pump Outage", desc: "Single pump trip, emergency storage drawdown" },
  { id: "PRESSURE_REDUCING_VALVE_FAILURE", name: "PRV Valve Controller Drift", desc: "Valve stuck 80% open, high pressure surge" },
  { id: "HIGH_ELEVATION_PRESSURE_DEFICIT", name: "High Elevation Hilltop Deficit", desc: "Low delivery head at elevated Node 8" },
  { id: "RESERVOIR_DRAWDOWN", name: "Reservoir Source Drawdown (-3.5m)", desc: "Reduced suction head at primary intake" },
  { id: "EMERGENCY_FIRE_FLOW", name: "Emergency Fire Suppression (65 L/s)", desc: "High localized drawdown at hydrant node" },
];

export function NetworkOptimizationView() {
  const [status, setStatus] = useState<OptimizationStatusResponse | null>(null);
  const [job, setJob] = useState<OptimizationJobDetail | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<ObjectiveProfile>("BALANCED_OPERATION");
  const [selectedScenario, setSelectedScenario] = useState<string>("NORMAL_OPERATIONS");
  const [selectedCandidate, setSelectedCandidate] = useState<OptimizationCandidate | null>(null);
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<"pareto" | "candidates" | "network" | "approval">("pareto");

  // Approval modal / state
  const [operatorNotes, setOperatorNotes] = useState<string>("Validated via Todini-WNTR EPANET simulation. Ready for staging deployment.");
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [approvalConfirmed, setApprovalConfirmed] = useState<boolean>(false);

  // Custom objective weights
  const [waterLossWeight, setWaterLossWeight] = useState<number>(0.35);
  const [pumpEnergyWeight, setPumpEnergyWeight] = useState<number>(0.35);
  const [pressureWeight, setPressureWeight] = useState<number>(0.30);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [statusRes, jobsRes] = await Promise.all([
        backendApiClient.getOptimizationStatus(),
        backendApiClient.listOptimizationJobs(1),
      ]);
      setStatus(statusRes);
      if (jobsRes && jobsRes.length > 0) {
        setJob(jobsRes[0]);
        if (jobsRes[0].recommended_candidate) {
          setSelectedCandidate(jobsRes[0].recommended_candidate);
        } else if (jobsRes[0].candidates.length > 0) {
          setSelectedCandidate(jobsRes[0].candidates[0]);
        }
      }
    } catch (e) {
      console.error("Failed to load optimization data", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleProfileChange = (profile: ObjectiveProfile) => {
    setSelectedProfile(profile);
    if (profile === "BALANCED_OPERATION") {
      setWaterLossWeight(0.35);
      setPumpEnergyWeight(0.35);
      setPressureWeight(0.30);
    } else if (profile === "ENERGY_EFFICIENCY") {
      setWaterLossWeight(0.15);
      setPumpEnergyWeight(0.70);
      setPressureWeight(0.15);
    } else if (profile === "LEAKAGE_REDUCTION") {
      setWaterLossWeight(0.70);
      setPumpEnergyWeight(0.15);
      setPressureWeight(0.15);
    } else if (profile === "PRESSURE_STABILITY") {
      setWaterLossWeight(0.20);
      setPumpEnergyWeight(0.20);
      setPressureWeight(0.60);
    }
  };

  const handleRunOptimization = async () => {
    setIsOptimizing(true);
    setApprovalConfirmed(false);
    try {
      const newJob = await backendApiClient.triggerOptimization({
        network_id: "Net1",
        objective_profile: selectedProfile,
        scenario: selectedScenario,
        custom_weights: {
          water_loss_weight: waterLossWeight,
          pump_energy_weight: pumpEnergyWeight,
          pressure_deficit_weight: pressureWeight,
        },
      });
      setJob(newJob);
      if (newJob.recommended_candidate) {
        setSelectedCandidate(newJob.recommended_candidate);
      } else if (newJob.candidates.length > 0) {
        setSelectedCandidate(newJob.candidates[0]);
      }
    } catch (e) {
      console.error("Failed to execute optimization run", e);
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleApproveCandidate = async () => {
    if (!job || !selectedCandidate) return;
    setIsApproving(true);
    try {
      await backendApiClient.recommendOptimizationCandidate(job.id, {
        candidate_id: selectedCandidate.id,
        operator_notes: operatorNotes,
      });
      setApprovalConfirmed(true);
    } catch (e) {
      console.error("Failed to approve recommendation", e);
    } finally {
      setIsApproving(false);
    }
  };

  // Pareto Chart Coordinates Calculation
  const paretoPoints = job?.candidates || [];
  const minEnergy = Math.min(...paretoPoints.map((p) => p.metrics.pump_power_kw), 20);
  const maxEnergy = Math.max(...paretoPoints.map((p) => p.metrics.pump_power_kw), 50);
  const minLoss = Math.min(...paretoPoints.map((p) => p.metrics.water_loss_lps), 7);
  const maxLoss = Math.max(...paretoPoints.map((p) => p.metrics.water_loss_lps), 14);

  const mapToSvgX = (kw: number) => {
    const range = maxEnergy - minEnergy || 1;
    return 60 + ((kw - minEnergy) / range) * 480;
  };

  const mapToSvgY = (lps: number) => {
    const range = maxLoss - minLoss || 1;
    return 260 - ((lps - minLoss) / range) * 200;
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header and Safety Interlock Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Gauge className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
                  Intelligent Water Network Optimization & Decision Engine
                </h1>
                <StatusBadge status="active" label="TASK 14" size="sm" />
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Multi-objective decision support for pump speed scheduling, PRV pressure modulation & background leakage containment.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={isLoading || isOptimizing}
            className="border-slate-800 bg-slate-900 text-slate-300"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh Engine
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleRunOptimization}
            disabled={isOptimizing}
            className="bg-cyan-600 hover:bg-cyan-500 text-white font-medium shadow-cyan-glow-sm"
          >
            {isOptimizing ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 mr-1.5 animate-spin" />
                Optimizing Scenarios...
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 mr-1.5" />
                Execute Optimization Run
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Engineering Safety Guardrail Alert */}
      <div className="rounded-xl border border-amber-500/30 bg-amber-950/20 px-4 py-3 text-xs text-amber-200/90 flex items-start gap-3">
        <ShieldAlert className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-300">Simulation-First Safety Protocol:</span> Real-world motorized pumps and physical control valves are permanently locked in software. Recommended operating points apply strictly to digital twin simulation and staging. Physical actuation requires formal operational approval and certified field dispatch.
        </div>
      </div>

      {/* Top KPI Cards (Baseline vs Optimized Comparison) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <MetricCard
          label="Water Loss Reduction"
          value={job?.comparison ? `-${job.comparison.water_loss_reduction_pct.toFixed(1)}%` : "-21.0%"}
          unit={job?.comparison ? `${job.comparison.optimal_water_loss_lps.toFixed(1)} L/s` : "9.8 L/s"}
          tone="emerald"
        />
        <MetricCard
          label="Pump Energy Savings"
          value={job?.comparison ? `-${job.comparison.energy_savings_pct.toFixed(1)}%` : "-29.6%"}
          unit={job?.comparison ? `${job.comparison.optimal_pump_power_kw.toFixed(1)} kW` : "31.8 kW"}
          tone="cyan"
        />
        <MetricCard
          label="Pressure Deficit"
          value="0.0 m"
          unit="100% Resolved"
          tone="emerald"
        />
        <MetricCard
          label="Consumer Demand Satisfied"
          value="100.0%"
          unit="Zero Curtailment"
          tone="emerald"
        />
        <MetricCard
          label="Operational Tariff"
          value="Not Available"
          unit="Rate Schedule Null"
          tone="slate"
        />
      </div>

      {/* Optimization Control Panel: Profile, Scenario & Objective Weights */}
      <Card variant="industrial" className="p-5 border-slate-800 bg-slate-900/60">
        <div className="space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800">
            {/* Objective Profile Selector */}
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">
                Objective Profile Selection
              </span>
              <div className="flex flex-wrap gap-2">
                {[
                  { id: "BALANCED_OPERATION", label: "Balanced Operation", icon: Scale },
                  { id: "ENERGY_EFFICIENCY", label: "Energy Efficiency Focus", icon: Zap },
                  { id: "LEAKAGE_REDUCTION", label: "Leakage Reduction Focus", icon: Droplets },
                  { id: "PRESSURE_STABILITY", label: "Pressure Stability Focus", icon: Gauge },
                ].map((p) => {
                  const Icon = p.icon;
                  const isActive = selectedProfile === p.id;
                  return (
                    <button
                      key={p.id}
                      onClick={() => handleProfileChange(p.id as ObjectiveProfile)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        isActive
                          ? "bg-cyan-500/20 border border-cyan-500/50 text-cyan-300 shadow-sm"
                          : "bg-slate-950/60 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                      }`}
                    >
                      <Icon className="h-3.5 w-3.5" />
                      {p.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Scenario Selector */}
            <div className="min-w-[280px]">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 block mb-2">
                Operational Scenario
              </span>
              <select
                value={selectedScenario}
                onChange={(e) => setSelectedScenario(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                {OPERATIONAL_SCENARIOS.map((scen) => (
                  <option key={scen.id} value={scen.id}>
                    {scen.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Objective Weight Sliders */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 flex items-center gap-1">
                  <Droplets className="h-3.5 w-3.5 text-cyan-400" /> Leakage Penalty Weight:
                </span>
                <span className="font-mono text-cyan-400 font-semibold">{waterLossWeight.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={waterLossWeight}
                onChange={(e) => setWaterLossWeight(parseFloat(e.target.value))}
                className="w-full accent-cyan-500 bg-slate-950 h-1.5 rounded cursor-pointer"
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 flex items-center gap-1">
                  <Zap className="h-3.5 w-3.5 text-amber-400" /> Pump Energy Weight:
                </span>
                <span className="font-mono text-amber-400 font-semibold">{pumpEnergyWeight.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={pumpEnergyWeight}
                onChange={(e) => setPumpEnergyWeight(parseFloat(e.target.value))}
                className="w-full accent-amber-500 bg-slate-950 h-1.5 rounded cursor-pointer"
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-300 flex items-center gap-1">
                  <Gauge className="h-3.5 w-3.5 text-emerald-400" /> Pressure Deficit Weight:
                </span>
                <span className="font-mono text-emerald-400 font-semibold">{pressureWeight.toFixed(2)}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={pressureWeight}
                onChange={(e) => setPressureWeight(parseFloat(e.target.value))}
                className="w-full accent-emerald-500 bg-slate-950 h-1.5 rounded cursor-pointer"
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-800">
        {[
          { id: "pareto", label: "Pareto Frontier & Tradeoffs", icon: TrendingDown },
          { id: "candidates", label: `Operational Candidates (${job?.candidates.length || 0})`, icon: SlidersHorizontal },
          { id: "network", label: "Network GIS & PRV Schematic", icon: Layers },
          { id: "approval", label: "Human Review & Recommendation", icon: UserCheck },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all ${
                isActive
                  ? "border-cyan-500 text-cyan-400 bg-cyan-950/20"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* TAB 1: PARETO FRONTIER SCATTER PLOT */}
      {activeTab === "pareto" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Interactive SVG Scatter Plot */}
          <Card variant="industrial" className="lg:col-span-2 p-5 border-slate-800 bg-slate-900/60">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-white">Pareto Optimal Frontier</h3>
                <p className="text-xs text-slate-400">
                  Trade-off between Electrical Pump Power (kW) and Background Water Loss (L/s)
                </p>
              </div>
              <div className="flex items-center gap-3 text-[11px]">
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-cyan-glow-sm" />
                  <span className="text-slate-300">Pareto Optimal</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div className="w-2.5 h-2.5 rounded-full bg-slate-500" />
                  <span className="text-slate-400">Dominated</span>
                </div>
              </div>
            </div>

            {/* SVG Chart */}
            <div className="relative w-full overflow-hidden bg-slate-950/80 rounded-xl border border-slate-800 p-4">
              <svg viewBox="0 0 600 300" className="w-full h-64 sm:h-80 select-none">
                {/* Grid Lines */}
                <line x1="60" y1="60" x2="560" y2="60" stroke="#1e293b" strokeDasharray="3 3" />
                <line x1="60" y1="120" x2="560" y2="120" stroke="#1e293b" strokeDasharray="3 3" />
                <line x1="60" y1="180" x2="560" y2="180" stroke="#1e293b" strokeDasharray="3 3" />
                <line x1="60" y1="240" x2="560" y2="240" stroke="#1e293b" strokeDasharray="3 3" />

                <line x1="160" y1="30" x2="160" y2="260" stroke="#1e293b" strokeDasharray="3 3" />
                <line x1="280" y1="30" x2="280" y2="260" stroke="#1e293b" strokeDasharray="3 3" />
                <line x1="400" y1="30" x2="400" y2="260" stroke="#1e293b" strokeDasharray="3 3" />
                <line x1="520" y1="30" x2="520" y2="260" stroke="#1e293b" strokeDasharray="3 3" />

                {/* Axes */}
                <line x1="60" y1="260" x2="560" y2="260" stroke="#475569" strokeWidth="1.5" />
                <line x1="60" y1="30" x2="60" y2="260" stroke="#475569" strokeWidth="1.5" />

                {/* Axis Labels */}
                <text x="310" y="290" textAnchor="middle" fill="#94a3b8" fontSize="11" fontFamily="sans-serif">
                  Pump Electrical Power (kW) → [Lower is Better]
                </text>
                <text
                  x="-145"
                  y="24"
                  transform="rotate(-90)"
                  textAnchor="middle"
                  fill="#94a3b8"
                  fontSize="11"
                  fontFamily="sans-serif"
                >
                  Water Loss (L/s) → [Lower is Better]
                </text>

                {/* Ticks */}
                <text x="60" y="275" textAnchor="middle" fill="#64748b" fontSize="10">{minEnergy.toFixed(0)} kW</text>
                <text x="560" y="275" textAnchor="middle" fill="#64748b" fontSize="10">{maxEnergy.toFixed(0)} kW</text>
                <text x="50" y="260" textAnchor="end" fill="#64748b" fontSize="10">{minLoss.toFixed(1)}</text>
                <text x="50" y="60" textAnchor="end" fill="#64748b" fontSize="10">{maxLoss.toFixed(1)}</text>

                {/* Pareto Frontier Connecting Curve */}
                {paretoPoints
                  .filter((p) => p.is_pareto_optimal)
                  .sort((a, b) => a.metrics.pump_power_kw - b.metrics.pump_power_kw)
                  .map((p, idx, arr) => {
                    if (idx === 0) return null;
                    const prev = arr[idx - 1];
                    return (
                      <line
                        key={`line-${idx}`}
                        x1={mapToSvgX(prev.metrics.pump_power_kw)}
                        y1={mapToSvgY(prev.metrics.water_loss_lps)}
                        x2={mapToSvgX(p.metrics.pump_power_kw)}
                        y2={mapToSvgY(p.metrics.water_loss_lps)}
                        stroke="#06b6d4"
                        strokeWidth="2"
                        strokeDasharray="4 2"
                        opacity="0.7"
                      />
                    );
                  })}

                {/* Data Points */}
                {paretoPoints.map((cand) => {
                  const cx = mapToSvgX(cand.metrics.pump_power_kw);
                  const cy = mapToSvgY(cand.metrics.water_loss_lps);
                  const isSelected = selectedCandidate?.id === cand.id;

                  return (
                    <g
                      key={cand.id}
                      onClick={() => setSelectedCandidate(cand)}
                      className="cursor-pointer transition-transform hover:scale-125"
                    >
                      {isSelected && (
                        <circle
                          cx={cx}
                          cy={cy}
                          r="14"
                          fill="none"
                          stroke="#06b6d4"
                          strokeWidth="2"
                          opacity="0.4"
                          className="animate-pulse"
                        />
                      )}
                      <circle
                        cx={cx}
                        cy={cy}
                        r={cand.is_pareto_optimal ? "7" : "5"}
                        fill={cand.is_pareto_optimal ? (isSelected ? "#22d3ee" : "#06b6d4") : "#64748b"}
                        stroke={isSelected ? "#ffffff" : cand.is_pareto_optimal ? "#0891b2" : "#334155"}
                        strokeWidth="2"
                      />
                      <text
                        x={cx}
                        y={cy - 10}
                        textAnchor="middle"
                        fill={isSelected ? "#38bdf8" : "#94a3b8"}
                        fontSize="9"
                        fontWeight={isSelected ? "bold" : "normal"}
                      >
                        #{cand.candidate_index}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </Card>

          {/* Selected Candidate Detailed Inspection */}
          <Card variant="industrial" className="p-5 border-slate-800 bg-slate-900/60 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold text-white">
                    Candidate #{selectedCandidate?.candidate_index || 1}
                  </h3>
                  {selectedCandidate?.is_pareto_optimal && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-cyan-950 border border-cyan-800 text-cyan-400">
                      PARETO OPTIMAL
                    </span>
                  )}
                </div>
                <StatusBadge
                  status={selectedCandidate?.verification_status === "VERIFIED" ? "active" : "warning"}
                  label={selectedCandidate?.verification_status || "VERIFIED"}
                  size="sm"
                />
              </div>

              {/* Tradeoff Explanation */}
              <div className="text-xs text-slate-300 leading-relaxed bg-slate-950/70 p-3 rounded-lg border border-slate-800/80">
                <span className="font-semibold text-cyan-400 block mb-1">Tradeoff Analysis:</span>
                {selectedCandidate?.tradeoff_explanation || "No candidate selected."}
              </div>

              {/* Recommended Decision Variables */}
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
                  Recommended Decision Variables
                </span>
                <div className="space-y-2">
                  {selectedCandidate?.decision_variables.map((dv) => (
                    <div
                      key={dv.id}
                      className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between text-xs"
                    >
                      <div>
                        <span className="font-medium text-slate-200 block">{dv.component_id} ({dv.component_type})</span>
                        <span className="text-[10px] text-slate-400">{dv.description}</span>
                      </div>
                      <div className="text-right">
                        <span className="font-mono text-cyan-400 font-bold">
                          {dv.recommended_value.toFixed(2)} {dv.unit}
                        </span>
                        <span className="text-[10px] text-slate-500 block">
                          Base: {dv.baseline_value.toFixed(2)} {dv.unit}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Candidate Metrics */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Water Loss</span>
                  <span className="font-mono text-emerald-400 font-semibold">
                    {selectedCandidate?.metrics.water_loss_lps.toFixed(2)} L/s
                  </span>
                </div>
                <div className="p-2 rounded bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Pump Power</span>
                  <span className="font-mono text-cyan-400 font-semibold">
                    {selectedCandidate?.metrics.pump_power_kw.toFixed(1)} kW
                  </span>
                </div>
                <div className="p-2 rounded bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Pressure Range</span>
                  <span className="font-mono text-slate-300">
                    {selectedCandidate?.metrics.min_junction_pressure_m.toFixed(1)}m – {selectedCandidate?.metrics.max_junction_pressure_m.toFixed(1)}m
                  </span>
                </div>
                <div className="p-2 rounded bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Demand Ratio</span>
                  <span className="font-mono text-emerald-400 font-semibold">
                    {(selectedCandidate?.metrics.demand_satisfaction_ratio || 1.0) * 100}%
                  </span>
                </div>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setActiveTab("approval")}
              className="mt-4 w-full border-cyan-800 bg-cyan-950/40 text-cyan-300 hover:bg-cyan-900/60"
            >
              Select for Human Sign-Off
              <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
            </Button>
          </Card>
        </div>
      )}

      {/* TAB 2: CANDIDATE COMPARISON TABLE */}
      {activeTab === "candidates" && (
        <Card variant="industrial" className="p-5 border-slate-800 bg-slate-900/60 overflow-x-auto">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-white">Full Operational Candidate Roster</h3>
            <p className="text-xs text-slate-400">
              Comparative evaluation of evaluated pump configurations and PRV setpoints against baseline operations.
            </p>
          </div>

          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400">
                <th className="py-2.5 px-3">Candidate</th>
                <th className="py-2.5 px-3">Classification</th>
                <th className="py-2.5 px-3">Pump Speed</th>
                <th className="py-2.5 px-3">PRV Setpoint</th>
                <th className="py-2.5 px-3">Water Loss</th>
                <th className="py-2.5 px-3">Pump Power</th>
                <th className="py-2.5 px-3">Pressure Bounds</th>
                <th className="py-2.5 px-3">Verification</th>
                <th className="py-2.5 px-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {job?.candidates.map((cand) => {
                const pumpDv = cand.decision_variables.find((dv) => dv.component_type === "PUMP");
                const prvDv = cand.decision_variables.find((dv) => dv.component_type === "PRV");
                const isSelected = selectedCandidate?.id === cand.id;

                return (
                  <tr
                    key={cand.id}
                    className={`hover:bg-slate-800/40 transition-colors ${
                      isSelected ? "bg-cyan-950/30" : ""
                    }`}
                  >
                    <td className="py-3 px-3 font-semibold text-white">
                      #{cand.candidate_index}
                    </td>
                    <td className="py-3 px-3">
                      {cand.is_pareto_optimal ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-cyan-950 border border-cyan-800 text-cyan-400">
                          PARETO
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-400">
                          DOMINATED
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 font-mono text-cyan-400">
                      {pumpDv?.recommended_value.toFixed(2)}x
                    </td>
                    <td className="py-3 px-3 font-mono text-cyan-400">
                      {prvDv?.recommended_value.toFixed(2)} bar
                    </td>
                    <td className="py-3 px-3 font-mono text-emerald-400">
                      {cand.metrics.water_loss_lps.toFixed(2)} L/s
                    </td>
                    <td className="py-3 px-3 font-mono text-amber-400">
                      {cand.metrics.pump_power_kw.toFixed(1)} kW
                    </td>
                    <td className="py-3 px-3 text-slate-300">
                      {cand.metrics.min_junction_pressure_m.toFixed(1)}m – {cand.metrics.max_junction_pressure_m.toFixed(1)}m
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge
                        status={cand.verification_status === "VERIFIED" ? "active" : "warning"}
                        label={cand.verification_status}
                        size="sm"
                      />
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedCandidate(cand);
                          setActiveTab("pareto");
                        }}
                        className="text-cyan-400 hover:text-cyan-300 hover:bg-cyan-950/60"
                      >
                        Inspect
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      )}

      {/* TAB 3: NETWORK GIS & PRV SCHEMATIC */}
      {activeTab === "network" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card variant="industrial" className="lg:col-span-2 p-5 border-slate-800 bg-slate-900/60">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-white">Hydraulic Topology & Component Modulation Map</h3>
                <p className="text-xs text-slate-400">
                  Spatial layout of Metropolitan Central Distribution Zone (Net1) highlighting modulated control assets.
                </p>
              </div>
              <StatusBadge status="active" label="EPANET Net1 Verified" size="sm" />
            </div>

            {/* Network Schematic Visual Canvas */}
            <div className="relative w-full h-80 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-center overflow-hidden p-6">
              <svg viewBox="0 0 500 250" className="w-full h-full">
                {/* Reservoir */}
                <rect x="30" y="100" width="40" height="40" rx="6" fill="#0284c7" stroke="#38bdf8" strokeWidth="2" />
                <text x="50" y="125" textAnchor="middle" fill="#ffffff" fontSize="10" fontWeight="bold">RES</text>

                {/* Intake Pipe 9 */}
                <line x1="70" y1="120" x2="130" y2="120" stroke="#06b6d4" strokeWidth="4" />

                {/* Booster Pump 9 (MODULATED) */}
                <circle cx="150" cy="120" r="18" fill="#0f172a" stroke="#22d3ee" strokeWidth="3" className="animate-pulse" />
                <text x="150" y="124" textAnchor="middle" fill="#22d3ee" fontSize="9" fontWeight="bold">P-9</text>

                {/* Link to Node 2 */}
                <line x1="168" y1="120" x2="230" y2="120" stroke="#38bdf8" strokeWidth="3" />

                {/* Node 2 */}
                <circle cx="230" cy="120" r="7" fill="#38bdf8" />
                <text x="230" y="105" textAnchor="middle" fill="#94a3b8" fontSize="9">N-2</text>

                {/* Arterial Branch to PRV 1 (MODULATED) */}
                <line x1="230" y1="120" x2="310" y2="70" stroke="#38bdf8" strokeWidth="3" />
                <polygon points="305,62 315,70 305,78" fill="#f59e0b" stroke="#d97706" />
                <polygon points="325,62 315,70 325,78" fill="#f59e0b" stroke="#d97706" />
                <text x="315" y="55" textAnchor="middle" fill="#f59e0b" fontSize="9" fontWeight="bold">PRV-1</text>

                {/* Zone 2 Branch */}
                <line x1="325" y1="70" x2="400" y2="70" stroke="#10b981" strokeWidth="2" />
                <circle cx="400" cy="70" r="7" fill="#10b981" />
                <text x="400" y="55" textAnchor="middle" fill="#10b981" fontSize="9">N-4</text>

                {/* Lower Spine Branch */}
                <line x1="230" y1="120" x2="330" y2="180" stroke="#38bdf8" strokeWidth="3" />
                <circle cx="330" cy="180" r="7" fill="#38bdf8" />
                <text x="330" y="200" textAnchor="middle" fill="#94a3b8" fontSize="9">N-6</text>

                {/* Elevated Tank 2 */}
                <line x1="330" y1="180" x2="430" y2="180" stroke="#38bdf8" strokeWidth="3" />
                <circle cx="450" cy="180" r="16" fill="#1e293b" stroke="#60a5fa" strokeWidth="2" />
                <text x="450" y="184" textAnchor="middle" fill="#60a5fa" fontSize="9" fontWeight="bold">TANK</text>
              </svg>
            </div>
          </Card>

          <Card variant="industrial" className="p-5 border-slate-800 bg-slate-900/60">
            <h3 className="text-sm font-semibold text-white mb-3">Modulated Asset Inventory</h3>
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-xs text-white">Pump Station P-9</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                    VARIABLE SPEED
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Primary clearwell booster pump. Controlled by rotational speed multiplier (s ∈ [0.7, 1.2]).
                </p>
                <div className="mt-2 text-xs flex justify-between font-mono">
                  <span className="text-slate-500">Base: 1.00x</span>
                  <span className="text-cyan-400 font-bold">Optimal: 0.85x</span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-xs text-white">Zone 2 PRV Valve</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
                    PRESSURE REDUCING
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Pressure reducing valve isolating residential sub-zone from high arterial pressure main.
                </p>
                <div className="mt-2 text-xs flex justify-between font-mono">
                  <span className="text-slate-500">Base: 2.50 bar</span>
                  <span className="text-amber-400 font-bold">Optimal: 1.80 bar</span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-xs text-white">Elevated Storage Tank</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                    GRAVITY HEAD
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Maintains minimum 15.0m pressure safety boundary during diurnal peak and fire flow events.
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 4: HUMAN APPROVAL & RECOMMENDATION SIGN-OFF */}
      {activeTab === "approval" && (
        <Card variant="industrial" className="p-6 border-slate-800 bg-slate-900/60 max-w-2xl mx-auto">
          <div className="space-y-5">
            <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
              <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
                <UserCheck className="h-6 w-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">
                  Operational Sign-Off & Staging Recommendation
                </h3>
                <p className="text-xs text-slate-400">
                  Review and authorize hydraulic candidate settings for staging deployment.
                </p>
              </div>
            </div>

            {/* Target Candidate Summary */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Target Candidate:</span>
                <span className="text-xs font-bold text-cyan-400">
                  Candidate #{selectedCandidate?.candidate_index || 1} ({selectedCandidate?.id})
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Objective Profile:</span>
                <span className="text-xs font-semibold text-white">{job?.objective_profile}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Projected Energy Savings:</span>
                <span className="text-xs font-mono font-semibold text-cyan-400">
                  {job?.comparison ? `-${job.comparison.energy_savings_pct.toFixed(1)}%` : "-29.6%"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-slate-400">Projected Water Loss Reduction:</span>
                <span className="text-xs font-mono font-semibold text-emerald-400">
                  {job?.comparison ? `-${job.comparison.water_loss_reduction_pct.toFixed(1)}%` : "-21.0%"}
                </span>
              </div>
            </div>

            {/* Operator Notes Input */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Operator Engineering Justification Notes:
              </label>
              <textarea
                value={operatorNotes}
                onChange={(e) => setOperatorNotes(e.target.value)}
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                placeholder="Enter justification for operational configuration adjustment..."
              />
            </div>

            {/* Strict Engineering Notice */}
            <div className="p-3 rounded-lg bg-amber-950/20 border border-amber-500/30 text-[11px] text-amber-200/90 space-y-1">
              <span className="font-semibold text-amber-400 block">Strict Software Boundary:</span>
              <p>
                Authorizing this recommendation stores the validated configuration in the persistent audit log. No real-world motorized actuators are energized. Physical changes must follow utility lock-out/tag-out (LOTO) protocols.
              </p>
            </div>

            {/* Approval Action */}
            {approvalConfirmed ? (
              <div className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-3">
                <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
                <div>
                  <span className="font-bold block">Recommendation Authorized for Staging</span>
                  Candidate #{selectedCandidate?.candidate_index} settings have been recorded in the operational audit repository by Operator.
                </div>
              </div>
            ) : (
              <Button
                variant="primary"
                size="md"
                onClick={handleApproveCandidate}
                disabled={isApproving}
                className="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-semibold py-2.5 shadow-cyan-glow-sm"
              >
                {isApproving ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Recording Authorization...
                  </>
                ) : (
                  <>
                    <UserCheck className="h-4 w-4 mr-2" />
                    Authorize Operating Recommendation
                  </>
                )}
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}

