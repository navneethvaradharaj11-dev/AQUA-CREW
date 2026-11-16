# AQUA CREW — TASK 14: Hydraulic Optimization Baseline Audit

**Document ID**: `AC-OPT-14-01`  
**Classification**: Engineering Baseline Audit & Hydraulic Specification  
**Status**: APPROVED  
**Author**: Principal Hydraulic Systems Engineer, Optimization Architect & Full-Stack Lead  
**Target Release**: AQUA CREW Core Platform v0.1.0 (Task 14)

---

## 1. Executive Summary & Purpose

The objective of **TASK 14** is to develop an intelligent, multi-objective water distribution network (WDN) optimization engine that evaluates and determines superior operating configurations under rigorous hydraulic and operational constraints.

Before introducing optimization decision variables and algorithms, this audit establishes:
1. The exact mathematical models, equations, and solvers currently implemented.
2. The hydraulic units, dimensional standards, and conversion factors.
3. Network topology, node types, link properties, and physical constraints.
4. Pump curves, operating boundaries, and energy computation formulas.
5. Pressure-reducing valve (PRV) behavior and pressure zone demarcations.
6. Torricelli-based emitter leakage models and pressure-dependent demand (PDD) mechanics.
7. Available simulation scenarios and solver interfaces (WNTR / EPANET 2.2 and Todini GGA).

---

## 2. Hydraulic Units & Dimensional Standardization

The platform maintains strict unit consistency between database persistence, computational solver engines, and external API interfaces:

| Parameter | Database & Schema Unit | Solver Internal Unit (WNTR/EPANET) | UI Display Unit | Conversion Factor |
|---|---|---|---|---|
| **Node Pressure** | `bar` | `m` (head) | `bar` / `psi` | $1\text{ bar} = 10.19716\text{ m H}_2\text{O} = 14.5038\text{ psi}$ |
| **Hydraulic Head** | `m` | `m` | `m` | $H = z + \frac{P}{\rho g}$ ($z$ = elevation) |
| **Elevation** | `m` | `m` | `m` | $1\text{ m} = 3.28084\text{ ft}$ |
| **Pipe Flow Rate** | `L/s` (LPS) | $\text{m}^3/\text{s}$ | `L/s` | $1\text{ m}^3/\text{s} = 1000\text{ L/s}$ |
| **Delivered Demand** | `L/s` (LPS) | $\text{m}^3/\text{s}$ | `L/s` / `m³/day` | $1\text{ L/s} = 86.4\text{ m}^3/\text{day}$ |
| **Leakage Volume** | `m³` | $\text{m}^3$ | `m³` / `m³/day` | Cumulative integral of leak flow over time |
| **Pipe Diameter** | `mm` | `m` | `mm` / `in` | $D\text{ (m)} = D\text{ (mm)} / 1000$ |
| **Pipe Length** | `m` | `m` | `m` | Direct SI metric |
| **Pump Speed** | Relative ratio ($s$) | Multiplier ($s \in [0.5, 1.2]$) | Ratio ($1.0 = \text{nominal}$) | Dimensionless |
| **Pump Electrical Power** | `kW` | $\text{W}$ / $\text{kW}$ | `kW` / `hp` | $1\text{ kW} = 1.34102\text{ hp}$ |
| **Energy Consumption** | `kWh` | $\text{kWh}$ | `kWh` / `MWh` | Integral of pump power over operating duration |
| **Energy Tariff** | `$/kWh` (USD) | `$/kWh` | `$/kWh` | Configurable tariff rate (or marked unknown) |

---

## 3. Network Topology & Physical Assets

The default municipal network (`NET-METRO-01` — Metro Central Water Supply Grid) represents a realistic looped and branched metropolitan distribution network:

```mermaid
graph LR
    R1["Northern Reservoir R1<br/>(Head: 85m)"] -->|Trunk A (750mm)| J1["Spine Junction J1<br/>(Elev: 16.5m)"]
    R1 -->|Booster Pump P1<br/>(45kW, Head: 65m)| J1
    R1 -->|Res Branch (350mm)| J6["Pinecrest Residential J6<br/>(Elev: 22m, Dem: 14 L/s)"]
    
    J1 -->|Trunk B1 (600mm)| J2["Metro Commercial J2<br/>(Elev: 14m, Dem: 18.5 L/s)"]
    J2 -->|Trunk B2 (600mm)| J3["Harbor Perimeter J3<br/>(Elev: 8m, Dem: 12 L/s)"]
    
    J1 -->|Feeder 1 (400mm)| J4["Eastern Industrial J4<br/>(Elev: 18m, Dem: 28 L/s)"]
    J4 -->|Feed Line (350mm)| T1["Elevated Tank T1<br/>(Diam: 18m, Lvl: 6.5m)"]
    
    J1 -->|Valve PRV-01<br/>(Target: 3.5 bar)| J5["Harbor Terminal J5<br/>(Elev: 6.5m, Dem: 15 L/s)"]
```

### 3.1 Nodes Summary (7 Active Nodes)
- **1 Source Reservoir**: `NODE-RES-01` (Northern Aqueduct Supply, Base Head = 85.0 m).
- **1 Storage Tank**: `NODE-TANK-01` (Elevated Tank T1, Elevation = 24.0 m, Min Lvl = 1.5 m, Max Lvl = 12.0 m, Init Lvl = 6.5 m, Diameter = 18.0 m).
- **5 Demand Junctions**:
  - `NODE-JUNC-01`: Grand Avenue Spine ($z = 16.5$ m, $Q_{base} = 22.0$ L/s).
  - `NODE-JUNC-02`: Commercial Core ($z = 14.0$ m, $Q_{base} = 18.5$ L/s).
  - `NODE-JUNC-03`: Western Harbor ($z = 8.0$ m, $Q_{base} = 12.0$ L/s).
  - `NODE-JUNC-04`: Eastern Industrial ($z = 18.0$ m, $Q_{base} = 28.0$ L/s).
  - `NODE-JUNC-05`: Harbor Low-Elevation Intake ($z = 6.5$ m, $Q_{base} = 15.0$ L/s).
  - `NODE-JUNC-06`: Pinecrest High-Elevation Branch ($z = 22.0$ m, $Q_{base} = 14.0$ L/s).
- **Total Base Municipal Demand**: $\sum Q_{base} = 109.5\text{ L/s} = 9,460.8\text{ m}^3/\text{day}$.

### 3.2 Links Summary (8 Physical Links)
- **6 Transmission & Distribution Pipes**:
  - `LINK-PIPE-TRUNK-A`: $L = 1050$ m, $D = 750$ mm, Hazen-Williams $C = 140$.
  - `LINK-PIPE-TRUNK-B1`: $L = 620$ m, $D = 600$ mm, $C = 130$ (corresponds to GIS segment `PIPE-SEC-4B-92`).
  - `LINK-PIPE-TRUNK-B2`: $L = 540$ m, $D = 600$ mm, $C = 130$.
  - `LINK-PIPE-IND-01`: $L = 820$ m, $D = 400$ mm, $C = 150$.
  - `LINK-PIPE-IND-TANK`: $L = 350$ m, $D = 350$ mm, $C = 140$.
  - `LINK-PIPE-RES-01`: $L = 940$ m, $D = 350$ mm, $C = 140$.
- **1 Control Valve**: `LINK-VALVE-HRB-PRV` (PRV, $D = 300$ mm, nominal setting = 3.5 bar downstream target).
- **1 Booster Pump Station**: `LINK-PUMP-BOOSTER-01` (P1, 45 kW electric motor, nominal speed $s = 1.0$).

---

## 4. Hydraulic Formulation & Governing Equations

### 4.1 Pipe Headloss (Hazen-Williams Equation)
The head loss $h_f$ across link $k$ of length $L$, diameter $D$, and roughness $C$ is computed via:
$$h_{f,k} = 10.67 \cdot \frac{L_k}{C_k^{1.852} \cdot D_k^{4.8704}} \cdot |Q_k|^{1.852} \cdot \text{sgn}(Q_k)$$

### 4.2 Pump Characteristic Curve & Affinity Laws
Booster pump P1 follows a standard 3-point multipoint head-discharge curve:
$$H_{pump}(Q, s) = s^2 \cdot h_0 - a \cdot \left(\frac{Q}{s}\right)^b$$
- Default baseline curve: $(Q=0, H=65.0\text{ m})$, $(Q=150\text{ L/s}, H=58.0\text{ m})$, $(Q=350\text{ L/s}, H=45.0\text{ m})$.
- Speed variation bounds: $s \in [0.5, 1.2]$.
- Shaft and wire-to-water power consumption:
  $$P_{hydraulic} = \rho \cdot g \cdot Q \cdot H_{pump} = 9.81 \cdot Q\text{ (m}^3/\text{s)} \cdot H\text{ (m) [kW]}$$
  $$P_{electric} = \frac{P_{hydraulic}}{\eta_{pump} \cdot \eta_{motor}}$$
  Where $\eta_{wire-to-water} = \eta_{pump} \cdot \eta_{motor} \approx 0.72$ at nominal design point.

### 4.3 Pressure-Dependent Demand (PDD / PDA)
Under pressure-driven simulation mode, delivered junction demand $q_j(t)$ is constrained by local nodal pressure $P_j$:
$$q_j(t) = \begin{cases}
0 & \text{if } P_j < P_{min} \\
Q_{req,j}(t) \cdot \sqrt{\frac{P_j - P_{min}}{P_{req} - P_{min}}} & \text{if } P_{min} \le P_j < P_{req} \\
Q_{req,j}(t) & \text{if } P_j \ge P_{req}
\end{cases}$$
- Minimum pressure threshold: $P_{min} = 0.5\text{ bar} = 5.1\text{ m}$.
- Required pressure threshold: $P_{req} = 1.5\text{ bar} = 15.3\text{ m}$.

### 4.4 Torricelli Leak Emitter Model
Orifice leakage discharging from junction $j$ is governed by Torricelli's orifice equation:
$$Q_{leak,j} = C_d \cdot A_{orifice} \cdot \sqrt{2 \cdot g \cdot \max(0, P_j)}$$
Or in EPANET emitter coefficient formulation:
$$Q_{leak,j} = C_{emitter} \cdot P_j^{\alpha} \quad (\alpha = 0.50)$$

---

## 5. Audit Conclusions & Optimization Constraints

1. **Solver Authority**: WNTR / EPANET 2.2 is established as the trusted hydraulic validation authority. All optimization candidate configurations must achieve successful hydraulic convergence and verified mass balance ($|\sum Q_{in} - \sum Q_{out}| < 10^{-3}$ L/s).
2. **Decision Variables Available for Optimization**:
   - Continuous pump speed $s \in [0.5, 1.2]$ for `LINK-PUMP-BOOSTER-01`.
   - Discrete pump schedule (hourly ON/OFF status $u \in \{0, 1\}$).
   - PRV downstream pressure setpoint $P_{setting} \in [1.5, 4.5]$ bar for `LINK-VALVE-HRB-PRV`.
3. **Mandatory Hydraulic Invariants**:
   - Minimum pressure at all demand junctions: $P_j \ge 1.5$ bar.
   - Maximum pressure constraint: $P_j \le 5.5$ bar (prevents pipe rupture and accelerated leakage).
   - Tank operational limits: $1.5\text{ m} \le L_{tank}(t) \le 12.0\text{ m}$.
   - Maximum pipeline velocity: $v_{pipe} \le 2.5$ m/s.
   - Delivered demand satisfaction: $\frac{\sum Q_{delivered}}{\sum Q_{requested}} \ge 99.5\%$.
4. **Physical Air-Gap**: The optimization engine evaluates candidates purely through the virtual digital twin; no actuation commands can be issued to physical hardware.

