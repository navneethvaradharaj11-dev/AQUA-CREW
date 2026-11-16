# AQUA CREW — Leak and Burst Scenario Modeling
## Physics of Pipe Ruptures, Water Loss & Hydraulic Vulnerability (Task 10)

---

### Executive Summary

This document specifies the hydraulic modeling methodology for **sub-surface pin-hole leaks** and **catastrophic pipe bursts** in the AQUA CREW Digital Twin. It details orifice discharge physics, pressure drop propagation, unserved consumer demand, and automated cross-system dispatch handoff.

---

### 1. Classification of Pipe Breaches

| Category | Characteristic Orifice Area ($A$) | Discharge Coefficient ($C_d$) | Expected Discharge Range | Hydraulic Impact | Detection Signature |
|---|---|---|---|---|---|
| **Micro-Fissure / Weep** | $< 0.5\text{ cm}^2$ | $0.65$ | $0.1 - 1.5\text{ L/s}$ | Negligible pressure drop ($< 0.05\text{ bar}$) | Ultrasonic acoustic hiss ($> 2.5\text{ kHz}$) |
| **Developing Pin-Hole Leak** | $1.0 - 5.0\text{ cm}^2$ | $0.75$ | $3.0 - 10.0\text{ L/s}$ | Measurable localized pressure dip ($0.1 - 0.4\text{ bar}$) | Task 07 multi-sensor fusion (acoustic + moisture) |
| **Structural Longitudinal Crack** | $10.0 - 25.0\text{ cm}^2$ | $0.80$ | $15.0 - 35.0\text{ L/s}$ | Widespread pressure degradation ($0.5 - 1.5\text{ bar}$) | Chronic pressure deficit at downstream nodes |
| **Catastrophic Circumferential Burst** | $> 30.0\text{ cm}^2$ | $0.85$ | $> 40.0\text{ L/s}$ | Acute pressure collapse ($< 1.5\text{ bar}$ deficit alarm) | High flow surge, cavitation, ground eruption |

---

### 2. Torricelli Orifice Flow Dynamics

The physical volume of water discharged through a ruptured pipe wall into ambient atmosphere/soil is:
$$Q_{\text{leak}} = C_d \cdot A_{\text{orifice}} \cdot \sqrt{\frac{2 \Delta P}{\rho}}$$

In hydraulic head notation where $h_p = (H_{\text{node}} - Z_{\text{node}})$:
$$Q_{\text{leak}} = C_d \cdot A_{\text{orifice}} \cdot \sqrt{2g \cdot h_p}$$

#### Worked Example: Trunk Main B Rupture (`PIPE-SEC-4B-92` / `NODE-JUNC-02`)
- **Pipeline Parameters**: Ductile Iron, Diameter $= 600\text{ mm}$, Operating pressure $P_{\text{nominal}} = 4.35\text{ bar}$ ($44.35\text{ m}$ head).
- **Rupture Orifice Area**: $A = 35.0\text{ cm}^2 = 0.0035\text{ m}^2$.
- **Discharge Coefficient**: $C_d = 0.80$.
- **Discharge Flow**:
  $$Q_{\text{burst}} = 0.80 \cdot 0.0035 \cdot \sqrt{2 \cdot 9.81 \cdot 44.35} = 0.80 \cdot 0.0035 \cdot 29.497 \approx 0.08259\text{ m}^3/\text{s} = 82.6\text{ L/s}$$
- **Hydraulic Feedback**:
  As $82.6\text{ L/s}$ discharges through the rupture, link velocity in feeder `LINK-PIPE-TRUNK-B1` spikes from $0.64\text{ m/s}$ to $1.82\text{ m/s}$. The resulting friction head loss through the trunk lowers available head at `NODE-JUNC-02`, self-regulating equilibrium burst discharge to approximately $39.5\text{ L/s}$ at a depressed node pressure of $1.15\text{ bar}$.

---

### 3. Network Pressure Wave & Deficit Propagation

When a rupture occurs at Node J2:
1. **Immediate Zone of Depression**:
   - `NODE-JUNC-02`: Pressure drops from $4.35\text{ bar}$ down to $1.15\text{ bar}$ ($-73.6\%$ drop). Drops below the regulatory minimum ($1.50\text{ bar}$), triggering a `DEFICIT` alarm.
2. **Upstream Trunk Gradient**:
   - `NODE-JUNC-01`: Pressure drops from $4.62\text{ bar}$ to $2.85\text{ bar}$ ($-38.3\%$ drop) due to increased velocity-induced friction loss along `LINK-PIPE-TRUNK-A`.
3. **Peripheral Node Impact**:
   - `NODE-JUNC-03` (Western Harbor): Drops to $1.20\text{ bar}$ (Deficit).
4. **Water Loss Metrics**:
   - Daily water loss: $142.5\text{ m}^3/\text{day}$.
   - System water loss percentage: $28.4\%$ of total municipal intake.

---

### 4. Cross-System Workflow: AI Detection -> Digital Twin -> Rover Dispatch

```
[Task 07 Acoustic & Pressure AI]
        |
        | Detects acoustic spike (78 dB) & localized pressure drop
        v
[Task 10 Digital Twin Engine]
        |
        | Injects Torricelli orifice leak @ NODE-JUNC-02 (A = 35 cm2)
        | Solves WNTR / EPANET PDA hydraulics
        | Confirms pressure drop < 1.5 bar (Critical Burst)
        v
[Cross-System Handoff: POST /handoff-rover-dispatch]
        |
        | Packages: coordinates [-74.011, 40.7115], urgency "CRITICAL_BURST"
        v
[Task 08 Autonomous Mission Planning & Dispatch]
        |
        | Selects Rover (Proteus Mk.IV, Suitability: 94.5%)
        | Routes rover through topological pipeline network
        | Generates Mission Recommendation (REC-DTWIN-XXXXXX)
        v
[Human Operator Approval Dashboard]
        |
        | Operator reviews What-If comparison delta & approves dispatch
        v
[Virtual Rover Autonomous Inspection Initiated]
```

