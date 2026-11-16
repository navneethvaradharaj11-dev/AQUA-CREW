# AQUA CREW — WebSocket Telemetry Protocol Specification
## Task 06: Real-Time Fleet Streaming Infrastructure

### 1. Overview & Connection Endpoint

The AQUA CREW backend provides a high-throughput, low-latency WebSocket connection for streaming real-time telemetry, state machine transitions, and mission execution events directly to frontend dashboards and GIS maps.

- **WebSocket URL**: `ws://<host>:<port>/api/v1/ws/telemetry`
- **Protocol**: Raw WebSocket with UTF-8 JSON payloads
- **Provenance**: Every message includes `is_simulated: true` and `provenance: "VIRTUAL_SIMULATION_BACKEND"`.

---

### 2. Connection Lifecycle & Handshake

#### 2.1 Connection Established
Immediately upon connection accept, the backend issues an initial handshake packet:
```json
{
  "type": "CONNECTION_ESTABLISHED",
  "message": "Connected to AQUA CREW Real-Time Fleet Telemetry Stream",
  "timestamp": "2026-11-15T16:50:00.123Z",
  "is_simulated": true,
  "provenance": "VIRTUAL_SIMULATION_BACKEND"
}
```

#### 2.2 Heartbeat (Ping / Pong)
Clients maintain the connection by sending periodic heartbeats (recommended interval: 15 seconds):
```json
// Client Request
{
  "type": "PING",
  "timestamp": "2026-11-15T16:50:15.000Z"
}

// Server Response
{
  "type": "PONG",
  "timestamp": "2026-11-15T16:50:15.000Z"
}
```

---

### 3. Event Message Payloads

#### 3.1 `ROVER_TELEMETRY_UPDATED`
Broadcast whenever a rover's kinematics, coordinates, or sensor diagnostics update during a simulation tick:
```json
{
  "type": "ROVER_TELEMETRY_UPDATED",
  "rover_id": "ROV-AQUA-01",
  "operating_state": "INSPECTING",
  "status": "ACTIVE",
  "battery_percentage": 85.8,
  "distance_travelled_km": 14.85,
  "velocity_mps": 0.28,
  "heading_deg": 178.4,
  "latitude": 40.712852,
  "longitude": -74.005988,
  "station_name": "Station 1205m",
  "pipe_segment_id": "PIPE-SEC-4B-92",
  "route_progress_pct": 65,
  "motor_temp_c": 38.6,
  "internal_temp_c": 31.4,
  "motor_current_amps": 1.62,
  "signal_rssi_dbm": -64.0,
  "acoustic_spl_db": 46.5,
  "timestamp": "2026-11-15T16:50:01.000Z",
  "is_simulated": true,
  "provenance": "VIRTUAL_SIMULATION_BACKEND"
}
```

#### 3.2 `ROVER_STATE_CHANGED`
Broadcast upon valid state transition:
```json
{
  "type": "ROVER_STATE_CHANGED",
  "rover_id": "ROV-AQUA-01",
  "previous_state": "IDLE",
  "new_state": "INSPECTING",
  "status": "ACTIVE",
  "reason": "Mission MSN-2026-042 assigned: Acoustic Pipe Survey",
  "triggered_by": "OPERATOR",
  "timestamp": "2026-11-15T16:50:00.000Z",
  "is_simulated": true,
  "provenance": "VIRTUAL_SIMULATION_BACKEND"
}
```

#### 3.3 `ROVER_EMERGENCY_STOP`
Broadcast when emergency stop is triggered on a rover:
```json
{
  "type": "ROVER_EMERGENCY_STOP",
  "rover_id": "ROV-AQUA-02",
  "reason": "Simulated acoustic spike >95 dB at Station 350m",
  "triggered_by": "SAFETY_INTERLOCK",
  "timestamp": "2026-11-15T16:50:02.000Z",
  "is_simulated": true,
  "provenance": "VIRTUAL_SIMULATION_BACKEND"
}
```

#### 3.4 `ROVER_MISSION_EVENT`
Broadcast on mission assignment, completion, or cancellation:
```json
{
  "type": "ROVER_MISSION_EVENT",
  "action": "ASSIGNED",
  "rover_id": "ROV-AQUA-03",
  "mission_id": "MSN-2026-044",
  "details": "Rover Hydra Pipe Probe assigned to Pressure Transient Test on segment PIPE-RES-3C-11",
  "timestamp": "2026-11-15T16:50:03.000Z",
  "is_simulated": true,
  "provenance": "VIRTUAL_SIMULATION_BACKEND"
}
```

#### 3.5 `SIMULATION_TICK`
Broadcast on every discrete engine pulse (default 1000ms):
```json
{
  "type": "SIMULATION_TICK",
  "tick_number": 428,
  "active_rover_count": 3,
  "timestamp": "2026-11-15T16:50:04.000Z",
  "is_simulated": true,
  "provenance": "VIRTUAL_SIMULATION_BACKEND"
}
```

#### 3.6 `SIMULATION_STATUS_CHANGED`
Broadcast when simulation starts, pauses, or resets:
```json
{
  "type": "SIMULATION_STATUS_CHANGED",
  "is_running": true,
  "interval_ms": 1000,
  "timestamp": "2026-11-15T16:50:05.000Z",
  "is_simulated": true,
  "provenance": "VIRTUAL_SIMULATION_BACKEND"
}
```

