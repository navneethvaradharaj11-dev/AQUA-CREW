# AQUA CREW — UNIFIED PRIORITY ENGINE
## Multi-Criteria Decision Analysis & Deterministic Ranking (Task 12 - Phase 5)

```
========================================================================================
AQUA CREW PLATFORM — MATHEMATICAL SPECIFICATION & PRIORITY FORMULATION
Milestone: TASK 12 — Unified Operational Intelligence & Decision Support Platform
Algorithm: Multi-Criteria Pareto-Calibrated Priority Engine
Methodology Version: v1.0.0-multi-criteria-pareto
========================================================================================
```

---

## 1. Principles of Operational Prioritisation

Water utility decision support requires prioritizing hundreds of potential maintenance, inspection, and repair actions across large metropolitan distribution networks. A naive summation of raw scores from disparate models (e.g. adding Task 07 anomaly probability to Task 11 vulnerability score) leads to severe mathematical distortion, uncalibrated dimensions, and dangerous operational decisions.

The AQUA CREW Unified Priority Engine adheres to four foundational design principles:

1. **Separation of Concerns**:
   - **Failure Likelihood** (Acoustic anomaly, asset health deficit, structural vulnerability).
   - **Failure Consequence** (Conduit diameter, arterial criticality, population served).
   - **Evidence Confidence** (Data coverage percentage, sensor baseline recency).
   - **Operational Feasibility** (Rover battery, thermal constraints, fleet availability).
2. **Feasibility Independence**:
   - Operational resource availability (e.g. whether a rover is currently idle or battery-depleted) **never alters the underlying infrastructure risk score**.
   - Feasibility is evaluated and presented as a separate operational constraint. A high-risk trunk main does not become "low priority" simply because an inspection robot is offline.
3. **No Uncalibrated Machine Learning**:
   - Machine learning is preserved where physics and signal processing warrant it (Task 07 acoustic random forest / isolation forest).
   - The operational prioritisation engine itself is **strictly deterministic, explainable, and multi-criteria**, ensuring 100% reproducibility and transparent auditability for utility regulators.
4. **Bounded Numerical Scaling**:
   - Every input dimension is normalized to $[0.0, 100.0]$.
   - The composite priority score is strictly bounded within $[0.0, 100.0]$.

---

## 2. Mathematical Formulation

The composite priority score $P \in [0.0, 100.0]$ is computed via a multi-criteria weighted linear combination, moderated by an empirical confidence discount:

$$P_{\text{raw}} = \sum_{k=1}^{6} w_k \cdot S_k$$

Where:
$$\sum_{k=1}^{6} w_k = 1.00$$

### Component Definitions & Weight Calibration

| Component $k$ | Variable | Description | Weight $w_k$ | Source Engine |
|---|---|---|---|---|
| **Incident Severity** | $S_{\text{inc}}$ | Normalized acoustic anomaly score ($0-100$) | $0.25$ | Task 07 AI Leak Detection |
| **Pipeline Vulnerability** | $S_{\text{vuln}}$ | Multi-factor vulnerability index ($0-100$) | $0.20$ | Task 11 Infrastructure Intelligence |
| **Asset Health Deficit** | $S_{\text{health}} = 100 - H$ | Inverted structural health index ($0-100$) | $0.20$ | Task 09 Predictive Maintenance |
| **Hydraulic Stress** | $S_{\text{hyd}}$ | Friction headloss and velocity stress ($0-100$) | $0.15$ | Task 10 Digital Twin |
| **Service Criticality** | $S_{\text{crit}}$ | Diameter and transmission consequence rating | $0.12$ | Physical Pipeline Attributes |
| **Historic Recurrence** | $S_{\text{rec}}$ | Frequency of previous leakage incidents | $0.08$ | Historical Event Logs |

### Service Criticality Scale ($S_{\text{crit}}$)
Transmission consequence scales with nominal diameter $D$ due to the volumetric discharge capacity and catastrophic flooding potential:

$$S_{\text{crit}}(D) = \begin{cases}
100.0 & \text{if } D \ge 600\text{ mm (Primary Arterial Transmission Main)} \\
80.0  & \text{if } 450\text{ mm} \le D < 600\text{ mm (Secondary Transmission Main)} \\
60.0  & \text{if } 300\text{ mm} \le D < 450\text{ mm (Primary Distribution Main)} \\
40.0  & \text{if } 150\text{ mm} \le D < 300\text{ mm (Secondary Distribution Feeder)} \\
20.0  & \text{if } D < 150\text{ mm (Service Connection Branch)}
\end{cases}$$

### Historic Recurrence Scale ($S_{\text{rec}}$)
Conduits experiencing repetitive joint or material failure receive escalating recurrence penalties, saturating at 5 prior events:

$$S_{\text{rec}}(N) = \min(100.0, N \cdot 20.0)$$

---

## 3. Confidence Moderation & Uncertainty Blending

When data completeness or sensor confidence $C \in [0.2, 1.0]$ is degraded (e.g. missing geotechnical measurements or stale acoustic records), raw priority is blended toward a neutral baseline score ($50.0$):

$$P = \text{round}\left(C \cdot P_{\text{raw}} + (1.0 - C) \cdot 50.0, \; 2\right)$$

- **High Confidence ($C = 0.95$)**: $P \approx P_{\text{raw}}$. High-risk conduits receive full emergency priority; healthy conduits remain low.
- **Low Confidence ($C = 0.50$)**: $P = 0.50 \cdot P_{\text{raw}} + 25.0$. Conduits are pulled into moderate monitoring tiers, prompting health review inspections.

---

## 4. Priority Tiers & Deterministic Action Mapping

The continuous composite priority score $P$ maps to five operational tiers via strict inclusive upper-boundary transitions:

$$\text{Priority Tier} = \begin{cases}
\text{CRITICAL\_IMMEDIATE} & \text{if } P \ge 80.0 \\
\text{URGENT}              & \text{if } 65.0 \le P < 80.0 \\
\text{HIGH\_PRIORITY}      & \text{if } 50.0 \le P < 65.0 \\
\text{ROUTINE}            & \text{if } 30.0 \le P < 50.0 \\
\text{DEFERRED}           & \text{if } P < 30.0
\end{cases}$$

---

## 5. Deterministic Queue Ranking Algorithm

In `OperationalPrioritisationService.rank_recommendations()`, items are sorted into a strict total order using a 4-tuple lexicographical sort key:

$$\text{Key}(\text{Item}) = \left(-P, \; -S_{\text{inc}}, \; -S_{\text{vuln}}, \; \text{timestamp}\right)$$

1. Primary: Composite priority score $P$ descending.
2. Secondary: Incident severity $S_{\text{inc}}$ descending (active leaks break ties).
3. Tertiary: Vulnerability score $S_{\text{vuln}}$ descending.
4. Quaternary: ISO-8601 creation timestamp ascending (earliest detected first).

This guarantees identical ranking across backend instances, automated test runs, and client sessions.

