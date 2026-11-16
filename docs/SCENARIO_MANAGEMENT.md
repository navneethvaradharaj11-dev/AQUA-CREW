# AQUA CREW — Scenario Management & What-If Engine
## Operating Scenarios, Contingency Analysis & Comparison Matrix (Task 10)

---

### Executive Overview

The **Scenario Management Subsystem** provides municipal water operators with a simulation sandbox to explore hydraulic contingencies without risking physical infrastructure. It enables operators to clone operating baselines, apply stress perturbations (peak demand, burst, pump trips, valve closures), execute solver runs, and compute differential comparison matrices.

---

### 1. Canonical Scenarios Reference

The system pre-seeds six benchmark municipal scenarios:

#### 1.1 `SCEN-BASELINE-01`: Baseline Municipal Operating Conditions
- **Purpose**: Establishes reference hydraulic operating state.
- **Parameters**: Demand multiplier $= 1.0\times$, 0 active leaks, nominal pump speed $= 1.0\times$, Harbor PRV $= 3.5\text{ bar}$.
- **Expected Results**: All junction pressures between $3.8\text{ bar}$ and $5.8\text{ bar}$, 0 deficit nodes, 0% water loss.

#### 1.2 `SCEN-PEAK-DEMAND-01`: Summer Morning Demand Surge
- **Purpose**: Evaluates grid resilience during extreme heatwaves and morning consumption spikes.
- **Parameters**: Demand multiplier $= 1.60\times$ across all consumer nodes.
- **Expected Results**: Higher flow velocities through trunk mains; minor pressure dips in peripheral nodes (e.g. Node J6 drops to $2.4\text{ bar}$).

#### 1.3 `SCEN-BURST-PIPE-02`: Severe Pipe Burst on Metro Central Trunk B
- **Purpose**: Assesses emergency impact of sudden structural failure on primary trunk main `PIPE-SEC-4B-92`.
- **Parameters**: Emitter orifice area $A = 0.0035\text{ m}^2$ ($35\text{ cm}^2$), $C_d = 0.80$ at `NODE-JUNC-02`.
- **Expected Results**: Water loss spikes to $28.4\%$; pressure at Node J2 drops to $1.15\text{ bar}$ (Critical Deficit); triggers automated rover dispatch handoff.

#### 1.4 `SCEN-MINOR-LEAK-03`: Developing Pin-Hole Leak at Industrial Feeder 1
- **Purpose**: Simulates an incipient sub-surface pipe leak on `PIPE-IND-1A-04` correlated with Task 07 acoustic anomalies.
- **Parameters**: Emitter area $A = 0.0004\text{ m}^2$ ($4\text{ cm}^2$), $C_d = 0.75$ at `NODE-JUNC-04`.
- **Expected Results**: $4.5\text{ L/s}$ localized leakage; pressure dip of $0.25\text{ bar}$; no acute regulatory deficit.

#### 1.5 `SCEN-PUMP-TRIP-04`: Grand Avenue Spine Booster Pump Trip
- **Purpose**: Simulates unannounced power failure or mechanical trip of Booster Pump Station P1.
- **Parameters**: Pump `LINK-PUMP-BOOSTER-01` status set to `CLOSED` (speed $= 0.0$).
- **Expected Results**: Loss of dynamic $+45\text{ m}$ head boost; network operates on pure reservoir gravity head; central junction pressures drop by $1.8 - 2.4\text{ bar}$.

#### 1.6 `SCEN-RECOVERY-05`: Post-Repair Controlled Recovery
- **Purpose**: Simulates pipeline isolation for repair and network re-pressurization via Industrial Storage Tank T1.
- **Parameters**: `LINK-PIPE-TRUNK-B1` set to `CLOSED`; pump speed boosted to $1.15\times$; Tank T1 actively supplies compensatory flow.
- **Expected Results**: Restored service pressures to peripheral nodes while ruptured trunk is safely isolated.

---

### 2. Differential Comparison Matrix Computation

When an operator compares any what-if scenario against baseline:
$$\Delta P_j = P_j^{\text{scenario}} - P_j^{\text{baseline}}$$
$$\text{Drop \%}_j = \frac{P_j^{\text{baseline}} - P_j^{\text{scenario}}}{P_j^{\text{baseline}}} \times 100\%$$
$$\Delta Q_e = Q_e^{\text{scenario}} - Q_e^{\text{baseline}}$$
$$\Delta V_e = V_e^{\text{scenario}} - V_e^{\text{baseline}}$$

#### Risk Thresholds:
- **Nodal Deficit**: $P_j^{\text{scenario}} < 1.50\text{ bar}$ (Regulatory threshold violated).
- **Severe Pressure Drop**: Drop $\%_j > 30\%$.
- **High-Risk Pipeline Velocity**: $V_e^{\text{scenario}} > 2.0\text{ m/s}$ (risk of erosion, cavitation, and water hammer upon sudden closure).

