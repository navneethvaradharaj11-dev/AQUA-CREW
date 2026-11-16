# AQUA CREW — System Architecture Document

## 1. Executive Summary & Vision

**AQUA CREW** is an autonomous water leakage detection, localization, and repair management platform engineered for municipal and metropolitan water distribution networks. The platform's ultimate mission is to mitigate non-revenue water (NRW) losses, prevent critical urban infrastructure disruptions, and automate repair lifecycle management through an integrated network of autonomous ground rovers, acoustic/pressure IoT sensors, AI-powered acoustic & flow anomaly detection engines, and a centralized operations command center.

### 1.1 Strict Software-First Strategy

To guarantee software reliability, deterministic testability, and architectural agility, AQUA CREW adopts a **Strict Software-First Engineering Strategy**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      AQUA CREW SOFTWARE PLATFORM                       │
│  ┌────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │   Command Center UI    │  │        FastAPI Core Gateway          │  │
│  └───────────┬────────────┘  └──────────────────┬───────────────────┘  │
│              │                                  │                      │
│  ┌───────────▼──────────────────────────────────▼───────────────────┐  │
│  │                    Hardware Abstraction Layer                    │  │
│  └──────────────────▲────────────────────────────▲──────────────────┘  │
└─────────────────────┼────────────────────────────┼─────────────────────┘
                      │                            │                      
       ┌──────────────┴──────────────┐             │ (Future Swap)        
       │  High-Fidelity Virtual      │             ▼                      
       │  Simulation Engine          │   ┌────────────────────┐           
       │  (Rovers, Sensors, Valves)  │   │ Physical Hardware  │           
       └─────────────────────────────┘   │ (Rovers, IoT Nodes)│           
                                         └────────────────────┘           
```

1. **Complete Decoupling**: All rover telemetry, pipe acoustics, pressure transients, flow metrics, and actuator controls are mediated through strict data contracts.
2. **Zero-Rewrite Hardware Transition**: Physical hardware integration will bind to the same contracts and APIs via a hardware gateway driver without altering business logic, state machines, or frontend dashboards.
3. **Deterministic Simulation**: Edge cases (burst pipes, sensor drifts, communication dropouts, rover battery depletion) can be systematically simulated and stress-tested in software before deploying physical units into utility pipelines.

---

## 2. Monorepo Organization & Boundaries

The repository is organized as an enterprise monorepo with clear separation of responsibilities:

```
AQUA-CREW/
├── apps/
│   ├── web/               # Next.js 14+ App Router Frontend (Dashboard, GIS, Fleet)
│   └── api/               # FastAPI Backend (REST, WebSockets, Business Logic)
├── packages/
│   └── contracts/         # Language-agnostic & typed data models (TypeScript & Python)
├── docs/
│   ├── ARCHITECTURE.md    # High-level architecture & module breakdown (this document)
│   ├── API_SPECIFICATION.md# REST & WebSocket protocol specifications
│   └── HARDWARE_INTEGRATION.md # Hardware abstraction, telemetry protocols & driver roadmap
├── .env.example           # Root environment variable documentation
├── .gitignore             # Unified VCS ignore rules
└── README.md              # Monorepo onboarding and operational guide
```

---

## 3. Technology Stack & Architectural Decisions

| Layer | Technology | Rationale & Architectural Choice |
| :--- | :--- | :--- |
| **Frontend Framework** | Next.js (TypeScript) | Server and Client components, rapid page rendering, API route proxying, and enterprise ecosystem support. |
| **Styling & Components**| Tailwind CSS + shadcn/ui | Accessible, customizable headless components with zero runtime CSS overhead. |
| **Icons & Visuals** | Lucide Icons | Consistent, lightweight SVG iconography across maps, telemetry cards, and controls. |
| **Backend Core** | FastAPI (Python 3.11+) | Asynchronous ASGI runtime, native OpenAPI generation, high throughput, and seamless integration with Python ML libraries. |
| **Data Validation** | Pydantic v2 | High-performance Rust-backed data validation and serialization for telemetry pipelines. |
| **Relational / GIS Store**| PostgreSQL + PostGIS | Industry-standard relational data store with spatial indexing and geometric queries for municipal pipe networks. |
| **Time-Series / Telemetry**| TimescaleDB / PostGIS | Temporal hyper-tables for high-frequency acoustic sensor and rover telemetry streaming. |
| **Real-time Messaging** | WebSockets & Async Queues | Bidirectional sub-second status synchronization between command center and simulated rovers. |
| **Future Transport** | MQTT (e.g., Eclipse Mosquitto) | Lightweight pub/sub protocol specifically tailored for bandwidth-constrained field telemetry. |
| **GIS & Mapping** | MapLibre GL + OSM | WebGL-accelerated vector tile rendering, offline map capability, and zero vendor lock-in. |
| **AI / ML Runtime** | Scikit-learn / PyTorch | Spectral acoustic analysis, anomaly detection, wavelet transforms, and multi-sensor fusion. |

---

## 4. Future Module Boundaries

The AQUA CREW platform defines 12 core modules. Each module maintains isolated data stores, interfaces, and service boundaries to prevent tight coupling:

### 1. Command Center (`apps/web/modules/command-center` & `apps/api/app/modules/command_center`)
- **Responsibility**: Centralized operational pane providing real-time situational awareness across the entire metropolitan network.
- **Key Capabilities**: Global network status, active incident summary, fleet readiness overview, and real-time alert feed.

### 2. Pipeline Mapping (`apps/api/app/modules/pipeline_mapping`)
- **Responsibility**: Management and spatial querying of underground pipeline topologies, pipe attributes (material, diameter, depth, installation year), and valve stations.
- **Key Capabilities**: GeoJSON export, PostGIS spatial queries (spatial buffers, shortest path across network), and pressure zone segmentation.

### 3. Rover Fleet Management (`apps/api/app/modules/fleet_management`)
- **Responsibility**: Tracking autonomous ground and in-pipe rovers, maintenance schedules, battery state-of-charge (SoC), and hardware diagnostics.
- **Key Capabilities**: Rover registry, heartbeat monitor, payload configuration, and docking station allocation.

### 4. Mission Control (`apps/api/app/modules/mission_control`)
- **Responsibility**: Mission planning, waypoint sequencing, dispatch scheduling, and autonomous execution monitoring.
- **Key Capabilities**: Patrol route generation, emergency intercept missions, abort/recall protocols, and progress telemetry.

### 5. Sensor Monitoring (`apps/api/app/modules/sensor_monitoring`)
- **Responsibility**: Ingestion, validation, and temporal aggregation of stationary network sensors (acoustic hydrophones, pressure transducers, flow meters).
- **Key Capabilities**: Time-series buffering, noise baseline calibration, anomaly trigger thresholds, and dead-sensor detection.

### 6. AI Leak Detection (`apps/api/app/modules/leak_detection`)
- **Responsibility**: Algorithmic identification of suspicious acoustic patterns, pressure drop signatures, and mass balance anomalies.
- **Key Capabilities**: FFT / Wavelet acoustic feature extraction, multi-sensor cross-correlation, false-positive suppression, and confidence scoring.

### 7. Leak Localization (`apps/api/app/modules/leak_localization`)
- **Responsibility**: Pinpointing leak coordinates along pipeline segments with sub-meter accuracy.
- **Key Capabilities**: Acoustic time-difference-of-arrival (TDOA) calculation, hydraulic pressure wave propagation modeling, and GIS coordinate snapping.

### 8. Repair Management (`apps/api/app/modules/repair_management`)
- **Responsibility**: End-to-end ticketing, dispatching field maintenance crews, work order status tracking, and utility permit coordination.
- **Key Capabilities**: Work order lifecycle (Reported -> Dispatched -> In Progress -> Repaired), priority ranking, and crew assignment.

### 9. Repair Verification (`apps/api/app/modules/repair_verification`)
- **Responsibility**: Post-repair acoustic and pressure testing to confirm structural integrity before restoring full service pressure.
- **Key Capabilities**: Verification rover mission dispatch, post-repair pressure ramp testing, and certification logging.

### 10. Analytics & Reporting (`apps/api/app/modules/analytics`)
- **Responsibility**: Macro-level performance metrics, water loss estimation (m³ saved), non-revenue water (NRW) reduction rate, and infrastructure depreciation models.
- **Key Capabilities**: Historical trend analysis, executive PDF reports, cost-benefit summaries, and compliance exports.

### 11. Alerts & Notifications (`apps/api/app/modules/alerts`)
- **Responsibility**: Multi-channel urgent dispatching for high-confidence bursts or rover safety anomalies.
- **Key Capabilities**: Webhook triggers, SMS/Email gateway integration, escalation policies, and in-app sound/banner notifications.

### 12. Hardware Communication Gateway (`apps/api/app/modules/hardware_gateway`)
- **Responsibility**: Bi-directional bridge translating physical hardware protocols (MQTT, serial, ROS2) into standardized internal contracts.
- **Key Capabilities**: Packet decoding, encryption/decryption, rate limiting, and simulation-mode/live-mode toggle.

---

## 5. Security & Architectural Principles

1. **Zero Secret Hardcoding**: All secrets, database URLs, and API tokens must be sourced from validated environment variables.
2. **Stateless Service Nodes**: The API tier is completely stateless; session or state tracking resides in persistent stores or in-memory caches.
3. **Fail-Closed Design**: Any unrecognized telemetry packet, unhandled exception, or sensor loss gracefully degrades to a safe operational state.
4. **Idempotent APIs**: Operational state transitions (e.g., dispatching a mission, acknowledging an alert) support idempotency keys.

