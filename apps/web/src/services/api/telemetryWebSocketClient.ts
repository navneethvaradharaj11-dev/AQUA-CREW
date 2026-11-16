/**
 * Real-Time Telemetry WebSocket Client
 * Connects to the backend WebSocket stream and dispatches incoming events
 * directly into the local roverEventBus for zero-latency reactive UI updates.
 */
import { roverEventBus } from "../simulation/roverEventBus";

export type WebSocketConnectionState = "CONNECTING" | "CONNECTED" | "DISCONNECTED" | "ERROR";

const DEFAULT_WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1/ws/telemetry";

class TelemetryWebSocketClient {
  private wsUrl: string;
  private socket: WebSocket | null = null;
  private state: WebSocketConnectionState = "DISCONNECTED";
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private statusListeners: Set<(state: WebSocketConnectionState) => void> = new Set();
  private intentionalDisconnect = false;

  constructor(wsUrl = DEFAULT_WS_URL) {
    this.wsUrl = wsUrl;
  }

  public getState(): WebSocketConnectionState {
    return this.state;
  }

  public onStatusChange(listener: (state: WebSocketConnectionState) => void): () => void {
    this.statusListeners.add(listener);
    listener(this.state);
    return () => {
      this.statusListeners.delete(listener);
    };
  }

  private setState(newState: WebSocketConnectionState): void {
    if (this.state !== newState) {
      this.state = newState;
      this.statusListeners.forEach((l) => l(newState));
    }
  }

  public connect(): void {
    if (typeof window === "undefined") return;
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.intentionalDisconnect = false;
    this.setState("CONNECTING");

    try {
      this.socket = new WebSocket(this.wsUrl);

      this.socket.onopen = () => {
        this.setState("CONNECTED");
        this.reconnectAttempts = 0;
        this.startHeartbeat();
      };

      this.socket.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          this.handleIncomingMessage(data);
        } catch (err) {
          console.warn("[WebSocket] Error parsing incoming message:", err);
        }
      };

      this.socket.onerror = () => {
        this.setState("ERROR");
      };

      this.socket.onclose = () => {
        this.stopHeartbeat();
        this.setState("DISCONNECTED");
        if (!this.intentionalDisconnect) {
          this.scheduleReconnect();
        }
      };
    } catch {
      this.setState("ERROR");
      this.scheduleReconnect();
    }
  }

  public disconnect(): void {
    this.intentionalDisconnect = true;
    this.stopHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.setState("DISCONNECTED");
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.pingInterval = setInterval(() => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({ type: "PING", timestamp: new Date().toISOString() }));
      }
    }, 15000);
  }

  private stopHeartbeat(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 8000);
    this.reconnectAttempts++;
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private handleIncomingMessage(msg: any): void {
    if (!msg || !msg.type) return;

    if (msg.type === "PONG" || msg.type === "CONNECTION_ESTABLISHED") {
      return;
    }

    // Bridge incoming backend events directly to client roverEventBus
    if (msg.type === "ROVER_TELEMETRY_UPDATED") {
      roverEventBus.publish({
        id: `WS-TEL-${msg.rover_id}-${Date.now()}`,
        type: "ROVER_TELEMETRY_UPDATED",
        roverId: msg.rover_id,
        rover: {
          isSimulated: true,
          source: "VIRTUAL_SIMULATION_ENGINE",
          simulatedAt: msg.timestamp || new Date().toISOString(),
          id: msg.rover_id,
          name: msg.name || msg.rover_id,
          model: msg.model || "Autonomous In-Pipe Crawler",
          status: msg.status || "ACTIVE",
          operatingState: msg.operating_state || "INSPECTING",
          connectionStatus: msg.connection_status || "ONLINE",
          batteryPercentage: msg.battery_percentage || 80,
          distanceTravelledKm: msg.distance_travelled_km || 0,
          currentMission: msg.current_mission || "Patrol",
          currentLocation: {
            stationName: msg.station_name || "",
            latitude: msg.latitude,
            longitude: msg.longitude,
            pipeSegmentId: msg.pipe_segment_id || "",
            routeProgressPct: msg.route_progress_pct || 0,
          },
          lastCommunication: "Just now",
          lastHeartbeatTimestamp: msg.timestamp || new Date().toISOString(),
          kinematics: {
            velocityMps: msg.velocity_mps || 0,
            headingDeg: msg.heading_deg || 0,
          },
          diagnostics: {
            internalTempC: msg.internal_temp_c || 25,
            motorTempC: msg.motor_temp_c || 28,
            motorCurrentAmps: msg.motor_current_amps || 1.2,
            signalRssiDbm: msg.signal_rssi_dbm || -65,
          },
          payloadSensors: {
            acousticSplDb: msg.acoustic_spl_db || 42,
            dominantFreqHz: msg.dominant_freq_hz || 500,
            groundMoisturePct: msg.ground_moisture_pct || 15,
          },
        },
        timestamp: msg.timestamp || new Date().toISOString(),
        isSimulated: true,
        provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
      });
    } else if (msg.type === "SIMULATION_TICK") {
      roverEventBus.publish({
        id: `WS-TICK-${msg.tick_number}`,
        type: "SIMULATION_TICK",
        tickNumber: msg.tick_number,
        activeRoverCount: msg.active_rover_count,
        timestamp: msg.timestamp || new Date().toISOString(),
        isSimulated: true,
        provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
      });
    } else if (msg.type === "SIMULATION_STATUS_CHANGED") {
      roverEventBus.publish({
        id: `WS-STATUS-${Date.now()}`,
        type: "SIMULATION_STATUS_CHANGED",
        isRunning: msg.is_running,
        intervalMs: msg.interval_ms || 1000,
        timestamp: msg.timestamp || new Date().toISOString(),
        isSimulated: true,
        provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
      });
    } else if (msg.type === "ROVER_STATE_CHANGED") {
      roverEventBus.publish({
        id: `WS-TR-${Date.now()}`,
        type: "ROVER_STATE_CHANGED",
        roverId: msg.rover_id,
        transition: {
          id: `TR-${Date.now()}`,
          roverId: msg.rover_id,
          previousState: msg.previous_state,
          newState: msg.new_state,
          timestamp: msg.timestamp,
          reason: msg.reason || "Backend transition",
          triggeredBy: msg.triggered_by || "OPERATOR",
          isSimulated: true,
          source: "VIRTUAL_SIMULATION_ENGINE",
        },
        timestamp: msg.timestamp || new Date().toISOString(),
        isSimulated: true,
        provenance: "VIRTUAL_SIMULATION_EVENT_BUS",
      });
    }
  }
}

export const telemetryWsClient = new TelemetryWebSocketClient();

