# AQUA CREW — Infrastructure Risk Prediction Model
## Multi-Horizon Forecasting, Degradation Velocity & Uncertainty Intervals (Task 11)

```
========================================================================================
AQUA CREW PLATFORM — INFRASTRUCTURE PREDICTION MODEL SPECIFICATION
Document ID: AC-T11-PRED-2026-V1
Classification: Predictive Infrastructure Degradation & Horizon Forecasting
Simulation Mode: Software-Only Virtual Infrastructure Simulation
Provenance: VIRTUAL_SIMULATION_ENGINE (is_simulated: true)
========================================================================================
```

---

## 1. Overview & Objective

Municipal water utilities cannot operate solely reactively; by the time a pipe bursts, catastrophic water loss, road subsidence, and localized contamination have already occurred. 

The **Infrastructure Risk Prediction Model** forecasts pipeline vulnerability into the future across three operational horizons:
1. **24-Hour Operational Horizon** ($T+24\text{h}$): Imminent rupture alerts for immediate dispatch.
2. **7-Day Tactical Horizon** ($T+7\text{d}$): Weekly maintenance scheduling and rover patrol planning.
3. **30-Day Strategic Horizon** ($T+30\text{d}$): Capital renewal prioritization, pipe relining, and pressure zone re-zoning.

---

## 2. Deterioration Velocity Formulation

### 2.1. Daily Risk Rate ($d\text{Risk}/dt$)

The instantaneous degradation rate $\alpha(s) = \frac{d\text{Risk}}{dt}$ (score points per day) is evaluated through a hybrid physical-empirical model:

$$\alpha(s) = \alpha_{\text{base}} + \Delta\alpha_{\text{material}} + \Delta\alpha_{\text{incidents}} + \Delta\alpha_{\text{trend}}$$

Where:
- $\alpha_{\text{base}} = 0.05\text{ pts/day}$ (nominal baseline wear under steady-state conditions).
- Material degradation factor $\Delta\alpha_{\text{material}}$:
  - Cast Iron: $+0.12\text{ pts/day}$ (external pitting and graphitization).
  - Concrete / PCCP: $+0.08\text{ pts/day}$ (mortar cracking and pre-stressing relaxation).
  - Ductile Iron: $+0.05\text{ pts/day}$ (joint degradation).
  - HDPE / PVC: $+0.00\text{ pts/day}$.
- Incident frequency factor $\Delta\alpha_{\text{incidents}} = N_{\text{detections}} \times 0.18\text{ pts/day}$.
- If an unverified high-severity leak alert is pending: $+0.25\text{ pts/day}$.
- If Task 09 historical trend data exists: $\alpha(s) = -\text{HealthSlopePerDay} \times 0.8$.

### 2.2. Trend Direction Classification

The structural direction of the conduit is classified based on the projected 7-day delta $\Delta_{7\text{d}} = 7 \cdot \alpha(s)$:

$$\text{TrendDirection}(s) = \begin{cases}
\text{DETERIORATING} & \Delta_{7\text{d}} > +1.50\text{ pts} \\
\text{IMPROVING} & \Delta_{7\text{d}} < -1.50\text{ pts (post-repair or pressure stabilization)} \\
\text{STABLE} & -1.50\text{ pts} \le \Delta_{7\text{d}} \le +1.50\text{ pts}
\end{cases}$$

Conduits exhibiting daily rates $\alpha(s) \ge 0.40\text{ pts/day}$ or $\Delta_{7\text{d}} \ge 2.50\text{ pts}$ are flagged as **`rapid_degradation: true`**.

---

## 3. Multi-Horizon Forecasting Formulation

### 3.1. Projected Risk Equations

Given the current vulnerability index $V_0(s)$, the projected vulnerability $V_t(s)$ at horizon $t \in \{24\text{h}, 7\text{d}, 30\text{d}\}$ is:

$$V_{24\text{h}}(s) = \min(100.0, \max(0.0, V_0(s) + 1.0 \cdot \alpha(s)))$$
$$V_{7\text{d}}(s) = \min(100.0, \max(0.0, V_0(s) + 7.0 \cdot \alpha(s)))$$
$$V_{30\text{d}}(s) = \min(100.0, \max(0.0, V_0(s) + 30.0 \cdot \alpha(s)))$$

### 3.2. Expanding Confidence Intervals

Uncertainty naturally increases over longer forecast horizons due to unpredictable hydraulic demand spikes, soil moisture shifts, and operational valving changes. The model establishes expanding confidence intervals $\text{CI}_t = [L_t, U_t]$:

$$\text{CI}_{24\text{h}}(s) = \left[\max(0.0, V_{24\text{h}} - 4.0), \min(100.0, V_{24\text{h}} + 4.0)\right]$$
$$\text{CI}_{7\text{d}}(s) = \left[\max(0.0, V_{7\text{d}} - 6.5), \min(100.0, V_{7\text{d}} + 6.5)\right]$$
$$\text{CI}_{30\text{d}}(s) = \left[\max(0.0, V_{30\text{d}} - 10.5), \min(100.0, V_{30\text{d}} + 10.5)\right]$$

---

## 4. Explainable Primary Risk Drivers

The prediction engine extracts explicit qualitative and quantitative drivers from the underlying sub-scores:
- *"High nominal operating pressure (65 psi) elevates burst stress at joints."*
- *"Acoustic anomaly density in vicinity indicates active subsurface water discharge."*
- *"Cast iron material subject to graphitization and structural embrittlement."*
- *"Large transmission diameter (600mm) presents catastrophic systemic consequence."*

---

## 5. Mitigation Urgency Rating

Mitigation urgency translates future risk projections into actionable utility commands:

$$\text{MitigationUrgency}(s) = \begin{cases}
\text{IMMEDIATE} & V_{24\text{h}} \ge 80.0 \text{ or } V_{7\text{d}} \ge 85.0 \text{ or } \text{rapid\_degradation} = \text{true} \\
\text{SHORT\_TERM} & V_{7\text{d}} \ge 60.0 \text{ or } V_{30\text{d}} \ge 70.0 \\
\text{PLANNED} & V_{30\text{d}} \ge 45.0 \\
\text{ROUTINE} & V_{30\text{d}} < 45.0
\end{cases}$$

