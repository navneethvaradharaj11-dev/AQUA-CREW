/**
 * AQUA CREW — IoT Device Ecosystem & Hardware Gateway Types (Task 18)
 * Strict typing for IoT devices, sensor calibrations, telemetry ingestion,
 * MQTT gateway status, safety guardrails, and cross-module bridges.
 */

export type DeviceType =
  | "ACOUSTIC_LOGGER"
  | "PRESSURE_SENSOR"
  | "FLOW_METER"
  | "MOISTURE_PROBE"
  | "WATER_QUALITY"
  | "OPTICAL_CAMERA"
  | "GATEWAY"
  | "EDGE_COMPUTE"
  | "VIRTUAL_SENSOR";

export type DeviceStatus =
  | "ACTIVE"
  | "OFFLINE"
  | "DEGRADED"
  | "MAINTENANCE"
  | "PROVISIONED"
  | "QUARANTINED"
  | "REVOKED";

export type SensorType =
  | "ACOUSTIC_LEAK"
  | "HYDROSTATIC_PRESSURE"
  | "VOLUMETRIC_FLOW"
  | "SOIL_MOISTURE"
  | "WATER_TEMPERATURE"
  | "OPTICAL_TURBIDITY"
  | "CHLORINE_RESIDUAL"
  | "VIBRATION_SPECTRAL";

export type ProvenanceType =
  | "MEASURED"
  | "SIMULATED"
  | "DERIVED"
  | "PREDICTED"
  | "OPERATOR_ENTERED"
  | "UNKNOWN";

export type DataQualityType =
  | "VALID"
  | "SUSPECT"
  | "DEGRADED"
  | "OUT_OF_BOUNDS"
  | "UNCALIBRATED"
  | "STALE"
  | "REJECTED";

export interface IoTDevice {
  id: string;
  name: string;
  device_type: DeviceType;
  status: DeviceStatus;
  hardware_version: string;
  firmware_version: string;
  mac_address?: string;
  ip_address?: string;
  serial_number?: string;
  manufacturer: string;
  pipeline_segment_id?: string;
  dma_zone?: string;
  latitude?: number;
  longitude?: number;
  elevation_m?: number;
  installation_date?: string;
  last_heartbeat?: string;
  battery_level_pct?: number;
  battery_health?: string;
  power_source: string;
  communication_protocol: string;
  is_quarantined: boolean;
  quarantine_reason?: string;
  is_revoked: boolean;
  revoked_at?: string;
  supported_sensor_types: string[];
  metadata_json?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface DeviceTelemetry {
  id: string;
  device_id: string;
  sensor_id?: string;
  sensor_type: string;
  timestamp: string;
  reading_value: number;
  unit: string;
  data_quality: DataQualityType;
  provenance: ProvenanceType;
  sequence_number?: number;
  pipeline_segment_id?: string;
  dma_zone?: string;
  raw_payload?: Record<string, any>;
  processing_notes?: string;
}

export interface SensorCalibration {
  id: string;
  sensor_id: string;
  device_id: string;
  calibration_date: string;
  next_due_date: string;
  calibration_method: string;
  calibration_reference: string;
  calibration_result: string;
  accuracy_tolerance: number;
  status: "CALIBRATED" | "DUE" | "OVERDUE" | "UNCALIBRATED" | "FAILED";
  technician?: string;
  certificate_reference?: string;
  notes?: string;
}

export interface IoTOverviewMetrics {
  total_devices: number;
  active_devices: number;
  offline_devices: number;
  degraded_devices: number;
  quarantined_devices: number;
  revoked_devices: number;
  total_sensors: number;
  calibrated_sensors: number;
  overdue_calibrations: number;
  telemetry_readings_24h: number;
  data_quality_pct: number;
  by_device_type: Record<string, number>;
  by_dma_zone: Record<string, number>;
}

export interface MqttGatewayStatus {
  connected: boolean;
  broker_host: string;
  broker_port: number;
  use_tls: boolean;
  messages_received: number;
  messages_published: number;
  dropped_messages: number;
  rate_limited_count: number;
  simulation_mode: boolean;
  active_subscriptions: string[];
  uptime_seconds: number;
}

export interface IoTStatusResponse {
  success: boolean;
  metrics: IoTOverviewMetrics;
  mqtt_status: MqttGatewayStatus;
  hardware_safety: string;
  timestamp: string;
}

export interface DeviceAuditLogItem {
  id: string;
  device_id?: string;
  action: string;
  actor?: string;
  status: string;
  ip_address?: string;
  details?: Record<string, any>;
  timestamp?: string;
}

export interface DigitalTwinComparisonResult {
  pipeline_segment_id: string;
  observed_pressure_bar: number;
  epanet_baseline_pressure_bar: number;
  pressure_delta_bar: number;
  pressure_residual_pct: number;
  observed_flow_lps?: number;
  epanet_baseline_flow_lps?: number;
  hydraulic_deviation_status:
    | "NORMAL"
    | "ANOMALOUS_PRESSURE_DROP"
    | "ANOMALOUS_SURGE"
    | "SUSPECT_SENSOR_READING";
  timestamp: string;
}

export interface AcousticLeakAnalysisResult {
  device_id: string;
  acoustic_spl_db: number;
  dominant_freq_hz: number;
  leak_probability_pct: number;
  risk_severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NORMAL";
  confidence_score: number;
  recommendation: string;
  timestamp: string;
}

export interface RegisterDevicePayload {
  id: string;
  name: string;
  device_type: DeviceType;
  manufacturer: string;
  hardware_version: string;
  firmware_version: string;
  communication_protocol?: string;
  pipeline_segment_id?: string;
  dma_zone?: string;
  latitude?: number;
  longitude?: number;
  power_source?: string;
  supported_sensor_types?: string[];
  credential_type?: string;
}

export interface RegisterCalibrationPayload {
  device_id: string;
  sensor_id: string;
  calibration_method: string;
  calibration_reference: string;
  calibration_result: string;
  accuracy_tolerance: number;
  technician?: string;
  certificate_reference?: string;
  next_due_date?: string;
  notes?: string;
}

