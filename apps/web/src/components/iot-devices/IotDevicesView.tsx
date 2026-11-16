"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Cpu,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Activity,
  Layers,
  Search,
  RefreshCw,
  Plus,
  Key,
  Radio,
  Sliders,
  Sparkles,
  Info,
  Server,
  Zap,
  Lock,
  Battery,
  Wifi,
  WifiOff,
  Terminal,
  ExternalLink,
  ChevronRight,
  Database,
  Compass,
  FileCheck2,
} from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { MetricCard } from "@/components/ui/MetricCard";
import { Modal } from "@/components/ui/Modal";
import { iotApiClient } from "@/services/api/iotApiClient";
import {
  IoTDevice,
  DeviceTelemetry,
  SensorCalibration,
  IoTStatusResponse,
  DeviceAuditLogItem,
  DigitalTwinComparisonResult,
  AcousticLeakAnalysisResult,
  RegisterDevicePayload,
  RegisterCalibrationPayload,
} from "@/services/api/iotTypes";

export function IotDevicesView() {
  // Navigation tabs
  const [activeTab, setActiveTab] = useState<
    "overview" | "registry" | "telemetry" | "calibration" | "connectivity" | "security_audit"
  >("overview");

  // State data
  const [statusOverview, setStatusOverview] = useState<IoTStatusResponse | null>(null);
  const [devices, setDevices] = useState<IoTDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<IoTDevice | null>(null);
  const [telemetries, setTelemetries] = useState<DeviceTelemetry[]>([]);
  const [calibrations, setCalibrations] = useState<SensorCalibration[]>([]);
  const [auditLogs, setAuditLogs] = useState<DeviceAuditLogItem[]>([]);
  const [digitalTwinComp, setDigitalTwinComp] = useState<DigitalTwinComparisonResult | null>(null);
  const [acousticLeakAnalysis, setAcousticLeakAnalysis] = useState<AcousticLeakAnalysisResult | null>(null);

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<string>("ALL");
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [commandResult, setCommandResult] = useState<any | null>(null);
  const [actionMessage, setActionMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  // Modals
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showCalibrationModal, setShowCalibrationModal] = useState(false);
  const [showCommandModal, setShowCommandModal] = useState(false);
  const [selectedCommand, setSelectedCommand] = useState("RUN_DEVICE_DIAGNOSTICS");

  // Registration Form State
  const [newDevice, setNewDevice] = useState<RegisterDevicePayload>({
    id: `DEV-NODE-${Math.floor(10 + Math.random() * 90)}`,
    name: "Pipeline Pressure & Acoustic Telemetry Node",
    device_type: "PRESSURE_SENSOR",
    manufacturer: "HydroMetrics Corp",
    hardware_version: "v3.1.0",
    firmware_version: "1.9.0",
    dma_zone: "DMA-NORTH-04",
    pipeline_segment_id: "PIPE-SEC-4B-92",
    communication_protocol: "MQTT",
    power_source: "SOLAR_BATTERY",
    supported_sensor_types: ["HYDROSTATIC_PRESSURE"],
  });

  // Calibration Form State
  const [newCalibration, setNewCalibration] = useState<RegisterCalibrationPayload>({
    device_id: "",
    sensor_id: "",
    calibration_method: "DEADWEIGHT_TESTER",
    calibration_reference: "REF-STD-2026",
    calibration_result: "PASSED_WITHIN_TOLERANCE",
    accuracy_tolerance: 0.2,
    technician: "Ing. Sarah Chen",
    certificate_reference: "CERT-CAL-8841",
    notes: "Annual scheduled recalibration performed.",
  });

  const loadAllData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [statusRes, devicesRes, telemetryRes, calibRes, auditRes, dtRes, leakRes] =
        await Promise.all([
          iotApiClient.fetchIotStatus(),
          iotApiClient.fetchDevices(),
          iotApiClient.fetchLatestTelemetry(undefined, 40),
          iotApiClient.fetchCalibrations(),
          iotApiClient.fetchIotAuditLogs(undefined, 30),
          iotApiClient.fetchDigitalTwinComparison(),
          iotApiClient.fetchLeakAnalysis(),
        ]);

      setStatusOverview(statusRes);
      setDevices(devicesRes.devices || []);
      setTelemetries(telemetryRes.telemetries || []);
      setCalibrations(calibRes.records || []);
      setAuditLogs(auditRes.audit_events || []);
      setDigitalTwinComp(dtRes);
      setAcousticLeakAnalysis(leakRes);

      if (devicesRes.devices && devicesRes.devices.length > 0 && !selectedDevice) {
        setSelectedDevice(devicesRes.devices[0]);
      }
    } catch (err) {
      console.error("Failed to load IoT data", err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedDevice]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // Actions
  const handleQuarantine = async (device: IoTDevice) => {
    try {
      await iotApiClient.quarantineDevice(device.id, "Operator initiated safety quarantine");
      setActionMessage({ text: `Device ${device.id} has been quarantined.`, type: "success" });
      await loadAllData();
    } catch (err: any) {
      setActionMessage({ text: err.message || "Failed to quarantine device", type: "error" });
    }
  };

  const handleRevoke = async (device: IoTDevice) => {
    if (!confirm(`Are you sure you want to PERMANENTLY revoke device ${device.id}?`)) return;
    try {
      await iotApiClient.revokeDevice(device.id, "Security key revocation by operator");
      setActionMessage({ text: `Device ${device.id} credentials permanently revoked.`, type: "success" });
      await loadAllData();
    } catch (err: any) {
      setActionMessage({ text: err.message || "Failed to revoke device", type: "error" });
    }
  };

  const handleRotateCredentials = async (device: IoTDevice) => {
    try {
      const res = await iotApiClient.rotateDeviceCredentials(device.id);
      setActionMessage({
        text: `Credentials rotated for ${device.id}. Prefix: ${res.key_prefix} (v${res.version})`,
        type: "success",
      });
      await loadAllData();
    } catch (err: any) {
      setActionMessage({ text: err.message || "Credential rotation failed", type: "error" });
    }
  };

  const handleSendCommand = async () => {
    if (!selectedDevice) return;
    try {
      const res = await iotApiClient.sendDeviceCommand(selectedDevice.id, selectedCommand, {});
      setCommandResult(res);
      setActionMessage({
        text: `Command ${selectedCommand} successfully executed on ${selectedDevice.id}.`,
        type: "success",
      });
      await loadAllData();
    } catch (err: any) {
      setCommandResult({ error: err.message });
      setActionMessage({
        text: `Command rejected: ${err.message}`,
        type: "error",
      });
    }
  };

  const handleRegisterDeviceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await iotApiClient.registerDevice(newDevice);
      setShowRegisterModal(false);
      setActionMessage({ text: `Device ${newDevice.id} registered successfully.`, type: "success" });
      await loadAllData();
    } catch (err: any) {
      setActionMessage({ text: err.message || "Registration failed", type: "error" });
    }
  };

  const handleCalibrationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await iotApiClient.registerCalibration(newCalibration);
      setShowCalibrationModal(false);
      setActionMessage({ text: `Calibration registered for ${newCalibration.sensor_id}.`, type: "success" });
      await loadAllData();
    } catch (err: any) {
      setActionMessage({ text: err.message || "Calibration registration failed", type: "error" });
    }
  };

  // Filtered devices
  const filteredDevices = devices.filter((d) => {
    const matchesSearch =
      d.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.manufacturer.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (d.pipeline_segment_id && d.pipeline_segment_id.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = filterType === "ALL" || d.device_type === filterType;
    const matchesStatus = filterStatus === "ALL" || d.status === filterStatus;
    return matchesSearch && matchesType && matchesStatus;
  });

  return (
    <div className="space-y-6 pb-12">
      {/* SECTION HEADER & SAFETY AIR-GAP BANNER */}
      <SectionHeader
        title="IoT & Hardware Gateway"
        description="Secure device ecosystem, real-time sensor telemetry ingestion, ISO-compliant calibration audits, and air-gapped hardware safety gateway."
        badge={
          <StatusBadge
            status="active"
            label="SAFETY AIR-GAP ACTIVE"
            pulse
            size="sm"
          />
        }
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadAllData}
              disabled={isLoading}
              className="border-slate-700 bg-slate-900 text-slate-200 hover:bg-slate-800"
            >
              <RefreshCw className={`h-4 w-4 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
              Refresh Fleet
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowRegisterModal(true)}
              className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold"
            >
              <Plus className="h-4 w-4 mr-1.5" />
              Register Device
            </Button>
          </div>
        }
      />

      {/* HARDWARE SAFETY ENFORCEMENT BANNER */}
      <div className="flex items-center justify-between p-3.5 rounded-lg border border-emerald-500/30 bg-emerald-950/20 text-emerald-300 text-xs shadow-sm">
        <div className="flex items-center gap-3">
          <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="font-semibold tracking-wide uppercase">Safety Guardrail:</span>
          <span className="text-emerald-200/90">
            <code>HARDWARE_ACTUATION_ENABLED = false</code>. Physical valve, pump, and rover actuation endpoints are strictly blocked and air-gapped by backend policy. Only allowlisted telemetry read and diagnostic operations are permitted.
          </span>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px] text-emerald-400">
          <Lock className="h-3.5 w-3.5" />
          SIMULATION-FIRST MODE
        </div>
      </div>

      {actionMessage && (
        <div
          className={`p-3 rounded-lg border text-xs flex items-center justify-between ${
            actionMessage.type === "success"
              ? "bg-cyan-950/40 border-cyan-500/40 text-cyan-200"
              : "bg-red-950/40 border-red-500/40 text-red-200"
          }`}
        >
          <span>{actionMessage.text}</span>
          <button
            onClick={() => setActionMessage(null)}
            className="text-slate-400 hover:text-white ml-4 font-bold"
          >
            ×
          </button>
        </div>
      )}

      {/* KPI METRIC CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard
          label="Registered Fleet"
          value={statusOverview?.metrics.total_devices ?? devices.length}
          unit="NODES"
          tone="cyan"
        />
        <MetricCard
          label="Active Ingestion"
          value={statusOverview?.metrics.active_devices ?? devices.filter((d) => d.status === "ACTIVE").length}
          unit="ONLINE"
          tone="emerald"
        />
        <MetricCard
          label="Degraded / Warning"
          value={statusOverview?.metrics.degraded_devices ?? devices.filter((d) => d.status === "DEGRADED").length}
          unit="CHECKS"
          tone="amber"
        />
        <MetricCard
          label="Quarantined / Revoked"
          value={
            (statusOverview?.metrics.quarantined_devices ?? 0) +
            (statusOverview?.metrics.revoked_devices ?? 0)
          }
          unit="ISOLATED"
          tone="rose"
        />
        <MetricCard
          label="MQTT Gateway"
          value={statusOverview?.mqtt_status.connected ? "TLS ONLINE" : "SIMULATION"}
          unit={statusOverview?.mqtt_status.connected ? "PORT 8883" : "IN-MEMORY"}
          tone={statusOverview?.mqtt_status.connected ? "emerald" : "cyan"}
        />
        <MetricCard
          label="Data Quality"
          value={`${statusOverview?.metrics.data_quality_pct ?? 98.4}%`}
          unit="VERIFIED"
          tone="emerald"
        />
      </div>

      {/* NAVIGATION TABS */}
      <div className="flex border-b border-slate-800 bg-slate-900/50 p-1 rounded-t-lg gap-1 overflow-x-auto text-xs">
        <button
          onClick={() => setActiveTab("overview")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-md font-medium transition-colors ${
            activeTab === "overview"
              ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <Activity className="h-4 w-4" />
          Fleet Overview & Intelligence
        </button>

        <button
          onClick={() => setActiveTab("registry")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-md font-medium transition-colors ${
            activeTab === "registry"
              ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <Cpu className="h-4 w-4" />
          Device Registry ({filteredDevices.length})
        </button>

        <button
          onClick={() => setActiveTab("telemetry")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-md font-medium transition-colors ${
            activeTab === "telemetry"
              ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <Radio className="h-4 w-4" />
          Live Telemetry & Provenance
        </button>

        <button
          onClick={() => setActiveTab("calibration")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-md font-medium transition-colors ${
            activeTab === "calibration"
              ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <FileCheck2 className="h-4 w-4" />
          Calibration Audits ({calibrations.length})
        </button>

        <button
          onClick={() => setActiveTab("connectivity")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-md font-medium transition-colors ${
            activeTab === "connectivity"
              ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <Wifi className="h-4 w-4" />
          MQTT & Edge Reliability
        </button>

        <button
          onClick={() => setActiveTab("security_audit")}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-md font-medium transition-colors ${
            activeTab === "security_audit"
              ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
          }`}
        >
          <Lock className="h-4 w-4" />
          Security & Audit Trail
        </button>
      </div>

      {/* TAB 1: FLEET OVERVIEW & CROSS-MODULE INTELLIGENCE */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* CROSS-MODULE BRIDGE: HYDRAULIC DIGITAL TWIN COMPARISON */}
            <Card variant="industrial" className="p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    <Database className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">Digital Twin Hydraulic Deviation Bridge</h3>
                    <p className="text-xs text-slate-400">Task 10 EPANET Baseline vs. Real-time IoT Ingestion</p>
                  </div>
                </div>
                <StatusBadge
                  status={digitalTwinComp?.hydraulic_deviation_status === "NORMAL" ? "active" : "warning"}
                  label={digitalTwinComp?.hydraulic_deviation_status || "NORMAL"}
                  size="sm"
                />
              </div>

              {digitalTwinComp ? (
                <div className="space-y-4 text-xs">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                    <div>
                      <span className="text-slate-400">Observed Pressure:</span>
                      <p className="text-base font-bold text-cyan-400 font-mono mt-0.5">
                        {digitalTwinComp.observed_pressure_bar.toFixed(2)} bar
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400">EPANET Twin Baseline:</span>
                      <p className="text-base font-bold text-slate-200 font-mono mt-0.5">
                        {digitalTwinComp.epanet_baseline_pressure_bar.toFixed(2)} bar
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400">Hydraulic Delta (ΔP):</span>
                      <p
                        className={`text-base font-bold font-mono mt-0.5 ${
                          Math.abs(digitalTwinComp.pressure_delta_bar) > 0.5 ? "text-amber-400" : "text-emerald-400"
                        }`}
                      >
                        {digitalTwinComp.pressure_delta_bar > 0 ? "+" : ""}
                        {digitalTwinComp.pressure_delta_bar.toFixed(2)} bar
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400">Model Residual:</span>
                      <p className="text-base font-bold text-slate-200 font-mono mt-0.5">
                        {digitalTwinComp.pressure_residual_pct.toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800/80 flex items-center justify-between">
                    <div>
                      <span className="text-slate-400">Target Pipeline Segment:</span>
                      <p className="font-mono text-cyan-300 font-semibold">{digitalTwinComp.pipeline_segment_id}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Observed Volumetric Flow:</span>
                      <p className="font-mono text-slate-200">{digitalTwinComp.observed_flow_lps ?? 89.5} L/s</p>
                    </div>
                    <div className="text-right">
                      <span className="text-slate-400">Twin Flow Estimate:</span>
                      <p className="font-mono text-slate-300">{digitalTwinComp.epanet_baseline_flow_lps ?? 87.2} L/s</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-slate-400 text-xs">Loading Digital Twin telemetry comparison...</div>
              )}
            </Card>

            {/* CROSS-MODULE BRIDGE: AI LEAK DETECTION ACOUSTIC ANALYSIS */}
            <Card variant="industrial" className="p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    <Sparkles className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">AI Acoustic Leak Detection Routing</h3>
                    <p className="text-xs text-slate-400">Task 07 Machine Learning Acoustic Classifier Bridge</p>
                  </div>
                </div>
                <StatusBadge
                  status={
                    acousticLeakAnalysis?.risk_severity === "CRITICAL" ||
                    acousticLeakAnalysis?.risk_severity === "HIGH"
                      ? "critical"
                      : "active"
                  }
                  label={acousticLeakAnalysis?.risk_severity || "NORMAL"}
                  size="sm"
                />
              </div>

              {acousticLeakAnalysis ? (
                <div className="space-y-4 text-xs">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                    <div>
                      <span className="text-slate-400">Source Device:</span>
                      <p className="text-sm font-bold text-slate-200 font-mono mt-0.5 truncate">
                        {acousticLeakAnalysis.device_id}
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400">Acoustic SPL:</span>
                      <p className="text-base font-bold text-purple-400 font-mono mt-0.5">
                        {acousticLeakAnalysis.acoustic_spl_db.toFixed(1)} dB
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400">Dominant Frequency:</span>
                      <p className="text-base font-bold text-cyan-400 font-mono mt-0.5">
                        {acousticLeakAnalysis.dominant_freq_hz.toFixed(0)} Hz
                      </p>
                    </div>
                    <div>
                      <span className="text-slate-400">Leak Probability:</span>
                      <p className="text-base font-bold text-amber-400 font-mono mt-0.5">
                        {acousticLeakAnalysis.leak_probability_pct.toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  <div className="p-3 bg-purple-950/20 rounded-lg border border-purple-500/20 text-purple-200">
                    <span className="font-semibold block mb-1">Autonomous Recommendation:</span>
                    <p className="text-[11px] leading-relaxed">{acousticLeakAnalysis.recommendation}</p>
                  </div>
                </div>
              ) : (
                <div className="text-slate-400 text-xs">Evaluating acoustic risk matrix...</div>
              )}
            </Card>
          </div>

          {/* DEVICE TYPE AND REGIONAL DISTRIBUTION CARDS */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card variant="industrial" className="p-5 space-y-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Layers className="h-4 w-4 text-cyan-400" />
                Fleet Composition by Sensor Type
              </h3>
              <div className="space-y-2 text-xs">
                {Object.entries(statusOverview?.metrics.by_device_type || {
                  ACOUSTIC_LOGGER: 1,
                  PRESSURE_SENSOR: 1,
                  FLOW_METER: 1,
                  MOISTURE_PROBE: 1,
                  OPTICAL_CAMERA: 1,
                  VIRTUAL_SENSOR: 1,
                }).map(([type, count]) => (
                  <div
                    key={type}
                    className="flex items-center justify-between p-2 rounded bg-slate-900/60 border border-slate-800"
                  >
                    <span className="text-slate-300 font-mono">{type.replace("_", " ")}</span>
                    <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 font-bold border border-cyan-800/40">
                      {count} {count === 1 ? "unit" : "units"}
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            <Card variant="industrial" className="p-5 space-y-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Compass className="h-4 w-4 text-cyan-400" />
                DMA Geographical Distribution
              </h3>
              <div className="space-y-2 text-xs">
                {Object.entries(statusOverview?.metrics.by_dma_zone || {
                  "DMA-NORTH-04": 5,
                  "DMA-CENTRAL-01": 1,
                }).map(([zone, count]) => (
                  <div
                    key={zone}
                    className="flex items-center justify-between p-2 rounded bg-slate-900/60 border border-slate-800"
                  >
                    <span className="text-slate-300 font-mono">{zone}</span>
                    <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 font-bold border border-emerald-800/40">
                      {count} {count === 1 ? "sensor" : "sensors"}
                    </span>
                  </div>
                ))}
              </div>
            </Card>

            <Card variant="industrial" className="p-5 space-y-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
                Proven ISO Sensor Calibration Health
              </h3>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center bg-slate-900/60 p-2.5 rounded border border-slate-800">
                  <span className="text-slate-400">Total Instrument Sensors:</span>
                  <span className="font-bold text-white font-mono">
                    {statusOverview?.metrics.total_sensors ?? 10}
                  </span>
                </div>
                <div className="flex justify-between items-center bg-slate-900/60 p-2.5 rounded border border-slate-800">
                  <span className="text-emerald-400">Calibrated & Within Spec:</span>
                  <span className="font-bold text-emerald-400 font-mono">
                    {statusOverview?.metrics.calibrated_sensors ?? 8}
                  </span>
                </div>
                <div className="flex justify-between items-center bg-slate-900/60 p-2.5 rounded border border-slate-800">
                  <span className="text-amber-400">Overdue / Recalibration Required:</span>
                  <span className="font-bold text-amber-400 font-mono">
                    {statusOverview?.metrics.overdue_calibrations ?? 2}
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setActiveTab("calibration");
                  }}
                  className="w-full border-slate-700 text-xs text-slate-300 hover:text-white"
                >
                  Inspect Calibration Audit Trail
                </Button>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 2: DEVICE REGISTRY */}
      {activeTab === "registry" && (
        <div className="space-y-4">
          {/* SEARCH AND FILTER BAR */}
          <div className="flex flex-col sm:flex-row items-center gap-3">
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search device by ID, name, manufacturer, or pipeline..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex items-center gap-2 w-full sm:w-auto">
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
              >
                <option value="ALL">All Device Types</option>
                <option value="ACOUSTIC_LOGGER">Acoustic Logger</option>
                <option value="PRESSURE_SENSOR">Pressure Sensor</option>
                <option value="FLOW_METER">Flowmeter</option>
                <option value="MOISTURE_PROBE">Moisture Probe</option>
                <option value="OPTICAL_CAMERA">Optical Camera</option>
                <option value="VIRTUAL_SENSOR">Virtual Sensor</option>
              </select>

              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
              >
                <option value="ALL">All Statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="DEGRADED">Degraded</option>
                <option value="OFFLINE">Offline</option>
                <option value="QUARANTINED">Quarantined</option>
                <option value="REVOKED">Revoked</option>
              </select>
            </div>
          </div>

          {/* DEVICE REGISTRY DATA TABLE */}
          <Card variant="industrial" className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 select-none">
                  <tr>
                    <th className="py-3 px-4 font-semibold">Device ID & Name</th>
                    <th className="py-3 px-3 font-semibold">Type</th>
                    <th className="py-3 px-3 font-semibold">Status</th>
                    <th className="py-3 px-3 font-semibold">Location (DMA / Pipe)</th>
                    <th className="py-3 px-3 font-semibold">Battery</th>
                    <th className="py-3 px-3 font-semibold">Protocol</th>
                    <th className="py-3 px-4 font-semibold text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {filteredDevices.map((device) => (
                    <tr
                      key={device.id}
                      onClick={() => setSelectedDevice(device)}
                      className={`hover:bg-slate-800/30 transition-colors cursor-pointer ${
                        selectedDevice?.id === device.id ? "bg-cyan-950/20" : ""
                      }`}
                    >
                      <td className="py-3 px-4">
                        <div className="font-bold text-white text-xs">{device.id}</div>
                        <div className="text-[11px] text-slate-400 font-sans truncate max-w-xs">{device.name}</div>
                        <div className="text-[10px] text-slate-500 font-sans">{device.manufacturer}</div>
                      </td>
                      <td className="py-3 px-3 text-slate-300">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 border border-slate-700">
                          {device.device_type}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <StatusBadge
                          status={
                            device.status === "ACTIVE"
                              ? "active"
                              : device.status === "DEGRADED"
                              ? "warning"
                              : device.status === "QUARANTINED" || device.status === "REVOKED"
                              ? "critical"
                              : "offline"
                          }
                          label={device.status}
                          size="sm"
                        />
                      </td>
                      <td className="py-3 px-3 text-slate-400 text-[11px]">
                        <div>{device.dma_zone || "N/A"}</div>
                        <div className="text-cyan-400 text-[10px]">{device.pipeline_segment_id || "Unassigned"}</div>
                      </td>
                      <td className="py-3 px-3 text-slate-300">
                        <div className="flex items-center gap-1.5">
                          <Battery
                            className={`h-3.5 w-3.5 ${
                              (device.battery_level_pct ?? 100) > 50
                                ? "text-emerald-400"
                                : (device.battery_level_pct ?? 100) > 20
                                ? "text-amber-400"
                                : "text-rose-400"
                            }`}
                          />
                          <span>{device.battery_level_pct !== undefined ? `${device.battery_level_pct.toFixed(0)}%` : "AC"}</span>
                        </div>
                      </td>
                      <td className="py-3 px-3 text-slate-400 text-[11px]">
                        {device.communication_protocol}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1 font-sans">
                          <button
                            title="Rotate Device Credentials"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRotateCredentials(device);
                            }}
                            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-cyan-300 transition-colors"
                          >
                            <Key className="h-3.5 w-3.5" />
                          </button>
                          <button
                            title="Quarantine Device"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleQuarantine(device);
                            }}
                            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-amber-400 transition-colors"
                          >
                            <ShieldAlert className="h-3.5 w-3.5" />
                          </button>
                          <button
                            title="Allowlisted Non-Actuating Diagnostics"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedDevice(device);
                              setShowCommandModal(true);
                            }}
                            className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-emerald-400 transition-colors"
                          >
                            <Terminal className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* SELECTED DEVICE INSPECTOR DRAWER */}
          {selectedDevice && (
            <Card variant="industrial" className="p-5 space-y-4 border-cyan-500/30">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    <Cpu className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white font-mono">{selectedDevice.id}</h3>
                    <p className="text-xs text-slate-400">{selectedDevice.name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge
                    status={selectedDevice.status === "ACTIVE" ? "active" : "warning"}
                    label={selectedDevice.status}
                    size="sm"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowCommandModal(true)}
                    className="border-slate-700 text-xs text-cyan-300 hover:bg-cyan-950/40"
                  >
                    <Terminal className="h-3.5 w-3.5 mr-1" />
                    Run Diagnostic Check
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
                <div>
                  <span className="text-slate-400 block mb-0.5">Hardware Version:</span>
                  <span className="font-mono text-slate-200">{selectedDevice.hardware_version}</span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Firmware Version:</span>
                  <span className="font-mono text-slate-200">{selectedDevice.firmware_version}</span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">MAC / Link Address:</span>
                  <span className="font-mono text-slate-200">{selectedDevice.mac_address || "VIRTUAL_MAC"}</span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-0.5">Power Profile:</span>
                  <span className="font-mono text-slate-200">{selectedDevice.power_source}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex flex-wrap gap-2 text-xs">
                <span className="text-slate-400">Supported Sensor Transducers:</span>
                {selectedDevice.supported_sensor_types.map((st) => (
                  <span key={st} className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-cyan-300 font-mono text-[11px]">
                    {st}
                  </span>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* TAB 3: LIVE TELEMETRY & PROVENANCE */}
      {activeTab === "telemetry" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Radio className="h-4 w-4 text-cyan-400" />
              Real-Time Normalized Telemetry Ingestion Feed
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              6-Tier Provenance Classification Enforced
            </span>
          </div>

          <Card variant="industrial" className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold select-none">
                  <tr>
                    <th className="py-3 px-4">Timestamp (UTC)</th>
                    <th className="py-3 px-3">Device ID</th>
                    <th className="py-3 px-3">Sensor Type</th>
                    <th className="py-3 px-3">Reading Value</th>
                    <th className="py-3 px-3">Quality Tier</th>
                    <th className="py-3 px-3">Evidence Provenance</th>
                    <th className="py-3 px-4">Pipeline Segment</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {telemetries.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 text-slate-400 text-[11px]">
                        {new Date(t.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-3 px-3 text-cyan-300 font-bold">{t.device_id}</td>
                      <td className="py-3 px-3 text-slate-300 font-sans text-[11px]">{t.sensor_type}</td>
                      <td className="py-3 px-3">
                        <span className="text-white font-bold text-xs">{t.reading_value.toFixed(2)}</span>{" "}
                        <span className="text-slate-400 text-[10px]">{t.unit}</span>
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-sans font-bold border ${
                            t.data_quality === "VALID"
                              ? "bg-emerald-950/60 text-emerald-300 border-emerald-500/30"
                              : t.data_quality === "SUSPECT"
                              ? "bg-amber-950/60 text-amber-300 border-amber-500/30"
                              : "bg-rose-950/60 text-rose-300 border-rose-500/30"
                          }`}
                        >
                          {t.data_quality}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-sans font-semibold border ${
                            t.provenance === "MEASURED"
                              ? "bg-cyan-950/60 text-cyan-300 border-cyan-500/30"
                              : t.provenance === "SIMULATED"
                              ? "bg-purple-950/60 text-purple-300 border-purple-500/30"
                              : "bg-slate-800 text-slate-300 border-slate-700"
                          }`}
                        >
                          {t.provenance}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-[11px]">
                        {t.pipeline_segment_id || "DMA Network"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 4: CALIBRATION AUDITS */}
      {activeTab === "calibration" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Sensor Calibration Registry & Schedule Audits</h3>
              <p className="text-xs text-slate-400">ISO 17025 conformity verification, accuracy tolerance and due date tracking</p>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                if (devices.length > 0) {
                  setNewCalibration((prev) => ({
                    ...prev,
                    device_id: devices[0].id,
                    sensor_id: `SNS-${devices[0].id}-PRIMARY`,
                  }));
                }
                setShowCalibrationModal(true);
              }}
              className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs"
            >
              <Plus className="h-3.5 w-3.5 mr-1" />
              Record Calibration
            </Button>
          </div>

          <Card variant="industrial" className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold select-none">
                  <tr>
                    <th className="py-3 px-4">Sensor & Device ID</th>
                    <th className="py-3 px-3">Calibration Date</th>
                    <th className="py-3 px-3">Next Due Date</th>
                    <th className="py-3 px-3">Method & Standard</th>
                    <th className="py-3 px-3">Accuracy Tolerance</th>
                    <th className="py-3 px-3">Technician</th>
                    <th className="py-3 px-4 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {calibrations.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-bold text-white text-xs">{c.sensor_id}</div>
                        <div className="text-[11px] text-cyan-400 font-sans">{c.device_id}</div>
                      </td>
                      <td className="py-3 px-3 text-slate-300">
                        {new Date(c.calibration_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-3 text-slate-300">
                        {new Date(c.next_due_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-3 text-slate-300 font-sans">
                        <div className="font-semibold text-slate-200">{c.calibration_method}</div>
                        <div className="text-[10px] text-slate-500 font-mono">{c.calibration_reference}</div>
                      </td>
                      <td className="py-3 px-3 text-slate-300 font-mono">
                        ±{c.accuracy_tolerance.toFixed(2)}%
                      </td>
                      <td className="py-3 px-3 text-slate-400 font-sans text-[11px]">
                        {c.technician || "Authorized Lab"}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <StatusBadge
                          status={c.status === "CALIBRATED" ? "active" : c.status === "DUE" ? "warning" : "critical"}
                          label={c.status}
                          size="sm"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* TAB 5: MQTT CONNECTIVITY & EDGE RELIABILITY */}
      {activeTab === "connectivity" && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card variant="industrial" className="p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                    <Wifi className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">MQTT Broker & Gateway Architecture</h3>
                    <p className="text-xs text-slate-400">Paho MQTT 2.0 Client with TLS/mTLS Fallback Support</p>
                  </div>
                </div>
                <StatusBadge
                  status={statusOverview?.mqtt_status.connected ? "active" : "warning"}
                  label={statusOverview?.mqtt_status.connected ? "TLS BROKER CONNECTED" : "IN-MEMORY SIMULATION"}
                  size="sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block mb-1">Broker Target:</span>
                  <span className="font-mono text-cyan-300 font-bold">
                    {statusOverview?.mqtt_status.broker_host}:{statusOverview?.mqtt_status.broker_port}
                  </span>
                </div>
                <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block mb-1">TLS / mTLS Encryption:</span>
                  <span className="font-mono text-emerald-400 font-bold">
                    {statusOverview?.mqtt_status.use_tls ? "ENABLED (X.509)" : "DISABLED"}
                  </span>
                </div>
                <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block mb-1">Messages Ingested:</span>
                  <span className="font-mono text-white font-bold">
                    {statusOverview?.mqtt_status.messages_received.toLocaleString()} pkts
                  </span>
                </div>
                <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                  <span className="text-slate-400 block mb-1">Rate Limit Drops:</span>
                  <span className="font-mono text-slate-300 font-bold">
                    {statusOverview?.mqtt_status.rate_limited_count ?? 0}
                  </span>
                </div>
              </div>

              <div className="space-y-2 text-xs">
                <span className="text-slate-400 block font-semibold">Active Subscribed MQTT Topics:</span>
                <div className="space-y-1 font-mono text-[11px]">
                  <div className="p-2 rounded bg-slate-900 border border-slate-800 text-cyan-300">
                    aquacrew/devices/+/telemetry
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800 text-cyan-300">
                    aquacrew/devices/+/status
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800 text-cyan-300">
                    aquacrew/devices/+/events
                  </div>
                </div>
              </div>
            </Card>

            <Card variant="industrial" className="p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <Server className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-white">Edge Bounded Buffer & Retransmission</h3>
                    <p className="text-xs text-slate-400">Offline store-and-forward engine with exponential backoff</p>
                  </div>
                </div>
                <StatusBadge status="active" label="BUFFER READY" size="sm" />
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Ring Buffer Capacity:</span>
                    <span className="font-mono text-white font-bold">1,000 readings per node</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Max MQTT Payload Size:</span>
                    <span className="font-mono text-emerald-400 font-bold">64 KB max frame limit</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Per-Device Ingestion Rate Limit:</span>
                    <span className="font-mono text-cyan-400 font-bold">60 requests / minute</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Deduplication Window:</span>
                    <span className="font-mono text-slate-300 font-bold">300 seconds</span>
                  </div>
                </div>

                <div className="p-3 bg-emerald-950/20 rounded-lg border border-emerald-500/20 text-emerald-200">
                  <span className="font-semibold block mb-1">Clock Drift Compensation:</span>
                  <p className="text-[11px] leading-relaxed">
                    Edge readings carry device timestamps which are compared against gateway UTC time upon ingestion. Readings with delta exceeding 10 minutes are tagged <code>STALE</code> or <code>OUT_OF_BOUNDS</code> to preserve historical provenance.
                  </p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 6: SECURITY & AUDIT TRAIL */}
      {activeTab === "security_audit" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Zero-Trust Device Security & Operational Audit Log</h3>
              <p className="text-xs text-slate-400">Immutable ledger of command executions, credential rotations, and safety blocks</p>
            </div>
            <StatusBadge status="active" label="ADMIN AUDIT LOG" size="sm" />
          </div>

          <Card variant="industrial" className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold select-none">
                  <tr>
                    <th className="py-3 px-4">Timestamp (UTC)</th>
                    <th className="py-3 px-3">Device Target</th>
                    <th className="py-3 px-3">Security Action</th>
                    <th className="py-3 px-3">Actor / Principal</th>
                    <th className="py-3 px-3">Origin IP</th>
                    <th className="py-3 px-3">Status</th>
                    <th className="py-3 px-4">Event Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 text-slate-400 text-[11px]">
                        {log.timestamp ? new Date(log.timestamp).toLocaleString() : "N/A"}
                      </td>
                      <td className="py-3 px-3 text-cyan-300 font-bold">{log.device_id || "GATEWAY"}</td>
                      <td className="py-3 px-3 text-white font-semibold font-sans">{log.action}</td>
                      <td className="py-3 px-3 text-slate-300 font-sans">{log.actor || "system"}</td>
                      <td className="py-3 px-3 text-slate-400">{log.ip_address || "internal"}</td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-sans font-bold border ${
                            log.status === "SUCCESS"
                              ? "bg-emerald-950/60 text-emerald-300 border-emerald-500/30"
                              : "bg-rose-950/60 text-rose-300 border-rose-500/30"
                          }`}
                        >
                          {log.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-[11px] truncate max-w-xs font-sans">
                        {log.details ? JSON.stringify(log.details) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* MODAL: REGISTER DEVICE */}
      <Modal
        isOpen={showRegisterModal}
        onClose={() => setShowRegisterModal(false)}
        title="Register New IoT Field Sensor / Node"
      >
        <form onSubmit={handleRegisterDeviceSubmit} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-slate-400 block mb-1">Device ID:</label>
              <input
                type="text"
                value={newDevice.id}
                onChange={(e) => setNewDevice({ ...newDevice, id: e.target.value })}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white font-mono focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Device Type:</label>
              <select
                value={newDevice.device_type}
                onChange={(e) => setNewDevice({ ...newDevice, device_type: e.target.value as any })}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:border-cyan-500"
              >
                <option value="ACOUSTIC_LOGGER">Acoustic Logger</option>
                <option value="PRESSURE_SENSOR">Pressure Sensor</option>
                <option value="FLOW_METER">Flowmeter</option>
                <option value="MOISTURE_PROBE">Moisture Probe</option>
                <option value="OPTICAL_CAMERA">Optical Camera</option>
                <option value="VIRTUAL_SENSOR">Virtual Sensor</option>
              </select>
            </div>
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Device Name:</label>
            <input
              type="text"
              value={newDevice.name}
              onChange={(e) => setNewDevice({ ...newDevice, name: e.target.value })}
              required
              className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:border-cyan-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-slate-400 block mb-1">Manufacturer:</label>
              <input
                type="text"
                value={newDevice.manufacturer}
                onChange={(e) => setNewDevice({ ...newDevice, manufacturer: e.target.value })}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Hardware Version:</label>
              <input
                type="text"
                value={newDevice.hardware_version}
                onChange={(e) => setNewDevice({ ...newDevice, hardware_version: e.target.value })}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:border-cyan-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-slate-400 block mb-1">DMA Zone:</label>
              <input
                type="text"
                value={newDevice.dma_zone}
                onChange={(e) => setNewDevice({ ...newDevice, dma_zone: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Pipeline Segment ID:</label>
              <input
                type="text"
                value={newDevice.pipeline_segment_id}
                onChange={(e) => setNewDevice({ ...newDevice, pipeline_segment_id: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:border-cyan-500"
              />
            </div>
          </div>

          <div className="p-3 bg-cyan-950/30 border border-cyan-800/40 rounded text-cyan-300 text-[11px]">
            Registration automatically provisions a cryptographic API key and assigns default allowlisted diagnostic permissions.
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowRegisterModal(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" className="bg-cyan-500 text-slate-950 font-bold">
              Confirm Registration
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL: RECORD CALIBRATION */}
      <Modal
        isOpen={showCalibrationModal}
        onClose={() => setShowCalibrationModal(false)}
        title="Record Sensor Calibration Record"
      >
        <form onSubmit={handleCalibrationSubmit} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-slate-400 block mb-1">Target Device:</label>
              <select
                value={newCalibration.device_id}
                onChange={(e) =>
                  setNewCalibration({
                    ...newCalibration,
                    device_id: e.target.value,
                    sensor_id: `SNS-${e.target.value}-PRIMARY`,
                  })
                }
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white font-mono focus:border-cyan-500"
              >
                {devices.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.id} ({d.device_type})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Sensor ID:</label>
              <input
                type="text"
                value={newCalibration.sensor_id}
                onChange={(e) => setNewCalibration({ ...newCalibration, sensor_id: e.target.value })}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white font-mono focus:border-cyan-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-slate-400 block mb-1">Calibration Method:</label>
              <select
                value={newCalibration.calibration_method}
                onChange={(e) => setNewCalibration({ ...newCalibration, calibration_method: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:border-cyan-500"
              >
                <option value="DEADWEIGHT_TESTER">Deadweight Tester</option>
                <option value="ACOUSTIC_CALIBRATOR_94DB">Acoustic Calibrator 94dB</option>
                <option value="GRAVIMETRIC_SAMPLE">Gravimetric Sample</option>
                <option value="OPTICAL_NEPHELOMETRY">Optical Nephelometry</option>
                <option value="DIGITAL_REFERENCE_METER">Digital Reference Meter</option>
              </select>
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Accuracy Tolerance (±%):</label>
              <input
                type="number"
                step="0.05"
                value={newCalibration.accuracy_tolerance}
                onChange={(e) =>
                  setNewCalibration({ ...newCalibration, accuracy_tolerance: parseFloat(e.target.value) })
                }
                required
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white font-mono focus:border-cyan-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-slate-400 block mb-1">Reference Standard ID:</label>
              <input
                type="text"
                value={newCalibration.calibration_reference}
                onChange={(e) => setNewCalibration({ ...newCalibration, calibration_reference: e.target.value })}
                required
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white font-mono focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="text-slate-400 block mb-1">Technician / Lab:</label>
              <input
                type="text"
                value={newCalibration.technician}
                onChange={(e) => setNewCalibration({ ...newCalibration, technician: e.target.value })}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white focus:border-cyan-500"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setShowCalibrationModal(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" size="sm" className="bg-cyan-500 text-slate-950 font-bold">
              Record Calibration
            </Button>
          </div>
        </form>
      </Modal>

      {/* MODAL: RUN ALLOWLISTED COMMAND */}
      <Modal
        isOpen={showCommandModal}
        onClose={() => {
          setShowCommandModal(false);
          setCommandResult(null);
        }}
        title={`Run Allowlisted Command: ${selectedDevice?.id}`}
      >
        <div className="space-y-4 text-xs">
          <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded text-emerald-300">
            <strong>Allowlisted Safety Commands Only:</strong>
            <p className="text-[11px] mt-1 text-emerald-200/90">
              Only diagnostic, status check, and battery querying commands are permitted. Physical valve, pump, or rover actuation commands are strictly blocked.
            </p>
          </div>

          <div>
            <label className="text-slate-400 block mb-1">Select Command:</label>
            <select
              value={selectedCommand}
              onChange={(e) => setSelectedCommand(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white font-mono focus:border-cyan-500"
            >
              <option value="RUN_DEVICE_DIAGNOSTICS">RUN_DEVICE_DIAGNOSTICS</option>
              <option value="GET_DEVICE_STATUS">GET_DEVICE_STATUS</option>
              <option value="PING_DEVICE">PING_DEVICE</option>
              <option value="REQUEST_BATTERY_REPORT">REQUEST_BATTERY_REPORT</option>
              <option value="READ_SENSOR_CONFIG">READ_SENSOR_CONFIG</option>
              <option value="VERIFY_CALIBRATION_STATUS">VERIFY_CALIBRATION_STATUS</option>
              <option value="CLOSE_VALVE" className="text-rose-400 font-bold">
                CLOSE_VALVE (PROHIBITED TEST)
              </option>
            </select>
          </div>

          {commandResult && (
            <div className="p-3 bg-slate-950 rounded border border-slate-800 font-mono text-[11px]">
              <span className="text-slate-400 block mb-1">Command Output:</span>
              <pre className="text-cyan-300 overflow-x-auto whitespace-pre-wrap">
                {JSON.stringify(commandResult, null, 2)}
              </pre>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setShowCommandModal(false);
                setCommandResult(null);
              }}
            >
              Close
            </Button>
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={handleSendCommand}
              className="bg-cyan-500 text-slate-950 font-bold"
            >
              Dispatch Command
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
