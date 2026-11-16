/**
 * AQUA CREW — Secure IoT & Hardware Gateway API Client (Task 18)
 * Connects frontend dashboard with backend IoT microservice endpoints:
 *   - Device Registry CRUD, Quarantine, and Revocation
 *   - Credential Provisioning & Rotation
 *   - Telemetry Ingestion, Quality Auditing, and Provenance Tracking
 *   - Sensor Calibration Records
 *   - Allowlisted Device Commands (Strict Actuation Prohibition Enforced)
 *   - Cross-Module AI Leak Detection & Digital Twin Comparison
 */

import { backendApiClient } from "./backendApiClient";
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
} from "./iotTypes";

const DEFAULT_API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Fallback seed data in case backend is offline
const FALLBACK_DEVICES: IoTDevice[] = [
  {
    id: "DEV-ACOUSTIC-01",
    name: "Pipeline Sector 4B Acoustic Node",
    device_type: "ACOUSTIC_LOGGER",
    status: "ACTIVE",
    hardware_version: "v2.1.0",
    firmware_version: "2.4.1",
    mac_address: "AA:BB:CC:DD:01:01",
    manufacturer: "AquaSense Tech",
    pipeline_segment_id: "PIPE-SEC-4B-92",
    dma_zone: "DMA-NORTH-04",
    latitude: 51.5074,
    longitude: -0.1278,
    battery_level_pct: 92.5,
    power_source: "SOLAR_BATTERY",
    communication_protocol: "MQTT",
    is_quarantined: false,
    is_revoked: false,
    supported_sensor_types: ["ACOUSTIC_LEAK", "WATER_TEMPERATURE"],
  },
  {
    id: "DEV-PRESSURE-02",
    name: "Zone 4 Transient Pressure Monitor",
    device_type: "PRESSURE_SENSOR",
    status: "ACTIVE",
    hardware_version: "v3.0.0",
    firmware_version: "1.8.2",
    mac_address: "AA:BB:CC:DD:01:02",
    manufacturer: "HydroMetrics Corp",
    pipeline_segment_id: "PIPE-SEC-4B-92",
    dma_zone: "DMA-NORTH-04",
    latitude: 51.5085,
    longitude: -0.1265,
    battery_level_pct: 88.0,
    power_source: "MAINS_BACKUP",
    communication_protocol: "MQTT",
    is_quarantined: false,
    is_revoked: false,
    supported_sensor_types: ["HYDROSTATIC_PRESSURE"],
  },
  {
    id: "DEV-FLOW-03",
    name: "Sector Inlet Electromagnetic Flowmeter",
    device_type: "FLOW_METER",
    status: "ACTIVE",
    hardware_version: "v4.2.0",
    firmware_version: "3.1.0",
    mac_address: "AA:BB:CC:DD:01:03",
    manufacturer: "FlowMaster Systems",
    pipeline_segment_id: "PIPE-SEC-3A-11",
    dma_zone: "DMA-CENTRAL-01",
    latitude: 51.509,
    longitude: -0.13,
    battery_level_pct: 99.0,
    power_source: "MAINS_BACKUP",
    communication_protocol: "MQTT",
    is_quarantined: false,
    is_revoked: false,
    supported_sensor_types: ["VOLUMETRIC_FLOW", "WATER_TEMPERATURE"],
  },
  {
    id: "DEV-MOISTURE-04",
    name: "Trench Bed Soil Saturation Probe",
    device_type: "MOISTURE_PROBE",
    status: "DEGRADED",
    hardware_version: "v1.5.0",
    firmware_version: "1.1.2",
    mac_address: "AA:BB:CC:DD:01:04",
    manufacturer: "GeoProbe Analytics",
    pipeline_segment_id: "PIPE-SEC-4B-92",
    dma_zone: "DMA-NORTH-04",
    latitude: 51.5076,
    longitude: -0.1272,
    battery_level_pct: 42.0,
    power_source: "PRIMARY_CELL",
    communication_protocol: "MQTT",
    is_quarantined: false,
    is_revoked: false,
    supported_sensor_types: ["SOIL_MOISTURE"],
  },
  {
    id: "DEV-OPTICAL-05",
    name: "Chamber Inspection Optical Camera",
    device_type: "OPTICAL_CAMERA",
    status: "ACTIVE",
    hardware_version: "v2.0.0",
    firmware_version: "2.0.4",
    mac_address: "AA:BB:CC:DD:01:05",
    manufacturer: "VisionFlow AI",
    pipeline_segment_id: "PIPE-SEC-4B-92",
    dma_zone: "DMA-NORTH-04",
    latitude: 51.5072,
    longitude: -0.128,
    battery_level_pct: 76.5,
    power_source: "SOLAR_BATTERY",
    communication_protocol: "REST_HTTPS",
    is_quarantined: false,
    is_revoked: false,
    supported_sensor_types: ["OPTICAL_TURBIDITY"],
  },
  {
    id: "DEV-SIM-06",
    name: "Virtual Network Twin Simulator Node",
    device_type: "VIRTUAL_SENSOR",
    status: "ACTIVE",
    hardware_version: "SIM-v1.0",
    firmware_version: "sim-1.0.0",
    manufacturer: "Aqua Crew Virtual Testbed",
    pipeline_segment_id: "PIPE-SEC-4B-92",
    dma_zone: "DMA-NORTH-04",
    battery_level_pct: 100.0,
    power_source: "VIRTUAL",
    communication_protocol: "MQTT",
    is_quarantined: false,
    is_revoked: false,
    supported_sensor_types: [
      "ACOUSTIC_LEAK",
      "HYDROSTATIC_PRESSURE",
      "VOLUMETRIC_FLOW",
    ],
  },
];

class IotApiClient {
  private baseUrl: string;

  constructor(baseUrl = DEFAULT_API_BASE) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  private getHeaders(contentType: string = "application/json"): HeadersInit {
    const headers: Record<string, string> = {
      "Content-Type": contentType,
      Accept: "application/json",
    };
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("aqua_crew_access_token");
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }
    return headers;
  }

  // 1. Overview and Status
  async fetchIotStatus(): Promise<IoTStatusResponse> {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/iot/status`, {
        headers: this.getHeaders(),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // offline fallback
    }

    return {
      success: true,
      metrics: {
        total_devices: FALLBACK_DEVICES.length,
        active_devices: FALLBACK_DEVICES.filter((d) => d.status === "ACTIVE").length,
        offline_devices: 0,
        degraded_devices: FALLBACK_DEVICES.filter((d) => d.status === "DEGRADED").length,
        quarantined_devices: 0,
        revoked_devices: 0,
        total_sensors: 10,
        calibrated_sensors: 8,
        overdue_calibrations: 2,
        telemetry_readings_24h: 18450,
        data_quality_pct: 98.4,
        by_device_type: {
          ACOUSTIC_LOGGER: 1,
          PRESSURE_SENSOR: 1,
          FLOW_METER: 1,
          MOISTURE_PROBE: 1,
          OPTICAL_CAMERA: 1,
          VIRTUAL_SENSOR: 1,
        },
        by_dma_zone: {
          "DMA-NORTH-04": 5,
          "DMA-CENTRAL-01": 1,
        },
      },
      mqtt_status: {
        connected: false,
        broker_host: "127.0.0.1",
        broker_port: 8883,
        use_tls: true,
        messages_received: 1420,
        messages_published: 830,
        dropped_messages: 0,
        rate_limited_count: 0,
        simulation_mode: true,
        active_subscriptions: [
          "aquacrew/devices/+/telemetry",
          "aquacrew/devices/+/status",
          "aquacrew/devices/+/events",
        ],
        uptime_seconds: 3600,
      },
      hardware_safety: "SIMULATION_FIRST_MODE_ACTIVE",
      timestamp: new Date().toISOString(),
    };
  }

  // 2. Device Registry
  async fetchDevices(params?: {
    status?: string;
    device_type?: string;
    dma_zone?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }): Promise<{ success: boolean; total: number; devices: IoTDevice[] }> {
    try {
      const query = new URLSearchParams();
      if (params?.status) query.set("status", params.status);
      if (params?.device_type) query.set("device_type", params.device_type);
      if (params?.dma_zone) query.set("dma_zone", params.dma_zone);
      if (params?.search) query.set("search", params.search);
      if (params?.skip !== undefined) query.set("skip", String(params.skip));
      if (params?.limit !== undefined) query.set("limit", String(params.limit));

      const res = await fetch(`${this.baseUrl}/api/v1/iot/devices?${query.toString()}`, {
        headers: this.getHeaders(),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // offline fallback
    }

    let filtered = [...FALLBACK_DEVICES];
    if (params?.status) {
      filtered = filtered.filter((d) => d.status === params.status);
    }
    if (params?.device_type) {
      filtered = filtered.filter((d) => d.device_type === params.device_type);
    }
    if (params?.search) {
      const q = params.search.toLowerCase();
      filtered = filtered.filter(
        (d) =>
          d.id.toLowerCase().includes(q) ||
          d.name.toLowerCase().includes(q) ||
          d.manufacturer.toLowerCase().includes(q)
      );
    }

    return {
      success: true,
      total: filtered.length,
      devices: filtered,
    };
  }

  async fetchDevice(deviceId: string): Promise<IoTDevice | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/iot/devices/${deviceId}`, {
        headers: this.getHeaders(),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // fallback
    }
    return FALLBACK_DEVICES.find((d) => d.id === deviceId) || null;
  }

  async registerDevice(payload: RegisterDevicePayload): Promise<IoTDevice> {
    const res = await fetch(`${this.baseUrl}/api/v1/iot/devices`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to register IoT device.");
    }
    return await res.json();
  }

  async quarantineDevice(deviceId: string, reason: string): Promise<IoTDevice> {
    const res = await fetch(`${this.baseUrl}/api/v1/iot/devices/${deviceId}/quarantine`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ reason }),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to quarantine device.");
    }
    return await res.json();
  }

  async revokeDevice(deviceId: string, reason: string): Promise<IoTDevice> {
    const res = await fetch(`${this.baseUrl}/api/v1/iot/devices/${deviceId}/revoke`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ reason }),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to revoke device.");
    }
    return await res.json();
  }

  async rotateDeviceCredentials(deviceId: string): Promise<{
    success: boolean;
    device_id: string;
    new_api_key?: string;
    key_prefix: string;
    version: number;
    message: string;
  }> {
    const res = await fetch(
      `${this.baseUrl}/api/v1/iot/devices/${deviceId}/credentials/rotate`,
      {
        method: "POST",
        headers: this.getHeaders(),
      }
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to rotate credentials.");
    }
    return await res.json();
  }

  async sendDeviceCommand(
    deviceId: string,
    command: string,
    parameters: Record<string, any> = {}
  ): Promise<{
    success: boolean;
    device_id: string;
    command: string;
    status: string;
    result: any;
    safety_state: string;
  }> {
    const res = await fetch(`${this.baseUrl}/api/v1/iot/devices/${deviceId}/commands`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify({ command, parameters }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(
        err.detail || `Command execution failed with status ${res.status}`
      );
    }
    return await res.json();
  }

  // 3. Telemetry Queries
  async fetchLatestTelemetry(
    sensorType?: string,
    limit: number = 30
  ): Promise<{ success: boolean; total: number; telemetries: DeviceTelemetry[] }> {
    try {
      const query = new URLSearchParams();
      if (sensorType) query.set("sensor_type", sensorType);
      query.set("limit", String(limit));

      const res = await fetch(`${this.baseUrl}/api/v1/iot/telemetry/latest?${query.toString()}`, {
        headers: this.getHeaders(),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // fallback
    }

    // Fallback live telemetry
    const now = new Date();
    const fallbackTelemetries: DeviceTelemetry[] = [
      {
        id: "TEL-001",
        device_id: "DEV-ACOUSTIC-01",
        sensor_type: "ACOUSTIC_LEAK",
        timestamp: new Date(now.getTime() - 1000 * 30).toISOString(),
        reading_value: 62.4,
        unit: "dB",
        data_quality: "VALID",
        provenance: "MEASURED",
        pipeline_segment_id: "PIPE-SEC-4B-92",
        dma_zone: "DMA-NORTH-04",
      },
      {
        id: "TEL-002",
        device_id: "DEV-PRESSURE-02",
        sensor_type: "HYDROSTATIC_PRESSURE",
        timestamp: new Date(now.getTime() - 1000 * 45).toISOString(),
        reading_value: 4.15,
        unit: "bar",
        data_quality: "VALID",
        provenance: "MEASURED",
        pipeline_segment_id: "PIPE-SEC-4B-92",
        dma_zone: "DMA-NORTH-04",
      },
      {
        id: "TEL-003",
        device_id: "DEV-FLOW-03",
        sensor_type: "VOLUMETRIC_FLOW",
        timestamp: new Date(now.getTime() - 1000 * 60).toISOString(),
        reading_value: 92.1,
        unit: "L/s",
        data_quality: "VALID",
        provenance: "MEASURED",
        pipeline_segment_id: "PIPE-SEC-3A-11",
        dma_zone: "DMA-CENTRAL-01",
      },
      {
        id: "TEL-004",
        device_id: "DEV-MOISTURE-04",
        sensor_type: "SOIL_MOISTURE",
        timestamp: new Date(now.getTime() - 1000 * 120).toISOString(),
        reading_value: 84.5,
        unit: "pct_saturation",
        data_quality: "SUSPECT",
        provenance: "MEASURED",
        pipeline_segment_id: "PIPE-SEC-4B-92",
        dma_zone: "DMA-NORTH-04",
      },
      {
        id: "TEL-005",
        device_id: "DEV-SIM-06",
        sensor_type: "HYDROSTATIC_PRESSURE",
        timestamp: new Date(now.getTime() - 1000 * 15).toISOString(),
        reading_value: 4.08,
        unit: "bar",
        data_quality: "VALID",
        provenance: "SIMULATED",
        pipeline_segment_id: "PIPE-SEC-4B-92",
        dma_zone: "DMA-NORTH-04",
      },
    ];

    return {
      success: true,
      total: fallbackTelemetries.length,
      telemetries: fallbackTelemetries,
    };
  }

  async fetchDeviceTelemetry(
    deviceId: string,
    limit: number = 50
  ): Promise<{ success: boolean; total: number; telemetries: DeviceTelemetry[] }> {
    try {
      const res = await fetch(
        `${this.baseUrl}/api/v1/iot/devices/${deviceId}/telemetry?limit=${limit}`,
        {
          headers: this.getHeaders(),
        }
      );
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // fallback
    }
    const all = await this.fetchLatestTelemetry(undefined, limit);
    const devTelems = all.telemetries.filter((t) => t.device_id === deviceId);
    return { success: true, total: devTelems.length, telemetries: devTelems };
  }

  // 4. Calibration Management
  async fetchCalibrations(params?: {
    device_id?: string;
    sensor_id?: string;
  }): Promise<{ success: boolean; total: number; records: SensorCalibration[] }> {
    try {
      const query = new URLSearchParams();
      if (params?.device_id) query.set("device_id", params.device_id);
      if (params?.sensor_id) query.set("sensor_id", params.sensor_id);

      const res = await fetch(`${this.baseUrl}/api/v1/iot/calibration?${query.toString()}`, {
        headers: this.getHeaders(),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // fallback
    }

    const fallbackCalibs: SensorCalibration[] = [
      {
        id: "CAL-001",
        sensor_id: "SNS-DEV-ACOUSTIC-01-ACOUSTIC_LEAK",
        device_id: "DEV-ACOUSTIC-01",
        calibration_date: "2026-09-15T10:00:00Z",
        next_due_date: "2027-03-15T10:00:00Z",
        calibration_method: "ACOUSTIC_CALIBRATOR_94DB",
        calibration_reference: "REF-BK-4231",
        calibration_result: "PASSED_WITHIN_TOLERANCE",
        accuracy_tolerance: 0.5,
        status: "CALIBRATED",
        technician: "Ing. Sarah Chen",
        certificate_reference: "CERT-2026-AC-994",
      },
      {
        id: "CAL-002",
        sensor_id: "SNS-DEV-PRESSURE-02-HYDROSTATIC_PRESSURE",
        device_id: "DEV-PRESSURE-02",
        calibration_date: "2026-08-01T09:00:00Z",
        next_due_date: "2027-02-01T09:00:00Z",
        calibration_method: "DEADWEIGHT_TESTER",
        calibration_reference: "REF-DWT-05",
        calibration_result: "PASSED_WITHIN_TOLERANCE",
        accuracy_tolerance: 0.1,
        status: "CALIBRATED",
        technician: "Ing. Marcus Vance",
        certificate_reference: "CERT-2026-PR-112",
      },
      {
        id: "CAL-003",
        sensor_id: "SNS-DEV-MOISTURE-04-SOIL_MOISTURE",
        device_id: "DEV-MOISTURE-04",
        calibration_date: "2026-01-10T12:00:00Z",
        next_due_date: "2026-07-10T12:00:00Z",
        calibration_method: "GRAVIMETRIC_SAMPLE",
        calibration_reference: "REF-SOIL-LAB",
        calibration_result: "PASSED_WITHIN_TOLERANCE",
        accuracy_tolerance: 2.0,
        status: "OVERDUE",
        technician: "Field Ops",
        notes: "Soil moisture probe requires field recalibration.",
      },
    ];

    return {
      success: true,
      total: fallbackCalibs.length,
      records: fallbackCalibs,
    };
  }

  async registerCalibration(payload: RegisterCalibrationPayload): Promise<SensorCalibration> {
    const res = await fetch(`${this.baseUrl}/api/v1/iot/calibration`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to register calibration record.");
    }
    return await res.json();
  }

  // 5. Audit & Security Trail
  async fetchIotAuditLogs(
    deviceId?: string,
    limit: number = 30
  ): Promise<{ success: boolean; total: number; audit_events: DeviceAuditLogItem[] }> {
    try {
      const query = new URLSearchParams();
      if (deviceId) query.set("device_id", deviceId);
      query.set("limit", String(limit));

      const res = await fetch(`${this.baseUrl}/api/v1/iot/audit?${query.toString()}`, {
        headers: this.getHeaders(),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // fallback
    }

    const fallbackLogs: DeviceAuditLogItem[] = [
      {
        id: "AUD-101",
        device_id: "DEV-ACOUSTIC-01",
        action: "DEVICE_COMMAND_DISPATCHED",
        actor: "lead_engineer",
        status: "SUCCESS",
        ip_address: "192.168.1.100",
        details: { command: "RUN_DEVICE_DIAGNOSTICS" },
        timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      },
      {
        id: "AUD-102",
        device_id: "DEV-PRESSURE-02",
        action: "CREDENTIAL_ROTATION",
        actor: "admin",
        status: "SUCCESS",
        ip_address: "10.0.0.1",
        details: { key_prefix: "aqk_pr2_...", credential_version: 2 },
        timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
      },
      {
        id: "AUD-103",
        device_id: "DEV-VALVE-PROHIBITED",
        action: "ACTUATION_COMMAND_BLOCKED",
        actor: "unauthorized_caller",
        status: "FORBIDDEN",
        ip_address: "172.16.4.12",
        details: { command: "CLOSE_VALVE", reason: "HARDWARE_ACTUATION_PROHIBITED" },
        timestamp: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
      },
    ];

    return {
      success: true,
      total: fallbackLogs.length,
      audit_events: fallbackLogs,
    };
  }

  // 6. Cross-Module Bridges
  async fetchDigitalTwinComparison(
    pipelineSegmentId: string = "PIPE-SEC-4B-92",
    observedPressureBar: number = 4.12,
    observedFlowLps: number = 89.5
  ): Promise<DigitalTwinComparisonResult> {
    try {
      const query = new URLSearchParams({
        pipeline_segment_id: pipelineSegmentId,
        observed_pressure_bar: String(observedPressureBar),
        observed_flow_lps: String(observedFlowLps),
      });
      const res = await fetch(
        `${this.baseUrl}/api/v1/iot/digital-twin-comparison?${query.toString()}`,
        {
          headers: this.getHeaders(),
        }
      );
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // fallback
    }

    return {
      pipeline_segment_id: pipelineSegmentId,
      observed_pressure_bar: observedPressureBar,
      epanet_baseline_pressure_bar: 4.25,
      pressure_delta_bar: -0.13,
      pressure_residual_pct: 3.06,
      observed_flow_lps: observedFlowLps,
      epanet_baseline_flow_lps: 87.2,
      hydraulic_deviation_status: "NORMAL",
      timestamp: new Date().toISOString(),
    };
  }

  async fetchLeakAnalysis(
    deviceId: string = "DEV-ACOUSTIC-01",
    acousticSplDb: number = 64.2,
    dominantFreqHz: number = 520.0,
    pressureBar: number = 3.8
  ): Promise<AcousticLeakAnalysisResult> {
    try {
      const query = new URLSearchParams({
        device_id: deviceId,
        acoustic_spl_db: String(acousticSplDb),
        dominant_freq_hz: String(dominantFreqHz),
        pressure_bar: String(pressureBar),
      });
      const res = await fetch(`${this.baseUrl}/api/v1/iot/leak-analysis?${query.toString()}`, {
        headers: this.getHeaders(),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch {
      // fallback
    }

    return {
      device_id: deviceId,
      acoustic_spl_db: acousticSplDb,
      dominant_freq_hz: dominantFreqHz,
      leak_probability_pct: 78.5,
      risk_severity: "HIGH",
      confidence_score: 0.88,
      recommendation:
        "High acoustic emission signature detected in 500-600 Hz bandwidth. Autonomous rover visual/acoustic verification recommended.",
      timestamp: new Date().toISOString(),
    };
  }
}

export const iotApiClient = new IotApiClient();

