# AQUA CREW 🌊🚀

> **Autonomous Water Leakage Detection, Localization & Repair Management Platform**  
> Engineered for metropolitan water distribution networks.

---

## 1. Project Overview & Strategy

**AQUA CREW** is an autonomous platform that connects ground rovers, in-pipe inspection crawlers, acoustic/pressure IoT sensors, AI-powered anomaly detection models, and a centralized operations command center to rapidly detect, pinpoint, and coordinate repairs for pipeline leaks.

### Strict Software-First Engineering Strategy
Physical hardware development is preceded by a comprehensive software foundation:
1. **Virtual Simulation First**: All rover telemetry, sensor transients, and network mechanics are simulated in software.
2. **Zero-Rewrite Hardware Abstraction**: Standardized data contracts and a Hardware Abstraction Layer (HAL) ensure physical hardware (MQTT, ROS2, LoRaWAN) can replace the virtual simulation without altering application logic or user interfaces.
3. **Decoupled Monorepo Architecture**: Frontend, backend, contracts, and documentation are strictly partitioned.

---

## 2. Monorepo Structure

```
AQUA-CREW/
├── apps/
│   ├── web/                    # Next.js 14+ Frontend (TypeScript, Tailwind CSS, Lucide)
│   │   ├── src/
│   │   │   ├── app/            # App Router (layout, globals.css, welcome page)
│   │   │   ├── components/     # Reusable UI primitives (Navbar, StatusCard, ModuleGrid, ApiHealthProbe)
│   │   │   └── lib/            # Utilities (cn helper)
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   └── api/                    # FastAPI Backend (Python 3.11+, Pydantic v2)
│       ├── app/
│       │   ├── main.py         # Application entry point with CORS & exception handlers
│       │   ├── config.py       # Pydantic BaseSettings environment configuration
│       │   ├── core/           # Logging & centralized exception handling
│       │   ├── schemas/        # Pydantic response models
│       │   ├── api/v1/         # Versioned API routes (/api/v1/health)
│       │   └── modules/        # 12 isolated domain module architectural boundaries
│       ├── requirements.txt
│       └── .env.example
│
├── packages/
│   └── contracts/              # Shared data & telemetry schemas
│       ├── src/                # TypeScript interfaces (telemetry.ts, api.ts)
│       └── python/             # Pydantic v2 schemas (telemetry.py, api.py)
│
├── docs/
│   ├── ARCHITECTURE.md         # Full architecture, data flow, and module boundaries
│   ├── API_SPECIFICATION.md    # REST endpoints, WebSocket streaming specs & envelopes
│   └── HARDWARE_INTEGRATION.md # Hardware abstraction, HAL drivers & telemetry roadmap
│
├── .gitignore                  # VCS ignore definitions
├── .env.example                # Root environment blueprint
└── README.md                   # This project guide
```

---

## 3. Technology Stack

- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons.
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, Uvicorn ASGI.
- **Data & Contracts**: Shared TypeScript interfaces and Pydantic models.
- **Database Target**: PostgreSQL + PostGIS (planned for spatial pipeline topology).
- **Communication Protocols**: REST API, WebSockets, MQTT (planned HAL).

---

## 4. Development Quickstart

### Prerequisites
- Node.js (v18+) & npm (v9+)
- Python (v3.11+)

---

### Step 1: Backend Setup (`apps/api`)

1. Open a terminal and navigate to the API directory:
   ```bash
   cd apps/api
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows (PowerShell):
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # macOS / Linux:
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Verify backend operation:
   - **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
   - **Swagger Docs**: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
   - **ReDoc**: [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)

---

### Step 2: Frontend Setup (`apps/web`)

1. In a separate terminal, navigate to the web directory:
   ```bash
   cd apps/web
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run TypeScript validation:
   ```bash
   npm run type-check
   ```

4. Start the Next.js development server:
   ```bash
   npm run dev
   ```

5. Open your browser and navigate to:
   - [http://localhost:3000](http://localhost:3000)

---

## 5. Architectural Modules (Roadmap)

| Module ID | Module Name | Scope |
| :--- | :--- | :--- |
| **MOD-01** | **Command Center** | Centralized real-time situational awareness & status dashboard |
| **MOD-02** | **Pipeline Mapping** | PostGIS-backed municipal pipe network GIS & pressure zones |
| **MOD-03** | **Rover Fleet Management** | Virtual & physical rover registry, battery SoC, telematics |
| **MOD-04** | **Mission Control** | Autonomous inspection patrol scheduling, dispatch, waypoints |
| **MOD-05** | **Sensor Monitoring** | Acoustic hydrophones, pressure transients & flow telemetry |
| **MOD-06** | **AI Leak Detection** | Spectral acoustic analysis & pressure drop anomaly inference |
| **MOD-07** | **Leak Localization** | Time-difference-of-arrival (TDOA) sub-meter coordinate snapping |
| **MOD-08** | **Repair Management** | Field crew work orders, ticketing, and repair lifecycle |
| **MOD-09** | **Repair Verification** | Post-repair acoustic and hydraulic certification testing |
| **MOD-10** | **Analytics & Reporting** | Non-revenue water (NRW) reduction, m³ saved, cost metrics |
| **MOD-11** | **Alerts & Notifications** | Urgent multi-channel alerting, sirens, and escalations |
| **MOD-12** | **Hardware Communication Gateway** | Hardware Abstraction Layer (HAL), MQTT, and ROS2 drivers |

---

## 6. Development Sequence

| Phase | Milestone | Status |
| :--- | :--- | :--- |
| **Task 01** | **Project Initialization & Architecture** | **COMPLETED** |
| Task 02 | Design System & UI Foundation | Next |
| Task 03 | AQUA CREW Command Center | Queued |
| Task 04 | Interactive Metropolitan Pipeline Map | Queued |
| Task 05 | Virtual Rover Fleet | Queued |
| Task 06 | Sensor Simulation | Queued |
| Task 07 | AI Leak Detection | Queued |
| Task 08 | Leak Localization | Queued |
| Task 09 | Mission Orchestration | Queued |
| Task 10 | Repair Management | Queued |
| Task 11 | Security & Safety | Queued |
| Task 12 | Integration & Testing | Queued |

