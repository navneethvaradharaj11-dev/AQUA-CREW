"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import {
  OperationalOverview,
  OperationalRecommendation,
  OperationalEvidence,
  OperationalImpact,
  IncidentCorrelation,
  ResourcePlanning,
  OperationalDecisionRecord,
  OperationalExecutionRecord,
} from "@/services/api/operationalIntelligenceTypes";
import { MapLayerVisibilityState, SelectedMapFeature } from "@/services/gis/types";
import { backendApiClient } from "@/services/api/backendApiClient";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Modal } from "@/components/ui/Modal";
import {
  ShieldAlert,
  ShieldCheck,
  Activity,
  AlertTriangle,
  Compass,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Clock,
  Droplets,
  Layers,
  MapPin,
  Bot,
  Sliders,
  ChevronRight,
  Info,
  Sparkles,
  ArrowRight,
  Lock,
  Flame,
  FileCheck,
  History,
  Cpu,
  BarChart3,
  ExternalLink,
} from "lucide-react";

// Dynamically import MapContainer to avoid SSR issues with MapLibre GL WebGL context
const MapContainer = dynamic(
  () => import("@/components/gis/MapContainer").then((mod) => mod.MapContainer),
  {
    ssr: false,
    loading: () => (
      <div className="h-96 w-full flex flex-col items-center justify-center bg-slate-950/80 border border-slate-800 rounded-xl text-slate-400 font-mono text-xs gap-2">
        <RefreshCw className="h-5 w-5 animate-spin text-cyan-400" />
        <span>Initializing MapLibre WebGL Operational Overlay...</span>
      </div>
    ),
  }
);

export function OperationalIntelligenceView() {
  const [activeTab, setActiveTab] = useState<
    "PRIORITY_QUEUE" | "CORRELATIONS" | "HYDRAULIC_IMPACT" | "RESOURCE_PLANNING" | "DECISIONS_HISTORY" | "GIS_MAP"
  >("PRIORITY_QUEUE");

  // State
  const [overview, setOverview] = useState<OperationalOverview | null>(null);
  const [recommendations, setRecommendations] = useState<OperationalRecommendation[]>([]);
  const [correlations, setCorrelations] = useState<IncidentCorrelation[]>([]);
  const [resourcePlans, setResourcePlans] = useState<ResourcePlanning[]>([]);
  const [decisions, setDecisions] = useState<OperationalDecisionRecord[]>([]);
  const [executions, setExecutions] = useState<OperationalExecutionRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAssessing, setIsAssessing] = useState(false);

  // Filter & Search
  const [categoryFilter, setCategoryFilter] = useState<string>("ALL");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Modal inspection & decision state
  const [selectedRec, setSelectedRec] = useState<OperationalRecommendation | null>(null);
  const [decisionModalOpen, setDecisionModalOpen] = useState(false);
  const [decisionType, setDecisionType] = useState<"APPROVED" | "REJECTED">("APPROVED");
  const [decisionReason, setDecisionReason] = useState("");
  const [isSubmittingDecision, setIsSubmittingDecision] = useState(false);
  const [decisionFeedback, setDecisionFeedback] = useState<string | null>(null);

  // What-If Hydraulic Simulation State
  const [whatIfSegmentId, setWhatIfSegmentId] = useState<string>("PIPE-SEC-4B-92");
  const [whatIfOrificeMm, setWhatIfOrificeMm] = useState<number>(15);
  const [whatIfResult, setWhatIfResult] = useState<any | null>(null);
  const [isSimulatingWhatIf, setIsSimulatingWhatIf] = useState(false);

  // Map Layer Toggles
  const [mapLayers, setMapLayers] = useState<MapLayerVisibilityState>({
    pipelines: { primary: true, secondary: true, distribution: true, service: false },
    leakIncidents: { critical: true, high: true, medium: true, low: false },
    rovers: true,
    sensorStations: { acoustic: true, pressure: true, flow: true, thermal: false, moisture: true },
    inspectionZones: true,
  });

  const loadAllData = async () => {
    setIsLoading(true);
    try {
      const [ov, recs, corrs, resP, decs, execs] = await Promise.all([
        backendApiClient.getOperationalOverview(),
        backendApiClient.getOperationalRecommendations(),
        backendApiClient.getIncidentCorrelations(),
        backendApiClient.getResourcePlanning(),
        backendApiClient.getOperatorDecisions(),
        backendApiClient.getExecutionHistory(),
      ]);

      setOverview(ov);
      setRecommendations(recs);
      setCorrelations(corrs);
      setResourcePlans(resP);
      setDecisions(decs);
      setExecutions(execs);
    } catch (err) {
      console.error("Error loading operational intelligence data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleRunAssessment = async () => {
    setIsAssessing(true);
    try {
      await backendApiClient.runOperationalAssessment();
      await loadAllData();
    } catch (err) {
      console.error("Error triggering operational assessment:", err);
    } finally {
      setIsAssessing(false);
    }
  };

  const handleOpenDecisionModal = (rec: OperationalRecommendation, type: "APPROVED" | "REJECTED") => {
    setSelectedRec(rec);
    setDecisionType(type);
    setDecisionReason(type === "APPROVED" ? "Risk verified by operator. Dispatched under standard operating procedure." : "Deferred due to planned pipeline scheduled maintenance window.");
    setDecisionFeedback(null);
    setDecisionModalOpen(true);
  };

  const handleConfirmDecision = async () => {
    if (!selectedRec) return;
    if (!decisionReason || decisionReason.trim().length < 3) {
      setDecisionFeedback("Decision reason must be at least 3 characters long.");
      return;
    }

    setIsSubmittingDecision(true);
    try {
      if (decisionType === "APPROVED") {
        await backendApiClient.approveOperationalRecommendation(selectedRec.id, decisionReason);
      } else {
        await backendApiClient.rejectOperationalRecommendation(selectedRec.id, decisionReason);
      }
      setDecisionModalOpen(false);
      await loadAllData();
    } catch (err: any) {
      setDecisionFeedback(err.message || "Failed to submit decision.");
    } finally {
      setIsSubmittingDecision(false);
    }
  };

  const handleRunWhatIf = async () => {
    setIsSimulatingWhatIf(true);
    try {
      const res = await backendApiClient.runWhatIfImpactAnalysis(whatIfSegmentId, whatIfOrificeMm);
      setWhatIfResult(res);
    } catch (err) {
      console.error("Error running what-if impact analysis:", err);
    } finally {
      setIsSimulatingWhatIf(false);
    }
  };

  // Filter recommendations
  const filteredRecs = recommendations.filter((r) => {
    if (categoryFilter !== "ALL" && r.category !== categoryFilter) return false;
    if (statusFilter !== "ALL" && r.status !== statusFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        r.segment_name.toLowerCase().includes(q) ||
        r.category.toLowerCase().includes(q) ||
        r.recommended_action.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* 1. AUTHORITATIVE OPERATOR GOVERNANCE & SAFETY RIBBON */}
      <div className="rounded-xl border border-cyan-800/60 bg-gradient-to-r from-slate-950 via-cyan-950/40 to-slate-950 p-4 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-cyan-500/20 border border-cyan-500/40 text-cyan-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-base font-bold text-white tracking-wide">
                  Unified Operational Intelligence & Decision Support Platform
                </h1>
                <span className="rounded bg-emerald-950/80 px-2 py-0.5 text-[10px] font-mono text-emerald-400 border border-emerald-800/60 font-semibold">
                  AUDITED & CERTIFIED
                </span>
                <span className="rounded bg-amber-950/80 px-2 py-0.5 text-[10px] font-mono text-amber-300 border border-amber-800/60 font-semibold">
                  SIMULATION MODE
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Multi-system decision engine synthesizing AI leak detections, hydraulic digital twin, asset health indices, and autonomous rover resources.
              </p>
              <div className="flex flex-wrap items-center gap-3 mt-2 text-[11px] font-mono text-slate-400">
                <span>Methodology: <strong className="text-cyan-300">{overview?.methodology_version || "v1.0.0-unified-operational-decision"}</strong></span>
                <span>•</span>
                <span>Provenance: <strong className="text-slate-300">VIRTUAL_SIMULATION_ENGINE (is_simulated: true)</strong></span>
                <span>•</span>
                <span className="flex items-center gap-1 text-amber-400 font-semibold">
                  <Lock className="h-3 w-3" /> Real-World Physical Actuators Permanently Disabled
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={loadAllData}
              disabled={isLoading}
              leftIcon={<RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />}
            >
              Refresh Telemetry
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleRunAssessment}
              disabled={isAssessing}
              leftIcon={<Sparkles className={`h-3.5 w-3.5 ${isAssessing ? "animate-spin" : ""}`} />}
            >
              {isAssessing ? "Assessing..." : "Run Full Assessment"}
            </Button>
          </div>
        </div>
      </div>

      {/* 2. OPERATIONAL OVERVIEW METRIC CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard
          label="Active Incidents"
          value={overview?.active_incidents_count ?? 0}
          unit="LEAKS"
          tone={overview?.active_incidents_count && overview.active_incidents_count > 0 ? "rose" : "slate"}
        />
        <MetricCard
          label="Critical Conduits"
          value={overview?.critical_segments_count ?? 0}
          unit="TRUNKS"
          tone={overview?.critical_segments_count && overview.critical_segments_count > 0 ? "amber" : "slate"}
        />
        <MetricCard
          label="Pending Review"
          value={overview?.pending_recommendations_count ?? 0}
          unit="ACTIONS"
          tone="cyan"
        />
        <MetricCard
          label="Approved Missions"
          value={overview?.approved_actions_count ?? 0}
          unit="LAUNCHED"
          tone="emerald"
        />
        <MetricCard
          label="Available Rovers"
          value={overview?.available_rovers_count ?? 0}
          unit="FLEET"
          tone={overview?.available_rovers_count && overview.available_rovers_count > 0 ? "emerald" : "amber"}
        />
        <MetricCard
          label="Network Health"
          value={overview?.network_health_score ?? 80.0}
          unit="/ 100"
          tone="cyan"
        />
      </div>

      {/* 3. NAVIGATION TABS */}
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-2 gap-2">
        <div className="flex flex-wrap items-center gap-1.5">
          <Button
            variant={activeTab === "PRIORITY_QUEUE" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("PRIORITY_QUEUE")}
            leftIcon={<Sliders className="h-3.5 w-3.5" />}
          >
            Priority Queue ({recommendations.length})
          </Button>
          <Button
            variant={activeTab === "CORRELATIONS" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("CORRELATIONS")}
            leftIcon={<Activity className="h-3.5 w-3.5" />}
          >
            Incident Correlations ({correlations.length})
          </Button>
          <Button
            variant={activeTab === "HYDRAULIC_IMPACT" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("HYDRAULIC_IMPACT")}
            leftIcon={<Droplets className="h-3.5 w-3.5" />}
          >
            Hydraulic What-If
          </Button>
          <Button
            variant={activeTab === "RESOURCE_PLANNING" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("RESOURCE_PLANNING")}
            leftIcon={<Bot className="h-3.5 w-3.5" />}
          >
            Rover Readiness ({resourcePlans.length})
          </Button>
          <Button
            variant={activeTab === "DECISIONS_HISTORY" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("DECISIONS_HISTORY")}
            leftIcon={<History className="h-3.5 w-3.5" />}
          >
            Audit History ({decisions.length})
          </Button>
          <Button
            variant={activeTab === "GIS_MAP" ? "primary" : "ghost"}
            size="sm"
            onClick={() => setActiveTab("GIS_MAP")}
            leftIcon={<Layers className="h-3.5 w-3.5" />}
          >
            GIS Operational Overlay
          </Button>
        </div>

        <div className="text-xs font-mono text-slate-400">
          Network Urgency: <strong className={overview?.network_urgency === "CRITICAL" ? "text-rose-400" : "text-amber-400"}>{overview?.network_urgency || "ROUTINE"}</strong>
        </div>
      </div>

      {/* TAB 1: UNIFIED PRIORITY QUEUE */}
      {activeTab === "PRIORITY_QUEUE" && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-lg border border-slate-800">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Search className="h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search by conduit, category, action..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded px-2.5 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-full sm:w-64"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Filter className="h-3.5 w-3.5" />
                <span>Category:</span>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white focus:outline-none"
                >
                  <option value="ALL">All Categories</option>
                  <option value="IMMEDIATE_INSPECTION">Immediate Inspection</option>
                  <option value="URGENT_LEAK_INVESTIGATION">Urgent Leak Investigation</option>
                  <option value="PREVENTIVE_MAINTENANCE">Preventive Maintenance</option>
                  <option value="HYDRAULIC_INVESTIGATION">Hydraulic Investigation</option>
                  <option value="PIPELINE_HEALTH_REVIEW">Pipeline Health Review</option>
                  <option value="CONTINUOUS_MONITORING">Continuous Monitoring</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <span>Status:</span>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-xs text-white focus:outline-none"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="PENDING_REVIEW">Pending Review</option>
                  <option value="GENERATED">Generated</option>
                  <option value="APPROVED">Approved</option>
                  <option value="REJECTED">Rejected</option>
                  <option value="EXECUTION_PENDING">Execution Pending</option>
                  <option value="IN_PROGRESS">In Progress</option>
                </select>
              </div>
            </div>
          </div>

          {/* Recommendations List */}
          <div className="space-y-3">
            {filteredRecs.length === 0 ? (
              <div className="p-8 text-center bg-slate-900/40 rounded-xl border border-slate-800 text-slate-400 text-xs">
                No operational recommendations matching the selected criteria.
              </div>
            ) : (
              filteredRecs.map((rec, index) => {
                const isSelected = selectedRec?.id === rec.id;
                return (
                  <Card
                    key={rec.id}
                    className={`transition-all ${
                      isSelected ? "border-cyan-500/80 bg-slate-900/80 shadow-cyan-glow-sm" : "border-slate-800/80 bg-slate-950/60"
                    }`}
                  >
                    <CardContent className="p-4 space-y-3">
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                        <div className="flex items-center gap-3">
                          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-slate-900 border border-slate-700 font-mono text-xs font-bold text-cyan-400">
                            #{index + 1}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-sm text-white">{rec.segment_name}</span>
                              <span className="text-xs font-mono text-slate-400">({rec.pipeline_segment_id})</span>
                              <span
                                className={`rounded px-1.5 py-0.5 text-[10px] font-mono font-bold ${
                                  rec.risk_severity === "CRITICAL"
                                    ? "bg-rose-950 text-rose-300 border border-rose-800"
                                    : rec.risk_severity === "HIGH"
                                    ? "bg-amber-950 text-amber-300 border border-amber-800"
                                    : "bg-cyan-950 text-cyan-300 border border-cyan-800"
                                }`}
                              >
                                {rec.risk_severity}
                              </span>
                            </div>
                            <div className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                              <span className="font-mono text-cyan-300 font-semibold">{rec.category}</span>
                              <span>•</span>
                              <span>Tier: <strong className="text-slate-300">{rec.priority_tier}</strong></span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <div className="text-[10px] font-mono text-slate-400 uppercase">Composite Priority</div>
                            <div className="text-lg font-bold font-mono text-cyan-400">
                              {rec.priority_score.toFixed(1)} <span className="text-xs text-slate-500 font-normal">/ 100</span>
                            </div>
                          </div>

                          <div className="flex items-center gap-1.5 pl-2 border-l border-slate-800">
                            {rec.status === "PENDING_REVIEW" || rec.status === "GENERATED" ? (
                              <>
                                <Button
                                  variant="primary"
                                  size="sm"
                                  onClick={() => handleOpenDecisionModal(rec, "APPROVED")}
                                  leftIcon={<CheckCircle2 className="h-3.5 w-3.5" />}
                                >
                                  Approve
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleOpenDecisionModal(rec, "REJECTED")}
                                  leftIcon={<XCircle className="h-3.5 w-3.5 text-rose-400" />}
                                >
                                  Reject
                                </Button>
                              </>
                            ) : (
                              <span
                                className={`rounded px-2.5 py-1 text-xs font-mono font-bold ${
                                  rec.status === "APPROVED" || rec.status === "EXECUTION_PENDING"
                                    ? "bg-emerald-950/80 text-emerald-400 border border-emerald-800"
                                    : "bg-slate-900 text-slate-400 border border-slate-800"
                                }`}
                              >
                                {rec.status}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* 10 Core Questions Explainability Breakdown */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                        <div className="space-y-1 bg-slate-900/40 p-2.5 rounded-lg border border-slate-800/60">
                          <div className="font-semibold text-slate-300 flex items-center gap-1.5">
                            <Info className="h-3.5 w-3.5 text-cyan-400" />
                            <span>1. Why Generated & Contributing Systems:</span>
                          </div>
                          <p className="text-slate-400 leading-relaxed">{rec.why_explanation}</p>
                          <div className="flex flex-wrap gap-1 mt-1 pt-1 border-t border-slate-800/40">
                            {rec.evidence_sources.map((s) => (
                              <span key={s} className="rounded bg-slate-950 px-1.5 py-0.5 text-[9px] font-mono text-slate-300 border border-slate-800">
                                {s}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div className="space-y-1 bg-slate-900/40 p-2.5 rounded-lg border border-slate-800/60">
                          <div className="font-semibold text-slate-300 flex items-center gap-1.5">
                            <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                            <span>2. Recommended Action & Expected Impact:</span>
                          </div>
                          <p className="text-slate-300 font-medium leading-relaxed">{rec.recommended_action}</p>
                          <p className="text-slate-400 mt-1 italic leading-relaxed">{rec.expected_impact}</p>
                        </div>
                      </div>

                      {/* Contributing Factors & Missing Evidence */}
                      <div className="flex flex-wrap items-center justify-between text-[11px] font-mono text-slate-400 pt-1 border-t border-slate-800/40 gap-2">
                        <div className="flex flex-wrap items-center gap-3">
                          <span>Confidence: <strong className="text-cyan-300">{(rec.confidence * 100).toFixed(0)}%</strong></span>
                          <span>•</span>
                          <span>Data Completeness: <strong className="text-slate-300">{rec.data_completeness_pct}%</strong></span>
                          <span>•</span>
                          <span>Uncertainty Margin: <strong className="text-amber-400">±{rec.uncertainty_margin} pts</strong></span>
                        </div>
                        <div className="text-slate-400 truncate max-w-md">
                          Missing Data: <span className="text-slate-300">{rec.what_missing}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* TAB 2: CROSS-SYSTEM INCIDENT CORRELATIONS */}
      {activeTab === "CORRELATIONS" && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 text-xs text-slate-400 flex items-center justify-between">
            <div>
              Cross-system engine evaluates co-occurrence between acoustic signatures, pressure drops, moisture levels, and spatial clusters.
              <span className="text-amber-300 ml-1 font-semibold">Strict Rule: Distinguishes physical causation from geographic coincidence.</span>
            </div>
            <div className="font-mono text-cyan-400 font-bold">{correlations.length} Correlations Evaluated</div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {correlations.map((corr) => (
              <Card key={corr.id} className="border-slate-800 bg-slate-950/70">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <span
                      className={`rounded px-2 py-0.5 text-[10px] font-mono font-bold ${
                        corr.correlation_type === "CONFIRMED_RELATIONSHIP"
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                          : corr.correlation_type === "POTENTIAL_RELATIONSHIP"
                          ? "bg-cyan-950 text-cyan-300 border border-cyan-800"
                          : corr.correlation_type === "GEOGRAPHIC_COINCIDENCE"
                          ? "bg-amber-950 text-amber-300 border border-amber-800"
                          : "bg-slate-900 text-slate-400 border border-slate-800"
                      }`}
                    >
                      {corr.correlation_type}
                    </span>
                    <span className="text-xs font-mono text-cyan-400 font-bold">
                      Strength: {(corr.correlation_strength * 100).toFixed(0)}%
                    </span>
                  </div>
                  <CardTitle className="text-sm text-white mt-1">{corr.primary_segment_name}</CardTitle>
                  <CardDescription className="text-xs font-mono text-slate-400">
                    ID: {corr.id} • Proximity: {corr.geographic_distance_m !== null ? `${corr.geographic_distance_m}m` : "Co-located"}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2.5 text-xs">
                  <p className="text-slate-300 leading-relaxed">{corr.explanation}</p>
                  <div className="space-y-1 bg-slate-900/60 p-2.5 rounded border border-slate-800">
                    <div className="text-[10px] font-mono text-slate-400 uppercase font-semibold">Supporting Telemetry Evidence:</div>
                    <ul className="list-disc list-inside space-y-0.5 text-slate-400">
                      {corr.supporting_evidence.map((ev, i) => (
                        <li key={i}>{ev}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-1">
                    <span>Temporal Delta: {corr.temporal_delta_hours ? `${corr.temporal_delta_hours}h` : "N/A"}</span>
                    <span>Uncertainty: ±{(corr.uncertainty * 100).toFixed(0)}%</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: HYDRAULIC WHAT-IF IMPACT ANALYSIS */}
      {activeTab === "HYDRAULIC_IMPACT" && (
        <div className="space-y-4">
          <Card className="border-slate-800 bg-slate-950/70">
            <CardHeader>
              <CardTitle className="text-base text-white flex items-center gap-2">
                <Droplets className="h-4 w-4 text-cyan-400" />
                Digital Twin Hydraulic Impact & What-If Analyzer
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Simulates Torricelli orifice discharge and network pressure deficit comparison using the Task 10 hydraulic solver.
                Preserves baseline scenarios. Real-world actuator actuation is disabled.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-mono text-slate-300 block mb-1">Target Conduit Segment:</label>
                  <select
                    value={whatIfSegmentId}
                    onChange={(e) => setWhatIfSegmentId(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none"
                  >
                    <option value="PIPE-SEC-4B-92">Metro Central Main Trunk Line B (600mm)</option>
                    <option value="PIPE-HRB-02-19">Harbor Utility Distribution Main (350mm)</option>
                    <option value="PIPE-IND-1A-04">Industrial Park Southern Feeder (250mm)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-mono text-slate-300 block mb-1">Simulated Orifice Diameter (mm):</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={whatIfOrificeMm}
                    onChange={(e) => setWhatIfOrificeMm(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none"
                  />
                </div>

                <div className="flex items-end">
                  <Button
                    variant="primary"
                    size="sm"
                    className="w-full"
                    onClick={handleRunWhatIf}
                    disabled={isSimulatingWhatIf}
                    leftIcon={<Activity className={`h-3.5 w-3.5 ${isSimulatingWhatIf ? "animate-spin" : ""}`} />}
                  >
                    {isSimulatingWhatIf ? "Simulating Digital Twin..." : "Execute Scenario What-If"}
                  </Button>
                </div>
              </div>

              {whatIfResult && (
                <div className="space-y-3 pt-3 border-t border-slate-800">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <MetricCard
                      label="Estimated Water Loss"
                      value={whatIfResult.estimated_water_loss_m3_day}
                      unit="m³/day"
                      tone="amber"
                    />
                    <MetricCard
                      label="Pressure Drop Delta"
                      value={whatIfResult.min_pressure_drop_bar}
                      unit="BAR"
                      tone="rose"
                    />
                    <MetricCard
                      label="Affected Nodes"
                      value={whatIfResult.affected_nodes_count}
                      unit="JUNCTIONS"
                      tone="cyan"
                    />
                    <MetricCard
                      label="Disruption Severity"
                      value={whatIfResult.service_disruption_risk}
                      unit="RISK"
                      tone={whatIfResult.service_disruption_risk === "SEVERE" ? "rose" : "amber"}
                    />
                  </div>

                  <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 text-xs font-mono space-y-1 text-slate-300">
                    <div>SCENARIO ID: <code className="text-cyan-400">{whatIfResult.scenario_id}</code></div>
                    <div>ESTIMATED LEAK DISCHARGE: {whatIfResult.estimated_leak_rate_lps} L/s (Torricelli Orifice Flow)</div>
                    <div>POPULATION IMPACT: ~{whatIfResult.affected_population_estimate?.toLocaleString()} residents affected</div>
                    <div>FINANCIAL SAVINGS: <span className="text-amber-400 font-bold">{whatIfResult.cost_impact_display}</span> (Omitted per governance rule)</div>
                    <div>SIMULATION ISOLATION: <span className="text-emerald-400 font-semibold">is_simulated: true • Physical Actuators Disabled</span></div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 4: ROVER FLEET RESOURCE PLANNING */}
      {activeTab === "RESOURCE_PLANNING" && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 text-xs text-slate-400 flex items-center justify-between">
            <div>
              Evaluates virtual rover fleet suitability for scheduled pipeline inspections.
              <span className="text-rose-400 ml-1 font-semibold">Hard Gate: Battery &lt; 20% or motor temp &ge; 65°C blocks dispatch.</span>
            </div>
            <div className="text-slate-400 font-mono">Workforce & Inventory: <span className="text-amber-400">NOT AVAILABLE (Simulation Mode)</span></div>
          </div>

          <div className="space-y-3">
            {resourcePlans.map((plan) => (
              <Card key={plan.recommendation_id} className="border-slate-800 bg-slate-950/70">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-sm text-white">{plan.segment_name}</CardTitle>
                      <CardDescription className="text-xs font-mono text-slate-400">
                        Target: {plan.pipeline_segment_id} • Estimated Inspection: {plan.estimated_distance_m}m ({plan.estimated_duration_min} min, ~{plan.estimated_energy_pct}% battery)
                      </CardDescription>
                    </div>
                    <span
                      className={`rounded px-2.5 py-0.5 text-[11px] font-mono font-bold ${
                        plan.dispatch_feasibility === "READY_FOR_DISPATCH"
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                          : "bg-rose-950 text-rose-300 border border-rose-800"
                      }`}
                    >
                      {plan.dispatch_feasibility}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-mono text-slate-300">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-500 text-[10px]">
                          <th className="py-1">Rover Name</th>
                          <th className="py-1">Operating State</th>
                          <th className="py-1">Battery</th>
                          <th className="py-1">Motor Temp</th>
                          <th className="py-1">Distance</th>
                          <th className="py-1">Suitability Score</th>
                          <th className="py-1">Eligibility Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {plan.suitable_rovers.map((rover) => (
                          <tr key={rover.rover_id} className="border-b border-slate-800/40 hover:bg-slate-900/40">
                            <td className="py-2 text-white font-semibold flex items-center gap-1.5">
                              <Bot className="h-3.5 w-3.5 text-cyan-400" />
                              {rover.rover_name}
                            </td>
                            <td className="py-2">{rover.operating_state}</td>
                            <td className="py-2">
                              <span className={rover.battery_percentage >= 20 ? "text-emerald-400" : "text-rose-400 font-bold"}>
                                {rover.battery_percentage}%
                              </span>
                            </td>
                            <td className="py-2">
                              <span className={rover.motor_temp_c < 65 ? "text-slate-300" : "text-rose-400 font-bold"}>
                                {rover.motor_temp_c}°C
                              </span>
                            </td>
                            <td className="py-2">{rover.distance_to_target_m}m</td>
                            <td className="py-2 text-cyan-400 font-bold">{rover.suitability_score.toFixed(1)}/100</td>
                            <td className="py-2">
                              {rover.is_eligible ? (
                                <span className="text-emerald-400 font-semibold flex items-center gap-1">
                                  <CheckCircle2 className="h-3 w-3" /> Eligible
                                </span>
                              ) : (
                                <span className="text-rose-400 text-[10px] flex items-center gap-1">
                                  <XCircle className="h-3 w-3" /> {rover.rejection_reasons[0] || "Ineligible"}
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: AUDIT DECISIONS & EXECUTION HISTORY */}
      {activeTab === "DECISIONS_HISTORY" && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 text-xs text-slate-400 flex items-center justify-between">
            <div>
              Immutable audit history of human operator decisions with SHA-256 signatures and execution stage telemetry.
            </div>
            <div className="font-mono text-cyan-400">{decisions.length} Decisions Logged</div>
          </div>

          <div className="space-y-3">
            {decisions.map((dec) => (
              <Card key={dec.id} className="border-slate-800 bg-slate-950/70">
                <CardContent className="p-4 space-y-2 text-xs">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded px-2 py-0.5 text-[10px] font-mono font-bold ${
                          dec.decision_type === "APPROVED"
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                            : "bg-rose-950 text-rose-300 border border-rose-800"
                        }`}
                      >
                        {dec.decision_type}
                      </span>
                      <span className="font-bold text-white font-mono">{dec.id}</span>
                      <span className="text-slate-400 font-mono">({dec.recommendation_id})</span>
                    </div>
                    <div className="text-slate-400 font-mono text-[11px]">
                      {new Date(dec.decision_timestamp).toLocaleString()}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-300">
                    <div>
                      Operator: <strong>{dec.operator_name}</strong> ({dec.operator_id})
                    </div>
                    <div>
                      Resulting Mission: <strong className="text-cyan-400">{dec.resulting_mission_id || "None (Rejected/Deferred)"}</strong>
                    </div>
                  </div>

                  <div className="bg-slate-900/40 p-2 rounded text-slate-300 italic border border-slate-800/60">
                    "{dec.decision_reason}"
                  </div>

                  {dec.audit_hash && (
                    <div className="text-[10px] font-mono text-slate-500 truncate">
                      SHA-256 AUDIT SIGNATURE: {dec.audit_hash}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* TAB 6: GIS OPERATIONAL OVERLAY */}
      {activeTab === "GIS_MAP" && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between bg-slate-900/60 p-3 rounded-lg border border-slate-800 gap-2">
            <div className="text-xs text-slate-300 flex items-center gap-2">
              <Layers className="h-4 w-4 text-cyan-400" />
              <span>MapLibre WebGL Live Operational GIS Layers:</span>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-slate-300">
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={mapLayers.pipelines.primary}
                  onChange={(e) =>
                    setMapLayers({
                      ...mapLayers,
                      pipelines: { ...mapLayers.pipelines, primary: e.target.checked },
                    })
                  }
                  className="rounded border-slate-800"
                />
                <span>Primary Mains</span>
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={mapLayers.leakIncidents.critical}
                  onChange={(e) =>
                    setMapLayers({
                      ...mapLayers,
                      leakIncidents: { ...mapLayers.leakIncidents, critical: e.target.checked },
                    })
                  }
                  className="rounded border-slate-800"
                />
                <span>Active Leaks</span>
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={mapLayers.inspectionZones}
                  onChange={(e) => setMapLayers({ ...mapLayers, inspectionZones: e.target.checked })}
                  className="rounded border-slate-800"
                />
                <span>Risk Zones</span>
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={mapLayers.rovers}
                  onChange={(e) => setMapLayers({ ...mapLayers, rovers: e.target.checked })}
                  className="rounded border-slate-800"
                />
                <span>Rover Fleet</span>
              </label>
            </div>
          </div>

          <div className="relative h-[520px] w-full rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
            <MapContainer
              layers={mapLayers}
              basemapStyle="dark"
              onSelectFeature={(feat: SelectedMapFeature) => {
                if (feat.type === "pipeline") {
                  setWhatIfSegmentId(feat.id);
                }
              }}
              onMouseMoveCoords={() => {}}
              onZoomChange={() => {}}
            />
          </div>
        </div>
      )}

      {/* HUMAN OPERATOR DECISION MODAL */}
      {decisionModalOpen && selectedRec && (
        <Modal
          isOpen={decisionModalOpen}
          onClose={() => setDecisionModalOpen(false)}
          title={`Human Operator Decision: ${decisionType}`}
        >
          <div className="space-y-4 text-xs">
            <div className="bg-slate-900/60 p-3 rounded border border-slate-800 space-y-1">
              <div className="text-slate-400 font-mono text-[10px] uppercase">Target Pipeline Segment</div>
              <div className="text-white font-bold text-sm">{selectedRec.segment_name} ({selectedRec.pipeline_segment_id})</div>
              <div className="text-slate-400">Action: {selectedRec.recommended_action}</div>
            </div>

            <div>
              <label className="text-slate-300 font-semibold block mb-1">
                Mandatory Operator Justification Reason:
              </label>
              <textarea
                rows={3}
                value={decisionReason}
                onChange={(e) => setDecisionReason(e.target.value)}
                placeholder="Enter justification for audit log..."
                className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-xs text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            {decisionFeedback && (
              <div className="p-2 rounded bg-rose-950/80 border border-rose-800 text-rose-300 text-xs">
                {decisionFeedback}
              </div>
            )}

            <div className="bg-amber-950/40 p-2.5 rounded border border-amber-800/60 text-amber-300 text-[11px] flex items-center gap-2">
              <Lock className="h-4 w-4 shrink-0 text-amber-400" />
              <span>
                Safety Assurance: This decision generates an immutable cryptographic audit record. Real-world physical actuators remain permanently disabled.
              </span>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <Button variant="outline" size="sm" onClick={() => setDecisionModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant={decisionType === "APPROVED" ? "primary" : "outline"}
                size="sm"
                onClick={handleConfirmDecision}
                disabled={isSubmittingDecision}
              >
                {isSubmittingDecision ? "Submitting..." : `Confirm ${decisionType}`}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
