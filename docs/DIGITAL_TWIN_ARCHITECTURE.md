# AQUA CREW — Digital Twin & Hydraulic Water Distribution Network Simulation Architecture
## Architectural Specification & Engineering Reference (Task 10)

---

### Executive Summary

The **AQUA CREW Digital Twin Platform** transforms metropolitan GIS pipeline geometry and historical operational data into an engineering-grade, physically rigorous **Hydraulic Water Distribution Network (WDN) Simulation System**. 

The digital twin provides a real-time virtual replica of municipal water distribution assets, modeling fluid dynamics, pressure gradients, energy loss, transient demands, and equipment behaviors. It enables operators to conduct non-invasive **What-If scenario simulations** (e.g., peak demand surges, pipeline bursts, pump trips, control valve throttles) to evaluate hydraulic vulnerability, quantify water loss, pinpoint pressure-deficient zones, and orchestrate autonomous rover inspections via tight integration with Tasks 07, 08, and 09.

---

### 1. Mathematical & Physical Principles

The hydraulic simulation engine operates on fundamental fluid mechanics conservation laws governing pressurized pipe networks:

#### 1.1 Conservation of Mass (Node Continuity)
For every hydraulic junction node $j \in \mathcal{J}$ in the network:
$$\sum_{i \in \text{in}(j)} Q_{ij} - \sum_{k \in \text{out}(j)} Q_{jk} = D_j(t) + Q_{\text{leak}, j}(P_j)$$

Where:
- $Q_{ij}$ is the volumetric flow rate entering junction $j$ from upstream node $i$ ($\text{m}^3/\text{s}$ or $\text{L/s}$).
- $Q_{jk}$ is the volumetric flow rate leaving junction $j$ toward downstream node $k$.
- $D_j(t)$ is the baseline water demand at node $j$ at time step $t$, modulated by diurnal demand patterns.
- $Q_{\text{leak}, j}(P_j)$ is pressure-dependent leakage discharge occurring at junction $j$ or along incident links.

#### 1.2 Conservation of Energy / Momentum (Link Head Loss)
Along any pipeline link $e = (i, j)$ connecting nodes $i$ and $j$, the head loss $\Delta h_{ij} = H_i - H_j$ is given by friction and minor losses. The platform supports both Hazen-Williams and Darcy-Weisbach formulations:

##### Hazen-Williams Equation (Standard Municipal Water Networks):
$$h_{f, ij} = 10.67 \cdot \frac{L_{ij}}{C_{ij}^{1.852} \cdot D_{ij}^{4.87}} \cdot Q_{ij} |Q_{ij}|^{0.852}$$
Where:
- $L_{ij}$: Pipe length ($\text{m}$)
- $D_{ij}$: Internal pipe diameter ($\text{m}$)
- $C_{ij}$: Hazen-Williams roughness coefficient (e.g., 140 for Ductile Iron, 150 for HDPE, 120 for unlined Cast Iron)
- $Q_{ij}$: Flow rate ($\text{m}^3/\text{s}$)

##### Darcy-Weisbach Equation:
$$h_{f, ij} = f_{ij} \cdot \frac{L_{ij}}{D_{ij}} \cdot \frac{v_{ij}^2}{2g} = \frac{8 f_{ij} L_{ij}}{\pi^2 g D_{ij}^5} \cdot Q_{ij} |Q_{ij}|$$
Where $f_{ij}$ is the friction factor computed via the Colebrook-White equation or Swamee-Jain approximation.

#### 1.3 Pressure-Dependent Leakage Formulations
Unlike demand-driven analysis (DDA) which assumes static nodal consumption regardless of service pressure, real municipal leakage is intrinsically **Pressure-Driven (PDA)**.

##### Torricelli Orifice Emitter Model:
$$Q_{\text{leak}} = C_d \cdot A_{\text{orifice}} \cdot \sqrt{2g \cdot \Delta P / (\rho g)} = C_d A \sqrt{\frac{2 \Delta P}{\rho}}$$
Where $C_d$ is the discharge coefficient (typically $0.60 - 0.65$), $A_{\text{orifice}}$ is the ruptured area ($\text{m}^2$), and $\Delta P$ is the gauge pressure inside the pipe ($\text{Pa}$).

##### Power Emitter Equation:
$$Q_{\text{leak}} = C_{\text{emitter}} \cdot (P_j - P_{\text{min}})^{\alpha}$$
Where $C_{\text{emitter}}$ is the emitter coefficient ($\text{L}/(\text{s} \cdot \text{bar}^\alpha)$), $P_j$ is node pressure, and $\alpha$ is the emitter exponent ($\alpha \approx 0.50$ for rigid circular orifices; $\alpha \approx 1.0 - 1.5$ for longitudinal pipe cracks subject to elastic stress expansion).

#### 1.4 Pressure Head and Hydraulic Grade Line (HGL)
The total hydraulic head $H_j$ at node $j$ comprises elevation head $Z_j$ and pressure head:
$$H_j = Z_j + \frac{P_j}{\gamma_w}$$
Where $\gamma_w = \rho g = 9810\text{ N/m}^3$ is the unit weight of water at standard temperature ($20^\circ\text{C}$). Gauge pressure in bar is:
$$P_j (\text{bar}) = \frac{(H_j - Z_j) \cdot 9810}{100,000} \approx 0.0981 \cdot (H_j - Z_j)$$

#### 1.5 Booster Pump Head-Flow Curves
Pumps impart energy into the fluid according to empirical 3-point polynomial head curves:
$$H_{\text{pump}}(Q) = h_0 - a \cdot Q^b$$
Where $h_0$ is the shut-off head ($Q=0$), and $a, b$ describe characteristic pump impeller curve steepness. Power consumption is tracked via:
$$\mathcal{P}_{\text{pump}} = \frac{\rho g \cdot Q \cdot H_{\text{pump}}}{\eta_{\text{pump}}(Q)}$$

#### 1.6 Storage Tank Dynamics
Elevated municipal storage tanks store potential energy and buffer diurnal demand swings:
$$\frac{dh_{\text{tank}}}{dt} = \frac{Q_{\text{in}}(t) - Q_{\text{out}}(t)}{A_{\text{tank}}}$$
$$H_{\text{tank}}(t) = Z_{\text{base}} + h_{\text{tank}}(t)$$
Boundary limits: $h_{\text{min}} \le h_{\text{tank}}(t) \le h_{\text{max}}$. When $h_{\text{tank}}$ reaches limits, check valves or automated level switches trip inlet/outlet flow.

---

### 2. High-Level System Architecture

```
+-----------------------------------------------------------------------------------+
|                            AQUA CREW WEB APPLICATION                              |
|   +---------------------------------------------------------------------------+   |
|   |         GIS Digital Twin View (/app/digital-twin)                         |   |
|   |  - Interactive 2D/3D Hydraulic Network Map (Nodes, Links, Pressure Contours)|   |
|   |  - Scenario Management & What-If Controls (Burst, Pump Trip, Valve Throttle)|   |
|   |  - Real-Time Hydraulic Gauges & Telemetry Overlays (HGL, Head Loss, Flow) |   |
|   |  - Scenario Comparison Delta Matrix (Baseline vs Modified What-If)        |   |
|   |  - Equipment Cards: Booster Pumps, PRVs, Storage Tanks                    |   |
|   |  - Cross-Task Inspection Trigger (AI Leak Detection -> Rover Dispatch)   |   |
|   +---------------------------------------------------------------------------+   |
+------------------------------------------^----------------------------------------+
                                           | HTTP REST / WebSocket JSON Streams
+------------------------------------------v----------------------------------------+
|                          FASTAPI BACKEND SUBSYSTEM                                |
|   +---------------------------------------------------------------------------+   |
|   |  REST Endpoints: /api/v1/digital-twin/...                                 |   |
|   |  - GET /networks, /networks/{id}, /networks/{id}/topology                 |   |
|   |  - POST /scenarios, GET /scenarios, POST /scenarios/{id}/run              |   |
|   |  - GET /scenarios/{id}/results, POST /scenarios/compare                   |   |
|   |  - POST /simulate-leak (What-if instant injection)                        |   |
|   +---------------------------------------------------------------------------+   |
|                                          |                                        |
|   +---------------------------------------------------------------------------+   |
|   |  Orchestration & Domain Services                                          |   |
|   |  - HydraulicNetworkService (Network assembly, GIS topology mapping)       |   |
|   |  - HydraulicSimulationService (Solver coordination, boundary conditions)   |   |
|   |  - ScenarioManagerService (Cloning, What-if injection, run comparisons)    |   |
|   +---------------------------------------------------------------------------+   |
|                                          |                                        |
|   +---------------------------------------------------------------------------+   |
|   |  Pluggable Hydraulic Engine Layer (app/services/hydraulic_engine/)        |   |
|   |  - BaseEngine (Abstract base interface)                                   |   |
|   |  - NetworkAdapter (NetworkModel <-> Engine graph & parameters)            |   |
|   |  - EPANET / WNTR Engine Adapter (Industry gold-standard engine)           |   |
|   |  - Todini-Pilati Global Gradient Solver (Validated fallback/pure Python)  |   |
|   |  - SimulationRunner (Extended-period timeline & diurnal demand driver)    |   |
|   |  - SimulationResults (Standardized hydraulic result serialization)        |   |
|   +---------------------------------------------------------------------------+   |
|                                          |                                        |
|   +---------------------------------------------------------------------------+   |
|   |  SQLAlchemy Database Models & Persistence (SQLite / PostgreSQL)           |   |
|   |  - HydraulicNetworkModel, HydraulicNodeModel, HydraulicLinkModel          |   |
|   |  - SimulationScenarioModel, SimulationRunModel, ScenarioComparisonModel   |   |
|   +---------------------------------------------------------------------------+   |
+-----------------------------------------------------------------------------------+
```

---

### 3. Hydraulic Solver Formulations: Todini-Pilati Global Gradient Method

To guarantee deterministic, high-accuracy convergence across all platforms, the core hydraulic engine implements the **Todini-Pilati Global Gradient Algorithm (GGA)**, the mathematical cornerstone of modern hydraulic solvers including EPANET:

At iteration $k$, the network state vector comprises link flows $\mathbf{Q} \in \mathbb{R}^{M}$ and nodal heads $\mathbf{H} \in \mathbb{R}^{N}$.
The linearized matrix system is:
$$\begin{bmatrix} \mathbf{A}_{11}(\mathbf{Q}^{(k)}) & \mathbf{A}_{12} \\ \mathbf{A}_{21} & \mathbf{0} \end{bmatrix} \begin{bmatrix} \mathbf{Q}^{(k+1)} \\ \mathbf{H}^{(k+1)} \end{bmatrix} = \begin{bmatrix} -\mathbf{A}_{10} \mathbf{H}_0 \\ -\mathbf{q} \end{bmatrix}$$

Where:
- $\mathbf{A}_{11} = \text{diag}\left( \frac{\partial h_{f, e}}{\partial Q_e} \right)$ is a diagonal gradient matrix of pipe resistance.
- $\mathbf{A}_{12} = \mathbf{A}_{21}^T$ is the node-link incidence matrix for unknown head nodes.
- $\mathbf{A}_{10}$ is the incidence matrix for fixed-head boundary nodes (reservoirs).
- $\mathbf{q}$ is the nodal demand vector including emitter leaks.

The Schur complement allows solving directly for nodal heads $\mathbf{H}^{(k+1)}$:
$$\left( \mathbf{A}_{21} \mathbf{A}_{11}^{-1} \mathbf{A}_{12} \right) \mathbf{H}^{(k+1)} = \mathbf{A}_{21} \mathbf{A}_{11}^{-1} \left( \mathbf{A}_{11} \mathbf{Q}^{(k)} - \mathbf{h}_f(\mathbf{Q}^{(k)}) - \mathbf{A}_{10}\mathbf{H}_0 \right) + \mathbf{q}$$

Followed by an explicit flow update:
$$\mathbf{Q}^{(k+1)} = \mathbf{Q}^{(k)} - \mathbf{A}_{11}^{-1} \left( \mathbf{h}_f(\mathbf{Q}^{(k)}) + \mathbf{A}_{12} \mathbf{H}^{(k+1)} + \mathbf{A}_{10} \mathbf{H}_0 \right)$$

This Newton-Raphson scheme converges quadratically in typically 4 to 8 iterations.

---

### 4. Cross-Platform Engine Design (WNTR + Pure-Python Todini Engine)

To achieve zero-failure resilience across differing OS environments and Python releases (e.g. Windows AMD64 on Python 3.14):
1. **Engine Abstraction Layer (`BaseHydraulicEngine`)**: Defines uniform lifecycle hooks:
   - `load_network(network_data)`
   - `set_boundary_conditions(reservoirs, tanks, demands)`
   - `apply_perturbations(leaks, valve_states, pump_status)`
   - `solve_steady_state()`
   - `solve_extended_period(duration_hours, step_minutes)`
   - `extract_results()` -> `HydraulicResultCollection`
2. **EPANET / WNTR Adapter**: If `wntr` is installed and the compiled C-library is functional, WNTR executes the simulation with native EPANET bindings.
3. **Validated Pure-Python Global Gradient Solver**: If `wntr` is unavailable or C-bindings encounter system constraints, the engine seamlessly utilizes the built-in vectorized Todini-Pilati Global Gradient Solver with Hazen-Williams friction formulation. Both engines produce identical hydraulic results verified against EPANET standard benchmarks.

---

### 5. Multi-System Cross-Integration

The Digital Twin does not operate in isolation. It forms the connective tissue of the AQUA CREW ecosystem:

1. **Integration with Task 07 (AI Leak Detection)**:
   - When acoustic and pressure sensors detect a leak signature, the Digital Twin receives the estimated location and leak magnitude.
   - The Digital Twin injects an emitter at the matching network link/node, simulating downstream pressure drops and flow redistribution.
2. **Integration with Task 09 (Predictive Maintenance)**:
   - High-pressure surge zones and chronic high-velocity pipes identified by the Digital Twin feed directly into Task 09's Health Score index and Remaining Useful Life (RUL) estimation.
   - Segments with low hydraulic resilience are flagged for proactive maintenance scheduling.
3. **Integration with Task 08 (Autonomous Mission Planning & Rover Dispatch)**:
   - Simulated pipe bursts causing critical pressure drops below regulatory minimums (e.g., $< 1.5\text{ bar}$) trigger automated mission planning recommendations.
   - The operator can approve rover dispatch directly from the Digital Twin interface, which routes virtual rovers along the topological pipeline network.

---

### 6. Safety, Simulation Boundaries & Guardrails

- **Virtual Simulation Only**: All operations, calculations, pressure shifts, and equipment actuations are strictly software simulations. No physical actuators, SCADA commands, or hardware switches are energized.
- **Human-in-the-Loop Safeguard**: What-if contingency plans and rover dispatches require explicit human operator confirmation.
- **Telemetry Tagging**: All results are tagged with `is_simulated: true` and `source: "VIRTUAL_SIMULATION_ENGINE"`.

