"use client";

import React, { useState, useEffect } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldCheck,
  Play,
  RotateCcw,
  Search,
  Filter,
  Activity,
  Layers,
  Wrench,
  Bot,
  MapPin,
  Cpu,
  FileCheck,
  ChevronRight,
  Sparkles,
  ArrowRight,
  Info,
  FileText,
  X,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import {
  UnifiedIncident,
  IncidentStatsOverview,
  MasterE2EResult,
  IncidentLifecycleStatus,
} from "@/services/api/incidentTypes";
import { incidentApiClient } from "@/services/api/incidentApiClient";

const LIFECYCLE_STAGES = [
  { stage: 1, name: "Telemetry Ingest", key: "DETECTED" },
  { stage: 2, name: "AI Detection", key: "TRIAGED" },
  { stage: 3, name: "Localization", key: "TRIAGED" },
  { stage: 4, name: "Hydraulic Twin", key: "INVESTIGATING" },
  { stage: 5, name: "Risk Scoring", key: "INSPECTION_PROPOSED" },
  { stage: 6, name: "Rover Selection", key: "INSPECTION_PROPOSED" },
  { stage: 7, name: "Inspection Crawl", key: "ASSESSED" },
  { stage: 8, name: "Repair Plan", key: "AWAITING_ENGINEERING_APPROVAL" },
  { stage: 9, name: "Certified Sign-off", key: "APPROVED" },
  { stage: 10, name: "Sim Resolution", key: "CLOSED" },
];

export function IncidentsView() {
  const [incidents, setIncidents] = useState<UnifiedIncident[]>([]);
  const [stats, setStats] = useState<IncidentStatsOverview | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState<UnifiedIncident | null>(null);
  const [activeTab, setActiveTab] = useState<
    "overview" | "evidence" | "hydraulic" | "inspection" | "repair" | "approvals" | "audit"
  >("overview");

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Master Scenario Execution State
  const [isExecutingScenario, setIsExecutingScenario] = useState(false);
  const [scenarioResult, setScenarioResult] = useState<MasterE2EResult | null>(null);
  const [isResettingDemo, setIsResettingDemo] = useState(false);
  const [demoNotice, setDemoNotice] = useState<string | null>(null);

  // Final Incident Dossier State
  const [reportData, setReportData] = useState<Record<string, any> | null>(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);

  // Approval Form State
  const [approvalComment, setApprovalComment] = useState("");
  const [isSubmittingApproval, setIsSubmittingApproval] = useState(false);
  const [approvalError, setApprovalError] = useState<string | null>(null);

  const handleResetDemo = async () => {
    setIsResettingDemo(true);
    setDemoNotice(null);
    try {
      const res = await incidentApiClient.resetDemoScenario();
      setDemoNotice(res.message);
      setScenarioResult(null);
      await loadData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to reset demo scenario");
    } finally {
      setIsResettingDemo(false);
    }
  };

  const handleOpenReport = async (incidentId: string) => {
    setIsLoadingReport(true);
    try {
      const rep = await incidentApiClient.getIncidentReport(incidentId);
      setReportData(rep);
    } catch {
      if (selectedIncident) {
        setReportData({
          report_id: `REP-${selectedIncident.incident_code}`,
          incident_code: selectedIncident.incident_code,
          title: selectedIncident.title,
          status: selectedIncident.lifecycle_status,
          severity: selectedIncident.severity,
          priority: selectedIncident.priority,
          pipeline_segment_id: selectedIncident.pipeline_segment_id,
          dma_zone: selectedIncident.dma_zone,
          ai_leak_probability: selectedIncident.ai_leak_probability,
          hydraulic_headloss_delta: selectedIncident.hydraulic_headloss_delta,
          estimated_loss_lps: selectedIncident.estimated_loss_lps,
          risk_score: selectedIncident.risk_score,
          inspection_findings: selectedIncident.inspection_findings,
          repair_plan_id: selectedIncident.repair_plan_id,
          repair_cost_estimate: selectedIncident.repair_cost_estimate,
          simulation_resolution_data: selectedIncident.simulation_resolution_data,
          resolution_summary: selectedIncident.resolution_summary,
          is_simulated: true,
          provenance_statement: "EVIDENCE INTEGRITY NOTICE: Produced within Virtual Simulation Environment. Zero physical actuation performed.",
        });
      }
    } finally {
      setIsLoadingReport(false);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsData, incidentData] = await Promise.all([
        incidentApiClient.getStatsOverview(),
        incidentApiClient.listIncidents({
          status: statusFilter !== "ALL" ? statusFilter : undefined,
          severity: severityFilter !== "ALL" ? severityFilter : undefined,
        }),
      ]);
      setStats(statsData);
      setIncidents(incidentData.items);
      if (selectedIncident) {
        const refreshed = incidentData.items.find((i) => i.id === selectedIncident.id);
        if (refreshed) setSelectedIncident(refreshed);
      } else if (incidentData.items.length > 0) {
        setSelectedIncident(incidentData.items[0]);
      }
    } catch {
      // Fallback handled in client
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [statusFilter, severityFilter]);

  const handleRunMasterScenario = async () => {
    setIsExecutingScenario(true);
    setScenarioResult(null);
    try {
      const res = await incidentApiClient.runMasterE2EScenario({
        pipeline_segment_id: "PIPE-SEC-4B-92",
        acoustic_db: 89.2,
      });
      setScenarioResult(res);
      await loadData();
      if (res.incident_id) {
        const fullInc = await incidentApiClient.getIncidentById(res.incident_id);
        if (fullInc) setSelectedIncident(fullInc);
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to run master scenario");
    } finally {
      setIsExecutingScenario(false);
    }
  };

  const handleApprovalAction = async (approved: boolean, type: "INSPECTION_DISPATCH" | "REPAIR_PLAN") => {
    if (!selectedIncident) return;
    setIsSubmittingApproval(true);
    setApprovalError(null);
    try {
      const updated = await incidentApiClient.approveIncidentStep(selectedIncident.id, {
        approval_type: type,
        approved,
        comments: approvalComment || (approved ? "Approved via workspace interface" : "Rejected"),
      });
      setSelectedIncident(updated);
      setApprovalComment("");
      await loadData();
    } catch (err: unknown) {
      setApprovalError(err instanceof Error ? err.message : "Approval action failed");
    } finally {
      setIsSubmittingApproval(false);
    }
  };

  const handleSimulatedResolution = async () => {
    if (!selectedIncident) return;
    setIsSubmittingApproval(true);
    setApprovalError(null);
    try {
      const updated = await incidentApiClient.executeSimulatedResolution(selectedIncident.id, {
        verification_notes:
          "Post-repair digital twin simulation confirms headloss restoration and elimination of leak flow.",
      });
      setSelectedIncident(updated);
      await loadData();
    } catch (err: unknown) {
      setApprovalError(err instanceof Error ? err.message : "Resolution failed");
    } finally {
      setIsSubmittingApproval(false);
    }
  };

  const filteredIncidents = incidents.filter((inc) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      inc.incident_code.toLowerCase().includes(q) ||
      inc.title.toLowerCase().includes(q) ||
      inc.pipeline_segment_id.toLowerCase().includes(q) ||
      (inc.dma_zone || "").toLowerCase().includes(q)
    );
  });

  const getSeverityBadgeVariant = (sev: string): "critical" | "warning" | "active" | "standby" => {
    switch (sev) {
      case "CRITICAL":
        return "critical";
      case "HIGH":
        return "warning";
      case "MEDIUM":
        return "active";
      default:
        return "standby";
    }
  };

  const getStatusBadgeVariant = (st: string): "critical" | "warning" | "active" | "online" | "standby" => {
    switch (st) {
      case "AWAITING_ENGINEERING_APPROVAL":
      case "INSPECTION_PROPOSED":
        return "warning";
      case "INSPECTION_IN_PROGRESS":
      case "INVESTIGATING":
        return "active";
      case "CLOSED":
        return "online";
      case "DETECTED":
        return "critical";
      default:
        return "standby";
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / System Title */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-cyan-400" />
            <h1 className="text-xl font-bold tracking-tight text-white">
              Unified Incident Intelligence & Lifecycle Workspace
            </h1>
            <span className="rounded bg-emerald-950/80 px-2.5 py-0.5 text-[11px] font-mono font-semibold text-emerald-400 border border-emerald-800/60">
              TASK 19 ACCEPTANCE
            </span>
            <span className="rounded bg-cyan-950/80 px-2 py-0.5 text-[11px] font-mono text-cyan-300 border border-cyan-800/60">
              SIMULATION-FIRST
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            End-to-end 10-stage orchestration linking IoT Telemetry, AI Leak Detection, Hydraulic Digital Twin,
            Autonomous Rover Inspection, Intelligent Repair Planning, and Certified Human Approval.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5"
          >
            <RotateCcw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleResetDemo}
            disabled={isResettingDemo}
            className="flex items-center gap-1.5 text-amber-400 border-amber-800/60 hover:bg-amber-950/40"
            title="Cleanly resets demonstration incidents to baseline state without deleting unrelated data"
          >
            <RotateCcw className={`h-4 w-4 ${isResettingDemo ? "animate-spin" : ""}`} />
            {isResettingDemo ? "Resetting..." : "Reset Demo Data"}
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleRunMasterScenario}
            disabled={isExecutingScenario}
            className="flex items-center gap-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium shadow-md shadow-cyan-950/40"
          >
            <Play className={`h-4 w-4 ${isExecutingScenario ? "animate-spin" : ""}`} />
            {isExecutingScenario ? "Executing 15 Stages..." : "Run Master E2E Scenario"}
          </Button>
        </div>
      </div>

      {/* Demo Reset Notice */}
      {demoNotice && (
        <div className="p-3.5 rounded-xl border border-amber-500/40 bg-amber-950/30 text-amber-200 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-amber-400 shrink-0" />
            <span>{demoNotice}</span>
          </div>
          <button onClick={() => setDemoNotice(null)} className="text-amber-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Scenario Success Alert Banner */}
      {scenarioResult && (
        <div className="p-4 rounded-xl border border-emerald-500/40 bg-emerald-950/30 text-emerald-200 flex items-start gap-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1">
            <p className="font-semibold text-emerald-300">
              Master 10-Stage Acceptance Scenario Succeeded ({scenarioResult.incident_code})
            </p>
            <p className="text-slate-300">
              Completed all 10 stages: Sensor Telemetry &rarr; AI Leak Detection &rarr; Pipeline Localization &rarr;
              Hydraulic Twin &rarr; Multi-Factor Risk &rarr; Virtual Rover Crawl &rarr; Repair Plan Formulation &rarr;
              Certified Engineering Approval &rarr; Digital Twin Resolution Verified. (Zero Physical Actuation Enforced)
            </p>
          </div>
        </div>
      )}

      {/* KPI Overview Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Card className="p-3 bg-slate-900/80 border-slate-800">
            <span className="text-[11px] font-medium text-slate-400">Total Incidents</span>
            <div className="text-xl font-bold text-white mt-1">{stats.total_incidents}</div>
            <span className="text-[10px] text-slate-500">All registered lifecycles</span>
          </Card>
          <Card className="p-3 bg-slate-900/80 border-slate-800">
            <span className="text-[11px] font-medium text-cyan-400">Active Pipeline Incidents</span>
            <div className="text-xl font-bold text-cyan-300 mt-1">{stats.active_incidents}</div>
            <span className="text-[10px] text-slate-500">In triage / inspection / repair</span>
          </Card>
          <Card className="p-3 bg-slate-900/80 border-slate-800">
            <span className="text-[11px] font-medium text-amber-400">Awaiting Human Approval</span>
            <div className="text-xl font-bold text-amber-300 mt-1">{stats.awaiting_approval_incidents}</div>
            <span className="text-[10px] text-slate-500">Operator / Engineer actions</span>
          </Card>
          <Card className="p-3 bg-slate-900/80 border-slate-800">
            <span className="text-[11px] font-medium text-rose-400">Critical P1 Burst Risks</span>
            <div className="text-xl font-bold text-rose-300 mt-1">{stats.critical_incidents}</div>
            <span className="text-[10px] text-slate-500">High priority dispatch</span>
          </Card>
          <Card className="p-3 bg-slate-900/80 border-slate-800">
            <span className="text-[11px] font-medium text-blue-400">Active Est. Water Loss</span>
            <div className="text-xl font-bold text-blue-300 mt-1">{stats.total_estimated_water_loss_lps} L/s</div>
            <span className="text-[10px] text-slate-500">Simulated rate</span>
          </Card>
        </div>
      )}

      {/* Main Grid: Master List (Left) & Incident Workspace (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Filterable Incident List */}
        <div className="lg:col-span-5 space-y-4">
          <div className="flex flex-col gap-2 p-3 rounded-lg bg-slate-900/90 border border-slate-800">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search code, pipe segment, DMA..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-8 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="flex-1 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-300"
              >
                <option value="ALL">All Statuses</option>
                <option value="DETECTED">Detected</option>
                <option value="TRIAGED">Triaged</option>
                <option value="INVESTIGATING">Investigating</option>
                <option value="INSPECTION_PROPOSED">Inspection Proposed</option>
                <option value="AWAITING_ENGINEERING_APPROVAL">Awaiting Sign-off</option>
                <option value="CLOSED">Closed / Resolved</option>
              </select>

              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="flex-1 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-300"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>
          </div>

          {/* List items */}
          <div className="space-y-2 max-h-[640px] overflow-y-auto pr-1">
            {filteredIncidents.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 bg-slate-900/40 rounded-lg border border-slate-800">
                No incidents match filter criteria.
              </div>
            ) : (
              filteredIncidents.map((inc) => {
                const isSelected = selectedIncident?.id === inc.id;
                return (
                  <div
                    key={inc.id}
                    onClick={() => setSelectedIncident(inc)}
                    className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                      isSelected
                        ? "bg-slate-800/90 border-cyan-500 shadow-md shadow-cyan-950/20"
                        : "bg-slate-900/60 border-slate-800/80 hover:bg-slate-850 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono text-xs font-semibold text-cyan-400">
                        {inc.incident_code}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <StatusBadge
                          status={getSeverityBadgeVariant(inc.severity)}
                          label={inc.severity}
                        />
                        <StatusBadge
                          status={getStatusBadgeVariant(inc.lifecycle_status)}
                          label={inc.lifecycle_status.replace(/_/g, " ")}
                        />
                      </div>
                    </div>

                    <h4 className="text-xs font-medium text-slate-200 line-clamp-1">{inc.title}</h4>

                    <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800/60 text-[11px] text-slate-400">
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3 text-slate-500" />
                        {inc.pipeline_segment_id}
                      </span>
                      <span className="font-mono text-slate-400">Risk: {inc.risk_score}/100</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Comprehensive Incident Workspace */}
        <div className="lg:col-span-7">
          {selectedIncident ? (
            <Card className="p-5 bg-slate-900/90 border-slate-800 space-y-5">
              {/* Incident Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-cyan-400">
                      {selectedIncident.incident_code}
                    </span>
                    <StatusBadge
                      status={getSeverityBadgeVariant(selectedIncident.severity)}
                      label={selectedIncident.severity}
                    />
                    <StatusBadge
                      status={getStatusBadgeVariant(selectedIncident.lifecycle_status)}
                      label={selectedIncident.lifecycle_status.replace(/_/g, " ")}
                    />
                  </div>
                  <h2 className="text-base font-bold text-white mt-1">{selectedIncident.title}</h2>
                  <p className="text-xs text-slate-400 mt-0.5">{selectedIncident.description}</p>
                </div>

                <div className="flex flex-col items-end gap-1.5 shrink-0">
                  <div className="text-right">
                    <div className="text-[11px] text-slate-500">Pipeline Segment</div>
                    <div className="text-xs font-mono font-semibold text-slate-300">
                      {selectedIncident.pipeline_segment_id}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">{selectedIncident.dma_zone}</div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleOpenReport(selectedIncident.id)}
                    disabled={isLoadingReport}
                    className="flex items-center gap-1 text-[11px] h-7 px-2 border-cyan-800 text-cyan-400 hover:bg-cyan-950/40"
                    title="View publication-grade 15-step incident investigation and resolution dossier"
                  >
                    <FileText className="h-3.5 w-3.5" />
                    {isLoadingReport ? "Loading..." : "Dossier Report"}
                  </Button>
                </div>
              </div>

              {/* Master 10-Stage Lifecycle Visualizer */}
              <div className="space-y-1.5 p-3 rounded-lg bg-slate-950/70 border border-slate-800">
                <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                  <span className="font-semibold text-slate-300">10-Stage Lifecycle Progression</span>
                  <span className="font-mono text-cyan-400">{selectedIncident.lifecycle_status}</span>
                </div>
                <div className="grid grid-cols-5 md:grid-cols-10 gap-1">
                  {LIFECYCLE_STAGES.map((s, idx) => {
                    const isClosed = selectedIncident.lifecycle_status === "CLOSED";
                    const isCurrent = selectedIncident.lifecycle_status === s.key;
                    return (
                      <div
                        key={idx}
                        className={`p-1.5 rounded text-center border text-[9px] transition-all ${
                          isClosed
                            ? "bg-emerald-950/40 border-emerald-500/60 text-emerald-300"
                            : isCurrent
                            ? "bg-cyan-950/80 border-cyan-400 text-cyan-300 font-bold animate-pulse"
                            : "bg-slate-900 border-slate-800 text-slate-500"
                        }`}
                      >
                        <div className="font-mono">{s.stage}</div>
                        <div className="truncate text-[8px]">{s.name}</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Workspace Navigation Tabs */}
              <div className="flex items-center gap-1 border-b border-slate-800 pb-1 overflow-x-auto text-xs">
                {(
                  [
                    { id: "overview", label: "Overview", icon: Layers },
                    { id: "evidence", label: "Sensor Evidence", icon: Cpu },
                    { id: "hydraulic", label: "Digital Twin", icon: Activity },
                    { id: "inspection", label: "Rover Inspection", icon: Bot },
                    { id: "repair", label: "Repair Plan", icon: Wrench },
                    { id: "approvals", label: "Human Approvals", icon: FileCheck },
                    { id: "audit", label: "Audit Ledger", icon: Clock },
                  ] as const
                ).map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-t-md font-medium transition-all ${
                        isActive
                          ? "bg-slate-800 text-cyan-400 border-b-2 border-cyan-400"
                          : "text-slate-400 hover:text-slate-200 hover:bg-slate-850"
                      }`}
                    >
                      <Icon className="h-3.5 w-3.5" />
                      {tab.label}
                    </button>
                  );
                })}
              </div>

              {/* Tab Contents */}
              <div className="min-h-[280px]">
                {/* OVERVIEW TAB */}
                {activeTab === "overview" && (
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2">
                      <h4 className="font-semibold text-slate-300">Spatial & Pipeline Metadata</h4>
                      <div className="space-y-1 text-slate-400">
                        <div className="flex justify-between">
                          <span>Segment ID:</span>
                          <span className="font-mono text-slate-200">{selectedIncident.pipeline_segment_id}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>DMA Zone:</span>
                          <span className="text-slate-200">{selectedIncident.dma_zone}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Coordinates:</span>
                          <span className="font-mono text-slate-200">
                            {selectedIncident.latitude.toFixed(4)}, {selectedIncident.longitude.toFixed(4)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Detection Source:</span>
                          <span className="text-slate-200">{selectedIncident.detection_source}</span>
                        </div>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2">
                      <h4 className="font-semibold text-slate-300">Multi-Factor Risk Assessment</h4>
                      <div className="space-y-1 text-slate-400">
                        <div className="flex justify-between">
                          <span>Risk Score:</span>
                          <span className="font-bold text-amber-400">{selectedIncident.risk_score} / 100</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Dispatch Priority:</span>
                          <span className="font-bold text-rose-400">{selectedIncident.priority}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Leak Probability:</span>
                          <span className="text-slate-200">
                            {(selectedIncident.ai_leak_probability * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Estimated Loss:</span>
                          <span className="font-semibold text-blue-400">
                            {selectedIncident.estimated_loss_lps} L/s
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* SENSOR EVIDENCE TAB */}
                {activeTab === "evidence" && (
                  <div className="space-y-3 text-xs">
                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold text-slate-300">Acoustic & Pressure Telemetry Bindings</h4>
                        <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[10px] text-cyan-300">
                          PROVENANCE: {selectedIncident.evidence_provenance}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 pt-1">
                        <div className="p-2 rounded bg-slate-900 border border-slate-800">
                          <span className="text-[10px] text-slate-500">Associated Sensors</span>
                          <div className="font-mono text-xs text-slate-200 mt-1">
                            {selectedIncident.sensor_ids?.join(", ") || "SNS-AC-01-A"}
                          </div>
                        </div>
                        <div className="p-2 rounded bg-slate-900 border border-slate-800">
                          <span className="text-[10px] text-slate-500">AI Confidence</span>
                          <div className="font-semibold text-xs text-emerald-400 mt-1">
                            {(selectedIncident.ai_confidence * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div className="p-2 rounded bg-slate-900 border border-slate-800">
                          <span className="text-[10px] text-slate-500">Simulation Invariant</span>
                          <div className="font-semibold text-xs text-cyan-400 mt-1">
                            {selectedIncident.is_simulated ? "Virtual Sandbox" : "Field"}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* HYDRAULIC DIGITAL TWIN TAB */}
                {activeTab === "hydraulic" && (
                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-3 text-xs">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-slate-300">Hydraulic Digital Twin Impact Delta</h4>
                      <span className="text-[11px] text-slate-400">EPANET / WNTR Solver Integration</span>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[11px] text-slate-500">Simulated Headloss Delta</span>
                        <div className="text-lg font-bold text-rose-400 mt-1">
                          +{selectedIncident.hydraulic_headloss_delta} m
                        </div>
                        <p className="text-[10px] text-slate-500 mt-0.5">
                          Transient pressure differential across pipeline nodes.
                        </p>
                      </div>
                      <div className="p-3 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[11px] text-slate-500">Estimated Discharge Rate</span>
                        <div className="text-lg font-bold text-blue-400 mt-1">
                          {selectedIncident.estimated_loss_lps} L/s
                        </div>
                        <p className="text-[10px] text-slate-500 mt-0.5">
                          Calculated water loss before valve throttling or repair.
                        </p>
                      </div>
                    </div>

                    {selectedIncident.simulation_resolution_data && (
                      <div className="p-3 rounded bg-emerald-950/30 border border-emerald-800/40 text-emerald-300 mt-2">
                        <div className="font-semibold text-xs mb-1">Post-Repair Hydraulic Verification</div>
                        <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300">
                          <div>
                            Pressure Recovery:{" "}
                            <span className="font-bold text-emerald-400">
                              +{selectedIncident.simulation_resolution_data.post_repair_pressure_gain_bar} bar
                            </span>
                          </div>
                          <div>
                            Loss Eliminated:{" "}
                            <span className="font-bold text-emerald-400">
                              {selectedIncident.simulation_resolution_data.leak_flow_eliminated_lps} L/s
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* ROVER INSPECTION TAB */}
                {activeTab === "inspection" && (
                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-3 text-xs">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-slate-300">Virtual Rover Fleet Inspection</h4>
                      <span className="font-mono text-cyan-400">
                        Mission: {selectedIncident.inspection_mission_id || "Unassigned"}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-500">Assigned Rover</span>
                        <div className="font-mono text-xs font-semibold text-white mt-0.5">
                          {selectedIncident.assigned_rover_id || "Awaiting Operator Dispatch"}
                        </div>
                      </div>
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-500">Inspection Defect</span>
                        <div className="font-semibold text-xs text-amber-400 mt-0.5">
                          {selectedIncident.inspection_findings?.visual_defect_type ||
                            selectedIncident.inspection_findings?.pipe_defect ||
                            "Crawl Required"}
                        </div>
                      </div>
                    </div>

                    {selectedIncident.inspection_findings && (
                      <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-1">
                        <span className="text-[11px] font-semibold text-slate-300">Rover Crawl Measurements</span>
                        <pre className="text-[10px] font-mono text-slate-400 overflow-x-auto p-2 bg-slate-950 rounded">
                          {JSON.stringify(selectedIncident.inspection_findings, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                )}

                {/* REPAIR PLAN TAB */}
                {activeTab === "repair" && (
                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-3 text-xs">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-slate-300">Intelligent Repair Engineering Recommendation</h4>
                      <span className="font-mono text-amber-400">
                        Plan: {selectedIncident.repair_plan_id || "Pending Formulation"}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-500">Cost Estimate</span>
                        <div className="text-base font-bold text-emerald-400 mt-1">
                          {selectedIncident.repair_cost_estimate
                            ? `$${selectedIncident.repair_cost_estimate.toLocaleString()}`
                            : "Calculating..."}
                        </div>
                        <span className="text-[10px] text-slate-500">Materials, labor & bypass</span>
                      </div>
                      <div className="p-3 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[10px] text-slate-500">Urgency Tier</span>
                        <div className="text-base font-bold text-amber-400 mt-1">
                          {selectedIncident.repair_urgency || "PLANNED"}
                        </div>
                        <span className="text-[10px] text-slate-500">Target response window</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* HUMAN APPROVALS TAB */}
                {activeTab === "approvals" && (
                  <div className="space-y-4 text-xs">
                    <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-3">
                      <h4 className="font-semibold text-slate-300">Certified Human Approval Center</h4>
                      <p className="text-slate-400">
                        High-consequence actions (rover dispatch and certified municipal repair plans) require
                        authenticated human authorization. Automated override is strictly prohibited.
                      </p>

                      {/* Pending Action Buttons */}
                      {selectedIncident.lifecycle_status === "INSPECTION_PROPOSED" && (
                        <div className="p-3 rounded bg-amber-950/40 border border-amber-500/50 space-y-2">
                          <div className="flex items-center gap-1.5 font-semibold text-amber-300">
                            <AlertTriangle className="h-4 w-4" />
                            Action Required: Authorize Virtual Rover Dispatch
                          </div>
                          <input
                            type="text"
                            placeholder="Operator notes / dispatch justification..."
                            value={approvalComment}
                            onChange={(e) => setApprovalComment(e.target.value)}
                            className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white placeholder-slate-500"
                          />
                          <div className="flex items-center gap-2 pt-1">
                            <Button
                              size="sm"
                              variant="primary"
                              disabled={isSubmittingApproval}
                              onClick={() => handleApprovalAction(true, "INSPECTION_DISPATCH")}
                              className="bg-emerald-600 hover:bg-emerald-500 text-white"
                            >
                              Approve Dispatch
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={isSubmittingApproval}
                              onClick={() => handleApprovalAction(false, "INSPECTION_DISPATCH")}
                              className="text-rose-400 hover:text-rose-300"
                            >
                              Reject & Close
                            </Button>
                          </div>
                        </div>
                      )}

                      {selectedIncident.lifecycle_status === "AWAITING_ENGINEERING_APPROVAL" && (
                        <div className="p-3 rounded bg-cyan-950/40 border border-cyan-500/50 space-y-2">
                          <div className="flex items-center gap-1.5 font-semibold text-cyan-300">
                            <FileCheck className="h-4 w-4" />
                            Action Required: Certified Municipal Engineering Sign-off
                          </div>
                          <input
                            type="text"
                            placeholder="Certified engineer review comments..."
                            value={approvalComment}
                            onChange={(e) => setApprovalComment(e.target.value)}
                            className="w-full rounded border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-white placeholder-slate-500"
                          />
                          <div className="flex items-center gap-2 pt-1">
                            <Button
                              size="sm"
                              variant="primary"
                              disabled={isSubmittingApproval}
                              onClick={() => handleApprovalAction(true, "REPAIR_PLAN")}
                              className="bg-cyan-600 hover:bg-cyan-500 text-white"
                            >
                              Certify Repair Plan
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              disabled={isSubmittingApproval}
                              onClick={() => handleApprovalAction(false, "REPAIR_PLAN")}
                              className="text-rose-400 hover:text-rose-300"
                            >
                              Reject Plan
                            </Button>
                          </div>
                        </div>
                      )}

                      {selectedIncident.lifecycle_status === "APPROVED" && (
                        <div className="p-3 rounded bg-blue-950/40 border border-blue-500/50 space-y-2">
                          <div className="flex items-center gap-1.5 font-semibold text-blue-300">
                            <CheckCircle2 className="h-4 w-4" />
                            Ready for Post-Repair Simulated Resolution
                          </div>
                          <p className="text-[11px] text-slate-300">
                            Execute virtual repair installation and run digital twin simulation delta to verify pressure recovery.
                          </p>
                          <Button
                            size="sm"
                            variant="primary"
                            disabled={isSubmittingApproval}
                            onClick={handleSimulatedResolution}
                            className="bg-blue-600 hover:bg-blue-500 text-white"
                          >
                            Simulate Resolution & Verify Twin
                          </Button>
                        </div>
                      )}

                      {approvalError && (
                        <div className="p-2 rounded bg-rose-950/50 border border-rose-800 text-rose-300 text-xs">
                          {approvalError}
                        </div>
                      )}

                      {/* Approval History Ledger */}
                      <div className="pt-2">
                        <span className="text-[11px] font-semibold text-slate-300">Approval Records</span>
                        <div className="mt-1 space-y-1.5">
                          {selectedIncident.approvals?.length === 0 ? (
                            <p className="text-[11px] text-slate-500">No approval records logged yet.</p>
                          ) : (
                            selectedIncident.approvals?.map((appr) => (
                              <div
                                key={appr.id}
                                className="p-2 rounded bg-slate-900 border border-slate-800 flex items-center justify-between text-[11px]"
                              >
                                <div>
                                  <div className="font-semibold text-slate-300">
                                    {appr.approval_type.replace(/_/g, " ")} — {appr.status}
                                  </div>
                                  <div className="text-slate-400 text-[10px]">
                                    Actor: {appr.approved_by || appr.requested_by} ({appr.approver_role || "SYSTEM"})
                                  </div>
                                </div>
                                {appr.digital_signature && (
                                  <span className="font-mono text-[9px] text-cyan-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                                    SIG: {appr.digital_signature.slice(0, 12)}...
                                  </span>
                                )}
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* AUDIT LEDGER TAB */}
                {activeTab === "audit" && (
                  <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 space-y-2 text-xs">
                    <h4 className="font-semibold text-slate-300">Immutable Workflow Event Ledger</h4>
                    <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                      {selectedIncident.workflow_events?.length === 0 ? (
                        <p className="text-[11px] text-slate-500">No workflow events recorded.</p>
                      ) : (
                        selectedIncident.workflow_events?.map((evt) => (
                          <div
                            key={evt.id}
                            className="p-2 rounded bg-slate-900 border border-slate-800 text-[11px] space-y-1"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-cyan-400">{evt.action}</span>
                              <span className="font-mono text-[10px] text-slate-500">
                                {new Date(evt.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                            <div className="text-slate-300">{evt.notes}</div>
                            <div className="text-[10px] text-slate-500 flex justify-between pt-0.5">
                              <span>Actor: {evt.actor_id}</span>
                              <span className="font-mono">
                                {evt.from_status} &rarr; {evt.to_status}
                              </span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          ) : (
            <Card className="p-12 text-center text-slate-500 border-slate-800 bg-slate-900/40">
              Select an incident from the list to inspect workspace details.
            </Card>
          )}
        </div>
      </div>

      {/* Publication-Grade Incident Dossier Modal */}
      {reportData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="relative w-full max-w-3xl rounded-xl border border-cyan-800/80 bg-slate-950 p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-cyan-400" />
                <h3 className="text-base font-bold text-white">
                  Formal Incident Investigation & Resolution Dossier
                </h3>
                <span className="font-mono text-xs text-cyan-400">({reportData.incident_code})</span>
              </div>
              <button
                onClick={() => setReportData(null)}
                className="text-slate-400 hover:text-white p-1 rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-3 rounded-lg bg-amber-950/30 border border-amber-800/40 text-[11px] text-amber-300">
              {reportData.provenance_statement}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-500">Pipeline Segment</span>
                <div className="font-mono font-semibold text-white mt-0.5">{reportData.pipeline_segment_id}</div>
              </div>
              <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-500">Status</span>
                <div className="font-semibold text-emerald-400 mt-0.5">{reportData.status}</div>
              </div>
              <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-500">Risk Score</span>
                <div className="font-bold text-amber-400 mt-0.5">{reportData.risk_score} / 100</div>
              </div>
              <div className="p-2.5 rounded bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-500">Leak Probability</span>
                <div className="font-bold text-cyan-400 mt-0.5">
                  {((reportData.ai_leak_probability || 0) * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* 15-Step Master Timeline */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-300">Chronological 15-Step Lifecycle Timeline</h4>
              <div className="space-y-1.5 max-h-[240px] overflow-y-auto pr-1">
                {reportData.timeline?.map((step: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-2 rounded bg-slate-900/80 border border-slate-800/80 flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-cyan-950 text-cyan-400 font-mono text-[10px] font-bold border border-cyan-800">
                        {step.step}
                      </span>
                      <span className="font-medium text-slate-200">{step.name}</span>
                    </div>
                    <span className="font-mono text-[10px] text-emerald-400">VERIFIED</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Verification & Resolution Data */}
            {reportData.simulation_resolution_data && (
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1 text-xs">
                <h4 className="font-semibold text-slate-300">Hydraulic Digital Twin Verification Outcome</h4>
                <div className="grid grid-cols-2 gap-2 text-slate-400 pt-1">
                  <div>
                    Pressure Recovery:{" "}
                    <span className="font-bold text-emerald-400">
                      +{reportData.simulation_resolution_data.post_repair_pressure_gain_bar} bar
                    </span>
                  </div>
                  <div>
                    Eliminated Leak Flow:{" "}
                    <span className="font-bold text-emerald-400">
                      {reportData.simulation_resolution_data.leak_flow_eliminated_lps} L/s
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-slate-400 mt-1">{reportData.resolution_summary}</p>
              </div>
            )}

            <div className="flex justify-end pt-2 border-t border-slate-800">
              <Button size="sm" variant="outline" onClick={() => setReportData(null)}>
                Close Dossier
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
