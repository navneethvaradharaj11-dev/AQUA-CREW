"use client";

import React, { useState, useEffect } from "react";
import {
  Radar,
  ShieldAlert,
  Bot,
  Activity,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  RotateCcw,
  Compass,
  Sparkles,
  RefreshCw,
  Search,
  Filter,
  FileText,
  Sliders,
  ChevronRight,
  Battery,
  Thermometer,
  Zap,
  Layers,
  ArrowUpRight,
  Eye,
  CheckSquare,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { MetricCard } from "@/components/ui/MetricCard";
import { backendApiClient } from "@/services/api/backendApiClient";
import {
  InspectionRecommendation,
  InspectionPlan,
  InspectionExecutionProgress,
  InspectionReport,
  PriorityCategory,
} from "@/services/api/inspectionIntelligenceTypes";

export function AutonomousInspectionView() {
  const [recommendations, setRecommendations] = useState<InspectionRecommendation[]>([]);
  const [activePlan, setActivePlan] = useState<InspectionPlan | null>(null);
  const [activeExecution, setActiveExecution] = useState<InspectionExecutionProgress | null>(null);
  const [reports, setReports] = useState<InspectionReport[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filterPriority, setFilterPriority] = useState<string>("ALL");
  const [selectedRec, setSelectedRec] = useState<InspectionRecommendation | null>(null);
  const [selectedReport, setSelectedReport] = useState<InspectionReport | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [operatorNotes, setOperatorNotes] = useState("");
  const [detourReason, setDetourReason] = useState("Acoustic surge detected (+14 dB) at station offset +180m.");

  const loadData = async () => {
    setIsLoading(true);
    try {
      const recs = await backendApiClient.getInspectionRecommendations();
      setRecommendations(recs);
      if (recs.length > 0 && !selectedRec) {
        setSelectedRec(recs[0]);
      }
      const plans = await backendApiClient.getInspectionPlans();
      if (plans.length > 0) {
        setActivePlan(plans[0]);
      }
      const reps = await backendApiClient.getInspectionReports();
      setReports(reps);
    } catch (err) {
      console.error("Failed to load inspection intelligence data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGeneratePlan = async () => {
    setIsLoading(true);
    try {
      const plan = await backendApiClient.generateInspectionPlan({
        plan_name: "Metropolitan Autonomous Priority Sweep",
        battery_safety_reserve_pct: 20.0,
      });
      setActivePlan(plan);
    } catch (err) {
      console.error("Plan generation error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprovePlan = async () => {
    if (!activePlan) return;
    setIsLoading(true);
    try {
      const approved = await backendApiClient.approveInspectionPlan(activePlan.id, operatorNotes || "Approved for virtual dispatch.");
      setActivePlan(approved);
    } catch (err) {
      console.error("Plan approval error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRejectPlan = async () => {
    if (!activePlan || !rejectionReason) return;
    setIsLoading(true);
    try {
      const rejected = await backendApiClient.rejectInspectionPlan(activePlan.id, rejectionReason);
      setActivePlan(rejected);
      setShowRejectModal(false);
      setRejectionReason("");
    } catch (err) {
      console.error("Plan rejection error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLaunchMission = async (roverId: string) => {
    if (!activePlan) return;
    setIsLoading(true);
    try {
      const exec = await backendApiClient.launchInspectionMission(activePlan.id, roverId);
      setActiveExecution(exec);
    } catch (err) {
      console.error("Mission launch error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdvanceStep = async () => {
    if (!activeExecution) return;
    try {
      const updated = await backendApiClient.advanceInspectionStep(activeExecution.mission_id, 120.0);
      setActiveExecution(updated);
      if (updated.status === "COMPLETED") {
        const reps = await backendApiClient.getInspectionReports();
        setReports(reps);
      }
    } catch (err) {
      console.error("Step advance error:", err);
    }
  };

  const handleAdaptRoute = async () => {
    if (!activeExecution) return;
    try {
      const adapted = await backendApiClient.adaptInspectionRoute(activeExecution.mission_id, detourReason);
      setActiveExecution(adapted);
    } catch (err) {
      console.error("Route adaptation error:", err);
    }
  };

  const filteredRecs = recommendations.filter((r) => {
    if (filterPriority === "ALL") return true;
    return r.priority_category === filterPriority;
  });

  const criticalCount = recommendations.filter((r) => r.priority_category === "CRITICAL").length;
  const highCount = recommendations.filter((r) => r.priority_category === "HIGH").length;

  return (
    <div className="space-y-6 pb-12 animate-in fade-in duration-300">
      {/* Simulation Warning Banner */}
      <div className="flex items-center justify-between rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-2.5 text-xs text-amber-300 shadow-sm">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400" />
          <span>
            <strong>VIRTUAL SIMULATION PLATFORM (TASK 15):</strong> Autonomous inspection commands operate within digital twin simulation models. No physical rovers or hydraulic actuators are modified. Human operator sign-off required for plan dispatch.
          </span>
        </div>
        <StatusBadge status="warning" label="VIRTUAL SIMULATION" size="sm" pulse />
      </div>

      {/* Header Bar */}
      <SectionHeader
        title="Autonomous Inspection Intelligence & Rover Orchestration"
        description="Unified multi-subsystem inspection priority engine, connected Dijkstra routing, adaptive multi-rover coordination, and evidence-grounded reports."
        badge={<StatusBadge status="active" label="TASK 15 ENGINE" size="sm" />}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
              disabled={isLoading}
              leftIcon={<RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />}
            >
              Refresh Subsystems
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleGeneratePlan}
              disabled={isLoading}
              leftIcon={<Sparkles className="h-3.5 w-3.5" />}
            >
              Generate Multi-Rover Plan
            </Button>
          </div>
        }
      />

      {/* 1. KPI Overview Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3">
        <MetricCard
          label="Urgent Targets"
          value={recommendations.length}
          unit="PIPES"
          tone="cyan"
        />
        <MetricCard
          label="Critical Queue"
          value={criticalCount}
          unit="TARGETS"
          tone="rose"
        />
        <MetricCard
          label="Fleet Readiness"
          value="3"
          unit="ONLINE"
          tone="emerald"
        />
        <MetricCard
          label="Active Campaign"
          value={activePlan ? activePlan.total_rovers_assigned : 0}
          unit="ROVERS"
          tone="cyan"
        />
        <MetricCard
          label="Verified Reports"
          value={reports.length}
          unit="ARCHIVED"
          tone="slate"
        />
      </div>

      {/* Main Grid: Critical Inspection Queue + Rover Allocation & Plan */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (7 Cols): Critical Inspection Queue */}
        <div className="lg:col-span-7 space-y-4">
          <Card variant="industrial" className="p-4 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Radar className="h-4 w-4 text-cyan-400" />
                  Multi-Factor Inspection Urgency Queue
                </h3>
                <p className="text-xs text-slate-400">
                  Synthesizes GIS vulnerability, predictive wear, acoustic AI detections, and hydraulic digital twin stress.
                </p>
              </div>
              <div className="flex items-center gap-1.5">
                {["ALL", "CRITICAL", "HIGH", "MEDIUM"].map((p) => (
                  <button
                    key={p}
                    onClick={() => setFilterPriority(p)}
                    className={`px-2.5 py-1 text-[11px] font-mono rounded border transition-colors ${
                      filterPriority === p
                        ? "bg-cyan-500/20 border-cyan-500/50 text-cyan-300 font-bold"
                        : "bg-slate-900 border-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            {/* Recommendations List */}
            <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
              {filteredRecs.map((rec) => {
                const isSelected = selectedRec?.id === rec.id;
                const catTone =
                  rec.priority_category === "CRITICAL"
                    ? "border-rose-500/50 bg-rose-500/10 text-rose-300"
                    : rec.priority_category === "HIGH"
                    ? "border-amber-500/50 bg-amber-500/10 text-amber-300"
                    : "border-cyan-500/50 bg-cyan-500/10 text-cyan-300";

                return (
                  <div
                    key={rec.id}
                    onClick={() => setSelectedRec(rec)}
                    className={`p-3 rounded-lg border transition-all cursor-pointer ${
                      isSelected
                        ? "border-cyan-500 bg-cyan-950/30 shadow-cyan-glow-sm"
                        : "border-slate-800/80 bg-slate-900/40 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${catTone}`}>
                            {rec.priority_category} ({rec.priority_score.toFixed(1)})
                          </span>
                          <span className="text-xs font-semibold text-white">{rec.segment_name}</span>
                          <span className="text-[10px] font-mono text-slate-500">[{rec.pipeline_segment_id}]</span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">{rec.recommended_action}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 border border-slate-700 text-cyan-400 shrink-0">
                        {rec.recommended_method.replace("_", " ")}
                      </span>
                    </div>

                    {/* Urgency Factor Progress Bars */}
                    <div className="mt-3 grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/60 text-[10px] font-mono">
                      <div>
                        <div className="flex justify-between text-slate-400">
                          <span>Vulnerability</span>
                          <span className="text-slate-200">{rec.urgency_factors.vulnerability?.toFixed(0)}%</span>
                        </div>
                        <div className="h-1 w-full bg-slate-800 rounded mt-0.5 overflow-hidden">
                          <div
                            className="h-full bg-cyan-400 rounded"
                            style={{ width: `${rec.urgency_factors.vulnerability || 0}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-slate-400">
                          <span>Acoustic AI</span>
                          <span className="text-slate-200">{rec.urgency_factors.active_leak_detection?.toFixed(0)}%</span>
                        </div>
                        <div className="h-1 w-full bg-slate-800 rounded mt-0.5 overflow-hidden">
                          <div
                            className="h-full bg-rose-400 rounded"
                            style={{ width: `${rec.urgency_factors.active_leak_detection || 0}%` }}
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-slate-400">
                          <span>Hydraulic Stress</span>
                          <span className="text-slate-200">{rec.urgency_factors.hydraulic_stress?.toFixed(0)}%</span>
                        </div>
                        <div className="h-1 w-full bg-slate-800 rounded mt-0.5 overflow-hidden">
                          <div
                            className="h-full bg-amber-400 rounded"
                            style={{ width: `${rec.urgency_factors.hydraulic_stress || 0}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Selected Target Deep-Dive & Evidence Provenance */}
          {selectedRec && (
            <Card variant="industrial" className="p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="text-xs font-semibold text-white flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-rose-400" />
                  Supporting Evidence & Provenance: {selectedRec.pipeline_segment_id}
                </h4>
                <span className="text-[10px] font-mono text-cyan-400">
                  CLASSIFICATION: {selectedRec.primary_classification}
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                {selectedRec.supporting_evidence.map((ev, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg border border-slate-800 bg-slate-900/60 space-y-1 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-cyan-400">{ev.source_subsystem}</span>
                      <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-slate-800 border border-slate-700 text-slate-300">
                        {ev.classification}
                      </span>
                    </div>
                    <div className="font-semibold text-white text-xs">{ev.metric_name}</div>
                    <p className="text-[11px] text-slate-400">{ev.description}</p>
                    <div className="text-[10px] font-mono text-slate-500">
                      CONFIDENCE: {(ev.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Right Column (5 Cols): Active Multi-Rover Plan & Live Mission Execution */}
        <div className="lg:col-span-5 space-y-4">
          {/* Active Coordinated Plan Card */}
          <Card variant="industrial" className="p-4 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="space-y-0.5">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Bot className="h-4 w-4 text-emerald-400" />
                  Coordinated Multi-Rover Plan
                </h3>
                <span className="text-[11px] font-mono text-slate-400">
                  {activePlan ? activePlan.plan_name : "No active plan formulated"}
                </span>
              </div>
              {activePlan && (
                <StatusBadge
                  status={activePlan.human_approval_status === "APPROVED" ? "active" : "warning"}
                  label={activePlan.human_approval_status}
                  size="sm"
                />
              )}
            </div>

            {activePlan ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2.5 rounded border border-slate-800 bg-slate-900/50">
                    <span className="text-slate-500 block text-[10px]">ROVERS ASSIGNED</span>
                    <span className="text-white text-sm font-bold">{activePlan.total_rovers_assigned} Virtual Fleet</span>
                  </div>
                  <div className="p-2.5 rounded border border-slate-800 bg-slate-900/50">
                    <span className="text-slate-500 block text-[10px]">TARGET CONDUITS</span>
                    <span className="text-cyan-400 text-sm font-bold">{activePlan.total_targets_covered} Segments</span>
                  </div>
                </div>

                {/* Rover Allocation Details */}
                <div className="space-y-2">
                  <span className="text-[11px] font-mono text-slate-400">ROVER ROUTE ALLOCATIONS:</span>
                  {activePlan.allocations.map((alloc) => (
                    <div
                      key={alloc.rover_id}
                      className="p-3 rounded-lg border border-slate-800 bg-slate-900/40 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Bot className="h-4 w-4 text-cyan-400" />
                          <span className="text-xs font-bold text-white">{alloc.rover_name}</span>
                        </div>
                        <span className="text-[10px] font-mono text-emerald-400">
                          Reserve: {alloc.projected_reserve_after_return_pct.toFixed(1)}%
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-relaxed">{alloc.route_selection_reason}</p>
                      <div className="flex items-center justify-between pt-1 border-t border-slate-800/60 text-[10px] font-mono text-slate-400">
                        <span>Distance: {alloc.total_route_distance_m.toFixed(0)}m</span>
                        <span>Est. Duration: {(alloc.estimated_mission_duration_s / 60).toFixed(0)} min</span>
                        {activePlan.human_approval_status === "APPROVED" && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleLaunchMission(alloc.rover_id)}
                            leftIcon={<Play className="h-3 w-3" />}
                          >
                            Launch
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Human Approval Action Controls */}
                {activePlan.human_approval_status === "PENDING_APPROVAL" && (
                  <div className="pt-2 border-t border-slate-800 space-y-2">
                    <input
                      type="text"
                      placeholder="Optional operator authorization notes..."
                      value={operatorNotes}
                      onChange={(e) => setOperatorNotes(e.target.value)}
                      className="w-full px-3 py-1.5 text-xs rounded border border-slate-800 bg-slate-900 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500 font-mono"
                    />
                    <div className="flex items-center gap-2">
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={handleApprovePlan}
                        className="flex-1"
                        leftIcon={<CheckCircle2 className="h-3.5 w-3.5 text-emerald-300" />}
                      >
                        Authorize & Approve Plan
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowRejectModal(true)}
                        className="text-rose-400 hover:text-rose-300 border-rose-900/50"
                        leftIcon={<XCircle className="h-3.5 w-3.5" />}
                      >
                        Reject
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-6 text-center text-xs text-slate-500 font-mono border border-dashed border-slate-800 rounded-lg">
                Click &ldquo;Generate Multi-Rover Plan&rdquo; to formulate coordinated route allocations.
              </div>
            )}
          </Card>

          {/* Live Mission Monitoring & Adaptive Rerouting */}
          {activeExecution && (
            <Card variant="industrial" className="p-4 space-y-3 border-cyan-500/40 bg-cyan-950/10">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-cyan-400 animate-pulse" />
                  <span className="text-xs font-bold text-white">
                    Live Mission Telemetry: {activeExecution.mission_id}
                  </span>
                </div>
                <StatusBadge status="active" label={activeExecution.status} size="sm" pulse />
              </div>

              {/* Progress & Kinematics */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-mono text-slate-400">
                  <span>Inspection Progress</span>
                  <span className="text-cyan-300 font-bold">{activeExecution.progress_percentage.toFixed(1)}%</span>
                </div>
                <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 transition-all duration-300"
                    style={{ width: `${activeExecution.progress_percentage}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-[10px] font-mono">
                <div className="p-2 rounded bg-slate-900/70 border border-slate-800">
                  <span className="text-slate-500 block">TRAVERSED</span>
                  <span className="text-slate-200 font-bold">{activeExecution.distance_traversed_m.toFixed(0)}m</span>
                </div>
                <div className="p-2 rounded bg-slate-900/70 border border-slate-800">
                  <span className="text-slate-500 block">BATTERY</span>
                  <span className="text-emerald-400 font-bold">{activeExecution.battery_percentage.toFixed(1)}%</span>
                </div>
                <div className="p-2 rounded bg-slate-900/70 border border-slate-800">
                  <span className="text-slate-500 block">ANOMALIES</span>
                  <span className="text-rose-400 font-bold">{activeExecution.active_anomalies_detected} Detected</span>
                </div>
              </div>

              {/* Adaptive Controls */}
              <div className="pt-2 border-t border-slate-800 flex items-center gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleAdvanceStep}
                  className="flex-1 text-xs"
                  leftIcon={<Play className="h-3.5 w-3.5" />}
                >
                  Advance Step (+120m)
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleAdaptRoute}
                  className="text-xs text-amber-300 border-amber-900/60"
                  leftIcon={<RotateCcw className="h-3.5 w-3.5" />}
                >
                  Adapt Route
                </Button>
              </div>

              {/* Adaptation History Log */}
              {activeExecution.adaptation_history.length > 0 && (
                <div className="p-2.5 rounded border border-amber-500/30 bg-amber-500/10 text-[11px] font-mono text-amber-200 space-y-1">
                  <div className="font-bold flex items-center gap-1.5">
                    <AlertTriangle className="h-3.5 w-3.5 text-amber-400" />
                    Adaptive Reroute Triggered
                  </div>
                  <p className="text-[10px] text-amber-300/80">
                    {activeExecution.adaptation_history[0].reason}
                  </p>
                </div>
              )}
            </Card>
          )}

          {/* Completed Reports List */}
          <Card variant="industrial" className="p-4 space-y-3">
            <h4 className="text-xs font-semibold text-white flex items-center gap-2 border-b border-slate-800 pb-2">
              <FileText className="h-4 w-4 text-cyan-400" />
              Evidence-Grounded Inspection Reports ({reports.length})
            </h4>
            <div className="space-y-2 max-h-[220px] overflow-y-auto">
              {reports.map((rep) => (
                <div
                  key={rep.id}
                  onClick={() => setSelectedReport(rep)}
                  className="p-2.5 rounded border border-slate-800 bg-slate-900/50 hover:border-slate-700 cursor-pointer flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-semibold text-white">{rep.segment_name}</div>
                    <div className="text-[10px] font-mono text-slate-500">
                      ID: {rep.id} | Outcome: {rep.inspection_outcome}
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                    {rep.operator_review_status}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Rejection Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <Card variant="industrial" className="max-w-md w-full p-6 space-y-4 border-rose-900/80">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <XCircle className="h-5 w-5 text-rose-400" />
              Reject Inspection Plan
            </h3>
            <p className="text-xs text-slate-400">
              Provide an engineering justification for rejecting this autonomous inspection campaign.
            </p>
            <textarea
              rows={3}
              placeholder="e.g. Inclement weather conditions or scheduled main valve closure in District 04."
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              className="w-full p-2.5 rounded border border-slate-800 bg-slate-900 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-rose-500 font-mono"
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" size="sm" onClick={() => setShowRejectModal(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleRejectPlan}
                disabled={!rejectionReason}
                className="bg-rose-600 hover:bg-rose-500 text-white"
              >
                Confirm Rejection
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
