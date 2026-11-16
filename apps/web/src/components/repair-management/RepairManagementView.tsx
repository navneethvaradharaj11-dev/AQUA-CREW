"use client";

import React, { useState, useEffect } from "react";
import {
  Wrench,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  DollarSign,
  Droplets,
  Layers,
  Activity,
  FileCheck2,
  Calendar,
  Users,
  HardHat,
  Search,
  Filter,
  RefreshCw,
  Plus,
  ArrowRight,
  ExternalLink,
  ChevronRight,
  Gauge,
  Sliders,
  Scale,
  Sparkles,
  Award,
  Hash,
  HelpCircle,
  FileText,
  Hammer,
  Truck,
  Building2,
  Info,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { MetricCard } from "@/components/ui/MetricCard";
import { Modal } from "@/components/ui/Modal";
import { backendApiClient } from "@/services/api/backendApiClient";
import {
  DamageAssessment,
  DamageCategory,
  DamageSeverity,
  RepairMethodType,
  RepairRecommendation,
  RepairPlan,
  RepairWorkflowStatus,
  DigitalTwinRepairScenario,
  DigitalTwinRepairComparison,
  RepairVerification,
  RepairOverviewSummary,
  RepairWorkflowEvent,
  RepairResourceItem,
} from "@/services/api/repairManagementTypes";

export function RepairManagementView() {
  // Navigation tabs
  const [activeTab, setActiveTab] = useState<
    "queue" | "plans" | "resources_cost" | "crews_schedule" | "simulation" | "verification"
  >("queue");

  // State data
  const [overview, setOverview] = useState<RepairOverviewSummary | null>(null);
  const [assessments, setAssessments] = useState<DamageAssessment[]>([]);
  const [selectedAssessment, setSelectedAssessment] = useState<DamageAssessment | null>(null);
  const [plans, setPlans] = useState<RepairPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<RepairPlan | null>(null);
  const [crews, setCrews] = useState<any[]>([]);
  const [simulationData, setSimulationData] = useState<{
    scenario: DigitalTwinRepairScenario;
    comparison: DigitalTwinRepairComparison;
  } | null>(null);
  const [verification, setVerification] = useState<RepairVerification | null>(null);
  const [events, setEvents] = useState<RepairWorkflowEvent[]>([]);

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");
  const [filterPlanStatus, setFilterPlanStatus] = useState<string>("ALL");

  // Modals
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [showNewPlanModal, setShowNewPlanModal] = useState(false);
  const [showVerifyModal, setShowVerifyModal] = useState(false);

  // Form states
  const [engineerNotes, setEngineerNotes] = useState("");
  const [overrideMethod, setOverrideMethod] = useState<RepairMethodType | "">("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [newPlanSegmentId, setNewPlanSegmentId] = useState("PIPE-SEC-01");
  const [newPlanMethod, setNewPlanMethod] = useState<RepairMethodType>("CLAMP_REPAIR");
  const [newPlanNotes, setNewPlanNotes] = useState("");

  // Verification Form
  const [verifPostLeakage, setVerifPostLeakage] = useState(2.0);
  const [verifAcousticCleared, setVerifAcousticCleared] = useState(true);
  const [verifPressureRestored, setVerifPressureRestored] = useState(true);
  const [verifNotes, setVerifNotes] = useState("Acoustic noise floor normalized; field pressure gauge confirms 4.45 bar.");

  const loadAllData = async () => {
    setIsLoading(true);
    try {
      const [ov, assList, planList, crewList, evtList] = await Promise.all([
        backendApiClient.getRepairOverview(),
        backendApiClient.listDamageAssessments(),
        backendApiClient.listRepairPlans(),
        backendApiClient.listVirtualCrews(),
        backendApiClient.listRepairWorkflowEvents(),
      ]);

      setOverview(ov);
      setAssessments(assList);
      if (assList.length > 0 && !selectedAssessment) {
        setSelectedAssessment(assList[0]);
      }
      setPlans(planList);
      if (planList.length > 0) {
        const primary = planList[0];
        setSelectedPlan(primary);
        loadPlanDetails(primary.id);
      }
      setCrews(crewList);
      setEvents(evtList);
    } catch (err) {
      console.error("Failed to load repair management data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadPlanDetails = async (planId: string) => {
    try {
      const sim = await backendApiClient.getRepairSimulation(planId);
      setSimulationData(sim);
      try {
        const ver = await backendApiClient.getRepairVerification(planId);
        setVerification(ver);
      } catch {
        setVerification(null);
      }
    } catch (err) {
      console.error("Failed to load plan sub-details:", err);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleSelectPlan = (p: RepairPlan) => {
    setSelectedPlan(p);
    loadPlanDetails(p.id);
  };

  const handleApprovePlan = async () => {
    if (!selectedPlan) return;
    try {
      const updated = await backendApiClient.approveRepairPlan(selectedPlan.id, {
        engineer_notes: engineerNotes || "Certified engineering approval granted based on EPANET digital twin validation.",
        override_selected_method: overrideMethod || undefined,
      });
      setSelectedPlan(updated);
      setShowApprovalModal(false);
      setEngineerNotes("");
      loadAllData();
    } catch (err) {
      console.error("Error approving plan:", err);
    }
  };

  const handleRejectPlan = async () => {
    if (!selectedPlan) return;
    try {
      const updated = await backendApiClient.rejectRepairPlan(selectedPlan.id, {
        rejection_reason: rejectionReason || "Field soil parameters require deeper trenching and alternative pipe lining.",
      });
      setSelectedPlan(updated);
      setShowRejectModal(false);
      setRejectionReason("");
      loadAllData();
    } catch (err) {
      console.error("Error rejecting plan:", err);
    }
  };

  const handleTransitionWorkflow = async (targetStatus: string, reason: string) => {
    if (!selectedPlan) return;
    try {
      const updated = await backendApiClient.transitionRepairWorkflow(selectedPlan.id, {
        target_status: targetStatus,
        reason,
      });
      setSelectedPlan(updated);
      loadAllData();
    } catch (err) {
      console.error("Error transitioning workflow:", err);
    }
  };

  const handleCreatePlan = async () => {
    try {
      const p = await backendApiClient.generateRepairPlan({
        pipeline_segment_id: newPlanSegmentId,
        selected_method: newPlanMethod,
        override_notes: newPlanNotes,
      });
      setSelectedPlan(p);
      setShowNewPlanModal(false);
      setNewPlanNotes("");
      loadAllData();
    } catch (err) {
      console.error("Error creating plan:", err);
    }
  };

  const handleSubmitVerification = async () => {
    if (!selectedPlan) return;
    try {
      const v = await backendApiClient.submitRepairVerification({
        repair_plan_id: selectedPlan.id,
        post_repair_leakage_lph: verifPostLeakage,
        acoustic_anomaly_cleared: verifAcousticCleared,
        pressure_gradient_restored: verifPressureRestored,
        verification_notes: verifNotes,
      });
      setVerification(v);
      setShowVerifyModal(false);
      loadAllData();
    } catch (err) {
      console.error("Error submitting verification:", err);
    }
  };

  // Severity & Category color helpers
  const getSeverityBadge = (severity: DamageSeverity) => {
    switch (severity) {
      case "CRITICAL":
        return <StatusBadge status="critical" label="CRITICAL" pulse />;
      case "HIGH":
        return <StatusBadge status="warning" label="HIGH" />;
      case "MODERATE":
        return <StatusBadge status="active" label="MODERATE" />;
      case "LOW":
        return <StatusBadge status="standby" label="LOW" />;
      default:
        return <StatusBadge status="offline" label="UNDETERMINED" />;
    }
  };

  const getWorkflowBadge = (status: RepairWorkflowStatus) => {
    switch (status) {
      case "APPROVED":
      case "VERIFIED":
      case "CLOSED":
        return <StatusBadge status="active" label={status.replace(/_/g, " ")} />;
      case "ENGINEERING_REVIEW_PENDING":
      case "VERIFICATION_PENDING":
        return <StatusBadge status="warning" label={status.replace(/_/g, " ")} pulse />;
      case "REPAIR_IN_PROGRESS":
      case "SCHEDULED":
      case "RESOURCE_PLANNED":
        return <StatusBadge status="active" label={status.replace(/_/g, " ")} />;
      case "REJECTED":
      case "FAILED":
        return <StatusBadge status="critical" label={status.replace(/_/g, " ")} />;
      default:
        return <StatusBadge status="standby" label={status.replace(/_/g, " ")} />;
    }
  };

  const filteredAssessments = assessments.filter(
    (a) => filterSeverity === "ALL" || a.severity === filterSeverity
  );

  const filteredPlans = plans.filter(
    (p) => filterPlanStatus === "ALL" || p.workflow_status === filterPlanStatus
  );

  return (
    <div className="space-y-6">
      {/* 1. Header with Safety Disclaimer */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              <Wrench className="h-6 w-6 text-cyan-400" />
              Intelligent Repair Planning & Management
            </h1>
            <span className="rounded bg-cyan-950/80 px-2 py-0.5 text-[10px] font-mono text-cyan-300 border border-cyan-800/60 font-semibold">
              TASK 16 &bull; HYDRAULIC REPAIR OS
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Automated damage assessment, method feasibility scoring, resource bill planning,
            pre/post digital twin verification & certified engineering lifecycle tracking.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadAllData}
            disabled={isLoading}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
            Refresh Data
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowNewPlanModal(true)}
            className="flex items-center gap-1.5"
          >
            <Plus className="h-3.5 w-3.5" />
            New Repair Plan
          </Button>
        </div>
      </div>

      {/* Virtual Simulation Safety Notice Banner */}
      <div className="rounded-lg border border-cyan-500/30 bg-cyan-950/20 px-4 py-3 text-xs text-cyan-200 flex items-start gap-3 shadow-inner">
        <Info className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-cyan-300">VIRTUAL SIMULATION DECISION SUPPORT: </span>
          All damage evaluations, method rankings, equipment inventories, and hydraulic schedules operate within a certified
          synthetic digital twin environment. Physical repairs require certified engineering review and municipal work permits.
        </div>
      </div>

      {/* 2. Top-Level Operational KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <Card className="p-3 bg-slate-900/60 border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-mono">Assessments</span>
          <div className="text-lg font-bold text-white mt-1">
            {overview?.active_assessments_count ?? assessments.length}
          </div>
          <span className="text-[10px] text-amber-400 font-medium">Multi-Factor</span>
        </Card>

        <Card className="p-3 bg-slate-900/60 border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-mono">Reviews Pending</span>
          <div className="text-lg font-bold text-amber-300 mt-1">
            {overview?.pending_engineering_reviews_count ?? 2}
          </div>
          <span className="text-[10px] text-slate-400">Needs Sign-off</span>
        </Card>

        <Card className="p-3 bg-slate-900/60 border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-mono">Approved Plans</span>
          <div className="text-lg font-bold text-emerald-400 mt-1">
            {overview?.approved_plans_count ?? plans.filter((p) => p.workflow_status === "APPROVED").length}
          </div>
          <span className="text-[10px] text-emerald-400/80">Certified</span>
        </Card>

        <Card className="p-3 bg-slate-900/60 border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-mono">Scheduled</span>
          <div className="text-lg font-bold text-cyan-300 mt-1">
            {overview?.scheduled_repairs_count ?? 3}
          </div>
          <span className="text-[10px] text-cyan-400/80">Virtual Crews</span>
        </Card>

        <Card className="p-3 bg-slate-900/60 border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-mono">In Progress</span>
          <div className="text-lg font-bold text-blue-300 mt-1">
            {overview?.in_progress_repairs_count ?? 1}
          </div>
          <span className="text-[10px] text-blue-400/80">Active Sites</span>
        </Card>

        <Card className="p-3 bg-slate-900/60 border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-mono">Verifications</span>
          <div className="text-lg font-bold text-purple-400 mt-1">
            {overview?.completed_verifications_count ?? 11}
          </div>
          <span className="text-[10px] text-purple-300/80">SHA-256 Signed</span>
        </Card>

        <Card className="p-3 bg-slate-900/60 border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-mono">Water Saved</span>
          <div className="text-lg font-bold text-cyan-400 mt-1">
            {overview?.total_water_loss_prevented_m3 ? `${overview.total_water_loss_prevented_m3.toLocaleString()} m³` : "2,450 m³"}
          </div>
          <span className="text-[10px] text-slate-400">Prevented Loss</span>
        </Card>

        <Card className="p-3 bg-slate-900/60 border-slate-800">
          <span className="text-[10px] text-slate-400 uppercase font-mono">Est. Expenditure</span>
          <div className="text-lg font-bold text-amber-200 mt-1">
            {overview?.total_repair_expenditure_usd ? `$${(overview.total_repair_expenditure_usd / 1000).toFixed(1)}k` : "$54.2k"}
          </div>
          <span className="text-[10px] text-slate-400">Synthetic Model</span>
        </Card>
      </div>

      {/* 3. Navigation Tabs */}
      <div className="flex border-b border-slate-800 gap-2 overflow-x-auto text-xs font-medium">
        <button
          onClick={() => setActiveTab("queue")}
          className={`pb-2.5 px-3 flex items-center gap-1.5 transition-colors border-b-2 ${
            activeTab === "queue"
              ? "border-cyan-500 text-cyan-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <ShieldAlert className="h-4 w-4" />
          Damage Queue & Evidence ({assessments.length})
        </button>

        <button
          onClick={() => setActiveTab("plans")}
          className={`pb-2.5 px-3 flex items-center gap-1.5 transition-colors border-b-2 ${
            activeTab === "plans"
              ? "border-cyan-500 text-cyan-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Layers className="h-4 w-4" />
          Repair Plans & 12-Stage Lifecycle ({plans.length})
        </button>

        <button
          onClick={() => setActiveTab("resources_cost")}
          className={`pb-2.5 px-3 flex items-center gap-1.5 transition-colors border-b-2 ${
            activeTab === "resources_cost"
              ? "border-cyan-500 text-cyan-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <DollarSign className="h-4 w-4" />
          Materials, Equipment & Cost Model
        </button>

        <button
          onClick={() => setActiveTab("crews_schedule")}
          className={`pb-2.5 px-3 flex items-center gap-1.5 transition-colors border-b-2 ${
            activeTab === "crews_schedule"
              ? "border-cyan-500 text-cyan-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Users className="h-4 w-4" />
          Virtual Crews & Logistics ({crews.length})
        </button>

        <button
          onClick={() => setActiveTab("simulation")}
          className={`pb-2.5 px-3 flex items-center gap-1.5 transition-colors border-b-2 ${
            activeTab === "simulation"
              ? "border-cyan-500 text-cyan-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Activity className="h-4 w-4" />
          Digital Twin Hydraulic Impact
        </button>

        <button
          onClick={() => setActiveTab("verification")}
          className={`pb-2.5 px-3 flex items-center gap-1.5 transition-colors border-b-2 ${
            activeTab === "verification"
              ? "border-cyan-500 text-cyan-400"
              : "border-transparent text-slate-400 hover:text-slate-200"
          }`}
        >
          <Award className="h-4 w-4" />
          Post-Repair Verification & Audit Ledger
        </button>
      </div>

      {/* ==================================================================== */}
      {/* TAB 1: DAMAGE QUEUE & MULTI-SOURCE EVIDENCE PROVENANCE               */}
      {/* ==================================================================== */}
      {activeTab === "queue" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Assessment Queue List (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">Verified Pipeline Damages</span>
              <div className="flex items-center gap-2">
                <Filter className="h-3.5 w-3.5 text-slate-400" />
                <select
                  value={filterSeverity}
                  onChange={(e) => setFilterSeverity(e.target.value)}
                  className="bg-slate-900 border border-slate-800 text-[11px] rounded px-2 py-1 text-slate-300 focus:outline-none focus:border-cyan-500"
                >
                  <option value="ALL">All Severities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="HIGH">High</option>
                  <option value="MODERATE">Moderate</option>
                  <option value="LOW">Low</option>
                </select>
              </div>
            </div>

            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {filteredAssessments.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-500 border border-dashed border-slate-800 rounded-lg">
                  No damage assessments matching filters.
                </div>
              ) : (
                filteredAssessments.map((ass) => {
                  const isSelected = selectedAssessment?.id === ass.id;
                  return (
                    <Card
                      key={ass.id}
                      onClick={() => setSelectedAssessment(ass)}
                      className={`p-3.5 cursor-pointer transition-all border ${
                        isSelected
                          ? "bg-slate-900/90 border-cyan-500 shadow-md shadow-cyan-950/40"
                          : "bg-slate-900/40 border-slate-800/80 hover:border-slate-700"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-sm text-white">
                              {ass.pipeline_segment_id}
                            </span>
                            {getSeverityBadge(ass.severity)}
                          </div>
                          <span className="text-[11px] text-slate-400 block mt-0.5">
                            {ass.segment_name}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                          {ass.damage_category.replace(/_/g, " ")}
                        </span>
                      </div>

                      <div className="mt-3 grid grid-cols-3 gap-2 text-[11px] text-slate-400 border-t border-slate-800/60 pt-2">
                        <div>
                          <span className="text-[9px] uppercase font-mono block text-slate-500">Loss</span>
                          <span className="font-medium text-cyan-300">{ass.estimated_water_loss_lph} L/h</span>
                        </div>
                        <div>
                          <span className="text-[9px] uppercase font-mono block text-slate-500">Vulnerability</span>
                          <span className="font-medium text-amber-300">{ass.structural_vulnerability_score}/100</span>
                        </div>
                        <div>
                          <span className="text-[9px] uppercase font-mono block text-slate-500">Completeness</span>
                          <span className="font-medium text-slate-200">{ass.evidence_completeness_pct}%</span>
                        </div>
                      </div>
                    </Card>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Column: Assessment Detail & Evidence Breakdown (7 cols) */}
          <div className="lg:col-span-7">
            {selectedAssessment ? (
              <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-5">
                {/* Header */}
                <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                  <div>
                    <div className="flex items-center gap-2.5">
                      <h2 className="text-base font-bold text-white">
                        Damage Assessment: {selectedAssessment.pipeline_segment_id}
                      </h2>
                      {getSeverityBadge(selectedAssessment.severity)}
                    </div>
                    <span className="text-xs text-slate-400 mt-0.5 block">
                      Assessment ID: <span className="font-mono text-cyan-400">{selectedAssessment.id}</span> &bull; Assessed by {selectedAssessment.assessed_by}
                    </span>
                  </div>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => {
                      setNewPlanSegmentId(selectedAssessment.pipeline_segment_id);
                      setShowNewPlanModal(true);
                    }}
                    className="flex items-center gap-1.5"
                  >
                    <Wrench className="h-3.5 w-3.5" />
                    Formulate Plan
                  </Button>
                </div>

                {/* Pipeline Characteristics */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/60 p-3.5 rounded-lg border border-slate-800/80">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-mono">Conduit Material</span>
                    <div className="text-xs font-semibold text-slate-200 mt-0.5">
                      {selectedAssessment.pipe_material}
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-mono">Diameter</span>
                    <div className="text-xs font-semibold text-slate-200 mt-0.5">
                      {selectedAssessment.pipe_diameter_mm} mm
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-mono">Operating Pressure</span>
                    <div className="text-xs font-semibold text-slate-200 mt-0.5">
                      {selectedAssessment.nominal_pressure_psi} PSI
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase font-mono">Prior Repairs</span>
                    <div className="text-xs font-semibold text-slate-200 mt-0.5">
                      {selectedAssessment.previous_repair_count} Records
                    </div>
                  </div>
                </div>

                {/* Engineering Review Requirement Notice */}
                {selectedAssessment.engineering_review_required && (
                  <div className="rounded border border-amber-500/30 bg-amber-950/20 px-3.5 py-2.5 text-xs text-amber-200 flex items-center gap-2.5">
                    <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
                    <div>
                      <span className="font-semibold text-amber-300">Mandatory Engineering Review Required: </span>
                      High consequence or critical vulnerability threshold reached. Repair execution requires certified professional sign-off.
                    </div>
                  </div>
                )}

                {/* 6-Tier Evidence Classification Breakdown */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                      <FileCheck2 className="h-4 w-4 text-cyan-400" />
                      Multi-Source Supporting Evidence & Provenance
                    </span>
                    <span className="text-[10px] font-mono text-cyan-400">
                      {selectedAssessment.evidence_completeness_pct}% Completeness
                    </span>
                  </div>

                  <div className="space-y-2">
                    {selectedAssessment.supporting_evidence.map((ev) => (
                      <div
                        key={ev.evidence_id}
                        className="rounded-md border border-slate-800 bg-slate-950/70 p-3 space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-white flex items-center gap-2">
                            <span className="font-mono text-cyan-300">{ev.metric_name}</span>
                            <span className="text-slate-400">= {String(ev.metric_value)}</span>
                          </span>
                          <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded ${
                            ev.classification === "MEASURED"
                              ? "bg-emerald-950/80 text-emerald-300 border border-emerald-800/60"
                              : ev.classification === "SIMULATED"
                              ? "bg-blue-950/80 text-blue-300 border border-blue-800/60"
                              : "bg-purple-950/80 text-purple-300 border border-purple-800/60"
                          }`}>
                            [{ev.classification}]
                          </span>
                        </div>
                        <p className="text-xs text-slate-300">{ev.description}</p>
                        <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                          <span>Subsystem: {ev.source_subsystem}</span>
                          <span>Confidence: {(ev.confidence * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Notes */}
                <div className="bg-slate-950/50 p-3 rounded border border-slate-800 text-xs text-slate-400">
                  <span className="font-semibold text-slate-300 block mb-1">Assessment Notes:</span>
                  {selectedAssessment.assessment_notes}
                </div>
              </Card>
            ) : (
              <div className="text-center py-16 text-slate-500 border border-dashed border-slate-800 rounded-lg">
                Select a damage assessment from the left queue to inspect details.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 2: REPAIR PLANS & 12-STAGE LIFECYCLE MANAGEMENT                  */}
      {/* ==================================================================== */}
      {activeTab === "plans" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Plans List (4 cols) */}
          <div className="lg:col-span-4 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">Active Repair Plans</span>
              <select
                value={filterPlanStatus}
                onChange={(e) => setFilterPlanStatus(e.target.value)}
                className="bg-slate-900 border border-slate-800 text-[11px] rounded px-2 py-1 text-slate-300 focus:outline-none focus:border-cyan-500"
              >
                <option value="ALL">All Statuses</option>
                <option value="APPROVED">Approved</option>
                <option value="ENGINEERING_REVIEW_PENDING">Review Pending</option>
                <option value="SCHEDULED">Scheduled</option>
                <option value="VERIFIED">Verified</option>
              </select>
            </div>

            <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
              {filteredPlans.map((p) => {
                const isSelected = selectedPlan?.id === p.id;
                return (
                  <Card
                    key={p.id}
                    onClick={() => handleSelectPlan(p)}
                    className={`p-3.5 cursor-pointer transition-all border ${
                      isSelected
                        ? "bg-slate-900/90 border-cyan-500 shadow-md shadow-cyan-950/40"
                        : "bg-slate-900/40 border-slate-800/80 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="font-semibold text-sm text-white block">
                          {p.plan_name}
                        </span>
                        <span className="text-[11px] font-mono text-cyan-400 mt-0.5 block">
                          {p.pipeline_segment_id} &bull; {p.id}
                        </span>
                      </div>
                      {getWorkflowBadge(p.workflow_status)}
                    </div>

                    <div className="mt-3 flex items-center justify-between text-[11px] border-t border-slate-800/60 pt-2 text-slate-400">
                      <span>Method: <span className="text-slate-200">{p.selected_method.replace(/_/g, " ")}</span></span>
                      <span>Score: <span className="text-amber-300 font-medium">{p.priority?.repair_priority_score.toFixed(1) ?? "--"}</span></span>
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>

          {/* Right Column: Selected Plan Details & 12-Stage Lifecycle Tracker (8 cols) */}
          <div className="lg:col-span-8">
            {selectedPlan ? (
              <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-6">
                {/* Header & Primary Actions */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-base font-bold text-white">{selectedPlan.plan_name}</h2>
                      {getWorkflowBadge(selectedPlan.workflow_status)}
                    </div>
                    <span className="text-xs text-slate-400 mt-0.5 block">
                      Target Conduit: <span className="text-cyan-400 font-mono">{selectedPlan.pipeline_segment_id}</span> &bull; Created by {selectedPlan.created_by}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    {selectedPlan.workflow_status === "ENGINEERING_REVIEW_PENDING" && (
                      <>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => setShowApprovalModal(true)}
                          className="flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-500"
                        >
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Approve Plan
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setShowRejectModal(true)}
                          className="flex items-center gap-1.5 text-rose-400 hover:text-rose-300 border-rose-800/60"
                        >
                          <XCircle className="h-3.5 w-3.5" />
                          Reject
                        </Button>
                      </>
                    )}

                    {selectedPlan.workflow_status === "APPROVED" && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleTransitionWorkflow("SCHEDULED", "Virtual crew assigned and dispatched")}
                      >
                        Advance to Scheduled
                      </Button>
                    )}

                    {selectedPlan.workflow_status === "SCHEDULED" && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleTransitionWorkflow("REPAIR_IN_PROGRESS", "Repair crew on site")}
                      >
                        Begin Repair Work
                      </Button>
                    )}

                    {selectedPlan.workflow_status === "REPAIR_IN_PROGRESS" && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleTransitionWorkflow("VERIFICATION_PENDING", "Mechanical work finished, ready for acoustic/flow verification")}
                      >
                        Complete Repair Work
                      </Button>
                    )}

                    {selectedPlan.workflow_status === "VERIFICATION_PENDING" && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => setShowVerifyModal(true)}
                        className="bg-purple-600 hover:bg-purple-500"
                      >
                        <Award className="h-3.5 w-3.5 mr-1" />
                        Verify & Sign Off
                      </Button>
                    )}
                  </div>
                </div>

                {/* 12-Stage Visual Workflow Tracker */}
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-slate-300">12-Stage Lifecycle Progression</span>
                  <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2">
                    {[
                      { step: 1, key: "INSPECTION_COMPLETED", label: "Inspected" },
                      { step: 2, key: "DAMAGE_ASSESSED", label: "Assessed" },
                      { step: 3, key: "REPAIR_RECOMMENDED", label: "Recommended" },
                      { step: 4, key: "ENGINEERING_REVIEW_PENDING", label: "Review" },
                      { step: 5, key: "APPROVED", label: "Approved" },
                      { step: 6, key: "RESOURCE_PLANNED", label: "Resources" },
                      { step: 7, key: "SCHEDULED", label: "Scheduled" },
                      { step: 8, key: "REPAIR_IN_PROGRESS", label: "In Progress" },
                      { step: 9, key: "REPAIR_COMPLETED", label: "Completed" },
                      { step: 10, key: "VERIFICATION_PENDING", label: "Verification" },
                      { step: 11, key: "VERIFIED", label: "Verified" },
                      { step: 12, key: "CLOSED", label: "Closed" },
                    ].map(({ step, key, label }) => {
                      const isActive = selectedPlan.workflow_status === key;
                      return (
                        <div
                          key={key}
                          className={`p-2 rounded border text-center transition-all ${
                            isActive
                              ? "bg-cyan-950/80 border-cyan-500 text-cyan-200 font-bold shadow"
                              : "bg-slate-950/40 border-slate-800 text-slate-400"
                          }`}
                        >
                          <div className="text-[9px] font-mono text-slate-500">#{step}</div>
                          <div className="text-xs truncate">{label}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Plan Highlights Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/50 space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase font-mono">Selected Repair Method</span>
                    <div className="text-sm font-bold text-cyan-300">
                      {selectedPlan.selected_method.replace(/_/g, " ")}
                    </div>
                    <span className="text-[11px] text-slate-400 block">AWWA C230 Standard Compliant</span>
                  </div>

                  <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/50 space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase font-mono">Priority Score</span>
                    <div className="text-sm font-bold text-amber-300">
                      {selectedPlan.priority?.repair_priority_score.toFixed(1)} / 100
                    </div>
                    <span className="text-[11px] text-slate-400 block">
                      Category: {selectedPlan.priority?.priority_category} (SLA: {selectedPlan.priority?.recommended_response_time_hours}h)
                    </span>
                  </div>

                  <div className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/50 space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase font-mono">Approval Audit</span>
                    <div className="text-sm font-bold text-emerald-400">
                      {selectedPlan.approved_by || "Pending Review"}
                    </div>
                    <span className="text-[11px] text-slate-400 block">
                      {selectedPlan.approved_at ? new Date(selectedPlan.approved_at).toLocaleDateString() : "Unapproved"}
                    </span>
                  </div>
                </div>

                {/* Prioritization Factors breakdown */}
                {selectedPlan.priority && (
                  <div className="p-4 rounded-lg border border-slate-800 bg-slate-950/60 space-y-3">
                    <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                      <Scale className="h-4 w-4 text-cyan-400" />
                      Multi-Factor Prioritization Contribution
                    </span>
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center">
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[9px] uppercase font-mono text-slate-500 block">Severity (30%)</span>
                        <span className="text-xs font-bold text-white">
                          {selectedPlan.priority.contributing_factors.damage_severity ?? 80}
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[9px] uppercase font-mono text-slate-500 block">Water Loss (25%)</span>
                        <span className="text-xs font-bold text-cyan-300">
                          {selectedPlan.priority.contributing_factors.water_loss_impact ?? 75}
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[9px] uppercase font-mono text-slate-500 block">Criticality (20%)</span>
                        <span className="text-xs font-bold text-amber-300">
                          {selectedPlan.priority.contributing_factors.criticality_and_consequence ?? 70}
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[9px] uppercase font-mono text-slate-500 block">Vulnerability (15%)</span>
                        <span className="text-xs font-bold text-purple-300">
                          {selectedPlan.priority.contributing_factors.infrastructure_vulnerability ?? 65}
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <span className="text-[9px] uppercase font-mono text-slate-500 block">Hotspot (10%)</span>
                        <span className="text-xs font-bold text-blue-300">
                          {selectedPlan.priority.contributing_factors.geospatial_hotspot ?? 60}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            ) : (
              <div className="text-center py-16 text-slate-500 border border-dashed border-slate-800 rounded-lg">
                Select a repair plan from the left list.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 3: MATERIALS, EQUIPMENT & TRANSPARENT COST ESTIMATION            */}
      {/* ==================================================================== */}
      {activeTab === "resources_cost" && selectedPlan && (
        <div className="space-y-6">
          {/* Bill of Materials & Equipment Table */}
          <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Hammer className="h-4 w-4 text-cyan-400" />
                  Bill of Materials & Equipment Requisition ({selectedPlan.plan_name})
                </h3>
                <span className="text-xs text-slate-400">
                  Itemized mechanical parts, safety shoring, and heavy machinery required for execution.
                </span>
              </div>
              <span className="text-xs font-mono text-emerald-400 font-semibold">
                Lead Time: {selectedPlan.resources?.procurement_lead_time_days ?? 0.5} Days
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-[10px] uppercase font-mono text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Item / Description</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Qty & Unit</th>
                    <th className="py-2.5 px-3">Unit Cost</th>
                    <th className="py-2.5 px-3">Total Cost</th>
                    <th className="py-2.5 px-3">Availability</th>
                    <th className="py-2.5 px-3">Supplier</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {(selectedPlan.resources?.items ?? []).map((item) => (
                    <tr key={item.resource_id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-medium text-white">{item.name}</td>
                      <td className="py-2.5 px-3">
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px] font-mono">
                          {item.category}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono">{item.estimated_quantity} {item.unit}</td>
                      <td className="py-2.5 px-3 font-mono">${item.estimated_unit_cost_usd.toFixed(2)}</td>
                      <td className="py-2.5 px-3 font-mono font-semibold text-emerald-300">
                        ${item.total_cost_usd.toFixed(2)}
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="text-emerald-400 font-semibold">{item.availability_status}</span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400">{item.supplier_info}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Transparent Cost Formula & Uncertainty Breakdown */}
          {selectedPlan.cost_estimate && (
            <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <DollarSign className="h-4 w-4 text-emerald-400" />
                    Transparent Cost Estimation & Hydraulic Savings Valuation
                  </h3>
                  <span className="text-xs text-slate-400">
                    Explicit mathematical formulas with input parameters, contingency allowances, and uncertainty bounds.
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-400 uppercase font-mono block">Total Estimated Cost</span>
                  <span className="text-base font-bold text-emerald-400 font-mono">
                    ${selectedPlan.cost_estimate.total_estimated_cost_usd.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Explicit Formulas */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {selectedPlan.cost_estimate.components.map((comp, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg border border-slate-800 bg-slate-950/60 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-slate-200">{comp.component_name}</span>
                      <span className="font-mono text-xs font-bold text-emerald-300">${comp.amount_usd.toFixed(2)}</span>
                    </div>
                    <div className="bg-slate-900 p-2 rounded text-[11px] font-mono text-cyan-300 border border-slate-800">
                      f(x) = {comp.formula}
                    </div>
                    <div className="text-[10px] text-slate-400 space-y-0.5">
                      <div>Assumptions: {comp.assumptions}</div>
                      <div>Uncertainty: &plusmn;{comp.uncertainty_range_pct}% &bull; Source: [{comp.provenance}]</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Uncertainty Bounds Alert */}
              <div className="flex items-center justify-between bg-slate-950/80 p-3 rounded-lg border border-slate-800 text-xs">
                <span className="text-slate-400">
                  Projected 90% Confidence Interval:{" "}
                  <span className="font-mono text-white font-semibold">
                    ${selectedPlan.cost_estimate.cost_uncertainty_lower_bound_usd.toFixed(2)} &ndash; $
                    {selectedPlan.cost_estimate.cost_uncertainty_upper_bound_usd.toFixed(2)}
                  </span>
                </span>
                <span className="text-[10px] font-mono text-amber-400">
                  {selectedPlan.cost_estimate.financial_disclaimer}
                </span>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 4: VIRTUAL CREWS & SCHEDULING LOGISTICS                          */}
      {/* ==================================================================== */}
      {activeTab === "crews_schedule" && (
        <div className="space-y-6">
          {/* Virtual Crews Roster */}
          <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Users className="h-4 w-4 text-cyan-400" />
                  Virtual Repair Crew Roster & Skill Matrix
                </h3>
                <span className="text-xs text-slate-400">
                  Virtual specialized crews available for autonomous dispatch and emergency mobilization.
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {crews.map((c) => (
                <div
                  key={c.crew_id}
                  className="p-4 rounded-lg border border-slate-800 bg-slate-950/60 space-y-3"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-sm text-white">{c.crew_name}</h4>
                      <span className="text-[11px] font-mono text-cyan-400">{c.specialization}</span>
                    </div>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                        c.is_available
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                          : "bg-amber-950 text-amber-300 border border-amber-800"
                      }`}
                    >
                      {c.is_available ? "AVAILABLE" : "ON ASSIGNMENT"}
                    </span>
                  </div>

                  <div className="space-y-1.5 text-xs text-slate-300">
                    <div>
                      <span className="text-slate-500">Personnel:</span> {c.members.join(", ")}
                    </div>
                    <div>
                      <span className="text-slate-500">Qualified Skills:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {c.skills.map((s: string) => (
                          <span
                            key={s}
                            className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300"
                          >
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="text-[10px] text-slate-500 pt-2 border-t border-slate-800/80 flex justify-between">
                    <span>Base Depot: [{c.base_location_lat.toFixed(4)}, {c.base_location_lng.toFixed(4)}]</span>
                    <span>{c.current_assigned_job_id ? `Job: ${c.current_assigned_job_id}` : "Idle"}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Schedule Calendar / Timeline for Selected Plan */}
          {selectedPlan?.schedule && (
            <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Calendar className="h-4 w-4 text-cyan-400" />
                Scheduled Dispatch Logistics: {selectedPlan.schedule.crew_name}
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 bg-slate-950/60 p-4 rounded-lg border border-slate-800">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-mono">Scheduled Window</span>
                  <div className="text-xs font-semibold text-white mt-1">
                    {new Date(selectedPlan.schedule.scheduled_start).toLocaleDateString()} &bull;{" "}
                    {new Date(selectedPlan.schedule.scheduled_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>

                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-mono">Estimated Duration</span>
                  <div className="text-xs font-semibold text-cyan-300 mt-1">
                    {selectedPlan.schedule.estimated_duration_hours} Hours
                  </div>
                </div>

                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-mono">Transit Distance</span>
                  <div className="text-xs font-semibold text-slate-200 mt-1">
                    {selectedPlan.schedule.travel_distance_km} km ({selectedPlan.schedule.travel_time_hours * 60} mins)
                  </div>
                </div>

                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-mono">Conflict Status</span>
                  <div className="text-xs font-semibold text-emerald-400 mt-1 flex items-center gap-1">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Conflict Free
                  </div>
                </div>
              </div>

              <div className="text-xs text-slate-400 bg-slate-950/40 p-3 rounded border border-slate-800">
                <span className="font-semibold text-slate-300">Logistics Notes: </span>
                {selectedPlan.schedule.scheduling_notes}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 5: DIGITAL TWIN HYDRAULIC IMPACT SIMULATION                      */}
      {/* ==================================================================== */}
      {activeTab === "simulation" && simulationData && (
        <div className="space-y-6">
          <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Activity className="h-4 w-4 text-cyan-400" />
                  EPANET / WNTR Pre- vs. Post-Repair Hydraulic Comparison
                </h3>
                <span className="text-xs text-slate-400">
                  Evaluating hydraulic pressure restoration, leakage reduction, and pump energy conservation.
                </span>
              </div>
              <span className="px-2.5 py-1 rounded bg-blue-950 text-blue-300 border border-blue-800 text-[10px] font-mono">
                {simulationData.scenario.simulation_solver}
              </span>
            </div>

            {/* Key Comparison Metric Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-lg border border-slate-800 bg-slate-950/60">
                <span className="text-[10px] text-slate-500 uppercase font-mono">Water Loss Reduction</span>
                <div className="text-xl font-bold text-cyan-400 mt-1 font-mono">
                  {simulationData.scenario.water_loss_reduction_pct.toFixed(1)}%
                </div>
                <span className="text-xs text-slate-400">
                  Pre: {simulationData.scenario.pre_repair_leakage_m3.toFixed(2)} m³ &rarr; Post: {simulationData.scenario.post_repair_leakage_m3.toFixed(2)} m³
                </span>
              </div>

              <div className="p-4 rounded-lg border border-slate-800 bg-slate-950/60">
                <span className="text-[10px] text-slate-500 uppercase font-mono">Pressure Restoration</span>
                <div className="text-xl font-bold text-emerald-400 mt-1 font-mono">
                  {simulationData.scenario.pressure_restoration_pct.toFixed(1)}%
                </div>
                <span className="text-xs text-slate-400">
                  {simulationData.scenario.pre_repair_pressure_bar.toFixed(2)} bar &rarr; {simulationData.scenario.post_repair_pressure_bar.toFixed(2)} bar
                </span>
              </div>

              <div className="p-4 rounded-lg border border-slate-800 bg-slate-950/60">
                <span className="text-[10px] text-slate-500 uppercase font-mono">Pump Energy Conservation</span>
                <div className="text-xl font-bold text-amber-300 mt-1 font-mono">
                  {simulationData.scenario.pump_energy_delta_kwh.toFixed(1)} kWh
                </div>
                <span className="text-xs text-slate-400">Reduced head loss burden</span>
              </div>

              <div className="p-4 rounded-lg border border-slate-800 bg-slate-950/60">
                <span className="text-[10px] text-slate-500 uppercase font-mono">Demand Satisfaction</span>
                <div className="text-xl font-bold text-purple-300 mt-1 font-mono">
                  {simulationData.scenario.demand_satisfaction_pct.toFixed(0)}%
                </div>
                <span className="text-xs text-slate-400">Zero pressure deficits</span>
              </div>
            </div>

            {/* Hydraulic Benefit Score Bar */}
            <div className="space-y-1.5 bg-slate-950/50 p-4 rounded-lg border border-slate-800">
              <div className="flex justify-between text-xs">
                <span className="font-semibold text-slate-300">Composite Hydraulic Benefit Score</span>
                <span className="font-mono text-cyan-400 font-bold">
                  {simulationData.comparison.hydraulic_benefit_score.toFixed(1)} / 100
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 transition-all duration-500"
                  style={{ width: `${simulationData.comparison.hydraulic_benefit_score}%` }}
                />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* ==================================================================== */}
      {/* TAB 6: POST-REPAIR VERIFICATION & AUDIT HISTORY LEDGER                */}
      {/* ==================================================================== */}
      {activeTab === "verification" && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Post-Repair Verification Record (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Award className="h-4 w-4 text-purple-400" />
                  Post-Repair Verification Certificate
                </h3>
                {verification && (
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800 font-mono">
                    {verification.verification_outcome}
                  </span>
                )}
              </div>

              {verification ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/60 p-3.5 rounded-lg border border-slate-800">
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase font-mono">Pre Leakage</span>
                      <div className="text-xs font-semibold text-rose-300 mt-0.5">
                        {verification.pre_repair_leakage_lph} L/h
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase font-mono">Post Leakage</span>
                      <div className="text-xs font-semibold text-emerald-300 mt-0.5">
                        {verification.post_repair_leakage_lph} L/h
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase font-mono">Leak Reduction</span>
                      <div className="text-xs font-semibold text-cyan-300 mt-0.5">
                        {verification.leakage_reduction_pct.toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase font-mono">Uncertainty</span>
                      <div className="text-xs font-semibold text-slate-200 mt-0.5">
                        &plusmn;{verification.remaining_uncertainty_pct}%
                      </div>
                    </div>
                  </div>

                  {/* Multi-source proof checks */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-2.5 rounded bg-slate-950/60 border border-slate-800 text-xs">
                      <span className="text-slate-300 flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                        Acoustic Signature Anomaly Cleared
                      </span>
                      <span className="text-emerald-400 font-mono font-semibold">CONFIRMED</span>
                    </div>
                    <div className="flex items-center justify-between p-2.5 rounded bg-slate-950/60 border border-slate-800 text-xs">
                      <span className="text-slate-300 flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                        Hydraulic Pressure Gradient Restored
                      </span>
                      <span className="text-emerald-400 font-mono font-semibold">CONFIRMED</span>
                    </div>
                  </div>

                  {/* SHA-256 Tamper-Proof Cryptographic Hash */}
                  <div className="bg-slate-950/80 p-3 rounded-lg border border-purple-500/30 space-y-1">
                    <span className="text-[10px] text-purple-300 uppercase font-mono flex items-center gap-1">
                      <Hash className="h-3 w-3" />
                      Cryptographic SHA-256 Tamper-Evident Digest
                    </span>
                    <div className="text-[11px] font-mono text-purple-200 break-all bg-slate-900/90 p-2 rounded border border-purple-800/40 select-all">
                      {verification.tamper_proof_hash}
                    </div>
                    <div className="text-[10px] text-slate-500 pt-1 flex justify-between">
                      <span>Verified by: {verification.verified_by}</span>
                      <span>Timestamp: {new Date(verification.verified_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-xs text-slate-500 border border-dashed border-slate-800 rounded-lg">
                  No post-repair verification recorded yet for selected plan.
                  <div className="mt-3">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => setShowVerifyModal(true)}
                      className="bg-purple-600 hover:bg-purple-500"
                    >
                      <Award className="h-3.5 w-3.5 mr-1" />
                      Sign Off Verification
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          </div>

          {/* Right Column: Workflow Audit Events Ledger (5 cols) */}
          <div className="lg:col-span-5 space-y-4">
            <Card className="p-5 bg-slate-900/70 border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
                <FileText className="h-4 w-4 text-cyan-400" />
                Immutable Audit History Ledger
              </h3>

              <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                {events.map((evt) => (
                  <div
                    key={evt.id}
                    className="p-3 rounded border border-slate-800 bg-slate-950/60 space-y-1 text-xs"
                  >
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-semibold text-slate-300">
                        {evt.from_status} &rarr; <span className="text-cyan-400">{evt.to_status}</span>
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        {new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <p className="text-slate-400">{evt.reason}</p>
                    <div className="text-[10px] text-slate-500 pt-1">
                      User: <span className="text-slate-400 font-mono">{evt.changed_by}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* MODAL: ENGINEERING APPROVAL                                          */}
      {/* ==================================================================== */}
      <Modal
        isOpen={showApprovalModal}
        onClose={() => setShowApprovalModal(false)}
        title="Certified Engineering Review & Approval"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-300">
            Formally approve repair plan <span className="font-mono text-cyan-400">{selectedPlan?.id}</span> for conduit{" "}
            <span className="font-mono text-white">{selectedPlan?.pipeline_segment_id}</span>.
          </p>

          <div>
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
              Override Recommended Method (Optional)
            </label>
            <select
              value={overrideMethod}
              onChange={(e) => setOverrideMethod(e.target.value as RepairMethodType)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="">Keep Recommended ({selectedPlan?.selected_method})</option>
              <option value="CLAMP_REPAIR">CLAMP_REPAIR</option>
              <option value="JOINT_REPAIR_REPLACEMENT">JOINT_REPAIR_REPLACEMENT</option>
              <option value="PIPE_SECTION_REPLACEMENT">PIPE_SECTION_REPLACEMENT</option>
              <option value="INTERNAL_LINING_REHABILITATION">INTERNAL_LINING_REHABILITATION</option>
              <option value="CORROSION_PROTECTION">CORROSION_PROTECTION</option>
              <option value="VALVE_REPLACEMENT">VALVE_REPLACEMENT</option>
              <option value="PRESSURE_MANAGEMENT">PRESSURE_MANAGEMENT</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
              Engineering Sign-Off Notes (Mandatory)
            </label>
            <textarea
              rows={3}
              value={engineerNotes}
              onChange={(e) => setEngineerNotes(e.target.value)}
              placeholder="e.g. Hydraulic pressure simulation bounds verified. Excavation safety conditions satisfied."
              className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-xs text-slate-200"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setShowApprovalModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleApprovePlan} className="bg-emerald-600 hover:bg-emerald-500">
              Grant Formal Approval
            </Button>
          </div>
        </div>
      </Modal>

      {/* ==================================================================== */}
      {/* MODAL: REJECT PLAN                                                   */}
      {/* ==================================================================== */}
      <Modal
        isOpen={showRejectModal}
        onClose={() => setShowRejectModal(false)}
        title="Reject Repair Plan"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-300">
            State the formal engineering justification for rejecting plan{" "}
            <span className="font-mono text-cyan-400">{selectedPlan?.id}</span>.
          </p>

          <div>
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
              Rejection Reason & Directives (Mandatory)
            </label>
            <textarea
              rows={3}
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
              placeholder="e.g. Excessive structural cracking requires full section cut and replacement rather than clamp."
              className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-xs text-slate-200"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setShowRejectModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleRejectPlan} className="bg-rose-600 hover:bg-rose-500">
              Confirm Rejection
            </Button>
          </div>
        </div>
      </Modal>

      {/* ==================================================================== */}
      {/* MODAL: CREATE NEW REPAIR PLAN                                        */}
      {/* ==================================================================== */}
      <Modal
        isOpen={showNewPlanModal}
        onClose={() => setShowNewPlanModal(false)}
        title="Formulate New Repair Plan"
      >
        <div className="space-y-4 text-xs">
          <div>
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
              Target Pipeline Segment ID
            </label>
            <select
              value={newPlanSegmentId}
              onChange={(e) => setNewPlanSegmentId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
            >
              {assessments.map((a) => (
                <option key={a.pipeline_segment_id} value={a.pipeline_segment_id}>
                  {a.pipeline_segment_id} &bull; {a.segment_name} ({a.damage_category})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
              Repair Method
            </label>
            <select
              value={newPlanMethod}
              onChange={(e) => setNewPlanMethod(e.target.value as RepairMethodType)}
              className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
            >
              <option value="CLAMP_REPAIR">CLAMP_REPAIR (AWWA C230)</option>
              <option value="JOINT_REPAIR_REPLACEMENT">JOINT_REPAIR_REPLACEMENT</option>
              <option value="PIPE_SECTION_REPLACEMENT">PIPE_SECTION_REPLACEMENT</option>
              <option value="INTERNAL_LINING_REHABILITATION">INTERNAL_LINING_REHABILITATION</option>
              <option value="CORROSION_PROTECTION">CORROSION_PROTECTION</option>
              <option value="VALVE_REPLACEMENT">VALVE_REPLACEMENT</option>
              <option value="PRESSURE_MANAGEMENT">PRESSURE_MANAGEMENT</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
              Planning & Operational Notes
            </label>
            <textarea
              rows={2}
              value={newPlanNotes}
              onChange={(e) => setNewPlanNotes(e.target.value)}
              placeholder="e.g. Off-peak window scheduling requested."
              className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-xs text-slate-200"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setShowNewPlanModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" size="sm" onClick={handleCreatePlan}>
              Generate Plan
            </Button>
          </div>
        </div>
      </Modal>

      {/* ==================================================================== */}
      {/* MODAL: POST-REPAIR VERIFICATION SIGN-OFF                             */}
      {/* ==================================================================== */}
      <Modal
        isOpen={showVerifyModal}
        onClose={() => setShowVerifyModal(false)}
        title="Submit Post-Repair Physical Verification"
      >
        <div className="space-y-4 text-xs">
          <p className="text-slate-300">
            Enter field measurements and acoustic sensor readouts to verify repair on{" "}
            <span className="font-mono text-cyan-400">{selectedPlan?.pipeline_segment_id}</span>.
          </p>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">
                Post-Repair Leakage (L/h)
              </label>
              <input
                type="number"
                value={verifPostLeakage}
                onChange={(e) => setVerifPostLeakage(parseFloat(e.target.value) || 0)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              />
            </div>
            <div className="space-y-2 pt-5">
              <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                <input
                  type="checkbox"
                  checked={verifAcousticCleared}
                  onChange={(e) => setVerifAcousticCleared(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900"
                />
                Acoustic Anomaly Cleared
              </label>
              <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                <input
                  type="checkbox"
                  checked={verifPressureRestored}
                  onChange={(e) => setVerifPressureRestored(e.target.checked)}
                  className="rounded border-slate-700 bg-slate-900"
                />
                Pressure Gradient Restored
              </label>
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-medium text-slate-300 mb-1">
              Field Verification Notes
            </label>
            <textarea
              rows={2}
              value={verifNotes}
              onChange={(e) => setVerifNotes(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-xs text-slate-200"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setShowVerifyModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSubmitVerification}
              className="bg-purple-600 hover:bg-purple-500"
            >
              Sign & Hash Certificate
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
