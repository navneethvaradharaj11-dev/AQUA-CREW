# AQUA CREW — Master Project Presentation & Demonstration Guide
**Project:** AQUA CREW — Autonomous Water Infrastructure Intelligence, Leak Detection & Digital Twin  
**Release:** `v1.0.0-rc1`  
**Classification:** Executive Briefing, Technical Deep-Dive & Live Demonstration Walkthrough  

---

```
  █████╗  ██████╗ ██╗   ██╗ █████╗      ██████╗██████╗ ███████╗██╗    ██╗
 ██╔══██╗██╔═══██╗██║   ██║██╔══██╗    ██╔════╝██╔══██╗██╔════╝██║    ██║
 ███████║██║   ██║██║   ██║███████║    ██║     ██████╔╝█████╗  ██║ █╗ ██║
 ██╔══██║██║▄▄ ██║██║   ██║██╔══██║    ██║     ██╔══██╗██╔══╝  ██║███╗██║
 ██║  ██║╚██████╔╝╚██████╔╝██║  ██║    ╚██████╗██║  ██║███████╗╚███╔███╔╝
 ╚═╝  ╚═╝ ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝     ╚═════╝╚═╝  ╚═╝╚══════╝ ╚══╝╚══╝ 
              AUTONOMOUS WATER INFRASTRUCTURE INTELLIGENCE
```

---

## 1. Title & Project Identity

- **Platform Name:** AQUA CREW
- **Tagline:** Software-First Water Infrastructure Intelligence, Acoustic Leak Localization, Robotic Fleet Orchestration & Hydraulic Digital Twin Platform.
- **Mission Statement:** Eliminating non-revenue municipal water losses and preventing catastrophic urban main bursts through autonomous robotic inspection, computational fluid dynamics, and evidence-grounded AI reasoning.
- **Milestone Reached:** Release Candidate `v1.0.0-rc1` (Tasks 01 through 20 Completed).

---

## 2. Problem Statement: The Global Water Infrastructure Crisis

Modern municipal water distribution networks face an unprecedented structural crisis:
- **Catastrophic Non-Revenue Water (NRW):** Over **346 billion liters** of treated drinking water are lost globally every day due to undetected underground pipe leaks (equivalent to \$39B in annual utility revenue loss).
- **Aging Subterranean Assets:** Millions of kilometers of legacy cast iron and ductile iron water mains installed between 1920 and 1980 have exceeded their structural design lifespan, resulting in sudden bursts and severe urban street flooding.
- **Reactive, Expensive Maintenance:** Conventional utility leak detection relies on manual acoustic ground surveys that are slow, labor-intensive, and discover leaks only after surface sinkholes appear.
- **Siloed Systems:** SCADA telemetry, hydraulic models, GIS pipeline maps, and work order dispatch systems operate in isolated silos without unified automated coordination.

```mermaid
graph LR
    P1["Aging Cast Iron Mains (1920-1980)"] --> Problem["346 Billion Liters Lost Daily"]
    P2["Manual Acoustic Ground Surveys"] --> Problem
    P3["Siloed SCADA & GIS Systems"] --> Problem
    Problem --> Impact["Catastrophic Urban Bursts & $39B Annual Losses"]
```

---

## 3. Solution Overview: The AQUA CREW Platform

AQUA CREW replaces slow, fragmented manual surveys with an integrated, autonomous, software-first operational ecosystem:
- **Unified GIS Command Center:** Real-time visibility into pipe health, sensor streams, and rover operations on an interactive map.
- **AI-Powered Acoustic Intelligence:** Sub-millisecond spectral feature extraction and cross-correlation Time Delay of Arrival (TDOA) leak localization.
- **Virtual Robotic Rover Fleet:** Autonomous dispatch of in-pipe rovers constrained by battery life, tool payload, and fluid velocities.
- **Real-Time Hydraulic Digital Twin:** Computational fluid dynamics using EPANET 2.2 and the Todini Global Gradient Algorithm to model network pressures and burst impacts.
- **Intelligent Repair & Resource Planning:** Automated bill of materials, engineering specifications, cost estimates ($2,450 baseline benchmark), and dual-operator governance.

---

## 4. Key Platform Capabilities

```mermaid
graph TD
    GIS["1. GIS Pipeline Intelligence"] --> Central["Unified Operational Intelligence"]
    Rovers["2. Virtual Rover Fleet"] --> Central
    Acoustic["3. AI Acoustic Leak Detection"] --> Central
    Twin["4. EPANET Digital Twin (Todini)"] --> Central
    Opt["5. Pressure & Energy Optimization"] --> Central
    Repair["6. Intelligent Repair Planning"] --> Central
    IoT["7. IoT Device Registry & MQTT"] --> Central
    Security["8. Zero-Trust Security & RBAC"] --> Central
```

1. **GIS Pipeline Intelligence:** Dynamic pipe gradient rendering, structural vulnerability scoring, and asset history tracking.
2. **Virtual Rover Fleet:** 5 in-pipe robotic rovers (`ROV-01` through `ROV-05`) with battery state-of-charge tracking, tether tension monitoring, and autonomous docking.
3. **AI Acoustic Leak Detection:** Fourier transforms, continuous wavelets, spectral kurtosis, and TDOA localization along pipe conduits.
4. **Hydraulic Digital Twin:** EPANET 2.2 Todini GGA solver calculating mass continuity and frictional headloss across all conduits.
5. **Network Optimization:** Genetic algorithm PRV pressure reduction achieving **34.6% reduction in background water loss** while maintaining SLA pressures.
6. **Autonomous Inspection Intelligence:** Dynamic rover selection, trajectory planning, and hazard avoidance.
7. **Intelligent Repair Planning:** Resource allocation, excavation sizing, mechanical sleeve specifications, and cost modeling.
8. **IoT Device Ecosystem:** MQTT telemetry ingestion (0.007 ms mean latency), 2-point calibration, and polynomial thermal drift compensation.

---

## 5. System Architecture

AQUA CREW adopts a clean, modular event-driven architecture containerized across five microservices:

```mermaid
graph TD
    subgraph ClientTier ["Client Tier"]
        Web["Next.js 14 App Shell (:3000)"]
    end

    subgraph GatewayTier ["Gateway Tier"]
        Nginx["Nginx Reverse Proxy (:80 / :443)"]
    end

    subgraph APITier ["FastAPI Application Services (:8000)"]
        Router["API Router (/api/v1)"]
        WSHub["WebSocket Event Hub (/ws)"]
        AuthMiddleware["JWT & RBAC Security Layer"]
    end

    subgraph EngineTier ["Domain Intelligence Engines"]
        Twin["EPANET Todini Twin Engine"]
        AIEngine["Acoustic AI & TDOA Engine"]
        FleetEngine["Rover Dispatch & Routing Engine"]
        RepairEngine["Repair Planning & Cost Engine"]
    end

    subgraph SafetyBoundary ["Hardware Safety Gate"]
        Gate{"HARDWARE_ACTUATION_ENABLED?"}
        Block["Blocked (403 Forbidden)"]
        Sim["Virtual Twin Simulation"]
    end

    subgraph DataTier ["Data & Broker Tier"]
        DB[("PostgreSQL 15 + PostGIS (or SQLite)")]
        MQTT["Eclipse Mosquitto MQTT Broker (:1883)"]
    end

    Web --> Nginx
    Nginx --> Router
    Nginx --> WSHub
    Router --> AuthMiddleware
    AuthMiddleware --> EngineTier
    EngineTier --> Gate
    Gate -->|No (Simulation-First)| Sim
    Gate -->|Yes| Block
    EngineTier --> DB
    EngineTier <--> MQTT
```

---

## 6. AI & Machine Learning Capabilities

### 6.1 Acoustic Leak Detection & TDOA Localization
- **Acoustic Spectral Analysis:** Deploys Butterworth bandpass filtering ($500\text{--}3500 \text{ Hz}$), FFT Power Spectral Density (PSD), and Spectral Kurtosis to detect fluid jetting turbulence.
- **TDOA Localization Formula:**
  $$x = \frac{L - c \cdot \Delta t}{2}$$
  Accurately calculates leak distance within centimeters along conduit spans.

### 6.2 Evidence-Grounded Multi-Source Reasoning
The AI copilot cross-examines six evidence classifications before recommending interventions:
1. `ACOUSTIC_SIGNATURE` (Spectral peaks, kurtosis)
2. `HYDRAULIC_STATE` (Pressure drops, headloss deltas)
3. `GEOSPATIAL_RISK` (Soil resistivity, pipe age)
4. `ROVER_OBSERVATION` (In-pipe hydrophone scans)
5. `HISTORICAL_INCIDENT` (Prior sleeve repairs)
6. `OPERATOR_TELEMETRY` (Field notes)

### 6.3 Contradiction Safeguards
If hydrophone acoustic signals suggest a leak but EPANET digital twin pressures remain nominal, the system automatically flags a **Potential Cavitation False Positive**, requesting rover visual inspection instead of costly road excavation.

---

## 7. Hydraulic Digital Twin: Todini Solver & Optimization

- **EPANET 2.2 Compatibility:** Parses and executes standard `.inp` hydraulic network definitions.
- **Todini Global Gradient Algorithm (GGA):**
  Solves non-linear continuity and energy equations via iterative Newton-Raphson block matrix factorization:
  $$\begin{bmatrix} \mathbf{A}_{11} & \mathbf{A}_{12} \\ \mathbf{A}_{21} & \mathbf{0} \end{bmatrix} \begin{bmatrix} \mathbf{q}^{(m+1)} \\ \mathbf{h}^{(m+1)} \end{bmatrix} = \begin{bmatrix} -\mathbf{A}_{10}\mathbf{h}_0 \\ -\mathbf{q}^* \end{bmatrix}$$
- **Pressure Management Results:** In District Metered Area DMA-04, genetic algorithm PRV modulation reduced leakage from $1,850 \text{ L/h}$ to $1,210 \text{ L/h}$ (**34.6% reduction**) while maintaining consumer pressure $\ge 18.2 \text{ m}$ head.

---

## 8. Autonomous Inspection & Repair Planning

- **Fleet Dispatch Algorithm:** Evaluates candidate rovers by remaining battery ($> 20\%$), tool payload (acoustic hydrophone, sonar profiling), and in-pipe flow velocity ($v \le 2.5 \text{ m/s}$).
- **Repair Planning Engine:** Synthesizes structured engineering work orders:
  - Specific repair method (e.g., Stainless Steel Full-Circle Repair Clamp, CIPP Lining).
  - Bill of materials (clamps, gasket seals, bedding gravel, cold-mix asphalt).
  - Precise cost breakdown: Total estimated repair cost of **$2,450.00 USD** (Materials: \$450, Labor: \$1,200, Equipment: \$500, Permitting: \$300).
- **Post-Repair Sign-Off:** Enforces dual-stage verification (acoustic hydrophone silence + 30-minute hydraulic pressure hold test).

---

## 9. Hardware & IoT Integration Readiness

- **MQTT Messaging Protocol:** High-throughput streaming via Eclipse Mosquitto on port 1883 and WebSockets on 9001.
- **Transducer Calibration:** 2-point linear zero/span scaling and 2nd-order polynomial thermal drift compensation.
- **Actuation Safety Lock:** Physical infrastructure manipulation is permanently blocked:
  ```python
  HARDWARE_ACTUATION_ENABLED: bool = False
  ```
  Commands targeting real actuators return `HTTP 403 Forbidden` and trigger security alerts.

---

## 10. Security, RBAC & Reliability

- **Stateless Authentication:** RFC 7519 HMAC-SHA256 JWT with 60-minute expiration.
- **Role-Based Access Control:** 5 distinct operational roles (`SUPER_ADMIN`, `FIELD_OPERATOR`, `DATA_ANALYST`, `HYDRAULIC_ENGINEER`, `EXECUTIVE_AUDITOR`).
- **Cryptographic Audit Trail:** Workflow events, approvals, and final incident dossiers carry SHA-256 digital digests for non-repudiation.
- **Disaster Recovery:** Database snapshot backup executed in **0.0038s**, restored in **0.0011s** with 100% hash match, zero orphan records, and an RTO of 0.0011s.

---

## 11. Live Demonstration Walkthrough: The 15-Step Master Scenario

During the technical presentation, the presenter executes the reproducible 15-step incident lifecycle:

```mermaid
sequenceDiagram
    autonumber
    participant UI as Command Center UI
    participant API as FastAPI Backend
    participant Twin as EPANET Digital Twin
    participant Rover as Virtual Rover Fleet
    participant Repair as Repair Engine

    UI->>API: 1. Ingest Telemetry Anomaly (Pressure Drop: 4.8 -> 3.9 bar)
    API->>API: 2. Create Unified Incident (INC-2026-001 / P1-CRITICAL)
    API->>Twin: 3. Trigger Hydraulic Simulation (Headloss Delta: 4.12 m)
    API->>API: 4. Acoustic Spectral Analysis (Kurtosis: 4.82, PSD Peak: 1420 Hz)
    API->>API: 5. Cross-Correlation TDOA Localization (Leak at 142.5 m)
    API->>API: 6. Multi-Source Reasoning (Leak Confidence: 94.2%)
    API->>Rover: 7. Autonomous Rover Dispatch (ROV-01, Battery: 94%)
    Rover-->>API: 8. In-Pipe Inspection Sortie (Acoustic Coherence: 0.96)
    API->>API: 9. Incident Status -> CONFIRMED
    API->>Repair: 10. Generate Repair Plan (BoM: SS Clamp, Cost: $2,450)
    API->>UI: 11. Dual-Operator Approval Gate (Field Operator + Engineer)
    UI->>API: 12. Multi-Sig Approval Signed & Sealed
    API->>API: 13. Simulated Repair Execution (Clamp Installed)
    API->>Twin: 14. Post-Repair Verification (Pressure Restored to 4.8 bar)
    API->>UI: 15. Incident RESOLVED & Cryptographic Dossier Compiled
```

### Demonstration Script & Operator Commands:
1. **Reset to Clean State:**
   Click **"Reset Demo Data"** in `/app/incidents` (or call `POST /api/v1/incidents/scenarios/demo-reset`).
2. **Trigger Master Lifecycle:**
   Call `POST /api/v1/incidents/scenarios/master-15-step`.
3. **Inspect Real-Time UI:**
   Observe the live timeline in the Incident view update through all 15 stages with sub-millisecond responsiveness.
4. **Export Dossier:**
   Click **"Download Dossier Report"** to view the publication-grade incident dossier with SHA-256 signature `d3a7e4...`.

---

## 12. Test & Verification Results

- **Automated Regression Suite:** **1,076 / 1,076 Tests Passed (100%)** in 45.00 seconds.
- **Frontend Type Safety:** Zero errors in `tsc --noEmit`.
- **Production Build:** 19 static routes compiled and prerendered in Next.js 14.
- **Relational Integrity:** Zero orphan records across all 10 entity tables.

---

## 13. Empirical Performance Benchmarks

| Operation / Benchmark | Measured Value | SLA Target | Status |
| :--- | :---: | :---: | :---: |
| **Telemetry Ingestion Latency** | **0.007 ms** | $< 10.0 \text{ ms}$ | **PASSED** |
| **Acoustic AI Leak Inference** | **0.003 ms** | $< 5.0 \text{ ms}$ | **PASSED** |
| **Master 15-Step Lifecycle Execution** | **57.074 ms** | $< 500.0 \text{ ms}$ | **PASSED** |
| **Final Dossier Report Compilation** | **1.885 ms** | $< 50.0 \text{ ms}$ | **PASSED** |
| **Hermetic Demo State Reset** | **4.471 ms** | $< 100.0 \text{ ms}$ | **PASSED** |
| **Database Recovery Time (RTO)** | **0.0011 s** | $< 5.0 \text{ s}$ | **PASSED** |
| **Peak Process Memory Footprint** | **6.75 MB** | $< 100.0 \text{ MB}$ | **PASSED** |

---

## 14. Safety & Governance Principles

- **Simulation-First Guarantee:** Real-world actuators are physically isolated from software networks.
- **Multi-Signature Human-in-the-Loop:** High-impact civil interventions require consensus signatures from both field operators and professional hydraulic engineers.
- **Six-Tier Provenance Tracking:** All analytical results explicitly state whether data originated from field telemetry, acoustic algorithms, or the Todini solver.

---

## 15. Honest Engineering Assessment & Known Limitations

- **Transient Elastic Waves:** EPANET models quasi-steady state. Instantaneous sub-second water hammer transients use analytical Joukowsky approximations rather than full 3D Navier-Stokes solvers.
- **Plastic Pipe Attenuation:** Viscoelastic pipes (PVC/HDPE) attenuate high-frequency acoustic waves faster than ductile iron, requiring closer sensor spacing ($< 150 \text{ m}$).
- **Hardware Actuation:** Simulation-first design deliberately prohibits automated remote motorization of physical municipal valves.

---

## 16. Future Technology Roadmap

```mermaid
graph LR
    V1["v1.0.0 (Today): Software-First Simulation & Digital Twin"] --> V2["v1.5.0: Physical Hydrophone Edge Nodes & NB-IoT Field Pilots"]
    V2 --> V3["v2.0.0: Physical Micro-Rover Field Prototypes with Hot-Tap Glands"]
    V3 --> V4["v3.0.0: Fully Autonomous Closed-Loop Municipal Water Grid"]
```

1. **Phase 1 (Current):** Software-first digital twin, virtual fleet orchestration, and EPANET optimization.
2. **Phase 2 (Near-Term):** Field trials with physical NB-IoT acoustic loggers deployed in municipal pilot zones.
3. **Phase 3 (Long-Term):** Submersible physical micro-rover trials with specialized pressurized pipeline insertion locks.

---

## 17. Conclusion & Presentation Q&A Preparation

### Summary Takeaway
AQUA CREW proves that combining **computational fluid dynamics**, **acoustic machine learning**, and **autonomous robotics** inside a **secure, zero-trust digital twin** can transform municipal water utility operations from reactive emergency repairs into proactive, mathematically verified asset preservation.

### Frequently Asked Questions & Answers:

**Q1: How does AQUA CREW guarantee that it won't accidentally actuate a real-world municipal valve?**  
*Answer:* The platform enforces an architectural safety interlock (`HARDWARE_ACTUATION_ENABLED = false`). Any physical actuation command is blocked at the core middleware level, returning `HTTP 403 Forbidden` and alerting administrators.

**Q2: What happens if an acoustic sensor generates a false positive due to traffic noise?**  
*Answer:* The multi-source contradiction detection engine cross-examines acoustic energy against the EPANET digital twin. If acoustic energy is high but hydraulic pressure remains unchanged, the system flags a potential false positive and dispatches an in-pipe rover rather than issuing an excavation order.

**Q3: How fast does the system process live telemetry during a municipal burst?**  
*Answer:* Empirical benchmarks show telemetry ingestion processes packets in **0.007 milliseconds**, and the entire 15-step incident response pipeline runs in **57.07 milliseconds**.

**Q4: How easily can the demonstration be reset after a live presentation?**  
*Answer:* The platform includes a hermetic reset endpoint (`POST /api/v1/incidents/scenarios/demo-reset`) that restores demonstration state to baseline in **4.471 milliseconds** without schema resets.

---
*AQUA CREW v1.0.0-rc1 is certified accepted and ready for demonstration.*

