# AQUA CREW — Temporal Trend Analysis Engine Specification
**Task 09 Technical Documentation — Degradation Velocity & Statistical Trajectory Estimation**

## 1. Overview

The **Temporal Trend Analysis Service** (`app/services/trend_analysis_service.py`) analyzes time-series telemetry over rolling lookback windows ($15\text{ min}$, $1\text{ hr}$, $24\text{ hr}$, $7\text{ days}$, $30\text{ days}$) to measure the **velocity of infrastructure deterioration**.

By fitting statistical linear regressions across successive health checkpoints, the service distinguishes benign, self-recovering fluctuations from compounding, structural deterioration.

---

## 2. Statistical Regression Formulation

For an ordered sequence of $k$ historical observation checkpoints $(t_1, H_1), (t_2, H_2), \dots, (t_k, H_k)$ sampled across the lookback window, the service computes the Ordinary Least Squares (OLS) regression slope $\beta$:

\[
\beta = \frac{\sum_{i=1}^{k} (t_i - \bar{t})(H_i - \bar{H})}{\sum_{i=1}^{k} (t_i - \bar{t})^2}
\]
where:
- $t_i$: Time in days moving forward ($t_k$ represents current time).
- $H_i$: Health index ($0 - 100$) at checkpoint $t_i$.
- $\beta$: Degradation velocity in **health points per day**.

---

## 3. Trend Classifications

| Trend Classification | Slope Threshold ($\beta$) | Physical Meaning | System Response |
| :--- | :--- | :--- | :--- |
| **`IMPROVING`** | $\beta > +0.5\text{ pts/day}$ | Pipeline recovering; pressure stabilizing post-maintenance. | Confirm positive trend; reduce alert urgency. |
| **`STABLE`** | $-0.5 \le \beta \le +0.5\text{ pts/day}$ | Stationary hydraulic equilibrium; negligible degradation drift. | Maintain nominal monitoring protocol. |
| **`DETERIORATING`** | $-2.0 \le \beta < -0.5\text{ pts/day}$ | Measurable steady wear; expanding fissure or packing degradation. | Escalate sensor polling; schedule inspection. |
| **`RAPIDLY_DETERIORATING`**| $\beta < -2.0\text{ pts/day}$ | Exponential structural failure or active high-rate washout. | Issue critical alert; recommend rover dispatch. |
| **`INSUFFICIENT_DATA`** | $k < 3$ checkpoints | Insufficient historical sampling history to compute slope. | Label as unverified; flag for data acquisition. |

---

## 4. Multi-Parametric Anomaly Metrics

In addition to health slope $\beta$, the trend engine evaluates secondary physical indicators:
1. **Pressure Variance ($\sigma_P^2$)**:
   \[
   \sigma_P^2 = \frac{1}{k} \sum_{i=1}^{k} (P_i - \bar{P})^2
   \]
   High variance indicates water hammer, cavitation, or faulty pressure reducing valves (PRVs).
2. **Acoustic Spike Frequency ($N_{\text{spikes}}$)**:
   Counts transient acoustic events where sound pressure level exceeds the background baseline by $\ge 15\text{ dB}$.
3. **Flow Mass Balance Ratio ($R_{\text{flow}}$)**:
   Tracks divergence between upstream injection meters and downstream billing meters.

---

## 5. UI Time-Series Chart Integration

The trend engine generates structured JSON payloads for frontend SVG charting (`PredictiveMaintenanceView.tsx`), including:
- Timestamp (ISO 8601)
- Day offset relative to current time
- Health score ($0 - 100$)
- Pressure in bar
- Flow in L/s
- Acoustic SPL in dB

---

## 6. Simulation Provenance

All temporal trends and historical points carry:
- `is_simulated: true`
- `source: "VIRTUAL_SIMULATION_ENGINE"`

