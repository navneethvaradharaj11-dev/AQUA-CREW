# AQUA CREW — HYDRAULIC IMPACT INTEGRATION
## Digital Twin What-If Analysis & Water Loss Quantification (Task 12 - Phase 6)

```
========================================================================================
AQUA CREW PLATFORM — HYDRAULIC DIGITAL TWIN INTEGRATION SPECIFICATION
Milestone: TASK 12 — Unified Operational Intelligence & Decision Support Platform
Engine: operational_hydraulic_impact_service.py
Solver Backing: Task 10 WNTR / EPANET & Todini Global Gradient Algorithm
Strict Safety Rule: Real-world physical actuators permanently disabled. Never changes
physical pump settings or valves in the live municipal distribution network.
========================================================================================
```

---

## 1. Digital Twin Hydraulic Integration Architecture

The AQUA CREW hydraulic digital twin (developed and verified in Tasks 10, 10.5, and 10.6) accurately models metropolitan water distribution physics using:
- **WNTR / EPANET 2.2** pressure-driven analysis (PDA).
- **Todini Global Gradient Algorithm (GGA)** with double-precision Cholesky linear system decomposition.
- **Strict Conservation Laws**: Zero mass-balance residual ($\sum Q_{\text{in}} - \sum Q_{\text{out}} = 0$) and energy loop closure residuals $\le 10^{-7}\text{ m}$.

Task 12 leverages this validated hydraulic solver directly through `OperationalHydraulicImpactService`, avoiding solver duplication while enabling operators to run on-demand **what-if impact simulations** for candidate pipe ruptures and leakage scenarios.

---

## 2. Orifice Discharge & Leak Rate Physics

The volumetric water discharge escaping through a simulated pipe-wall orifice is governed by the classical **Torricelli Orifice Flow Equation**:

$$Q_{\text{leak}} = C_d \cdot A \cdot \sqrt{2 g \cdot h} \quad \left[\text{m}^3/\text{s}\right]$$

Where:
- $C_d = 0.62$: Calibrated dimensionless discharge coefficient for sharp-edged circular apertures in municipal iron conduits (AWWA standard).
- $A = \frac{\pi d^2}{4}$: Cross-sectional area of the orifice aperture in $\text{m}^2$ ($d = \text{diameter in meters}$).
- $g = 9.80665\text{ m/s}^2$: Gravitational acceleration.
- $h$: Hydraulic head in meters of water column above atmospheric pressure:
  $$h = \frac{P}{\rho g} \approx P_{\text{bar}} \cdot 10.1972\text{ m}$$

### Daily Volumetric Water Loss
$$V_{\text{day}} = Q_{\text{leak}} \cdot 86,400\text{ seconds} \quad \left[\text{m}^3/\text{day}\right]$$

---

## 3. Network Pressure Deficit & Service Disruption Classification

When a leak is simulated in the digital twin, the increased discharge reduces localized pressure across surrounding junctions. The severity of service disruption is classified based on simulated discharge rate and pressure drop:

| Leak Rate $Q$ (L/s) | Pressure Drop $\Delta P$ (bar) | Disruption Risk | Affected Population Estimate | Operational Action |
|---|---|---|---|---|
| $> 25.0$ | $\ge 1.45$ | `SEVERE` | $> 10,000$ | Immediate emergency isolation & rover acoustic dispatch |
| $10.0 - 25.0$ | $0.85 - 1.45$ | `MODERATE` | $4,000 - 10,000$ | Throttling simulation & 24h repair scheduling |
| $2.0 - 10.0$ | $0.35 - 0.85$ | `LOW` | $1,000 - 4,000$ | Autonomous crawler patrol within 48h |
| $< 2.0$ | $< 0.35$ | `NONE` | Minimal | Continuous background acoustic logging |

---

## 4. Strict Governance & Provenance Rules

### Rule 1: Estimated vs. Measured Water Loss
- Every output from the digital twin what-if engine sets:
  ```json
  "is_water_loss_measured": false,
  "data_quality_rating": "ESTIMATED_SIMULATED"
  ```
- The platform explicitly distinguishes simulated orifice discharge estimates from certified billing meters or real-world acoustic ultrasonic flow meter readings.

### Rule 2: Prohibition of Fabricated Cost Figures
- In accordance with the Project Development Rules: **Do not fabricate financial savings or operational benefits.**
- If real utility billing tariff structures or labor cost databases are not connected, the cost display strictly returns:
  ```json
  "cost_impact_display": "NOT AVAILABLE"
  ```
- Fabricated dollar or euro currency figures are strictly prohibited.

### Rule 3: Permanent Actuator Interlock
- The what-if engine runs in an isolated virtual sandbox.
- It produces mathematical comparisons between a `BASELINE` scenario and a `LEAK_WHATIF` scenario without issuing commands to physical pumps, variable frequency drives (VFDs), or motorized control valves.

