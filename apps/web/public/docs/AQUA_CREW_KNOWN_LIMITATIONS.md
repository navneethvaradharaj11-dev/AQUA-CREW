# AQUA CREW — Comprehensive Known Limitations & Engineering Assumptions
**Release:** v1.0.0-rc1  
**Category:** Engineering Transparency, Operational Constraints, Boundary Conditions, and Future Work  

---

## 1. Physical Actuation & Hardware Boundaries

### 1.1 Strict Simulation-First Invariant
- **Limitation:** AQUA CREW does not perform direct physical actuation (e.g., automated valve motorization or physical pump cutoff) on real-world municipal infrastructure.
- **Architectural Reason:** The platform permanently enforces `HARDWARE_ACTUATION_ENABLED = false` to eliminate any risk of unverified remote control over drinking water assets.
- **Operational Reality:** All pressure modulations and isolation schemes are simulated in the EPANET digital twin. Execution in the physical world requires certified field crews or human SCADA operators.

### 1.2 Robotic Rover In-Pipe Mechanical Constraints
- **Limitation:** In-pipe rover tracking is modeled via virtual simulation and edge telemetry ingestion.
- **Physical Engineering Dependencies:** Physical deployment of rovers inside live pressurized conduits ($> 4 \text{ bar}$) requires specialized hot-tapping insertion glands, pressurized tether seals, and intrinsic spark-proof electrical certifications (ATEX / IECEx) that lie beyond the software scope.

---

## 2. Computational Hydraulic Assumptions

### 2.1 1D Quasi-Steady & Extended Period Simulation (EPS)
- **Limitation:** The hydraulic digital twin utilizes the Todini Global Gradient Algorithm (GGA) to model 1D network flows.
- **Transient Fluid Dynamics:** Severe sub-second water hammer transients induced by instantaneous valve closure or sudden pump trip are evaluated using analytical Joukowsky estimates ($\Delta P = \rho \cdot a \cdot \Delta v$) rather than a full 2D/3D Method of Characteristics (MOC) compressible Navier-Stokes solver.

### 2.2 Roughness & Temperature Dependencies
- **Limitation:** Hazen-Williams coefficients ($C$) are modeled as static or age-degraded constants.
- **Viscosity:** Fluid kinematic viscosity is standardized for water at $20^\circ\text{C}$ ($1.004 \times 10^{-6} \text{ m}^2/\text{s}$). Sub-zero freezing effects or high-temperature industrial effluents require manual override parameters.

---

## 3. Acoustic AI Signal Processing Boundaries

### 3.1 Material-Dependent Acoustic Attenuation
- **Metallic Pipes (Cast Iron, Ductile Iron, Steel):** Acoustic waves propagate long distances ($500\text{--}1500 \text{ m}$) with low attenuation ($2\text{--}5 \text{ dB/100m}$).
- **Viscoelastic Pipes (PVC, HDPE, MDPE):** Plastic pipe walls absorb high-frequency shear waves, yielding high attenuation ($15\text{--}35 \text{ dB/100m}$). Cross-correlation localization on plastic mains requires closely spaced hydrophone insertion points ($< 150 \text{ m}$).

### 3.2 Acoustic Interference & False Positives
- **Background Noise:** Urban traffic rumble, underground railway vibrations, or nearby pressure-reducing valve cavitation generate acoustic energy. While bandpass filters ($500\text{--}3500 \text{ Hz}$) reject low-frequency traffic rumble, anomalous throttling valve cavitation requires the multi-source contradiction detection engine to avoid false positive alerts.

---

## 4. Scalability Boundaries & Enterprise Dimensions

### 4.1 Validated Network Scale
- **Tested Dimensions:** The platform has been rigorously validated on networks up to 5,000 pipes, 5,000 junctions, and 50 simultaneous rovers.
- **Extremely Large Conurbations:** Networks exceeding 100,000 conduit elements (e.g., Greater London or New York City distribution grids) would require distributed graph partitioning (e.g., ParMETIS or sub-network decomposition) to maintain sub-second EPANET matrix inversions.

---

## 5. AI Assistant & LLM Connectivity

### 5.1 Cloud Provider Fallback
- **Limitation:** Live natural language generation using NVIDIA NIM or OpenAI APIs requires active internet egress and valid API credentials.
- **Air-Gapped Behavior:** In disconnected or air-gapped municipal control rooms, the platform automatically falls back to its deterministic, rule-based reasoning engine. While facts and evidence citations remain 100% accurate, narrative flexibility is limited to pre-compiled engineering templates.

