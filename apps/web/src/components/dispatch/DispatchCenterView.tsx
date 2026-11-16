"use client";

import React, { useState, useEffect } from "react";
import {
  MissionRecommendation,
  RoverSuitability,
  MissionProgressInfo,
} from "@/services/api/dispatchTypes";
import { AiDetection } from "@/services/api/aiTypes";
import { backendApiClient } from "@/services/api/backendApiClient";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { MetricCard } from "@/components/ui/MetricCard";
import {
  Navigation,
  Send,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Bot,
  MapPin,
  Activity,
  Clock,
  ShieldAlert,
  Search,
  Filter,
  Sparkles,
  RefreshCw,
  Sliders,
  ChevronRight,
  BatteryMedium,
  Check,
  FileText,
  Radio,
} from "lucide-react";

export function DispatchCenterView() {
  const [recommendations, setRecommendations] = useState<MissionRecommendation[]>([]);
  const [selectedRec, setSelectedRec] = useState<MissionRecommendation | null>(null);
  const [detections, setDetections] = useState<AiDetection[]>([]);
  const [rovers, setRovers] = useState<RoverSuitability[]>([]);
  const [activeProgress, setActiveProgress] = useState<MissionProgressInfo | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Operator Action State
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [isRejecting, setIsRejecting] = useState<boolean>(false);
  const [rejectReason, setRejectReason] = useState<string>("");
  const [operatorNotes, setOperatorNotes] = useState<string>("");
  const [showRejectModal, setShowRejectModal] = useState<boolean>(false);
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);

  // Filters
  const [filterPriority, setFilterPriority] = useState<string>("ALL");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [recs, dets, rvs] = await Promise.all([
        backendApiClient.getRecommendations(),
        backendApiClient.getAiDetections(),
        backendApiClient.getEligibleRovers(),
      ]);
      setRecommendations(recs);
      if (recs.length > 0 && !selectedRec) {
        setSelectedRec(recs[0]);
      }
      setDetections(dets);
      setRovers(rvs);

      // Check progress for the first approved mission if available
      const approved = recs.find((r) => r.status === "APPROVED" && r.assigned_mission_id);
      if (approved?.assigned_mission_id) {
        const prog = await backendApiClient.getMissionProgress(approved.assigned_mission_id);
        setActiveProgress(prog);
      }
    } catch (err) {
      console.error("Failed to load dispatch telemetry:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleApprove = async () => {
    if (!selectedRec) return;
    setIsApproving(true);
    setActionSuccessMessage(null);
    try {
      const res = await backendApiClient.approveRecommendation(
        selectedRec.id,
        "CHIEF_OPERATOR",
        operatorNotes || undefined
      );
      if (res.success) {
        setActionSuccessMessage(res.message);
        setRecommendations((prev) =>
          prev.map((r) =>
            r.id === selectedRec.id
              ? { ...r, status: "APPROVED", assigned_mission_id: res.mission_id }
              : r
          )
        );
        setSelectedRec((prev) => (prev ? { ...prev, status: "APPROVED", assigned_mission_id: res.mission_id } : null));

        if (res.mission_id) {
          const prog = await backendApiClient.getMissionProgress(res.mission_id);
          setActiveProgress(prog);
        }
      }
    } catch (err) {
      console.error("Approval failed:", err);
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async () => {
    if (!selectedRec || !rejectReason.trim()) return;
    setIsRejecting(true);
    setActionSuccessMessage(null);
    try {
      const updated = await backendApiClient.rejectRecommendation(
        selectedRec.id,
        rejectReason,
        operatorNotes || undefined
      );
      if (updated) {
        setRecommendations((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
        setSelectedRec(updated);
        setShowRejectModal(false);
        setRejectReason("");
        setOperatorNotes("");
        setActionSuccessMessage(`Recommendation ${updated.id} rejected.`);
      }
    } catch (err) {
      console.error("Rejection failed:", err);
    } finally {
      setIsRejecting(false);
    }
  };

  const handleRecalculate = async () => {
    if (!selectedRec) return;
    setIsLoading(true);
    try {
      const updated = await backendApiClient.recalculateRecommendation(selectedRec.id);
      if (updated) {
        setSelectedRec(updated);
        setRecommendations((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      }
    } catch (err) {
      console.error("Recalculation failed:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlanForDetection = async (detId: string) => {
    setIsLoading(true);
    try {
      const rec = await backendApiClient.planMission(detId);
      setRecommendations((prev) => [rec, ...prev.filter((r) => r.id !== rec.id)]);
      setSelectedRec(rec);
    } catch (err) {
      console.error("Failed to plan mission for detection:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter recommendations
  const filteredRecs = recommendations.filter((r) => {
    if (filterPriority !== "ALL" && r.priority_category.toUpperCase() !== filterPriority.toUpperCase()) {
      return false;
    }
    if (filterStatus !== "ALL" && r.status.toUpperCase() !== filterStatus.toUpperCase()) {
      return false;
    }
    return true;
  });

  const pendingApprovals = recommendations.filter((r) => r.status === "PENDING_APPROVAL").length;
  const activeMissionsCount = rovers.filter((r) => r.operating_state === "INSPECTING" || r.operating_state === "MOVING").length;
  const availableRoversCount = rovers.filter((r) => r.is_eligible).length;

  return (
    <div className="space-y-6">
      {/* Top Banner: Autonomous Planning & Human Approval Requirement */}
      <div className="rounded-lg border border-cyan-800/80 bg-cyan-950/30 p-4 text-cyan-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-cyan-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-white">
                  AUTONOMOUS MISSION PLANNING & DISPATCH CENTER
                </span>
                <span className="rounded bg-cyan-900/60 px-2 py-0.5 text-[10px] font-mono text-cyan-300 border border-cyan-700">
                  TASK 08 READY
                </span>
              </div>
              <p className="text-xs text-cyan-200/90 leading-relaxed">
                Connects AI leak detection alerts to the virtual rover fleet. Dijkstra topological pathfinding calculates
                continuous underground pipeline routes. All movements and battery consumptions are simulated in software.
                Human operator verification is strictly enforced before autonomous dispatch.
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            leftIcon={<RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />}
            className="shrink-0 border-cyan-700/60 text-cyan-300 hover:bg-cyan-900/40"
          >
            Refresh Telemetry
          </Button>
        </div>
      </div>

      {actionSuccessMessage && (
        <div className="rounded-lg border border-emerald-800 bg-emerald-950/40 p-3 text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Check className="h-4 w-4 text-emerald-400" />
            <span>{actionSuccessMessage}</span>
          </div>
          <button onClick={() => setActionSuccessMessage(null)} className="text-emerald-400 hover:text-white">
            &times;
          </button>
        </div>
      )}

      {/* KPI Cards Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Pending Dispatch Approvals"
          value={pendingApprovals}
          unit="RECOMMENDATIONS"
          tone="amber"
        />
        <MetricCard
          label="Active Rover Missions"
          value={activeMissionsCount}
          unit="EN ROUTE"
          tone="cyan"
        />
        <MetricCard
          label="Eligible Standby Fleet"
          value={availableRoversCount}
          unit={`OF ${rovers.length} ROVERS`}
          tone="emerald"
        />
        <MetricCard
          label="Routing Feasibility"
          value="100%"
          unit="GRAPH CONNECTED"
          tone="slate"
        />
      </div>

      {/* Main Grid: Left Triage Queue & Recommendations (7 Cols), Right Route Preview & Operator Action (5 Cols) */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Left Column (7 Cols) */}
        <div className="xl:col-span-7 space-y-6">
          {/* Section B: Mission Recommendations Queue */}
          <Card variant="industrial">
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Navigation className="h-5 w-5 text-cyan-400" />
                  <div>
                    <CardTitle className="text-base">Mission Recommendations Queue</CardTitle>
                    <CardDescription>
                      Algorithmic rover selection, battery reserve validation & pipeline routes
                    </CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                  <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
                  <span>DISPATCH BROKER READY</span>
                </div>
              </div>

              {/* Filters */}
              <div className="grid grid-cols-2 gap-2 pt-2">
                <div>
                  <label className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Priority</label>
                  <select
                    value={filterPriority}
                    onChange={(e) => setFilterPriority(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  >
                    <option value="ALL">All Priorities</option>
                    <option value="CRITICAL">Critical (90–100)</option>
                    <option value="HIGH">High (70–89)</option>
                    <option value="MEDIUM">Medium (40–69)</option>
                    <option value="LOW">Low (0–39)</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Status</label>
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  >
                    <option value="ALL">All States</option>
                    <option value="PENDING_APPROVAL">Pending Approval</option>
                    <option value="APPROVED">Approved / Dispatched</option>
                    <option value="REJECTED">Rejected</option>
                  </select>
                </div>
              </div>
            </CardHeader>

            <CardContent>
              {filteredRecs.length === 0 ? (
                <div className="py-12 text-center text-slate-400 text-xs">
                  No mission recommendations match the current filter criteria.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {filteredRecs.map((rec) => {
                    const isSelected = selectedRec?.id === rec.id;
                    const isCritical = rec.priority_category === "CRITICAL";
                    const isHigh = rec.priority_category === "HIGH";
                    const isApproved = rec.status === "APPROVED";
                    const isRejected = rec.status === "REJECTED";

                    return (
                      <div
                        key={rec.id}
                        onClick={() => setSelectedRec(rec)}
                        className={`group relative flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-lg border transition-all cursor-pointer ${
                          isSelected
                            ? "bg-cyan-950/40 border-cyan-500 shadow-cyan-glow-sm"
                            : "bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900"
                        }`}
                      >
                        <div className="space-y-1 sm:max-w-md">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-xs font-bold text-white">{rec.id}</span>
                            <span className="text-[11px] font-mono text-cyan-400">{rec.pipeline_segment_id}</span>
                            <span
                              className={`rounded px-1.5 py-0.5 text-[9px] font-mono font-bold uppercase border ${
                                isCritical
                                  ? "bg-rose-950/80 text-rose-300 border-rose-800"
                                  : isHigh
                                  ? "bg-amber-950/80 text-amber-300 border-amber-800"
                                  : "bg-slate-800 text-slate-300 border-slate-700"
                              }`}
                            >
                              {rec.priority_category} ({rec.priority_score.toFixed(0)})
                            </span>
                            <span
                              className={`rounded px-1.5 py-0.5 text-[9px] font-mono uppercase ${
                                isApproved
                                  ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                                  : isRejected
                                  ? "bg-rose-950 text-rose-300 border border-rose-800"
                                  : "bg-amber-950/80 text-amber-300 border border-amber-800"
                              }`}
                            >
                              {rec.status.replace(/_/g, " ")}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-xs text-slate-300">
                            <Bot className="h-3.5 w-3.5 text-cyan-400" />
                            <span>Recommended: <strong className="text-white">{rec.recommended_rover_name}</strong></span>
                            <span className="text-slate-500">({rec.recommended_rover_id})</span>
                          </div>
                          <p className="text-xs text-slate-400 line-clamp-1">
                            {rec.explanation}
                          </p>
                        </div>

                        <div className="flex items-center gap-4 mt-2 sm:mt-0 text-right shrink-0">
                          <div>
                            <div className="text-[10px] font-mono text-slate-400">Route Dist</div>
                            <div className="text-xs font-mono font-bold text-cyan-400">
                              {rec.route_distance_m.toFixed(0)} <span className="text-[9px]">m</span>
                            </div>
                          </div>
                          <div>
                            <div className="text-[10px] font-mono text-slate-400">Batt Reserve</div>
                            <div className="text-xs font-mono font-bold text-emerald-400">
                              {rec.battery_reserve_after_pct.toFixed(0)}%
                            </div>
                          </div>
                          <ChevronRight className="h-4 w-4 text-slate-500 group-hover:text-cyan-400 transition-colors" />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Section A: Priority Queue of AI Leak Detections */}
          <Card variant="industrial">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-amber-400" />
                  <div>
                    <CardTitle className="text-sm">AI Detection Source Queue</CardTitle>
                    <CardDescription>Verified Task 07 leak alerts available for mission planning</CardDescription>
                  </div>
                </div>
                <span className="text-[10px] font-mono text-slate-400">{detections.length} Detections Logged</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {detections.slice(0, 4).map((d) => (
                  <div
                    key={d.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-2.5 rounded bg-slate-900/60 border border-slate-800 text-xs gap-2"
                  >
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-white">{d.id}</span>
                        <span className="text-cyan-400 font-mono">{d.pipeline_segment_id}</span>
                        <span className="rounded bg-rose-950 text-rose-300 px-1.5 py-0.2 text-[9px] font-mono border border-rose-800">
                          {d.risk_level}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        Loss: {d.estimated_loss_lph.toFixed(0)} L/h | Uncertainty: ±{d.localization_uncertainty_m || 20}m
                      </div>
                    </div>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePlanForDetection(d.id)}
                      leftIcon={<Sparkles className="h-3 w-3 text-cyan-400" />}
                      className="text-[11px] shrink-0 border-cyan-800 text-cyan-300 hover:bg-cyan-950"
                    >
                      Plan Route & Rover
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Section C: Rover Availability Status */}
          <Card variant="industrial">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-emerald-400" />
                <div>
                  <CardTitle className="text-sm">Virtual Rover Fleet Availability & Battery Gauges</CardTitle>
                  <CardDescription>Autonomous crawler readiness and operational interlocks</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {rovers.map((rov) => {
                  const isEligible = rov.is_eligible;
                  return (
                    <div
                      key={rov.rover_id}
                      className={`p-3 rounded-lg border text-xs space-y-1.5 ${
                        isEligible
                          ? "bg-slate-900/80 border-slate-800"
                          : "bg-slate-950/80 border-slate-900 opacity-80"
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-white">{rov.rover_name}</span>
                        <span
                          className={`rounded px-1.5 py-0.5 text-[9px] font-mono font-bold uppercase ${
                            isEligible
                              ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                              : "bg-slate-800 text-slate-400"
                          }`}
                        >
                          {rov.operating_state}
                        </span>
                      </div>
                      <div className="flex justify-between text-[11px] font-mono text-slate-400">
                        <span>Battery: <strong className="text-emerald-400">{rov.battery_percentage}%</strong></span>
                        <span>Projected Reserve: {rov.battery_reserve_after_pct}%</span>
                      </div>
                      <p className="text-[11px] text-slate-400 italic line-clamp-1">
                        {rov.suitability_explanation}
                      </p>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Section D (Route Preview) & Section E (Approval Panel) & Section F (Active Mission) */}
        <div className="xl:col-span-5 space-y-6">
          {selectedRec ? (
            <>
              {/* Section D: Route Preview & GIS Polyline Card */}
              <Card variant="industrial" className="border-cyan-500/40">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MapPin className="h-5 w-5 text-cyan-400" />
                      <div>
                        <CardTitle className="text-sm font-mono">{selectedRec.id} — Route Preview</CardTitle>
                        <CardDescription>Dijkstra shortest path along connected pipelines</CardDescription>
                      </div>
                    </div>
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-cyan-400 border border-slate-700">
                      [SIMULATED PATH]
                    </span>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  {/* Route Summary Pills */}
                  <div className="grid grid-cols-3 gap-2 text-center text-xs">
                    <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                      <div className="text-[10px] font-mono text-slate-400">Distance</div>
                      <div className="text-xs font-bold font-mono text-cyan-400">
                        {selectedRec.route_distance_m.toFixed(0)} m
                      </div>
                    </div>
                    <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                      <div className="text-[10px] font-mono text-slate-400">Est. Time</div>
                      <div className="text-xs font-bold font-mono text-white">
                        {(selectedRec.estimated_duration_s / 60).toFixed(1)} min
                      </div>
                    </div>
                    <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                      <div className="text-[10px] font-mono text-slate-400">Uncertainty</div>
                      <div className="text-xs font-bold font-mono text-amber-400">
                        ±{selectedRec.localization_uncertainty_m?.toFixed(0) || 15} m
                      </div>
                    </div>
                  </div>

                  {/* SVG Route Visualization Preview */}
                  <div className="rounded-lg border border-slate-800 bg-slate-950 p-3 space-y-1">
                    <div className="flex justify-between text-[11px] font-mono text-slate-400">
                      <span>Pipeline Topological Route</span>
                      <span>{selectedRec.waypoints.length} Waypoints</span>
                    </div>

                    <div className="h-36 w-full flex items-center justify-center relative overflow-hidden bg-slate-950/80 rounded border border-slate-800/80">
                      <svg viewBox="0 0 400 120" className="w-full h-full p-2">
                        {/* Pipeline grid lines */}
                        <line x1="20" y1="60" x2="380" y2="60" stroke="#1e293b" strokeWidth="2" strokeDasharray="4 4" />
                        <line x1="200" y1="10" x2="200" y2="110" stroke="#1e293b" strokeWidth="2" strokeDasharray="4 4" />

                        {/* Trajectory Polyline */}
                        <polyline
                          fill="none"
                          stroke="#06b6d4"
                          strokeWidth="3"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          points="30,85 120,40 220,70 340,35"
                        />

                        {/* Start Node (Rover) */}
                        <circle cx="30" cy="85" r="5" fill="#10b981" />
                        <text x="25" y="105" fill="#94a3b8" fontSize="8" fontFamily="monospace">ROVER</text>

                        {/* Waypoints */}
                        <circle cx="120" cy="40" r="3" fill="#06b6d4" />
                        <circle cx="220" cy="70" r="3" fill="#06b6d4" />

                        {/* Destination Target & Uncertainty Ring */}
                        <circle cx="340" cy="35" r="16" fill="rgba(244, 63, 94, 0.15)" stroke="#f43f5e" strokeWidth="1" strokeDasharray="2 2" />
                        <circle cx="340" cy="35" r="5" fill="#f43f5e" />
                        <text x="325" y="65" fill="#f43f5e" fontSize="8" fontFamily="monospace">TARGET</text>
                      </svg>
                    </div>

                    <div className="text-[10px] font-mono text-slate-400 flex justify-between pt-1">
                      <span>Segments: {selectedRec.segments_traversed.join(" → ")}</span>
                    </div>
                  </div>

                  {/* Section E: Operator Approval & Governance Panel */}
                  <div className="rounded border border-slate-800 bg-slate-900/60 p-3 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white flex items-center gap-1.5">
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                        <span>Operator Dispatch Authorization</span>
                      </span>
                      <span className="text-[10px] font-mono text-amber-300">
                        {selectedRec.status.replace(/_/g, " ")}
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed">
                      {selectedRec.explanation}
                    </p>

                    <div className="space-y-1">
                      <label className="text-[10px] font-mono uppercase text-slate-400 block">Operator Notes</label>
                      <input
                        type="text"
                        placeholder="Add mission inspection directives or acoustic survey notes..."
                        value={operatorNotes}
                        onChange={(e) => setOperatorNotes(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                      />
                    </div>

                    {selectedRec.status === "PENDING_APPROVAL" ? (
                      <div className="grid grid-cols-2 gap-2 pt-1">
                        <Button
                          variant="primary"
                          size="sm"
                          disabled={isApproving}
                          onClick={handleApprove}
                          leftIcon={<Send className={`h-3.5 w-3.5 ${isApproving ? "animate-spin" : ""}`} />}
                          className="bg-emerald-600 hover:bg-emerald-500 text-xs w-full"
                        >
                          {isApproving ? "Dispatching..." : "Approve & Dispatch"}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setShowRejectModal(true)}
                          className="border-rose-800 text-rose-300 hover:bg-rose-950 text-xs w-full"
                        >
                          Reject Mission
                        </Button>
                      </div>
                    ) : selectedRec.status === "APPROVED" ? (
                      <div className="rounded bg-emerald-950/60 border border-emerald-800 p-2 text-xs text-emerald-300 flex items-center justify-between">
                        <span>Rover Dispatched. Mission ID: <strong>{selectedRec.assigned_mission_id}</strong></span>
                        <Check className="h-4 w-4 text-emerald-400" />
                      </div>
                    ) : (
                      <div className="rounded bg-rose-950/60 border border-rose-800 p-2 text-xs text-rose-300">
                        Rejected: {selectedRec.rejection_reason}
                      </div>
                    )}

                    <div className="flex justify-end pt-1">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleRecalculate}
                        leftIcon={<RotateCcw className="h-3 w-3" />}
                        className="text-[10px] border-slate-700 text-slate-400"
                      >
                        Recalculate Route & Battery
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Section F: Active Mission Monitoring */}
              {activeProgress && (
                <Card variant="industrial">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Radio className="h-5 w-5 text-cyan-400" />
                        <div>
                          <CardTitle className="text-sm">Active Mission Execution Progress</CardTitle>
                          <CardDescription>{activeProgress.mission_id} in {activeProgress.status}</CardDescription>
                        </div>
                      </div>
                      <span className="text-xs font-mono font-bold text-cyan-400">
                        {activeProgress.progress_percentage}%
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 transition-all duration-500"
                        style={{ width: `${activeProgress.progress_percentage}%` }}
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-[11px] font-mono text-slate-400">
                      <div>Inspected: <strong className="text-white">{activeProgress.inspected_distance_m}m</strong></div>
                      <div>Waypoints: <strong className="text-white">{activeProgress.completed_waypoints}/{activeProgress.total_waypoints}</strong></div>
                      <div>Remaining: <strong className="text-white">{activeProgress.estimated_completion_time}</strong></div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card variant="industrial">
              <div className="p-12 text-center text-slate-400 text-xs">
                Select a recommendation from the queue to review route waypoints and authorize rover dispatch.
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-md w-full space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-400" />
                Reject Mission Recommendation
              </h3>
              <button
                onClick={() => setShowRejectModal(false)}
                className="text-slate-400 hover:text-white"
              >
                &times;
              </button>
            </div>

            <p className="text-xs text-slate-300">
              Provide a mandatory documented reason for municipal audit records explaining why this dispatch was rejected.
            </p>

            <textarea
              rows={3}
              placeholder="e.g. Scheduled pipeline valve maintenance conflict, secondary leak under review..."
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded p-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
            />

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowRejectModal(false)}
                className="text-xs border-slate-700"
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                disabled={isRejecting || !rejectReason.trim()}
                onClick={handleReject}
                className="bg-rose-600 hover:bg-rose-500 text-xs"
              >
                {isRejecting ? "Rejecting..." : "Confirm Rejection"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

