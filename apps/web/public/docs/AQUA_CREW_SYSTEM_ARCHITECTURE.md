# AQUA CREW — System Architecture Specification
**Release:** v1.0.0-rc1  
**Architecture Classification:** Modular Event-Driven Hexagonal Architecture with Strict Simulation-First Boundaries  

---

## 1. Architectural Overview

AQUA CREW is engineered as a loosely coupled, highly cohesive modular system comprising an asynchronous REST and WebSocket API gateway, domain-specific intelligence micro-services, an EPANET-compliant hydraulic digital twin, an AI acoustic processing pipeline, and an interactive GIS frontend.

```mermaid
graph TD
    subgraph ClientLayer ["Client & Visualization Tier"]
        UI["Next.js 14 App Shell (/app)"]
        GISMap["Leaflet GIS View (/app/map)"]
        AIAssistant["Interactive AI Copilot (/app/intelligence)"]
        Dashboard["Command Center KPI Deck (/app)"]
    end

    subgraph GatewayTier ["Gateway & Reverse Proxy Tier"]
        Nginx["Nginx Reverse Proxy Gateway (:80)"]
    end

    subgraph APITier ["FastAPI Application Services (:8000)"]
        AuthMiddleware["JWT & RBAC Security Middleware"]
        RateLimiter["IP Rate Limiter"]
        APIRouter["API Router (/api/v1)"]
        WSHub["WebSocket Event Hub (/ws)"]
    end

    subgraph DomainEngines ["Domain Intelligence Services"]
        IncidentService["Incident Orchestration Service"]
        AIEngine["AI Acoustic Leak Localization Engine"]
        TwinService["EPANET Todini Digital Twin Engine"]
        OptimizationService["Genetic Pressure Optimization Service"]
        FleetService["Virtual Rover Fleet Dispatcher"]
        InspectionService["Autonomous Inspection Engine"]
        RepairService["Repair Planning & Cost Model"]
        IoTService["IoT Registry & Calibration Service"]
    end

    subgraph SafetyLayer ["Hardware & Actuation Safety Boundary"]
        SafetyGate{"HARDWARE_ACTUATION_ENABLED == true?"}
        Block["HTTP 403 / HardwareActuationForbiddenError"]
        VirtualActuator["Virtual Network Simulator (EPANET Twin)"]
    end

    subgraph DataTier ["Data & Persistence Tier"]
        DB[("SQLAlchemy / PostgreSQL + PostGIS (or SQLite)")]
        MQTT["Eclipse Mosquitto MQTT Broker (:1883)"]
        AuditLog[("Cryptographic Audit Trail (SHA-256)")]
    end

    UI --> Nginx
    GISMap --> Nginx
    AIAssistant --> Nginx
    Dashboard --> Nginx

    Nginx -->|REST /api/v1/*| APIRouter
    Nginx -->|WebSocket /ws/*| WSHub

    APIRouter --> AuthMiddleware
    AuthMiddleware --> RateLimiter

    RateLimiter --> IncidentService
    RateLimiter --> AIEngine
    RateLimiter --> TwinService
    RateLimiter --> OptimizationService
    RateLimiter --> FleetService
    RateLimiter --> InspectionService
    RateLimiter --> RepairService
    RateLimiter --> IoTService

    IncidentService --> TwinService
    IncidentService --> FleetService
    IncidentService --> RepairService
    IncidentService --> WSHub

    IoTService --> SafetyGate
    OptimizationService --> SafetyGate

    SafetyGate -->|No (Default)| VirtualActuator
    SafetyGate -->|Yes| Block

    DomainEngines --> DB
    DomainEngines --> AuditLog
    IoTService <--> MQTT
```

---

## 2. Component Subsystems & Responsibilities

### 2.1 Web Application Tier (`apps/web`)
- **Framework:** Next.js 14 utilizing the React Server Components & App Router model.
- **State Management:** React hooks (`useIncidentStore`, `useTelemetryStore`) with reactive WebSocket integration.
- **Geospatial Mapping:** React-Leaflet with custom SVG overlays, pipe gradient rendering, rover pathing, and confidence ellipses.
- **UI System:** Custom dark-mode design system with Tailwind CSS and Lucide iconography.

### 2.2 API & Security Layer (`apps/api/app/core` & `api/v1`)
- **Framework:** FastAPI on ASGI Uvicorn server.
- **Authentication:** OAuth2 with Password Flow issuing HMAC-SHA256 signed JSON Web Tokens (JWT).
- **Access Control:** Role-Based Access Control (RBAC) enforcing granular permissions (`SUPER_ADMIN`, `FIELD_OPERATOR`, `DATA_ANALYST`, `HYDRAULIC_ENGINEER`, `EXECUTIVE_AUDITOR`).
- **Security Middlewares:** Security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options), client IP rate limiting (100 req/min baseline, 10 req/min for auth routes), and strict CORS origin whitelisting.

### 2.3 Domain Service Architecture (`apps/api/app/services`)
1. **`incident_orchestration_service.py`**: Coordinates the end-to-end 15-step incident lifecycle from transient pressure drop detection to acoustic verification and dossier compilation.
2. **`digital_twin_service.py`**: Implements hydraulic simulation using the Todini Global Gradient Algorithm (GGA) to solve non-linear mass and energy conservation equations.
3. **`leak_detection_service.py`**: Executes acoustic feature extraction (FFT, wavelets, kurtosis, spectral centroid) and cross-correlation time delay of arrival ($\Delta t$) for pipe leak localization.
4. **`network_optimization_service.py`**: Executes multi-objective pressure management optimizing PRV settings and pump schedules using genetic algorithms.
5. **`inspection_intelligence_service.py`**: Dispatches robotic rovers based on battery SoC, acoustic sensor suite, and hydraulic velocity constraints.
6. **`repair_management_service.py`**: Synthesizes resource allocations, bills of materials, cost estimation ($2,450 baseline benchmark), and verification checklists.
7. **`iot_device_service.py`**: Manages sensor telemetry ingestion, 2-point zero/span calibration, polynomial drift compensation, and MQTT topics.

---

## 3. Communication Protocols & Data Exchange

| Channel | Protocol | Port | Encoding | Primary Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Client REST API** | HTTPS / HTTP/1.1 | 80 / 8000 | JSON | CRUD operations, scenario triggers, reports |
| **Real-Time Feed** | WebSockets (RFC 6455) | 80 / 8000 | JSON | Live rover coordinates, pressure alarms, incident updates |
| **IoT Telemetry** | MQTT v3.1.1 / v5.0 | 1883 | JSON / Binary | Edge sensor streaming (`aquacrew/telemetry/+`) |
| **Database Access** | PostGIS wire protocol | 5432 | Binary | Relational schema persistence and spatial queries |

---

## 4. Hardware Safety Boundary & Provenance Model

A fundamental architectural invariant of AQUA CREW is the **Hardware Safety Gate**:
```python
HARDWARE_ACTUATION_ENABLED: bool = False
```
Physical control commands (e.g., closing real-world valves or throttling physical pumps) are strictly intercepted by [safety_interlocks.py](file:///e:/BRIDGE%20ASSIGNMENTS/Aqua%20Crew/apps/api/app/core/safety_interlocks.py). Invocations return `HTTP 403 Forbidden` with the error:
`"Physical hardware actuation is disabled in this simulation-first deployment"`.

All operational recommendations are redirected to the EPANET digital twin for virtual validation. Furthermore, all telemetry and analytical outputs are stamped with one of six provenance tiers:
1. `VIRTUAL_SIMULATION_ENGINE`
2. `ACOUSTIC_ANALYTICS_SERVICE`
3. `DIGITAL_TWIN_TODINI_SOLVER`
4. `FIELD_ROVER_TELEMETRY`
5. `CALIBRATED_IOT_TRANSDUCER`
6. `OPERATOR_MANUAL_ENTRY`

