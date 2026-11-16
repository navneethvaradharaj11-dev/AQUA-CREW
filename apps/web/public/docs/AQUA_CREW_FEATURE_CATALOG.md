# AQUA CREW — COMPLETE FEATURE CATALOG
## Operational Capabilities, Analytical Engines & Module Feature Matrix

---

### 1. Operations Command Center (`/app`)

- **Live Telemetry & Health KPIs**: Real-time aggregated statistics on total pipeline kilometers monitored, active leak incidents, critical bursts, connected IoT sensors, and active virtual rovers.
- **District Metered Area (DMA) Breakdown**: Live hydraulic zone statuses (`DMA-METRO-CENTRAL`, `DMA-HARBOR-EAST`, `DMA-UPTOWN-NORTH`).
- **Interactive Operational Alerts**: Centralized alert acknowledgment feed with severity badges and rapid navigation to affected segments.
- **Master Acceptance Scenario Runner**: One-click execution of the reproducible 15-step demonstration scenario.

---

### 2. GIS Pipeline Intelligence (`/app/map`)

- **Interactive Vector & Topology Map**: High-performance Mapbox GL / Leaflet rendering of metropolitan distribution mains, valves, junctions, and storage reservoirs.
- **Layer Controls**: Toggle pipelines, sensor nodes, virtual rovers, DMA boundaries, and heatmaps.
- **Dynamic Segment Inspection**: Click on any pipeline to inspect material (Ductile Iron, Cast Iron, PVC, HDPE), diameter (mm), age, operating pressure (psi), and historical incident count.

---

### 3. AI Leak Detection & Acoustic Intelligence (`/app/intelligence`)

- **Spectral Signal Processing**: Fast Fourier Transform (FFT) and Power Spectral Density (PSD) analysis of hydrophone telemetry.
- **Deep Acoustic Classification**: Neural network classification detecting orifice leaks, circumferential cracks, and pressure surges with confidence intervals.
- **Signal Quality Diagnostics**: ISO 17025 calibration audits, signal-to-noise ratio (SNR) calculation, and acoustic energy distribution.

---

### 4. Fleet Management & Autonomous Inspection (`/app/fleet`, `/app/inspection-intelligence`)

- **Virtual Rover Roster**: Real-time tracking of `ROV-001`, `ROV-002`, `ROV-003` with battery percentage, operational state, speed, and payload status.
- **Autonomous Path Planning**: Dijkstra and A* shortest-path trajectory routing through pipe networks avoiding impassable valves.
- **Synthetic Defect Quantification**: Simulated in-pipe camera inspection measuring defect dimensions (crack length, crack width mm).

---

### 5. Hydraulic Digital Twin & Network Optimization (`/app/digital-twin`, `/app/optimization`)

- **EPANET / WNTR Hydraulic Engine**: Physics-informed headloss calculations (Hazen-Williams & Darcy-Weisbach) and Todini resilience index.
- **Transient Headloss Delta**: Models the exact pressure and discharge impact of leaks across adjacent junctions.
- **Pump & Pressure Optimization**: Multi-objective genetic algorithms minimizing energy consumption while guaranteeing minimum customer pressure.

---

### 6. Intelligent Repair Planning & Incident Workspace (`/app/repair-management`, `/app/incidents`)

- **Multi-Option Repair Recommendation**: Evaluates full-circle stainless steel clamps, epoxy sleeves, and pipe replacements based on crack severity and pressure.
- **Transparent Cost Estimation**: Granular bill of materials, equipment rental, labor hours, and excavation cost breakdowns.
- **10-Stage Lifecycle Visualizer**: Step-by-step progress tracker from anomaly detection through certified engineering approval and simulated closure.
- **Cryptographic Audit Dossier**: Generates formal 15-step incident investigation reports with SHA-256 digital signatures.

---

### 7. Secure IoT Device Ecosystem (`/app/iot-devices`)

- **Device Registry & Lifecycle**: Provisioning, quarantine, revocation, and credential rotation for ESP32 and acoustic nodes.
- **Edge Buffering & Retransmission**: Bounded circular buffer preventing telemetry loss during simulated network connectivity outages.
- **Air-Gapped Safety Interlocks**: Permanent enforcement of `HARDWARE_ACTUATION_ENABLED = false` rejecting all physical actuation commands.

