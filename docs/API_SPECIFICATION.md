# AQUA CREW — API Specification
## Version 1.0 (Task 06 Implementation)

### 1. Overview & Protocol Design

The AQUA CREW communication infrastructure uses a dual-protocol architecture:
1. **REST APIs (HTTP/1.1 & HTTP/2, JSON)**: For fleet orchestration, state machine command dispatching, mission planning, historical telemetry queries, and simulation lifecycle controls.
2. **WebSockets (WS/WSS, JSON)**: For low-latency broadcasting of telemetry packets, state transitions, mission waypoints, and emergency stop interlocks.

Base URL: `http://localhost:8000/api/v1`

---

### 2. Complete REST Endpoint Reference

#### 2.1 System & Health
- `GET /api/v1/health`: Checks system health, version, environment, and subsystem status (`database`, `simulation_engine`, `hardware_gateway`).

#### 2.2 Rover Fleet & Commands
- `GET /api/v1/rovers`: Lists all 5 rovers in the fleet. Supports optional query parameters: `status` (`ONLINE`, `ACTIVE`, `IDLE`, `WARNING`, `OFFLINE`) and `operating_state` (`IDLE`, `MOVING`, `INSPECTING`, `PAUSED`, `RETURNING`, `CHARGING`, `OFFLINE`, `ERROR`, `EMERGENCY_STOP`).
- `GET /api/v1/rovers/{rover_id}`: Retrieves complete state, kinematics, diagnostics, and payload sensor readings for a single rover.
- `POST /api/v1/rovers/{rover_id}/commands`: Dispatches state-changing command to a rover.
  - Body:
    ```json
    {
      "command": "PAUSE | RESUME | RETURN_BASE | EMERGENCY_STOP | RESET_ESTOP | SET_STATE",
      "target_state": "INSPECTING",
      "reason": "Operator survey dispatch",
      "triggered_by": "OPERATOR"
    }
    ```
- `GET /api/v1/rovers/{rover_id}/telemetry`: Retrieves latest real-time telemetry snapshot for a specific rover.
- `GET /api/v1/rovers/{rover_id}/events`: Retrieves state transition audit trail for a specific rover.

#### 2.3 Missions
- `GET /api/v1/missions`: Lists all inspection missions. Optional filter: `status` (`In Progress`, `Scheduled`, `Paused`, `Completed`, `Cancelled`).
- `GET /api/v1/missions/{mission_id}`: Retrieves mission details, assigned rover, route progress %, and waypoint completion.
- `POST /api/v1/missions`: Creates a new scheduled inspection mission.
- `POST /api/v1/missions/{mission_id}/assign`: Assigns an available `IDLE` rover to a mission. Rejects duplicate assignments or busy rovers.
- `POST /api/v1/missions/{mission_id}/start`: Transitions mission to `In Progress`.
- `POST /api/v1/missions/{mission_id}/pause`: Pauses active mission.
- `POST /api/v1/missions/{mission_id}/resume`: Resumes paused mission.
- `POST /api/v1/missions/{mission_id}/cancel`: Cancels mission and returns assigned rover to `IDLE` or `RETURNING`.

#### 2.4 Telemetry
- `GET /api/v1/telemetry/latest`: Returns real-time telemetry snapshot for all rovers.
- `GET /api/v1/telemetry/history`: Retrieves paginated historical telemetry records (`page`, `page_size`, optional `rover_id`).
- `GET /api/v1/telemetry/health`: Retrieves fleet telemetry health summary (battery average, active units, temperature warnings).

#### 2.5 Simulation Controls
- `GET /api/v1/simulation/status`: Returns current simulation loop state (`is_running`, `tick_interval_ms`, `total_ticks`, `active_rovers_count`).
- `POST /api/v1/simulation/start`: Starts background tick loop.
- `POST /api/v1/simulation/pause`: Halts tick loop.
- `POST /api/v1/simulation/resume`: Resumes tick loop.
- `POST /api/v1/simulation/reset`: Resets rovers and missions to pristine default baseline.

#### 2.6 Audit Events
- `GET /api/v1/events`: Retrieves paginated system and mission audit logs.
- `GET /api/v1/events/recent`: Retrieves the 25 most recent events for live UI timeline streams.

#### 2.7 WebSocket
- `WebSocket /api/v1/ws/telemetry`: Real-time bidirectional streaming endpoint (see `WEBSOCKET_SPECIFICATION.md`).
