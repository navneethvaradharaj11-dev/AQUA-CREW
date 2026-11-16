"use client";

import React, { useState, useEffect } from "react";
import {
  PipelineHealth,
  PredictiveRisk,
  HistoricalTrend,
  MaintenanceRecommendation,
  PredictiveMaintenanceOverview,
} from "@/services/api/maintenanceTypes";
import { backendApiClient } from "@/services/api/backendApiClient";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import {
  Wrench,
  ShieldAlert,
  Activity,
  AlertTriangle,
  TrendingDown,
  TrendingUp,
  Clock,
  Send,
  CheckCircle2,
  XCircle,
  Search,
  Filter,
  Layers,
  Sparkles,
  RefreshCw,
  Sliders,
  ChevronRight,
  Droplets,
  Radio,
  FileText,
  Navigation,
  Compass,
} from "lucide-react";

export function PredictiveMaintenanceView() {
  const [overview, setOverview] = useState<PredictiveMaintenanceOverview | null>(null);
  const [healthList, setHealthList] = useState<PipelineHealth[]>([]);
  const [predictions, setPredictions] = useState<PredictiveRisk[]>([]);
  const [recommendations, setRecommendations] = useState<MaintenanceRecommendation[]>([]);
  const [selectedSegmentId, setSelectedSegmentId] = useState<string>("PIPE-SEC-4B-92");
  const [selectedHealth, setSelectedHealth] = useState<PipelineHealth | null>(null);
  const [selectedPrediction, setSelectedPrediction] = useState<PredictiveRisk | null>(null);
  const [selectedTrend, setSelectedTrend] = useState<HistoricalTrend | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Filters
  const [filterCategory, setFilterCategory] = useState<string>("ALL");
  const [filterUrgency, setFilterUrgency] = useState<string>("ALL");
  const [searchSegment, setSearchSegment] = useState<string>("");

  // Review & Dispatch State
  const [isReviewing, setIsReviewing] = useState<boolean>(false);
  const [operatorNotes, setOperatorNotes] = useState<string>("");
  const [actionSuccessMessage, setActionSuccessMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [ov, hl, pr, rc] = await Promise.all([
        backendApiClient.getMaintenanceOverview(),
        backendApiClient.getHealthAssessments(),
        backendApiClient.getPredictions(),
        backendApiClient.getMaintenanceRecommendations(),
      ]);
      setOverview(ov);
      setHealthList(hl);
      setPredictions(pr);
      setRecommendations(rc);

      const targetId = selectedSegmentId || (hl[0]?.pipeline_segment_id ?? "PIPE-SEC-4B-92");
      setSelectedSegmentId(targetId);

      const [h, p, tr] = await Promise.all([
        backendApiClient.getSegmentHealth(targetId),
        backendApiClient.getSegmentPrediction(targetId),
        backendApiClient.getTrends(targetId),
      ]);
      setSelectedHealth(h);
      setSelectedPrediction(p);
      setSelectedTrend(tr[0] || null);
    } catch (err) {
      console.error("Failed to load predictive maintenance data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectSegment = async (segId: string) => {
    setSelectedSegmentId(segId);
    try {
      const [h, p, tr] = await Promise.all([
        backendApiClient.getSegmentHealth(segId),
        backendApiClient.getSegmentPrediction(segId),
        backendApiClient.getTrends(segId),
      ]);
      setSelectedHealth(h);
      setSelectedPrediction(p);
      setSelectedTrend(tr[0] || null);
    } catch (err) {
      console.error(`Failed to fetch segment ${segId} metrics:`, err);
    }
  };

  const handleReviewAction = async (
    recId: string,
    action: "ACKNOWLEDGE" | "DISMISS" | "DISPATCH"
  ) => {
    setIsReviewing(true);
    setActionSuccessMessage(null);
    try {
      const updated = await backendApiClient.reviewMaintenanceRecommendation(
        recId,
        action,
        "OPERATOR_CHIEF",
        operatorNotes || undefined
      );
      setRecommendations((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
      if (action === "DISPATCH") {
        setActionSuccessMessage(
          `Success: Recommendation ${recId} sent to Task 08 Autonomous Dispatch Center! Mission proposal generated (${updated.dispatched_mission_id || "REC-2026-..."}).`
        );
      } else {
        setActionSuccessMessage(`Recommendation ${recId} status updated to ${action}.`);
      }
      setOperatorNotes("");
    } catch (err: any) {
      alert(`Action failed: ${err.message || err}`);
    } finally {
      setIsReviewing(false);
    }
  };

  // Filtered segments
  const filteredHealthList = healthList.filter((h) => {
    if (filterCategory !== "ALL" && h.health_category !== filterCategory) return false;
    if (searchSegment && !h.pipeline_segment_id.toLowerCase().includes(searchSegment.toLowerCase()))
      return false;
    return true;
  });

  const getHealthColor = (cat: string) => {
    switch (cat) {
      case "EXCELLENT":
        return "text-emerald-400 bg-emerald-950/60 border-emerald-800";
      case "GOOD":
        return "text-cyan-400 bg-cyan-950/60 border-cyan-800";
      case "FAIR":
        return "text-amber-400 bg-amber-950/60 border-amber-800";
      case "POOR":
        return "text-orange-400 bg-orange-950/60 border-orange-800";
      case "CRITICAL":
        return "text-rose-400 bg-rose-950/60 border-rose-800";
      default:
        return "text-slate-400 bg-slate-900 border-slate-700";
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return "text-rose-400 bg-rose-950/80 border-rose-700 animate-pulse";
      case "HIGH":
        return "text-orange-400 bg-orange-950/80 border-orange-700";
      case "MODERATE":
        return "text-amber-400 bg-amber-950/80 border-amber-700";
      case "LOW":
        return "text-emerald-400 bg-emerald-950/80 border-emerald-700";
      default:
        return "text-slate-400 bg-slate-900 border-slate-700";
    }
  };

  return (
    <div className="space-y-6 text-slate-100">
      {/* Simulation Provenance Banner */}
      <div className="rounded-lg border border-amber-800/80 bg-amber-950/30 p-4 text-amber-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm text-white">
                  PREDICTIVE MAINTENANCE & INFRASTRUCTURE HEALTH PLATFORM (TASK 09)
                </span>
                <span className="rounded bg-amber-900/60 px-2 py-0.5 text-[10px] font-mono text-amber-300 border border-amber-700">
                  MODEL v1.0.0-RF-GRADIENT
                </span>
              </div>
              <p className="text-xs text-amber-300/80 leading-relaxed">
                Aggregates historical time-series sensor telemetry, calculates multi-criteria pipeline health indices (0–100),
                forecasts multi-horizon failure probabilities (24h, 7d, 30d), and links directly to Task 08 Autonomous Dispatch with Human Operator governance.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadData}
              disabled={isLoading}
              className="border-amber-700 text-amber-200 hover:bg-amber-900/40 text-xs shrink-0"
            >
              <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
              Refresh Data
            </Button>
            <a
              href="/app/dispatch"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 transition-colors"
            >
              <Navigation className="h-3.5 w-3.5" />
              Dispatch Center &rarr;
            </a>
          </div>
        </div>
      </div>

      {actionSuccessMessage && (
        <div className="rounded-lg border border-emerald-700/80 bg-emerald-950/40 p-3 text-xs text-emerald-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>{actionSuccessMessage}</span>
          </div>
          <a
            href="/app/dispatch"
            className="text-[11px] underline text-cyan-300 hover:text-cyan-200 font-mono"
          >
            Open Dispatch &rarr;
          </a>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SECTION A: INFRASTRUCTURE HEALTH OVERVIEW                                 */}
      {/* ========================================================================= */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard
          label="Total Monitored"
          value={overview?.total_segments_monitored ?? 8}
          unit="Segments"
          tone="slate"
        />
        <MetricCard
          label="Network Avg Health"
          value={`${overview?.average_health_score ?? 81.4}`}
          unit="/ 100"
          tone="cyan"
        />
        <MetricCard
          label="Excellent (90-100)"
          value={overview?.excellent_count ?? 3}
          unit="Pipes"
          tone="emerald"
        />
        <MetricCard
          label="Good (75-89)"
          value={overview?.good_count ?? 3}
          unit="Pipes"
          tone="cyan"
        />
        <MetricCard
          label="Fair (50-74)"
          value={overview?.fair_count ?? 1}
          unit="Pipes"
          tone="amber"
        />
        <MetricCard
          label="High Risk (Poor/Crit)"
          value={overview?.high_risk_segment_count ?? 1}
          unit="Alert"
          tone={overview?.high_risk_segment_count ? "rose" : "slate"}
        />
      </div>

      {/* Main Grid: Left Column (Map & Segment List), Right Column (Risk & Inspector) */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* ======================================================================= */}
        {/* SECTION B: PIPELINE HEALTH MAP & SEGMENT LIST (5 COLS)                  */}
        {/* ======================================================================= */}
        <div className="xl:col-span-5 space-y-6">
          <Card variant="industrial">
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Layers className="h-4 w-4 text-cyan-400" />
                  <CardTitle className="text-sm">Metropolitan Pipeline Health Map</CardTitle>
                </div>
                <span className="text-[10px] font-mono text-slate-400">GIS SECTOR MONITORING</span>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* GIS Vector Map Visualizer */}
              <div className="relative h-60 w-full rounded-lg bg-slate-950 border border-slate-800 p-2 overflow-hidden flex flex-col justify-between">
                <div className="absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(#06b6d4_1px,transparent_1px)] [background-size:16px_16px]" />
                <svg className="w-full h-full" viewBox="0 0 500 240">
                  {/* Grid Lines */}
                  <line x1="20" y1="60" x2="480" y2="60" stroke="#1e293b" strokeDasharray="4,4" />
                  <line x1="20" y1="120" x2="480" y2="120" stroke="#1e293b" strokeDasharray="4,4" />
                  <line x1="20" y1="180" x2="480" y2="180" stroke="#1e293b" strokeDasharray="4,4" />

                  {/* Trunk Line B (Stressed Segment: PIPE-SEC-4B-92) */}
                  <path
                    d="M 60 180 L 140 140 L 250 110 L 360 85 L 440 60"
                    fill="none"
                    stroke={selectedSegmentId === "PIPE-SEC-4B-92" ? "#f43f5e" : "#fb923c"}
                    strokeWidth={selectedSegmentId === "PIPE-SEC-4B-92" ? "5" : "3"}
                    className="cursor-pointer transition-all hover:stroke-rose-400"
                    onClick={() => handleSelectSegment("PIPE-SEC-4B-92")}
                  />
                  {/* Spine Trunk Line A (PIPE-SEC-4A-10) */}
                  <path
                    d="M 250 20 L 250 110 L 250 220"
                    fill="none"
                    stroke={selectedSegmentId === "PIPE-SEC-4A-10" ? "#06b6d4" : "#10b981"}
                    strokeWidth={selectedSegmentId === "PIPE-SEC-4A-10" ? "5" : "3"}
                    className="cursor-pointer transition-all hover:stroke-cyan-400"
                    onClick={() => handleSelectSegment("PIPE-SEC-4A-10")}
                  />
                  {/* Industrial Feeder (PIPE-IND-1A-04) */}
                  <path
                    d="M 250 110 L 320 160 L 410 190"
                    fill="none"
                    stroke={selectedSegmentId === "PIPE-IND-1A-04" ? "#10b981" : "#34d399"}
                    strokeWidth={selectedSegmentId === "PIPE-IND-1A-04" ? "5" : "3"}
                    className="cursor-pointer transition-all hover:stroke-emerald-400"
                    onClick={() => handleSelectSegment("PIPE-IND-1A-04")}
                  />

                  {/* Junction Node */}
                  <circle cx="250" cy="110" r="6" fill="#38bdf8" stroke="#0284c7" strokeWidth="2" />
                  <text x="260" y="105" fill="#94a3b8" fontSize="9" fontFamily="monospace">J-CENTRAL</text>

                  {/* Micro-fissure alert marker on PIPE-SEC-4B-92 */}
                  <circle cx="195" cy="125" r="5" fill="#f43f5e" className="animate-ping" />
                  <circle cx="195" cy="125" r="4" fill="#f43f5e" />
                  <text x="140" y="115" fill="#f43f5e" fontSize="9" fontWeight="bold">RISK: 48% 24h</text>
                </svg>

                <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono bg-slate-900/80 px-2 py-1 rounded">
                  <span>CLICK SEGMENT TO INSPECT</span>
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-400" /> Excellent</span>
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-cyan-400" /> Good</span>
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-orange-400" /> Poor</span>
                    <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-rose-400" /> Critical</span>
                  </div>
                </div>
              </div>

              {/* Filters & Search */}
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="text"
                  placeholder="Search segment..."
                  value={searchSegment}
                  onChange={(e) => setSearchSegment(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
                />
                <select
                  value={filterCategory}
                  onChange={(e) => setFilterCategory(e.target.value)}
                  className="bg-slate-900 border border-slate-700 rounded px-2 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                >
                  <option value="ALL">All Categories</option>
                  <option value="EXCELLENT">Excellent</option>
                  <option value="GOOD">Good</option>
                  <option value="FAIR">Fair</option>
                  <option value="POOR">Poor</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </div>

              {/* Segment List */}
              <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {filteredHealthList.map((h) => {
                  const isSelected = h.pipeline_segment_id === selectedSegmentId;
                  return (
                    <div
                      key={h.id}
                      onClick={() => handleSelectSegment(h.pipeline_segment_id)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all flex items-center justify-between ${
                        isSelected
                          ? "bg-slate-800/90 border-cyan-500 shadow-cyan-glow-sm"
                          : "bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40"
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-white">
                            {h.pipeline_segment_id}
                          </span>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-mono border ${getHealthColor(
                              h.health_category
                            )}`}
                          >
                            {h.health_category}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400 line-clamp-1">
                          {h.explanation}
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-base font-bold font-mono text-white">
                          {h.health_score.toFixed(0)}
                          <span className="text-[10px] text-slate-400">/100</span>
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          Cov: {h.data_coverage_pct.toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* ===================================================================== */}
          {/* SECTION D: HISTORICAL TREND ANALYSIS (TIME-SERIES)                    */}
          {/* ===================================================================== */}
          <Card variant="industrial">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-cyan-400" />
                  <CardTitle className="text-sm">Temporal Trend & Degradation Velocity</CardTitle>
                </div>
                {selectedTrend && (
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      selectedTrend.trend_direction.includes("DETERIORATING")
                        ? "bg-rose-950 text-rose-300 border border-rose-800 animate-pulse"
                        : "bg-emerald-950 text-emerald-300 border border-emerald-800"
                    }`}
                  >
                    {selectedTrend.trend_direction}
                  </span>
                )}
              </div>
              <CardDescription>
                Ordinary least squares regression over 30-day time-series window
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {selectedTrend && selectedTrend.time_series_points.length > 0 ? (
                <>
                  <div className="h-32 w-full bg-slate-950 rounded border border-slate-800 p-2 flex flex-col justify-between">
                    <svg className="w-full h-full" viewBox="0 0 400 100">
                      {/* Trend Polyline */}
                      <polyline
                        fill="none"
                        stroke="#06b6d4"
                        strokeWidth="2.5"
                        points={selectedTrend.time_series_points
                          .map((pt, idx) => {
                            const x = (idx / (selectedTrend.time_series_points.length - 1)) * 380 + 10;
                            const y = 90 - (pt.health_score / 100) * 80;
                            return `${x},${y}`;
                          })
                          .join(" ")}
                      />
                      {/* Checkpoint dots */}
                      {selectedTrend.time_series_points.map((pt, idx) => {
                        const x = (idx / (selectedTrend.time_series_points.length - 1)) * 380 + 10;
                        const y = 90 - (pt.health_score / 100) * 80;
                        return (
                          <circle
                            key={idx}
                            cx={x}
                            cy={y}
                            r="3"
                            fill={pt.health_score < 50 ? "#f43f5e" : "#06b6d4"}
                          />
                        );
                      })}
                    </svg>
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
                      <span>-30 DAYS</span>
                      <span>SLOPE: {selectedTrend.health_slope_per_day} pts/day</span>
                      <span>TODAY</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
                    <div className="p-2 rounded bg-slate-900 border border-slate-800">
                      <div className="text-[10px] text-slate-400">PRESSURE VAR</div>
                      <div className="font-bold text-white">{selectedTrend.pressure_variance} bar²</div>
                    </div>
                    <div className="p-2 rounded bg-slate-900 border border-slate-800">
                      <div className="text-[10px] text-slate-400">ACOUSTIC SPIKES</div>
                      <div className="font-bold text-white">{selectedTrend.acoustic_emission_count} Events</div>
                    </div>
                    <div className="p-2 rounded bg-slate-900 border border-slate-800">
                      <div className="text-[10px] text-slate-400">HISTORIC LEAKS</div>
                      <div className="font-bold text-white">{selectedTrend.historical_leak_count} Logged</div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="p-4 text-center text-slate-500 text-xs">
                  Select a pipeline segment to view 30-day degradation slope.
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* ======================================================================= */}
        {/* RIGHT COLUMN: PREDICTIVE RISK, INSPECTOR & RECOMMENDATIONS (7 COLS)     */}
        {/* ======================================================================= */}
        <div className="xl:col-span-7 space-y-6">
          {/* ===================================================================== */}
          {/* SECTION C & F: PREDICTIVE RISK & SEGMENT DEEP-DIVE                    */}
          {/* ===================================================================== */}
          <Card variant="industrial">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-cyan-400" />
                    Segment Health & Multi-Horizon Failure Risk
                  </CardTitle>
                  <CardDescription>
                    Inspecting {selectedSegmentId} with calibrated failure forecasting
                  </CardDescription>
                </div>
                {selectedPrediction && (
                  <span
                    className={`px-2.5 py-1 rounded text-xs font-mono font-bold border ${getRiskColor(
                      selectedPrediction.overall_risk_level
                    )}`}
                  >
                    {selectedPrediction.overall_risk_level} RISK
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Multi-Horizon Risk Probabilities */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">24-Hour Horizon</div>
                  <div className="text-2xl font-bold font-mono text-white">
                    {selectedPrediction ? (selectedPrediction.failure_prob_24h * 100).toFixed(1) : 0}%
                  </div>
                  <div className="text-[10px] text-slate-400">Acute transient / rupture risk</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">7-Day Horizon</div>
                  <div className="text-2xl font-bold font-mono text-cyan-400">
                    {selectedPrediction ? (selectedPrediction.failure_prob_7d * 100).toFixed(1) : 0}%
                  </div>
                  <div className="text-[10px] text-slate-400">Cumulative acoustic degradation</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                  <div className="text-[10px] font-mono text-slate-400 uppercase">30-Day Horizon</div>
                  <div className="text-2xl font-bold font-mono text-amber-400">
                    {selectedPrediction ? (selectedPrediction.failure_prob_30d * 100).toFixed(1) : 0}%
                  </div>
                  <div className="text-[10px] text-slate-400">Long-term structural fatigue</div>
                </div>
              </div>

              {/* Subsystem Stability Scores */}
              {selectedHealth && (
                <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 space-y-3">
                  <div className="text-xs font-mono uppercase font-bold text-slate-300">
                    Hydraulic Subsystem Stability Scores
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                    <div>
                      <span className="text-slate-400 block text-[10px]">Acoustic</span>
                      <span className="text-white font-bold">{selectedHealth.acoustic_stability_score}%</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Pressure</span>
                      <span className="text-white font-bold">{selectedHealth.pressure_stability_score}%</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Flow Balance</span>
                      <span className="text-white font-bold">{selectedHealth.flow_stability_score}%</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[10px]">Soil Moisture</span>
                      <span className="text-white font-bold">{selectedHealth.moisture_anomaly_score}%</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed pt-1 border-t border-slate-800">
                    {selectedHealth.explanation}
                  </p>
                </div>
              )}

              {/* Contributing Risk Factors & Positive Indicators */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded bg-slate-900/50 border border-slate-800 space-y-1.5">
                  <span className="text-[10px] font-mono uppercase text-rose-400 font-bold flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3" /> Contributing Risk Deductions
                  </span>
                  {selectedHealth && Object.keys(selectedHealth.contributing_factors).length > 0 ? (
                    <ul className="space-y-1 text-slate-300 text-[11px]">
                      {Object.entries(selectedHealth.contributing_factors).map(([k, v]) => (
                        <li key={k} className="flex justify-between font-mono">
                          <span>{k.replace(/_/g, " ")}:</span>
                          <span className="text-rose-400">-{v.toFixed(0)} pts</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <span className="text-slate-500 text-[11px]">No active risk penalties</span>
                  )}
                </div>

                <div className="p-3 rounded bg-slate-900/50 border border-slate-800 space-y-1.5">
                  <span className="text-[10px] font-mono uppercase text-emerald-400 font-bold flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" /> Positive Condition Indicators
                  </span>
                  {selectedHealth && selectedHealth.positive_indicators.length > 0 ? (
                    <ul className="space-y-1 text-slate-300 text-[11px]">
                      {selectedHealth.positive_indicators.map((ind, i) => (
                        <li key={i} className="flex items-center gap-1.5">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                          <span>{ind}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <span className="text-slate-500 text-[11px]">No positive indicators recorded</span>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* ===================================================================== */}
          {/* SECTION E & G: MAINTENANCE RECOMMENDATIONS & DISPATCH INTEGRATION    */}
          {/* ===================================================================== */}
          <Card variant="industrial">
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Wrench className="h-4 w-4 text-cyan-400" />
                  <CardTitle className="text-base">Explainable Maintenance Recommendations</CardTitle>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={filterUrgency}
                    onChange={(e) => setFilterUrgency(e.target.value)}
                    className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
                  >
                    <option value="ALL">All Urgencies</option>
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="ROUTINE">Routine</option>
                  </select>
                </div>
              </div>
              <CardDescription>
                Operator review station: Acknowledge, dismiss, or dispatch autonomous rover inspection
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                {recommendations
                  .filter((r) => filterUrgency === "ALL" || r.urgency === filterUrgency)
                  .map((rec) => (
                    <div
                      key={rec.id}
                      className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-3"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-xs font-bold text-white">{rec.id}</span>
                          <span className="font-mono text-xs text-slate-400">
                            [{rec.pipeline_segment_id}]
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                              rec.urgency === "CRITICAL"
                                ? "bg-rose-950 text-rose-300 border-rose-800 animate-pulse"
                                : rec.urgency === "HIGH"
                                ? "bg-orange-950 text-orange-300 border-orange-800"
                                : rec.urgency === "MEDIUM"
                                ? "bg-amber-950 text-amber-300 border-amber-800"
                                : "bg-slate-950 text-slate-300 border-slate-800"
                            }`}
                          >
                            {rec.urgency} URGENCY
                          </span>
                          <span className="rounded bg-cyan-950 px-2 py-0.5 text-[10px] font-mono text-cyan-300 border border-cyan-800">
                            ACTION: {rec.recommended_action.replace(/_/g, " ")}
                          </span>
                        </div>
                        <span className="text-xs font-mono text-slate-400">
                          Status: <strong className="text-white">{rec.status}</strong>
                        </span>
                      </div>

                      <p className="text-xs text-slate-300 leading-relaxed">{rec.explanation}</p>

                      {rec.dispatched_mission_id && (
                        <div className="p-2 rounded bg-cyan-950/60 border border-cyan-800 text-xs text-cyan-300 flex items-center justify-between font-mono">
                          <span>LINKED DISPATCH MISSION: {rec.dispatched_mission_id}</span>
                          <a
                            href="/app/dispatch"
                            className="underline text-white hover:text-cyan-200"
                          >
                            View in Dispatch &rarr;
                          </a>
                        </div>
                      )}

                      {/* Operator Action Bar */}
                      {rec.status === "PENDING_REVIEW" && (
                        <div className="pt-2 border-t border-slate-800 space-y-2">
                          <input
                            type="text"
                            placeholder="Operator verification notes (optional)..."
                            value={operatorNotes}
                            onChange={(e) => setOperatorNotes(e.target.value)}
                            className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
                          />
                          <div className="flex items-center gap-2">
                            <Button
                              variant="primary"
                              size="sm"
                              disabled={isReviewing}
                              onClick={() => handleReviewAction(rec.id, "DISPATCH")}
                              className="bg-cyan-600 hover:bg-cyan-500 text-xs font-medium"
                            >
                              <Navigation className="h-3 w-3 mr-1" />
                              Dispatch Rover Inspection
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={isReviewing}
                              onClick={() => handleReviewAction(rec.id, "ACKNOWLEDGE")}
                              className="border-slate-700 text-slate-300 text-xs"
                            >
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              Acknowledge
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={isReviewing}
                              onClick={() => handleReviewAction(rec.id, "DISMISS")}
                              className="border-slate-700 text-slate-400 text-xs"
                            >
                              <XCircle className="h-3 w-3 mr-1" />
                              Dismiss
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

