/**
 * Rover Location Coordinates
 */
export interface GeoCoordinates {
  latitude: number;
  longitude: number;
  elevation_m?: number;
  pipe_segment_id?: string;
  pipe_distance_m?: number;
}

/**
 * Rover Kinematics
 */
export interface RoverKinematics {
  velocity_mps: number;
  heading_deg: number;
  pitch_deg?: number;
  roll_deg?: number;
}

/**
 * Rover Hardware Diagnostics
 */
export interface RoverDiagnostics {
  battery_soc_pct: number;
  internal_temp_c: number;
  motor_current_amps: number;
  signal_rssi_dbm: number;
}

/**
 * Rover Inspection Payload Readings
 */
export interface RoverSensorPayload {
  acoustic_spl_db: number;
  acoustic_dominant_freq_hz: number;
  ground_moisture_pct?: number;
  ambient_temperature_c?: number;
}

/**
 * Full Rover Telemetry Packet
 */
export interface RoverTelemetryPacket {
  device_id: string;
  device_type: 'autonomous_ground_rover' | 'in_pipe_crawler' | 'aerial_survey_drone';
  timestamp: string;
  status: 'idle' | 'surveying' | 'returning' | 'maintenance' | 'error';
  location: GeoCoordinates;
  kinematics: RoverKinematics;
  diagnostics: RoverDiagnostics;
  payload_sensors: RoverSensorPayload;
}

/**
 * Stationary IoT Pipe Sensor Reading
 */
export interface StationarySensorReading {
  sensor_id: string;
  pipe_id: string;
  timestamp: string;
  pressure_psi: number;
  flow_rate_lpm: number;
  acoustic_noise_level_db: number;
  battery_voltage_v: number;
}

/**
 * AI Leak Detection Event
 */
export interface LeakDetectionAlert {
  alert_id: string;
  detected_at: string;
  pipe_segment_id: string;
  coordinates: {
    latitude: number;
    longitude: number;
  };
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence_score: number;
  estimated_loss_rate_lpm: number;
  acoustic_signature_peak_hz: number;
  status: 'suspected' | 'investigating' | 'confirmed' | 'repaired';
}

