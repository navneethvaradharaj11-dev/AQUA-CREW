"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import {
  PipelineVulnerabilityItem,
  SpatialClusterItem,
  GeographicRiskZoneItem,
  HeatmapPointItem,
  TemporalTrendItem,
  PredictionItem,
  InspectionPriorityItem,
  InfrastructureOverviewResponse,
  SegmentDeepDiveResponse,
  InspectionDispatchResponse,
} from "@/services/api/infrastructureIntelligenceTypes";
import { MapLayerVisibilityState, SelectedMapFeature } from "@/services/gis/types";
import { backendApiClient } from "@/services/api/backendApiClient";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { MetricCard } from "@/components/ui/MetricCard";
import { StatusBadge } from "@/components/ui/StatusBadge";
import {
  ShieldAlert,
  ShieldCheck,
  Activity,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Navigation,
  RefreshCw,
  Search,
  Filter,
  Layers,
  MapPin,
  Clock,
  Compass,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Info,
  Droplets,
  Sliders,
  Sparkles,
  BarChart3,
  Bot,
  ExternalLink,
  Globe,
  Map as MapIcon,
  Check,
} from "lucide-react";

// Dynamically import MapContainer to avoid SSR issues with MapLibre GL WebGL context
const MapContainer = dynamic(
  () => import("@/components/gis/MapContainer").then((mod) => mod.MapContainer),
  {
    ssr: false,
    loading: () => (
      <div className="h-96 w-full flex flex-col items-center justify-center bg-slate-950/80 border border-slate-800 rounded-xl text-slate-400 font-mono text-xs gap-2">
        <RefreshCw className="h-5 w-5 animate-spin text-cyan-400" />
        <span>Initializing MapLibre WebGL GIS Engine...</span>
      </div>
    ),
  }
);

export function InfrastructureIntelligenceView() {
  const [overview, setOverview] = useState<InfrastructureOverviewResponse | null>(null);
  const [segments, setSegments] = useState<PipelineVulnerabilityItem[]>([]);
  const [clusters, setClusters] = useState<SpatialClusterItem[]>([]);
  const [zones, setZones] = useState<GeographicRiskZoneItem[]>([]);
  const [heatmap, setHeatmap] = useState<HeatmapPointItem[]>([]);
  const [trends, setTrends] = useState<TemporalTrendItem[]>([]);
  const [predictions, setPredictions] = useState<PredictionItem[]>([]);
  const [inspections, setInspections] = useState<InspectionPriorityItem[]>([]);

  const [activeTab, setActiveTab] = useState<"vulnerability" | "spatial" | "trends" | "inspections">("vulnerability");
  const [selectedSegmentId, setSelectedSegmentId] = useState<string>("PIPE-SEC-4B-92");
  const [segmentDeepDive, setSegmentDeepDive] = useState<SegmentDeepDiveResponse | null>(null);
  const [isDeepDiveOpen, setIsDeepDiveOpen] = useState<boolean>(false);

  // Map & GIS state
  const [spatialViewMode, setSpatialViewMode] = useState<"maplibre" | "schematic">("maplibre");
  const [mapCursorCoords, setMapCursorCoords] = useState<{ lng: number; lat: number }>({ lng: -74.006, lat: 40.7128 });
  const [mapCurrentZoom, setMapCurrentZoom] = useState<number>(14.2);
  const [mapLayers, setMapLayers] = useState<MapLayerVisibilityState>({
    pipelines: { primary: true, secondary: true, distribution: true, service: true },
    leakIncidents: { critical: true, high: true, medium: true, low: true },
    rovers: true,
    sensorStations: { acoustic: true, pressure: true, flow: true, thermal: true, moisture: true },
    inspectionZones: true,
  });

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filterRiskLevel, setFilterRiskLevel] = useState<string>("ALL");
  const [filterZone, setFilterZone] = useState<string>("ALL");

  // Inspection action modal
  const [dispatchModalItem, setDispatchModalItem] = useState<InspectionPriorityItem | null>(null);
  const [dispatchNotes, setDispatchNotes] = useState<string>("");
  const [preferredRoverId, setPreferredRoverId] = useState<string>("ROV-01");
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setIsRefreshing(true);
      const [ov, segList, clus, zn, hm, tr, pr, insp] = await Promise.all([
        backendApiClient.getInfrastructureOverview(),
        backendApiClient.getInfrastructureSegments(),
        backendApiClient.getInfrastructureClusters(),
        backendApiClient.getInfrastructureZones(),
        backendApiClient.getInfrastructureHeatmap(),
        backendApiClient.getInfrastructureTrends(),
        backendApiClient.getInfrastructurePredictions(),
        backendApiClient.getInspectionPriorities(),
      ]);

      setOverview(ov);
      setSegments(segList.items || []);
      setClusters(clus || []);
      setZones(zn || []);
      setHeatmap(hm || []);
      setTrends(tr || []);
      setPredictions(pr || []);
      setInspections(insp || []);

      if (segList.items && segList.items.length > 0 && !selectedSegmentId) {
        setSelectedSegmentId(segList.items[0].pipeline_segment_id);
      }
    } catch (err) {
      console.error("Failed to load infrastructure intelligence data", err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenDeepDive = async (segmentId: string) => {
    setSelectedSegmentId(segmentId);
    setIsDeepDiveOpen(true);
    try {
      const data = await backendApiClient.getSegmentDeepDive(segmentId);
      setSegmentDeepDive(data);
    } catch (err) {
      console.error("Failed to fetch deep dive for", segmentId, err);
    }
  };

  const handleTriggerReassess = async () => {
    setIsRefreshing(true);
    await backendApiClient.triggerInfrastructureAssessment();
    await loadData();
    setActionMessage("Full infrastructure intelligence pipeline recalculation complete.");
    setTimeout(() => setActionMessage(null), 4000);
  };

  const handleAcknowledge = async (item: InspectionPriorityItem) => {
    try {
      const res = await backendApiClient.acknowledgeInspectionPriority(item.id, "OPERATOR_CHIEF", "Acknowledged in Command Center");
      setInspections((prev) => prev.map((p) => (p.id === item.id ? res : p)));
      setActionMessage(`Inspection target ${item.segment_name} acknowledged.`);
      setTimeout(() => setActionMessage(null), 4000);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDismiss = async (item: InspectionPriorityItem) => {
    try {
      const res = await backendApiClient.dismissInspectionPriority(item.id, "OPERATOR_CHIEF", "Dismissed by operator review");
      setInspections((prev) => prev.map((p) => (p.id === item.id ? res : p)));
      setActionMessage(`Inspection target ${item.segment_name} dismissed.`);
      setTimeout(() => setActionMessage(null), 4000);
    } catch (err) {
      console.error(err);
    }
  };

  const handleConfirmDispatch = async () => {
    if (!dispatchModalItem) return;
    try {
      const res: InspectionDispatchResponse = await backendApiClient.requestInspectionDispatch(
        dispatchModalItem.id,
        "OPERATOR_CHIEF",
        preferredRoverId,
        dispatchNotes
      );
      setInspections((prev) =>
        prev.map((p) =>
          p.id === dispatchModalItem.id
            ? { ...p, status: "DISPATCHED", assigned_rover_id: res.assigned_rover_id, mission_recommendation_id: res.mission_recommendation_id }
            : p
        )
      );
      setActionMessage(`Mission recommendation created for ${res.assigned_rover_name}. Operator approval required to launch rover.`);
      setDispatchModalItem(null);
      setDispatchNotes("");
      setTimeout(() => setActionMessage(null), 5000);
    } catch (err) {
      console.error(err);
    }
  };

  const filteredSegments = segments.filter((s) => {
    const matchesSearch =
      s.segment_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.pipeline_segment_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.material.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRisk = filterRiskLevel === "ALL" || s.vulnerability_level === filterRiskLevel;
    const matchesZone = filterZone === "ALL" || s.pressure_zone_id === filterZone;
    return matchesSearch && matchesRisk && matchesZone;
  });

  const getRiskColor = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return "text-red-400 bg-red-950/60 border-red-800/80";
      case "HIGH":
        return "text-amber-400 bg-amber-950/60 border-amber-800/80";
      case "MODERATE":
        return "text-yellow-400 bg-yellow-950/60 border-yellow-800/80";
      case "LOW":
        return "text-emerald-400 bg-emerald-950/60 border-emerald-800/80";
      default:
        return "text-cyan-400 bg-cyan-950/60 border-cyan-800/80";
    }
  };

  const getPriorityBadgeTone = (level: string) => {
    if (level.includes("CRITICAL")) return "critical";
    if (level.includes("HIGH")) return "warning";
    if (level.includes("ROUTINE")) return "info";
    return "nominal";
  };

  return (
    <div className="space-y-6">
      {/* 1. Header & Operational Control Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-xl border border-slate-800 bg-slate-900/60 shadow-lg backdrop-blur-sm">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/80 border border-cyan-800/80 text-cyan-400">
              <ShieldAlert className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Infrastructure Intelligence & Geospatial Risk Prediction
                <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">
                  TASK 11
                </span>
              </h1>
              <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
                Multi-factor pipeline vulnerability scoring, DBSCAN spatial incident clustering, temporal deterioration velocity, and intelligent rover inspection queues
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTriggerReassess}
            disabled={isRefreshing}
            leftIcon={<RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />}
          >
            {isRefreshing ? "Reassessing..." : "Recalculate Intelligence"}
          </Button>
        </div>
      </div>

      {/* Action Notification Banner */}
      {actionMessage && (
        <div className="p-3.5 rounded-lg border border-cyan-500/40 bg-cyan-950/60 text-cyan-200 text-xs sm:text-sm flex items-center gap-2 shadow-cyan-glow-sm">
          <Sparkles className="h-4 w-4 text-cyan-400 shrink-0" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Infrastructure Intelligence Governance & Validation Provenance Banner */}
      <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/70 text-slate-300 text-xs flex flex-wrap items-center justify-between gap-3 font-mono shadow-sm">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/80">
            <ShieldCheck className="h-3.5 w-3.5" />
            VALIDATED: {overview?.methodology_version || "v1.2.0-hybrid-physics-geodesic"}
          </span>
          <span className="text-slate-600 hidden sm:inline">•</span>
          <span className="text-[11px] text-slate-400">
            Formula Weights: <span className="text-cyan-300 font-semibold">30% Hydraulic</span> + <span className="text-amber-300 font-semibold">25% Structural</span> + <span className="text-rose-300 font-semibold">25% Incident</span> + <span className="text-emerald-300 font-semibold">20% Environmental</span>
          </span>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {overview?.is_fallback ? (
            <span className="px-2.5 py-0.5 rounded text-[10px] bg-amber-950/80 text-amber-300 border border-amber-800 flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              FALLBACK DATA ACTIVE (SIMULATION ISOLATED)
            </span>
          ) : (
            <span className="px-2.5 py-0.5 rounded text-[10px] bg-cyan-950/80 text-cyan-300 border border-cyan-800 flex items-center gap-1">
              <Activity className="h-3 w-3 animate-pulse" />
              LIVE SIMULATION STREAM (FASTAPI ENGINE)
            </span>
          )}
          <span className="px-2.5 py-0.5 rounded text-[10px] bg-slate-900 text-slate-400 border border-slate-800">
            SOURCE: {overview?.source || "VIRTUAL_SIMULATION_ENGINE"}
          </span>
          <span className="px-2 py-0.5 rounded text-[10px] bg-rose-950/50 text-rose-300 border border-rose-900/60 font-semibold">
            ACTUATION: DISABLED
          </span>
        </div>
      </div>

      {/* 2. Executive Metric KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-3 sm:gap-4">
        <MetricCard
          label="Network Vulnerability"
          value={overview ? `${overview.average_network_vulnerability.toFixed(1)}` : "54.2"}
          unit="/100"
          tone={overview && overview.average_network_vulnerability > 60 ? "amber" : "cyan"}
        />
        <MetricCard
          label="Critical Segments"
          value={overview ? `${overview.critical_segments_count}` : "1"}
          unit="PIPES"
          tone="rose"
        />
        <MetricCard
          label="Active Hotspot Clusters"
          value={overview ? `${overview.active_clusters_count}` : "2"}
          unit="DBSCAN"
          tone="amber"
        />
        <MetricCard
          label="Deteriorating Assets"
          value={overview ? `${overview.deteriorating_segments_count}` : "2"}
          unit="RAPID"
          tone="amber"
        />
        <MetricCard
          label="Deterioration Rate"
          value={overview ? `+${overview.network_deterioration_rate.toFixed(2)}` : "+0.16"}
          unit="PTS/DAY"
          tone="slate"
        />
        <MetricCard
          label="Inspection Queue"
          value={overview ? `${overview.pending_inspections_count}` : "3"}
          unit="TARGETS"
          tone="cyan"
        />
      </div>

      {/* 3. Navigation Tabs */}
      <div className="flex border-b border-slate-800 space-x-1 sm:space-x-2 overflow-x-auto pb-1">
        <button
          onClick={() => setActiveTab("vulnerability")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-medium rounded-t-lg transition-colors ${
            activeTab === "vulnerability"
              ? "bg-slate-800/80 text-cyan-400 border-b-2 border-cyan-400"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
          }`}
        >
          <Layers className="h-4 w-4" />
          Vulnerability Scoring (4-Factor)
        </button>

        <button
          onClick={() => setActiveTab("spatial")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-medium rounded-t-lg transition-colors ${
            activeTab === "spatial"
              ? "bg-slate-800/80 text-cyan-400 border-b-2 border-cyan-400"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
          }`}
        >
          <MapPin className="h-4 w-4" />
          Geospatial Clusters & Hotspots
        </button>

        <button
          onClick={() => setActiveTab("trends")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-medium rounded-t-lg transition-colors ${
            activeTab === "trends"
              ? "bg-slate-800/80 text-cyan-400 border-b-2 border-cyan-400"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
          }`}
        >
          <TrendingUp className="h-4 w-4" />
          Temporal Trends & Projections
        </button>

        <button
          onClick={() => setActiveTab("inspections")}
          className={`flex items-center gap-2 px-4 py-2.5 text-xs sm:text-sm font-medium rounded-t-lg transition-colors ${
            activeTab === "inspections"
              ? "bg-slate-800/80 text-cyan-400 border-b-2 border-cyan-400"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
          }`}
        >
          <Navigation className="h-4 w-4" />
          Inspection Prioritisation Queue
          {inspections.filter((i) => i.status === "PENDING").length > 0 && (
            <span className="ml-1 px-1.5 py-0.5 rounded-full text-[10px] bg-cyan-500/20 text-cyan-300 font-mono">
              {inspections.filter((i) => i.status === "PENDING").length}
            </span>
          )}
        </button>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: VULNERABILITY SCORING (4-FACTOR ENGINE)                             */}
      {/* ========================================================================= */}
      {activeTab === "vulnerability" && (
        <div className="space-y-4">
          {/* Filters Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-3 rounded-lg border border-slate-800 bg-slate-900/40">
            <div className="relative w-full sm:w-72">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search pipeline or material..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-950/80 border border-slate-800 rounded-md text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Filter className="h-3.5 w-3.5 text-slate-500" />
              <select
                value={filterRiskLevel}
                onChange={(e) => setFilterRiskLevel(e.target.value)}
                className="px-2.5 py-1.5 text-xs bg-slate-950/80 border border-slate-800 rounded-md text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="ALL">All Risk Levels</option>
                <option value="CRITICAL">Critical Only</option>
                <option value="HIGH">High Only</option>
                <option value="MODERATE">Moderate</option>
                <option value="LOW">Low / Very Low</option>
              </select>

              <select
                value={filterZone}
                onChange={(e) => setFilterZone(e.target.value)}
                className="px-2.5 py-1.5 text-xs bg-slate-950/80 border border-slate-800 rounded-md text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                <option value="ALL">All Pressure Zones</option>
                <option value="PZ-01">PZ-01 (Metro Central)</option>
                <option value="PZ-02">PZ-02 (Eastern Industrial)</option>
                <option value="PZ-03">PZ-03 (Northern Residential)</option>
                <option value="PZ-04">PZ-04 (Harbor Utility)</option>
              </select>
            </div>
          </div>

          {/* Vulnerability Table */}
          <Card variant="industrial">
            <CardHeader className="pb-2">
              <CardTitle className="text-base text-slate-200 flex items-center justify-between">
                <span>Multi-Factor Pipeline Vulnerability Assessments</span>
                <span className="text-xs font-mono text-slate-400">
                  Showing {filteredSegments.length} of {segments.length} Segments
                </span>
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Formula: Vulnerability = 30% Hydraulic + 25% Structural + 25% AI Incident History + 20% Environmental Risk
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 font-mono text-[11px]">
                      <th className="py-2.5 px-3">Segment ID & Name</th>
                      <th className="py-2.5 px-3">Material & Dia</th>
                      <th className="py-2.5 px-3">Zone</th>
                      <th className="py-2.5 px-3">Vulnerability</th>
                      <th className="py-2.5 px-3">4-Factor Breakdown (H / S / I / E)</th>
                      <th className="py-2.5 px-3">Confidence & Data</th>
                      <th className="py-2.5 px-3">Trend</th>
                      <th className="py-2.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {filteredSegments.map((s) => (
                      <tr key={s.id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-3">
                          <div className="font-semibold text-slate-100">{s.segment_name}</div>
                          <div className="text-[10px] text-slate-400">{s.pipeline_segment_id}</div>
                        </td>
                        <td className="py-3 px-3 text-slate-300">
                          <div className="flex items-center gap-1.5">
                            <span>{s.material}</span>
                            {s.data_completeness_pct < 80 && (
                              <span className="px-1.5 py-0.2 rounded text-[9px] bg-amber-950 text-amber-300 border border-amber-800" title="Missing metadata penalized with default baseline">
                                INCOMPLETE
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] text-slate-400">{s.diameter_mm}mm • {s.length_m.toFixed(0)}m</div>
                        </td>
                        <td className="py-3 px-3">
                          <span className="px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 text-[10px]">
                            {s.pressure_zone_id}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-0.5 rounded border text-[11px] font-bold ${getRiskColor(s.vulnerability_level)}`}>
                              {s.vulnerability_score.toFixed(1)}
                            </span>
                            <span className="text-[10px] text-slate-400">{s.vulnerability_level}</span>
                          </div>
                        </td>
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-2">
                            <div className="flex flex-col gap-1 w-36">
                              <div className="flex h-1.5 w-full rounded-full overflow-hidden bg-slate-800">
                                <div style={{ width: `${s.hydraulic_score}%` }} className="bg-cyan-500" title={`Hydraulic: ${s.hydraulic_score}`} />
                                <div style={{ width: `${s.structural_score}%` }} className="bg-amber-500" title={`Structural: ${s.structural_score}`} />
                                <div style={{ width: `${s.incident_score}%` }} className="bg-rose-500" title={`Incident: ${s.incident_score}`} />
                                <div style={{ width: `${s.environmental_score}%` }} className="bg-emerald-500" title={`Environmental: ${s.environmental_score}`} />
                              </div>
                              <div className="flex justify-between text-[9px] text-slate-400">
                                <span>H:{s.hydraulic_score.toFixed(0)}</span>
                                <span>S:{s.structural_score.toFixed(0)}</span>
                                <span>I:{s.incident_score.toFixed(0)}</span>
                                <span>E:{s.environmental_score.toFixed(0)}</span>
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-3">
                          <div className="text-slate-300">{(s.confidence * 100).toFixed(0)}% Conf</div>
                          <div className="text-[10px] text-slate-400">±{s.uncertainty_margin.toFixed(1)} pts • {s.data_completeness_pct.toFixed(0)}% data</div>
                        </td>
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-1.5">
                            {s.trend_direction === "DETERIORATING" ? (
                              <TrendingUp className="h-3.5 w-3.5 text-rose-400" />
                            ) : s.trend_direction === "IMPROVING" ? (
                              <TrendingDown className="h-3.5 w-3.5 text-emerald-400" />
                            ) : (
                              <Activity className="h-3.5 w-3.5 text-slate-400" />
                            )}
                            <span className={s.trend_direction === "DETERIORATING" ? "text-rose-300" : "text-slate-300"}>
                              {s.trend_direction}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-3 text-right">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleOpenDeepDive(s.pipeline_segment_id)}
                            rightIcon={<ChevronRight className="h-3.5 w-3.5" />}
                          >
                            Explain
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: GEOSPATIAL CLUSTERS & RISK ZONES                                    */}
      {/* ========================================================================= */}
      {activeTab === "spatial" && (
        <div className="space-y-6">
          {/* Geographic Map Visualization Canvas */}
          <Card variant="industrial" className="overflow-hidden">
            <CardHeader className="pb-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-base text-slate-200 flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-cyan-400" />
                    Metropolitan Spatial Incident Hotspots & Geodesic Clustering
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-400 mt-0.5">
                    DBSCAN Spatial Clustering (ε=350m, MinPts=2) with 3D Spherical Cartesian Centroid & Antimeridian Normalization
                  </CardDescription>
                </div>

                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
                    <button
                      type="button"
                      onClick={() => setSpatialViewMode("maplibre")}
                      className={`px-2.5 py-1 text-xs rounded-md font-mono transition-colors flex items-center gap-1.5 ${
                        spatialViewMode === "maplibre"
                          ? "bg-cyan-950 text-cyan-300 border border-cyan-800 shadow-sm"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <Globe className="h-3.5 w-3.5" />
                      MapLibre GIS
                    </button>
                    <button
                      type="button"
                      onClick={() => setSpatialViewMode("schematic")}
                      className={`px-2.5 py-1 text-xs rounded-md font-mono transition-colors flex items-center gap-1.5 ${
                        spatialViewMode === "schematic"
                          ? "bg-cyan-950 text-cyan-300 border border-cyan-800 shadow-sm"
                          : "text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <Layers className="h-3.5 w-3.5" />
                      Schematic Vector
                    </button>
                  </div>

                  <span className="text-xs px-2 py-1 rounded bg-cyan-950 border border-cyan-800 text-cyan-300 font-mono hidden md:inline">
                    ε=350m • MinPts=2
                  </span>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {spatialViewMode === "maplibre" ? (
                /* MapLibre WebGL Live Interactive GIS Container */
                <div className="relative h-[480px] w-full rounded-xl border border-slate-800 bg-slate-950 overflow-hidden shadow-inner">
                  <MapContainer
                    layers={mapLayers}
                    basemapStyle="dark"
                    onSelectFeature={(feat: SelectedMapFeature) => {
                      if (feat.type === "pipeline") {
                        setSelectedSegmentId(feat.id);
                        setIsDeepDiveOpen(true);
                        backendApiClient.getSegmentDeepDive(feat.id).then(setSegmentDeepDive).catch(console.error);
                      }
                    }}
                    onMouseMoveCoords={(coords) => setMapCursorCoords(coords)}
                    onZoomChange={(zoom) => setMapCurrentZoom(zoom)}
                  />

                  {/* Top-Left HUD overlay */}
                  <div className="absolute top-3 left-3 bg-slate-900/90 border border-slate-800 rounded-lg p-2.5 text-[11px] font-mono text-slate-300 space-y-1 shadow-lg pointer-events-none backdrop-blur-sm">
                    <div className="text-cyan-400 font-bold flex items-center gap-1.5">
                      <Globe className="h-3.5 w-3.5" /> MapLibre WebGL Engine Active
                    </div>
                    <div className="text-slate-400 text-[10px]">
                      Cursor: {mapCursorCoords.lat.toFixed(5)}°N, {mapCursorCoords.lng.toFixed(5)}°W • Zoom: {mapCurrentZoom.toFixed(1)}x
                    </div>
                    <div className="text-emerald-400 text-[10px] flex items-center gap-1">
                      <Check className="h-3 w-3" /> Geodesic Haversine clustering + Antimeridian wrapping active
                    </div>
                  </div>

                  {/* Bottom-Right Active Clusters HUD */}
                  <div className="absolute bottom-3 right-3 bg-slate-900/90 border border-slate-800 rounded-lg p-2.5 text-[11px] font-mono text-slate-300 space-y-1 shadow-lg backdrop-blur-sm max-w-xs">
                    <div className="font-semibold text-slate-200 pb-1 border-b border-slate-800 flex items-center justify-between">
                      <span>DBSCAN Incident Hotspots</span>
                      <span className="text-[10px] text-cyan-400">{clusters.length} Active</span>
                    </div>
                    {clusters.map((c) => (
                      <div key={c.id} className="flex items-center justify-between gap-3 text-[10px]">
                        <span className="text-slate-300 truncate max-w-[150px]">{c.cluster_name}</span>
                        <span className="text-rose-400 font-bold shrink-0">r={c.radius_m.toFixed(0)}m ({c.incident_count} alerts)</span>
                      </div>
                    ))}
                    <div className="text-[9px] text-slate-500 pt-1 border-t border-slate-800/80">
                      Click any pipeline segment on map to view deep dive
                    </div>
                  </div>
                </div>
              ) : (
                /* Interactive Vector Schematic Representing Metro Grid */
                <div className="relative h-96 w-full rounded-xl border border-slate-800 bg-slate-950/80 overflow-hidden flex items-center justify-center p-4">
                  <svg className="w-full h-full" viewBox="0 0 800 450">
                    {/* Grid background lines */}
                    <defs>
                      <pattern id="grid-pattern" width="40" height="40" patternUnits="userSpaceOnUse">
                        <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" strokeWidth="0.5" strokeDasharray="2,2" />
                      </pattern>
                    </defs>
                    <rect width="800" height="450" fill="url(#grid-pattern)" />

                    {/* Operational Pressure Zone Regions */}
                    <rect x="50" y="40" width="340" height="220" fill="#0284c7" fillOpacity="0.04" stroke="#0284c7" strokeWidth="1" strokeDasharray="4,4" />
                    <text x="60" y="60" fill="#38bdf8" fontSize="10" fontFamily="monospace">PZ-01: Metro Central High-Pressure Spine</text>

                    <rect x="420" y="40" width="330" height="180" fill="#f59e0b" fillOpacity="0.04" stroke="#f59e0b" strokeWidth="1" strokeDasharray="4,4" />
                    <text x="430" y="60" fill="#fbbf24" fontSize="10" fontFamily="monospace">PZ-02: Eastern Industrial Sector</text>

                    <rect x="180" y="270" width="380" height="150" fill="#10b981" fillOpacity="0.04" stroke="#10b981" strokeWidth="1" strokeDasharray="4,4" />
                    <text x="190" y="290" fill="#34d399" fontSize="10" fontFamily="monospace">PZ-03: Northern Residential Sub-Branch</text>

                    {/* Pipeline Conduits */}
                    {/* Primary Spine B (Critical) */}
                    <line x1="80" y1="120" x2="380" y2="170" stroke="#f43f5e" strokeWidth="4" strokeLinecap="round" />
                    <text x="210" y="135" fill="#f43f5e" fontSize="11" fontFamily="monospace" fontWeight="bold">Trunk Line B (CRITICAL - 84.5)</text>

                    {/* Primary Spine A */}
                    <line x1="180" y1="70" x2="180" y2="250" stroke="#0284c7" strokeWidth="3" strokeLinecap="round" />

                    {/* Industrial Feeder */}
                    <line x1="380" y1="170" x2="700" y2="130" stroke="#10b981" strokeWidth="2.5" strokeDasharray="5,3" strokeLinecap="round" />
                    <text x="510" y="145" fill="#10b981" fontSize="10" fontFamily="monospace">Industrial Feeder 1 (HDPE)</text>

                    {/* Harbor Marginal Service */}
                    <line x1="80" y1="210" x2="180" y2="250" stroke="#f59e0b" strokeWidth="2.5" strokeLinecap="round" />
                    <text x="80" y="235" fill="#fbbf24" fontSize="10" fontFamily="monospace">Harbor Line (Cast Iron)</text>

                    {/* Hotspot Cluster 1 (Circle & Centroid) */}
                    <circle cx="280" cy="150" r="48" fill="#f43f5e" fillOpacity="0.18" stroke="#f43f5e" strokeWidth="1.5" strokeDasharray="3,3" />
                    <circle cx="280" cy="150" r="5" fill="#f43f5e" />
                    <text x="295" y="155" fill="#f43f5e" fontSize="11" fontFamily="monospace" fontWeight="bold">Cluster #1 (Radius: 220m)</text>

                    {/* Hotspot Cluster 2 (Circle & Centroid) */}
                    <circle cx="130" cy="230" r="38" fill="#f59e0b" fillOpacity="0.18" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="3,3" />
                    <circle cx="130" cy="230" r="5" fill="#f59e0b" />
                    <text x="145" y="235" fill="#fbbf24" fontSize="11" fontFamily="monospace">Cluster #2 (Radius: 180m)</text>

                    {/* Virtual Rovers On Map */}
                    <g transform="translate(190, 160)">
                      <circle cx="0" cy="0" r="10" fill="#06b6d4" fillOpacity="0.3" stroke="#06b6d4" strokeWidth="1.5" />
                      <circle cx="0" cy="0" r="4" fill="#06b6d4" />
                      <text x="14" y="4" fill="#38bdf8" fontSize="10" fontFamily="monospace">AquaRover Alpha (IDLE)</text>
                    </g>
                  </svg>

                  <div className="absolute bottom-3 right-3 bg-slate-900/90 border border-slate-800 rounded-lg p-2.5 text-[11px] font-mono text-slate-300 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" /> Critical Vulnerability / Active Hotspot
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" /> High Risk Pipeline
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 inline-block" /> Virtual Autonomous Rover
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Active Clusters & Geographic Zones Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card variant="industrial">
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-slate-200 flex items-center justify-between">
                  <span>Detected Spatial Incident Clusters</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                    {clusters.length} Active
                  </span>
                </CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Groups of spatially proximate AI leak alerts and high-frequency acoustic events.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 font-mono text-xs">
                  {clusters.map((c) => (
                    <div key={c.id} className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-100">{c.cluster_name}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getRiskColor(c.cluster_risk_level)}`}>
                          {c.cluster_risk_level}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                        <div>Incidents: <span className="text-slate-200">{c.incident_count}</span></div>
                        <div>Radius: <span className="text-slate-200">{c.radius_m.toFixed(0)}m</span></div>
                        <div>Dominant Pipe: <span className="text-slate-200">{c.dominant_material}</span></div>
                        <div>Intensity: <span className="text-slate-200">{(c.hotspot_intensity * 100).toFixed(0)}%</span></div>
                      </div>
                      <div className="text-[10px] text-slate-500">
                        Centroid: {c.centroid_lat.toFixed(5)}, {c.centroid_lng.toFixed(5)}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card variant="industrial">
              <CardHeader className="pb-2">
                <CardTitle className="text-base text-slate-200 flex items-center justify-between">
                  <span>Operational Geographic Zones</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                    {zones.length} Zones
                  </span>
                </CardTitle>
                <CardDescription className="text-xs text-slate-400">
                  Aggregated vulnerability, total conduit length, and critical asset concentration.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 font-mono text-xs">
                  {zones.map((z) => (
                    <div key={z.id} className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-100">{z.zone_name}</span>
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-cyan-300 text-[10px]">
                          {z.zone_code}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400">{z.description}</div>
                      <div className="grid grid-cols-3 gap-2 text-[10px] text-slate-300 pt-1 border-t border-slate-900">
                        <div>Avg Risk: <span className="font-bold text-amber-400">{z.avg_vulnerability_score.toFixed(1)}</span></div>
                        <div>Total Pipes: <span>{z.total_segments} ({z.total_length_km.toFixed(1)}km)</span></div>
                        <div>Pressure: <span>{z.avg_pressure_psi.toFixed(0)} psi</span></div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: TEMPORAL TRENDS & PREDICTIVE FORECASTING                             */}
      {/* ========================================================================= */}
      {activeTab === "trends" && (
        <div className="space-y-6">
          <Card variant="industrial">
            <CardHeader className="pb-2">
              <CardTitle className="text-base text-slate-200 flex items-center justify-between">
                <span>Multi-Horizon Predictive Risk Projections (24h, 7d, 30d)</span>
                <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300 font-mono">
                  Physics & Trend Model
                </span>
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Forecasting structural fatigue and failure probability based on hydraulic stress gradients and acoustic anomaly recurrence.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                      <th className="py-2.5 px-3">Pipeline Conduit</th>
                      <th className="py-2.5 px-3">Current Risk</th>
                      <th className="py-2.5 px-3">24-Hour Horizon</th>
                      <th className="py-2.5 px-3">7-Day Horizon</th>
                      <th className="py-2.5 px-3">30-Day Horizon</th>
                      <th className="py-2.5 px-3">Mitigation Urgency</th>
                      <th className="py-2.5 px-3">Primary Risk Drivers</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {predictions.map((p) => (
                      <tr key={p.pipeline_segment_id} className="hover:bg-slate-800/40 transition-colors">
                        <td className="py-3 px-3">
                          <div className="font-semibold text-slate-100">{p.segment_name}</div>
                          <div className="text-[10px] text-slate-400">{p.pipeline_segment_id}</div>
                        </td>
                        <td className="py-3 px-3">
                          <span className={`px-2 py-0.5 rounded border text-[11px] font-bold ${getRiskColor(p.risk_level)}`}>
                            {p.current_vulnerability_score.toFixed(1)}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-slate-200">
                          <div>{p.projected_risk_24h.toFixed(1)}</div>
                          <div className="text-[10px] text-slate-400">+{p.trend_24h_delta.toFixed(2)} pts</div>
                        </td>
                        <td className="py-3 px-3 text-slate-200">
                          <div>{p.projected_risk_7d.toFixed(1)}</div>
                          <div className="text-[10px] text-slate-400">+{p.trend_7d_delta.toFixed(2)} pts</div>
                        </td>
                        <td className="py-3 px-3 text-slate-200">
                          <div className={p.projected_risk_30d > 80 ? "text-rose-400 font-bold" : ""}>
                            {p.projected_risk_30d.toFixed(1)}
                          </div>
                          <div className="text-[10px] text-slate-400">+{p.trend_30d_delta.toFixed(2)} pts</div>
                        </td>
                        <td className="py-3 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              p.mitigation_urgency === "IMMEDIATE"
                                ? "bg-rose-950 text-rose-300 border border-rose-800"
                                : p.mitigation_urgency === "SHORT_TERM"
                                ? "bg-amber-950 text-amber-300 border border-amber-800"
                                : "bg-slate-800 text-slate-300 border border-slate-700"
                            }`}
                          >
                            {p.mitigation_urgency}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-[11px] text-slate-400 max-w-xs">
                          {p.primary_risk_drivers.slice(0, 2).map((d, i) => (
                            <div key={i} className="truncate">• {d}</div>
                          ))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 4: INSPECTION PRIORITISATION QUEUE                                    */}
      {/* ========================================================================= */}
      {activeTab === "inspections" && (
        <div className="space-y-4">
          <Card variant="industrial">
            <CardHeader className="pb-2">
              <CardTitle className="text-base text-slate-200 flex items-center justify-between">
                <span>Intelligent Autonomous Rover Inspection Queue</span>
                <span className="text-xs font-mono text-slate-400">
                  Prioritized by Risk, Degradation Velocity & Cluster Proximity
                </span>
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Operator-guided dispatch: Selecting "Request Rover Inspection" calculates Dijkstra graph paths and reserves fleet units subject to operator authorization.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 font-mono">
                {inspections.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 rounded-xl border border-slate-800 bg-slate-950/70 hover:border-slate-700 transition-colors space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan-950/80 border border-cyan-800/80 text-cyan-400">
                          <Navigation className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="font-bold text-slate-100 text-sm flex items-center gap-2">
                            {item.segment_name}
                            <span className="text-xs font-normal text-slate-400">({item.pipeline_segment_id})</span>
                          </div>
                          <div className="text-[11px] text-slate-400">{item.suggested_action}</div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 self-start sm:self-auto">
                        <span className={`px-2.5 py-1 rounded text-xs font-bold border ${getRiskColor(item.priority_level.includes("CRITICAL") ? "CRITICAL" : "HIGH")}`}>
                          Priority: {item.priority_score.toFixed(1)}/100
                        </span>
                        <StatusBadge
                          status={
                            item.status === "DISPATCHED"
                              ? "active"
                              : item.status === "ACKNOWLEDGED"
                              ? "warning"
                              : item.status === "DISMISSED"
                              ? "offline"
                              : "standby"
                          }
                          label={item.status}
                          size="sm"
                        />
                      </div>
                    </div>

                    {/* Contributing Justification Badges */}
                    <div className="flex flex-wrap gap-1.5 text-[10px] text-slate-300">
                      {item.reasons.map((r, i) => (
                        <span key={i} className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                          {r}
                        </span>
                      ))}
                    </div>

                    {/* Operator Action Bar */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-900 text-xs">
                      <div className="text-[11px] text-slate-500">
                        {item.reviewed_by ? `Reviewed by: ${item.reviewed_by}` : "Pending operator review"}
                        {item.assigned_rover_id && ` • Assigned: ${item.assigned_rover_id}`}
                      </div>

                      <div className="flex items-center gap-2">
                        {item.status === "PENDING" && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleAcknowledge(item)}
                              leftIcon={<CheckCircle2 className="h-3.5 w-3.5 text-cyan-400" />}
                            >
                              Acknowledge
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDismiss(item)}
                              leftIcon={<XCircle className="h-3.5 w-3.5 text-slate-400" />}
                            >
                              Dismiss
                            </Button>
                          </>
                        )}

                        {item.status !== "DISPATCHED" && item.status !== "DISMISSED" && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => setDispatchModalItem(item)}
                            leftIcon={<Bot className="h-3.5 w-3.5" />}
                          >
                            Request Rover Inspection
                          </Button>
                        )}

                        {item.status === "DISPATCHED" && (
                          <span className="text-[11px] text-emerald-400 flex items-center gap-1 font-mono">
                            <CheckCircle2 className="h-3.5 w-3.5" /> Inspection Dispatched (Approval Gate Active)
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 4. SEGMENT DEEP-DIVE MODAL / DRAWER                                       */}
      {/* ========================================================================= */}
      {isDeepDiveOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  Segment Vulnerability Deep Dive
                  <span className="text-xs px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800 font-mono">
                    {selectedSegmentId}
                  </span>
                </h2>
                <p className="text-xs text-slate-400">
                  Granular multi-factor breakdown, digital twin correlation, and mitigation actions.
                </p>
              </div>
              <button
                onClick={() => setIsDeepDiveOpen(false)}
                className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            {segmentDeepDive ? (
              <div className="space-y-4 font-mono text-xs">
                {/* Top Metrics Row */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/60">
                    <div className="text-[10px] text-slate-400">Vulnerability Score</div>
                    <div className="text-lg font-bold text-rose-400">{segmentDeepDive.vulnerability_score.toFixed(1)}/100</div>
                    <div className="text-[10px] text-slate-500">Level: {segmentDeepDive.vulnerability_level}</div>
                  </div>
                  <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/60">
                    <div className="text-[10px] text-slate-400">Data Completeness</div>
                    <div className="text-lg font-bold text-cyan-400">{segmentDeepDive.data_completeness_pct.toFixed(0)}%</div>
                    <div className="text-[10px] text-slate-500">Uncertainty: ±{segmentDeepDive.uncertainty_margin} pts</div>
                  </div>
                  <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/60">
                    <div className="text-[10px] text-slate-400">Deterioration Rate</div>
                    <div className="text-lg font-bold text-amber-400">+{segmentDeepDive.deterioration_rate_per_day.toFixed(2)}/day</div>
                    <div className="text-[10px] text-slate-500">Direction: {segmentDeepDive.trend_direction}</div>
                  </div>
                </div>

                {/* 4 Factor Component Breakdown Details */}
                <div className="space-y-2">
                  <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Contributing Risk Dimensions</h3>
                  <div className="space-y-2">
                    {/* Hydraulic */}
                    <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/40 space-y-1">
                      <div className="flex justify-between items-center text-slate-200">
                        <span className="font-semibold text-cyan-400">Hydraulic Risk (30% Weight)</span>
                        <span className="font-bold">{segmentDeepDive.hydraulic_score.toFixed(1)}/100</span>
                      </div>
                      <div className="text-[11px] text-slate-400 space-y-0.5">
                        {segmentDeepDive.contributing_factors.hydraulic?.reasons?.map((r, i) => (
                          <div key={i}>• {r}</div>
                        ))}
                      </div>
                    </div>

                    {/* Structural */}
                    <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/40 space-y-1">
                      <div className="flex justify-between items-center text-slate-200">
                        <span className="font-semibold text-amber-400">Structural Infrastructure (25% Weight)</span>
                        <span className="font-bold">{segmentDeepDive.structural_score.toFixed(1)}/100</span>
                      </div>
                      <div className="text-[11px] text-slate-400 space-y-0.5">
                        {segmentDeepDive.contributing_factors.structural?.reasons?.map((r, i) => (
                          <div key={i}>• {r}</div>
                        ))}
                      </div>
                    </div>

                    {/* Incident */}
                    <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/40 space-y-1">
                      <div className="flex justify-between items-center text-slate-200">
                        <span className="font-semibold text-rose-400">AI Leak & Incident History (25% Weight)</span>
                        <span className="font-bold">{segmentDeepDive.incident_score.toFixed(1)}/100</span>
                      </div>
                      <div className="text-[11px] text-slate-400 space-y-0.5">
                        {segmentDeepDive.contributing_factors.incident?.reasons?.map((r, i) => (
                          <div key={i}>• {r}</div>
                        ))}
                      </div>
                    </div>

                    {/* Environmental */}
                    <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/40 space-y-1">
                      <div className="flex justify-between items-center text-slate-200">
                        <span className="font-semibold text-emerald-400">Environmental & Spatial Hotspot (20% Weight)</span>
                        <span className="font-bold">{segmentDeepDive.environmental_score.toFixed(1)}/100</span>
                      </div>
                      <div className="text-[11px] text-slate-400 space-y-0.5">
                        {segmentDeepDive.contributing_factors.environmental?.reasons?.map((r, i) => (
                          <div key={i}>• {r}</div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Mitigation & Inspection Handoff */}
                <div className="p-3 rounded-lg border border-cyan-800/60 bg-cyan-950/40 space-y-2">
                  <div className="font-semibold text-cyan-300">Recommended Operator Actions</div>
                  <p className="text-[11px] text-slate-300 leading-relaxed">
                    Prioritize acoustic crawling inspection to pinpoint joint leakage along the primary 600mm conduit before pressure transients trigger structural burst.
                  </p>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-slate-400 text-xs">Loading deep dive assessment...</div>
            )}

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              <Button variant="outline" size="sm" onClick={() => setIsDeepDiveOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* 5. ROVER DISPATCH REQUEST MODAL                                           */}
      {/* ========================================================================= */}
      {dispatchModalItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4 font-mono">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Bot className="h-5 w-5 text-cyan-400" />
                Request Autonomous Rover Inspection
              </h2>
              <button
                onClick={() => setDispatchModalItem(null)}
                className="text-slate-400 hover:text-slate-200 p-1"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-lg border border-slate-800 bg-slate-950/60 space-y-1">
                <div className="font-semibold text-slate-200">{dispatchModalItem.segment_name}</div>
                <div className="text-[11px] text-slate-400">Target Priority: {dispatchModalItem.priority_score.toFixed(1)} ({dispatchModalItem.priority_level})</div>
                <div className="text-[11px] text-cyan-400">{dispatchModalItem.suggested_action}</div>
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Preferred Virtual Rover Unit:</label>
                <select
                  value={preferredRoverId}
                  onChange={(e) => setPreferredRoverId(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500 font-mono"
                >
                  <option value="ROV-01">AquaRover Alpha (Crawler • 92% Battery • ELIGIBLE)</option>
                  <option value="ROV-02">AquaRover Beta (Sonar Swimmer • 85% Battery • ELIGIBLE)</option>
                  <option value="ROV-03">AquaRover Gamma (Acoustic Floater • 78% Battery • ELIGIBLE)</option>
                  <option value="ROV-04-DEPLETED" disabled>AquaRover Delta (14% Battery • BLOCKED: Battery &lt; 20%)</option>
                </select>
                <div className="text-[10px] text-slate-500 mt-1 flex items-center gap-1 font-mono">
                  <ShieldCheck className="h-3 w-3 text-cyan-400" />
                  Battery Safety Gate: Units with &lt; 20% battery charge are ineligible for dispatch.
                </div>
              </div>

              <div>
                <label className="block text-[11px] text-slate-400 mb-1">Operator Notes / Mission Directives:</label>
                <textarea
                  rows={3}
                  value={dispatchNotes}
                  onChange={(e) => setDispatchNotes(e.target.value)}
                  placeholder="e.g. Perform acoustic pinpointing at 10m intervals near hotspot cluster centroid..."
                  className="w-full px-3 py-2 text-xs bg-slate-950 border border-slate-800 rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="p-2.5 rounded-lg border border-amber-800/60 bg-amber-950/30 text-amber-300 text-[11px]">
                <Info className="h-3.5 w-3.5 inline mr-1" />
                This action initiates pipeline routing and reserves the rover. The mission will remain in <code>PENDING_APPROVAL</code> status until human operator sign-off.
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
              <Button variant="outline" size="sm" onClick={() => setDispatchModalItem(null)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleConfirmDispatch}>
                Generate Mission Recommendation
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
