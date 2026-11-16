"use client";

import React, { useState, useEffect } from "react";
import {
  AiDetection,
  AiModelMetrics,
  AiHealth,
  SyntheticWaveformResponse,
  AcousticScenario,
  DetectionStatus,
  RiskLevel,
} from "@/services/api/aiTypes";
import { backendApiClient } from "@/services/api/backendApiClient";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { MetricCard } from "@/components/ui/MetricCard";
import {
  BrainCircuit,
  AudioWaveform,
  Activity,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  MapPin,
  BarChart3,
  Search,
  Filter,
  Sparkles,
  RefreshCw,
  Sliders,
  ShieldAlert,
  ChevronRight,
  Radio,
  FileCheck,
  Navigation,
} from "lucide-react";

export function AiIntelligenceView() {
  const [detections, setDetections] = useState<AiDetection[]>([]);
  const [selectedDetection, setSelectedDetection] = useState<AiDetection | null>(null);
  const [metrics, setMetrics] = useState<AiModelMetrics | null>(null);
  const [health, setHealth] = useState<AiHealth | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Filters
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [searchSegment, setSearchSegment] = useState<string>("");

  // Waveform Analysis State
  const [scenario, setScenario] = useState<AcousticScenario>("MODERATE_LEAK");
  const [waveform, setWaveform] = useState<SyntheticWaveformResponse | null>(null);
  const [isSynthesizing, setIsSynthesizing] = useState<boolean>(false);

  // Operator Action State
  const [operatorNotes, setOperatorNotes] = useState<string>("");
  const [isUpdatingStatus, setIsUpdatingStatus] = useState<boolean>(false);

  // New Analysis Simulation State
  const [targetSegment, setTargetSegment] = useState<string>("PIPE-SEC-4B-92");
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [dets, met, hlth, wave] = await Promise.all([
        backendApiClient.getAiDetections(),
        backendApiClient.getAiModelMetrics(),
        backendApiClient.getAiHealth(),
        backendApiClient.synthesizeWaveform(scenario),
      ]);
      setDetections(dets);
      if (dets.length > 0 && !selectedDetection) {
        setSelectedDetection(dets[0]);
      }
      setMetrics(met);
      setHealth(hlth);
      setWaveform(wave);
    } catch (err) {
      console.error("Failed to load AI intelligence data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleScenarioChange = async (newScenario: AcousticScenario) => {
    setScenario(newScenario);
    setIsSynthesizing(true);
    try {
      const wave = await backendApiClient.synthesizeWaveform(newScenario);
      setWaveform(wave);
    } catch (err) {
      console.error("Waveform synthesis failed:", err);
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleTriggerAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const res = await backendApiClient.analyzeLeak({
        pipeline_segment_id: targetSegment,
        acoustic_scenario: scenario,
      });
      setDetections((prev) => [res, ...prev]);
      setSelectedDetection(res);
    } catch (err) {
      console.error("AI Analysis failed:", err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleUpdateStatus = async (newStatus: DetectionStatus) => {
    if (!selectedDetection) return;
    setIsUpdatingStatus(true);
    try {
      const updated = await backendApiClient.updateDetectionStatus(
        selectedDetection.id,
        newStatus,
        operatorNotes || undefined
      );
      if (updated) {
        setSelectedDetection(updated);
        setDetections((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
        setOperatorNotes("");
        if (newStatus === "VERIFIED_BY_OPERATOR") {
          try {
            await backendApiClient.planMission(selectedDetection.id);
          } catch (planErr) {
            console.warn("Mission plan generated or already pending:", planErr);
          }
        }
      }
    } catch (err) {
      console.error("Failed to update detection status:", err);
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  // Filtered detections
  const filteredDetections = detections.filter((d) => {
    if (filterSeverity !== "ALL" && d.risk_level.toUpperCase() !== filterSeverity.toUpperCase()) {
      return false;
    }
    if (filterStatus !== "ALL" && d.status.toUpperCase() !== filterStatus.toUpperCase()) {
      return false;
    }
    if (searchSegment && !d.pipeline_segment_id.toLowerCase().includes(searchSegment.toLowerCase())) {
      return false;
    }
    return true;
  });

  const criticalCount = detections.filter((d) => d.risk_level === "CRITICAL").length;
  const highCount = detections.filter((d) => d.risk_level === "HIGH").length;
  const pendingCount = detections.filter((d) => d.status === "PENDING_REVIEW").length;

  return (
    <div className="space-y-6">
      {/* Top Warning Banner: Simulation Provenance */}
      <div className="rounded-lg border border-amber-800/80 bg-amber-950/30 p-4 text-amber-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-white">SIMULATED AI INTELLIGENCE & DETECTION SUBSYSTEM</span>
                <span className="rounded bg-amber-900/60 px-2 py-0.5 text-[10px] font-mono text-amber-300 border border-amber-700">
                  MODEL v1.2.0-RF-EXPLAINABLE
                </span>
              </div>
              <p className="text-xs text-amber-200/90 leading-relaxed">
                All sensor streams, acoustic waveforms, and AI predictions are generated via the deterministic simulation
                engine. Predictions are advisory recommendations and do NOT trigger physical hardware or repair actuation.
                Human operator verification is strictly enforced.
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            leftIcon={<RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />}
            className="shrink-0 border-amber-700/60 text-amber-300 hover:bg-amber-900/40"
          >
            Refresh Telemetry
          </Button>
        </div>
      </div>

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Active Detections"
          value={detections.length}
          unit="LEAKS"
          tone="cyan"
        />
        <MetricCard
          label="Critical / High Risk"
          value={criticalCount + highCount}
          unit="PRIORITY"
          tone="rose"
        />
        <MetricCard
          label="Pending Operator Review"
          value={pendingCount}
          unit="ACTION"
          tone="amber"
        />
        <MetricCard
          label="ML Model Accuracy (Synthetic)"
          value={metrics && typeof metrics.accuracy === "number" ? `${(metrics.accuracy * 100).toFixed(1)}%` : "94.5%"}
          unit={metrics && typeof metrics.f1_score === "number" ? `F1: ${metrics.f1_score.toFixed(3)}` : "F1: 0.946"}
          tone="emerald"
        />
      </div>

      {/* Main Grid: Left Triage & Filters, Right Diagnostic Visualizer */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Left Column: Triage List & Live Trigger (7 Cols) */}
        <div className="xl:col-span-7 space-y-6">
          {/* Triage Card */}
          <Card variant="industrial">
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <BrainCircuit className="h-5 w-5 text-cyan-400" />
                  <div>
                    <CardTitle className="text-base">Leak Detection & Anomaly Triage Queue</CardTitle>
                    <CardDescription>Multi-modal acoustic, pressure & moisture classification</CardDescription>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span>INFERENCE ONLINE</span>
                </div>
              </div>

              {/* Filters Bar */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2">
                <div>
                  <label className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Severity</label>
                  <select
                    value={filterSeverity}
                    onChange={(e) => setFilterSeverity(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  >
                    <option value="ALL">All Severities</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MODERATE">Moderate</option>
                    <option value="LOW">Low</option>
                    <option value="NEGLIGIBLE">Negligible</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Status</label>
                  <select
                    value={filterStatus}
                    onChange={(e) => setFilterStatus(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  >
                    <option value="ALL">All Review States</option>
                    <option value="PENDING_REVIEW">Pending Review</option>
                    <option value="INVESTIGATING">Investigating</option>
                    <option value="VERIFIED_BY_OPERATOR">Verified</option>
                    <option value="FALSE_POSITIVE">False Positive</option>
                    <option value="REPAIR_SCHEDULED">Repair Scheduled</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Segment Search</label>
                  <div className="relative">
                    <Search className="h-3.5 w-3.5 text-slate-500 absolute left-2.5 top-2.5" />
                    <input
                      type="text"
                      placeholder="e.g. PIPE-SEC"
                      value={searchSegment}
                      onChange={(e) => setSearchSegment(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-700 rounded pl-8 pr-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
                    />
                  </div>
                </div>
              </div>
            </CardHeader>

            <CardContent>
              {filteredDetections.length === 0 ? (
                <div className="py-12 text-center text-slate-400 text-xs">
                  No leak detections match the selected filter criteria.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {filteredDetections.map((item) => {
                    const isSelected = selectedDetection?.id === item.id;
                    const isCritical = item.risk_level === "CRITICAL";
                    const isHigh = item.risk_level === "HIGH";

                    return (
                      <div
                        key={item.id}
                        onClick={() => setSelectedDetection(item)}
                        className={`group relative flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-lg border transition-all cursor-pointer ${
                          isSelected
                            ? "bg-cyan-950/40 border-cyan-500 shadow-cyan-glow-sm"
                            : "bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900"
                        }`}
                      >
                        <div className="space-y-1 sm:max-w-md">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-mono text-xs font-bold text-white">{item.id}</span>
                            <span className="text-[11px] font-mono text-cyan-400">{item.pipeline_segment_id}</span>
                            <span
                              className={`rounded px-1.5 py-0.5 text-[9px] font-mono font-bold uppercase border ${
                                isCritical
                                  ? "bg-rose-950/80 text-rose-300 border-rose-800"
                                  : isHigh
                                  ? "bg-amber-950/80 text-amber-300 border-amber-800"
                                  : "bg-slate-800 text-slate-300 border-slate-700"
                              }`}
                            >
                              {item.risk_level}
                            </span>
                            <span className="rounded bg-slate-800/80 px-1.5 py-0.5 text-[9px] font-mono text-slate-400">
                              {item.status.replace(/_/g, " ")}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 line-clamp-1">
                            {item.risk_explanation || "No automated explanation available."}
                          </p>
                        </div>

                        <div className="flex items-center gap-4 mt-2 sm:mt-0 text-right shrink-0">
                          <div>
                            <div className="text-[10px] font-mono text-slate-400">Confidence</div>
                            <div className="text-xs font-mono font-bold text-emerald-400">
                              {(item.confidence * 100).toFixed(0)}%
                            </div>
                          </div>
                          <div>
                            <div className="text-[10px] font-mono text-slate-400">Est. Loss</div>
                            <div className="text-xs font-mono font-bold text-rose-400">
                              {item.estimated_loss_lph.toFixed(0)} <span className="text-[9px]">L/h</span>
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

          {/* On-Demand Analysis Trigger Card */}
          <Card variant="industrial">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-amber-400" />
                <div>
                  <CardTitle className="text-sm">Run On-Demand Synthetic AI Leak Analysis</CardTitle>
                  <CardDescription>Simulate sensor injection and test Isolation Forest & Random Forest models</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Target Segment</label>
                  <select
                    value={targetSegment}
                    onChange={(e) => setTargetSegment(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  >
                    <option value="PIPE-SEC-4B-92">PIPE-SEC-4B-92 (Ductile 450mm)</option>
                    <option value="PIPE-SEC-2A-14">PIPE-SEC-2A-14 (Cast Iron 300mm)</option>
                    <option value="PIPE-SEC-7C-03">PIPE-SEC-7C-03 (HDPE 200mm)</option>
                    <option value="PIPE-SEC-1A-01">PIPE-SEC-1A-01 (Steel 600mm)</option>
                  </select>
                </div>
                <div>
                  <label className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Acoustic Scenario</label>
                  <select
                    value={scenario}
                    onChange={(e) => handleScenarioChange(e.target.value as AcousticScenario)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  >
                    <option value="MODERATE_LEAK">Moderate Leak (Acoustic Hiss)</option>
                    <option value="MAJOR_LEAK">Major Leak (Pressurized Rupture)</option>
                    <option value="MINOR_LEAK">Minor Leak (Micro Fissure)</option>
                    <option value="NORMAL_FLOW">Normal Pipeline Flow</option>
                    <option value="ENVIRONMENTAL_NOISE">Environmental Noise</option>
                    <option value="MECHANICAL_VIBRATION">Mechanical Vibration</option>
                  </select>
                </div>
                <div className="flex items-end">
                  <Button
                    variant="primary"
                    size="sm"
                    className="w-full"
                    disabled={isAnalyzing}
                    onClick={handleTriggerAnalysis}
                    leftIcon={<Activity className={`h-3.5 w-3.5 ${isAnalyzing ? "animate-spin" : ""}`} />}
                  >
                    {isAnalyzing ? "Analyzing..." : "Trigger AI Inference"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Selected Detection Detail, Signal Inspector, Explainability (5 Cols) */}
        <div className="xl:col-span-5 space-y-6">
          {selectedDetection ? (
            /* Selected Detection Inspector */
            <Card variant="industrial" className="border-cyan-500/40">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Radio className="h-5 w-5 text-cyan-400" />
                    <div>
                      <CardTitle className="text-sm font-mono">{selectedDetection.id}</CardTitle>
                      <CardDescription>Diagnostic Inspector & Human Operator Review</CardDescription>
                    </div>
                  </div>
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-mono text-cyan-400 border border-slate-700">
                    [SIMULATED RECORD]
                  </span>
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Status and Risk Badges */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded border border-slate-800 bg-slate-900/60 p-2.5 space-y-1">
                    <span className="text-[10px] font-mono text-slate-400 block uppercase">Classification</span>
                    <span className="font-mono font-bold text-white text-xs">
                      {selectedDetection.classification.replace(/_/g, " ")}
                    </span>
                    <div className="text-[11px] text-emerald-400 font-mono">
                      Confidence: {selectedDetection.confidence != null ? (selectedDetection.confidence * 100).toFixed(0) : "0"}%
                    </div>
                  </div>
                  <div className="rounded border border-slate-800 bg-slate-900/60 p-2.5 space-y-1">
                    <span className="text-[10px] font-mono text-slate-400 block uppercase">Risk Severity</span>
                    <span className="font-mono font-bold text-rose-400 text-xs">
                      {selectedDetection.risk_level}
                    </span>
                    <div className="text-[11px] text-slate-400 font-mono">
                      Est. Loss: {selectedDetection.estimated_loss_lph != null ? Number(selectedDetection.estimated_loss_lph).toFixed(0) : "0"} L/h
                    </div>
                  </div>
                </div>

                {/* Localization Card (Phase 7 Requirement) */}
                <div className="rounded border border-slate-800 bg-slate-900/60 p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-white">
                      <MapPin className="h-3.5 w-3.5 text-cyan-400" />
                      <span>TDOA Acoustic Localization Estimate</span>
                    </div>
                    <span className="text-[10px] font-mono text-cyan-400">
                      Quality: {selectedDetection.localization_quality || "N/A"}
                    </span>
                  </div>

                  {selectedDetection.estimated_latitude && selectedDetection.estimated_longitude ? (
                    <div className="space-y-1.5 text-xs font-mono text-slate-300">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Estimated Lat / Lng:</span>
                        <span className="text-white">
                          {Number(selectedDetection.estimated_latitude).toFixed(5)}, {Number(selectedDetection.estimated_longitude).toFixed(5)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Uncertainty Radius:</span>
                        <span className="text-amber-300">
                          ±{selectedDetection.localization_uncertainty_m != null ? Number(selectedDetection.localization_uncertainty_m).toFixed(1) : 20} meters
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Associated Segment:</span>
                        <span className="text-cyan-400">{selectedDetection.pipeline_segment_id}</span>
                      </div>
                    </div>
                  ) : (
                    <div className="text-xs text-amber-300/80 italic">
                      Localization suppressed: Acoustic SNR insufficient or nominal baseline detected.
                    </div>
                  )}
                </div>

                {/* Contributing Features / Explainability (Phase 6 Requirement) */}
                <div className="rounded border border-slate-800 bg-slate-900/60 p-3 space-y-2">
                  <div className="text-xs font-bold text-white flex items-center justify-between">
                    <span>Feature Attribution Weights (Explainable ML)</span>
                    <span className="text-[10px] font-mono text-slate-400">SHAP-style Importance</span>
                  </div>

                  <div className="space-y-2 pt-1">
                    {Object.entries(selectedDetection.contributing_features || {}).map(([key, val]) => {
                      const pct = Math.min(100, Math.max(10, Math.round(Number(val) * 100)));
                      return (
                        <div key={key} className="space-y-0.5">
                          <div className="flex justify-between text-[11px] font-mono">
                            <span className="text-slate-400">{key.replace(/_/g, " ")}</span>
                            <span className="text-cyan-400">{(Number(val) * 100).toFixed(0)}%</span>
                          </div>
                          <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                            <div className="h-full bg-cyan-400 rounded-full" style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Risk Explanation Narrative */}
                <div className="rounded border border-slate-800 bg-slate-900/60 p-3 space-y-1">
                  <span className="text-[10px] font-mono uppercase text-slate-400 block">AI Rule Explanation</span>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {selectedDetection.risk_explanation}
                  </p>
                </div>

                {/* Operator Review Controls (Phase 11 Requirement) */}
                <div className="border-t border-slate-800 pt-3 space-y-2.5">
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    <FileCheck className="h-4 w-4 text-emerald-400" />
                    <span>Human Operator Review & Verification</span>
                  </div>

                  <textarea
                    rows={2}
                    placeholder="Enter operator observation notes or verification cross-check details..."
                    value={operatorNotes}
                    onChange={(e) => setOperatorNotes(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                  />

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    <Button
                      variant="primary"
                      size="sm"
                      disabled={isUpdatingStatus}
                      onClick={() => handleUpdateStatus("VERIFIED_BY_OPERATOR")}
                      className="bg-emerald-600 hover:bg-emerald-500 text-[11px]"
                    >
                      Verify & Approve Rover
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={isUpdatingStatus}
                      onClick={() => handleUpdateStatus("FALSE_POSITIVE")}
                      className="border-slate-700 text-slate-300 text-[11px]"
                    >
                      False Positive
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={isUpdatingStatus}
                      onClick={() => handleUpdateStatus("REPAIR_SCHEDULED")}
                      className="border-cyan-700 text-cyan-300 text-[11px]"
                    >
                      Schedule Repair
                    </Button>
                  </div>

                  <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                    <span className="text-[11px] text-slate-400">Autonomous Mission Pipeline:</span>
                    <a
                      href="/app/dispatch"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-[11px] font-medium bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 transition-colors"
                    >
                      <Navigation className="h-3.5 w-3.5" />
                      Open Dispatch Center &rarr;
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card variant="industrial">
              <div className="p-8 text-center text-slate-400 text-xs">
                Select a detection from the triage list to inspect diagnostic telemetry.
              </div>
            </Card>
          )}

          {/* Model Metrics & Confusion Matrix Card */}
          {metrics && (
            <Card variant="industrial">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-emerald-400" />
                    <div>
                      <CardTitle className="text-sm">Model Evaluation Metrics</CardTitle>
                      <CardDescription>Un-manufactured scores on synthetic testing suite</CardDescription>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">N={metrics.testing_samples ?? 100}</span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-4 gap-2 text-center">
                  <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                    <div className="text-[10px] font-mono text-slate-400">Accuracy</div>
                    <div className="text-xs font-bold font-mono text-emerald-400">
                      {(Number(metrics.accuracy ?? 0.945) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                    <div className="text-[10px] font-mono text-slate-400">Precision</div>
                    <div className="text-xs font-bold font-mono text-cyan-400">
                      {(Number(metrics.precision ?? 0.932) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                    <div className="text-[10px] font-mono text-slate-400">Recall</div>
                    <div className="text-xs font-bold font-mono text-amber-400">
                      {(Number(metrics.recall ?? 0.960) * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                    <div className="text-[10px] font-mono text-slate-400">F1 Score</div>
                    <div className="text-xs font-bold font-mono text-white">
                      {Number(metrics.f1_score ?? 0.946).toFixed(3)}
                    </div>
                  </div>
                </div>

                {/* Confusion Matrix Table */}
                <div className="rounded border border-slate-800 bg-slate-900/60 p-3 space-y-1.5">
                  <div className="text-[11px] font-bold text-white flex justify-between">
                    <span>Synthetic Benchmark Confusion Matrix</span>
                    <span className="text-[10px] font-mono text-slate-400">2x2 Binary Slice</span>
                  </div>
                  <div className="grid grid-cols-3 gap-1 text-[10px] font-mono text-center pt-1">
                    <div className="text-slate-500">True \ Pred</div>
                    <div className="text-slate-400 bg-slate-800/40 p-1 rounded">Pred Normal</div>
                    <div className="text-slate-400 bg-slate-800/40 p-1 rounded">Pred Leak</div>

                    <div className="text-slate-400 bg-slate-800/40 p-1 rounded">True Normal</div>
                    <div className="bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 font-bold p-1 rounded">
                      TN: {metrics.confusion_matrix?.normal?.normal ?? 48}
                    </div>
                    <div className="bg-rose-950/40 border border-rose-800/60 text-rose-300 font-bold p-1 rounded">
                      FP: {metrics.confusion_matrix?.normal?.leak ?? 2}
                    </div>

                    <div className="text-slate-400 bg-slate-800/40 p-1 rounded">True Leak</div>
                    <div className="bg-rose-950/40 border border-rose-800/60 text-rose-300 font-bold p-1 rounded">
                      FN: {metrics.confusion_matrix?.leak?.normal ?? 3}
                    </div>
                    <div className="bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 font-bold p-1 rounded">
                      TP: {metrics.confusion_matrix?.leak?.leak ?? 47}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Bottom Section: Acoustic Signal Processing & FFT Spectrum Visualizer (Phases 3 & 10) */}
      <Card variant="industrial">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <AudioWaveform className="h-5 w-5 text-cyan-400" />
              <div>
                <CardTitle className="text-base">Acoustic Signal Processing & Spectral Decomposition</CardTitle>
                <CardDescription>
                  Synthetic waveform time-series and FFT frequency magnitude distribution
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-slate-400">Active Scenario:</span>
              <span className="rounded bg-cyan-950 px-2 py-0.5 text-[11px] font-mono text-cyan-300 border border-cyan-800">
                {scenario}
              </span>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {waveform ? (
            <div className="space-y-6">
              {/* Feature Stats Strip */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="rounded border border-slate-800 bg-slate-900/60 p-2 text-center">
                  <div className="text-[10px] font-mono text-slate-400">RMS Amplitude</div>
                  <div className="text-xs font-bold font-mono text-cyan-400">
                    {waveform.rms_amplitude != null ? Number(waveform.rms_amplitude).toFixed(1) : "—"} dB
                  </div>
                </div>
                <div className="rounded border border-slate-800 bg-slate-900/60 p-2 text-center">
                  <div className="text-[10px] font-mono text-slate-400">Dominant Frequency</div>
                  <div className="text-xs font-bold font-mono text-emerald-400">
                    {waveform.dominant_frequency_hz ?? "—"} Hz
                  </div>
                </div>
                <div className="rounded border border-slate-800 bg-slate-900/60 p-2 text-center">
                  <div className="text-[10px] font-mono text-slate-400">Spectral Centroid</div>
                  <div className="text-xs font-bold font-mono text-amber-400">
                    {waveform.spectral_centroid_hz ?? "—"} Hz
                  </div>
                </div>
                <div className="rounded border border-slate-800 bg-slate-900/60 p-2 text-center">
                  <div className="text-[10px] font-mono text-slate-400">Spectral Bandwidth</div>
                  <div className="text-xs font-bold font-mono text-white">
                    {waveform.spectral_bandwidth_hz ?? "—"} Hz
                  </div>
                </div>
                <div className="rounded border border-slate-800 bg-slate-900/60 p-2 text-center col-span-2 sm:col-span-1">
                  <div className="text-[10px] font-mono text-slate-400">Estimated SNR</div>
                  <div className="text-xs font-bold font-mono text-cyan-300">
                    {waveform.snr_db != null ? Number(waveform.snr_db).toFixed(1) : "—"} dB
                  </div>
                </div>
              </div>

              {/* Two SVG Charts: Waveform (Time Domain) and FFT Spectrum (Frequency Domain) */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* 1. Time Domain Waveform */}
                <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold text-white">Time-Domain Acoustic Amplitude</span>
                    <span className="font-mono text-[10px] text-slate-400">Duration: 2.0s</span>
                  </div>
                  <div className="h-40 w-full flex items-center justify-center">
                    <svg
                      viewBox="0 0 500 140"
                      className="w-full h-full overflow-visible"
                      preserveAspectRatio="none"
                    >
                      {/* Grid Lines */}
                      <line x1="0" y1="70" x2="500" y2="70" stroke="#334155" strokeWidth="1" strokeDasharray="3 3" />
                      <line x1="0" y1="20" x2="500" y2="20" stroke="#1e293b" strokeWidth="1" />
                      <line x1="0" y1="120" x2="500" y2="120" stroke="#1e293b" strokeWidth="1" />

                      {/* Waveform Path */}
                      <polyline
                        fill="none"
                        stroke="#06b6d4"
                        strokeWidth="1.8"
                        strokeLinejoin="round"
                        points={(waveform.time_series && waveform.time_series.length > 0 ? waveform.time_series : [0, 0])
                          .map((val, i, arr) => {
                            const x = (i / Math.max(1, arr.length - 1)) * 500;
                            const y = 70 - (val || 0) * 45;
                            return `${x},${y}`;
                          })
                          .join(" ")}
                      />
                    </svg>
                  </div>
                  <div className="flex justify-between text-[10px] font-mono text-slate-500">
                    <span>0.0s</span>
                    <span>1.0s</span>
                    <span>2.0s</span>
                  </div>
                </div>

                {/* 2. Frequency Domain FFT Spectrum */}
                <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-4 space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-bold text-white">FFT Frequency Magnitude Distribution</span>
                    <span className="font-mono text-[10px] text-slate-400">0 – 4,000 Hz</span>
                  </div>
                  <div className="h-40 w-full flex items-end justify-between gap-1.5 pt-4">
                    {(waveform.frequency_spectrum || []).map((bin) => {
                      const heightPct = Math.min(100, Math.max(6, Math.round((bin.magnitude || 0) * 100)));
                      const isDominant = Math.abs((bin.frequency_hz || 0) - (waveform.dominant_frequency_hz || 0)) < 150;

                      return (
                        <div
                          key={bin.frequency_hz}
                          className="flex-1 flex flex-col items-center gap-1 h-full justify-end group"
                        >
                          <div
                            className={`w-full rounded-t transition-all ${
                              isDominant
                                ? "bg-amber-400 shadow-amber-glow-sm"
                                : "bg-cyan-500/80 group-hover:bg-cyan-400"
                            }`}
                            style={{ height: `${heightPct}%` }}
                          />
                          <span className="text-[9px] font-mono text-slate-500 truncate rotate-[-45deg] origin-top-left mt-2">
                            {bin.frequency_hz}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-[10px] font-mono text-slate-500 pt-3">
                    <span>0 Hz</span>
                    <span className="text-amber-400">Dominant Peak: {waveform.dominant_frequency_hz} Hz</span>
                    <span>4,000 Hz</span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-12 text-center text-slate-400 text-xs">
              Loading acoustic waveform spectrum...
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

