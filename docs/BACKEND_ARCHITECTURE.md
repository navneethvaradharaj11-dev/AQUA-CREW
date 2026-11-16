# AQUA CREW — Backend Fleet Intelligence & Real-Time Telemetry Architecture
## Task 06: Migration Strategy & System Architecture

### 1. Executive Summary

AQUA CREW evolves from a client-side simulated prototype (Tasks 01–05) into a backend-driven distributed robotics platform. The FastAPI backend (`apps/api`) becomes the authoritative source of truth for:
1. Virtual rover states and kinematics.
2. Mission planning, assignment, and execution tracking.
3. Telemetry generation and archival.
4. Real-time event broadcasting over WebSockets.
5. Persistent storage via SQLAlchemy 2.x repositories (SQLite in development, PostgreSQL + PostGIS in production).

---

### 2. Migration Strategy: Client-Side Simulation to Backend Authority

```
[ PHASE 01-05 (Legacy Prototype) ]
Browser (Next.js) ──> roverSimulationEngine.ts (Local Client Interval) ──> UI Components

[ PHASE 06 (Backend-Authoritative Architecture) ]
PostgreSQL / PostGIS (or SQLite Dev Adapter)
       ▲
       │ SQLAlchemy 2.x Repository Pattern
       ▼
apps/api/app/services/simulation_service.py (Async Tick Loop)
       │
       ├──> apps/api/app/api/v1/endpoints/ (REST Endpoints)
       │           ▲
       │           │ HTTP (GET / POST)
       │           ▼
       │     apps/web/src/services/api/backendApiClient.ts
       │
       └──> apps/api/app/websocket/connection_manager.py
                   │
                   │ WebSocket (/api/v1/ws/telemetry)
                   ▼
             apps/web/src/services/api/telemetryWebSocketClient.ts
                   │
                   ▼ Dispatches to Local RoverEventBus
             UI Components (/app, /app/fleet, /app/map)
```

#### Core Migration Rules:
1. **Single Source of Truth**: When the backend is operational, the backend simulation loop drives state. The frontend does not run an uncoordinated second simulation loop.
2. **Backward Compatibility & Offline Graceful Fallback**: If the backend is unreachable or during transitional states, the frontend displays clear connection status badges (`CONNECTED` vs `DISCONNECTED`) and maintains UI stability.
3. **Software-First Continuity**: All telemetry remains simulated and carries `is_simulated: true` and `source: "VIRTUAL_SIMULATION_ENGINE"`. Physical actuators remain disconnected.

---

### 3. Backend Package Architecture

```
apps/api/app/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   ├── health.py        # System health & sub-service status
│       │   ├── rovers.py        # Rover state, telemetry, commands
│       │   ├── missions.py      # Mission creation, assignment, lifecycle
│       │   ├── telemetry.py     # Latest snapshot, history, health
│       │   ├── events.py        # Event logs & audit trail
│       │   ├── simulation.py    # Global simulation start/pause/resume/reset
│       │   └── ws.py            # WebSocket /api/v1/ws/telemetry
│       └── router.py            # Central v1 route aggregator
├── core/
│   ├── config.py                # Environment-driven settings (pydantic-settings)
│   ├── logging.py               # Structured log formatting
│   └── exceptions.py            # Custom exceptions & HTTP exception handlers
├── database/
│   ├── session.py               # Engine, sessionmaker, get_db dependency
│   └── base.py                  # Base declarative class
├── models/
│   ├── rover.py                 # Rover persistent model
│   ├── mission.py               # Mission persistent model
│   ├── telemetry.py             # Telemetry record history
│   ├── state_transition.py      # State transition records
│   ├── event.py                 # Mission & system event audit
│   └── pipeline_segment.py      # Pipeline geospatial geometry
├── repositories/
│   ├── base.py                  # Generic repository interface
│   ├── rover_repository.py      # Rover CRUD & state updates
│   ├── mission_repository.py    # Mission queries & assignment
│   └── telemetry_repository.py  # Time-series telemetry logging
├── schemas/
│   ├── rover.py                 # Pydantic schemas for rovers & commands
│   ├── mission.py               # Pydantic schemas for missions
│   ├── telemetry.py             # Pydantic schemas for telemetry packets
│   ├── events.py                # Pydantic schemas for events
│   └── simulation.py            # Pydantic schemas for simulation controls
├── services/
│   ├── rover_service.py         # Rover domain & command validation
│   ├── mission_service.py       # Mission assignment & progression
│   ├── telemetry_service.py     # Kinematics & sensor bounds
│   ├── simulation_service.py    # Background tick loop & state interpolation
│   └── event_service.py         # Event logging & WebSocket dispatching
├── websocket/
│   └── connection_manager.py    # Client registry, broadcast, heartbeat
└── main.py                      # FastAPI application & lifespan lifecycle
```

---

### 4. Database Strategy & PostGIS Production Target

1. **Development Persistence Adapter**: Uses SQLite (`sqlite:///./aqua_crew_dev.db`) for instant zero-dependency local development and automated pytest runs.
2. **Production Target**: PostgreSQL 16+ with PostGIS extension. Geometry columns store pipeline LineStrings and rover Point coordinates.
3. **No False Claims**: The development environment accurately reports SQLite persistence while maintaining PostGIS-ready schemas.

