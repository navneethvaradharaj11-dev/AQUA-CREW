# AQUA CREW — Pipeline Health Scoring Engine Specification
**Task 09 Technical Documentation — Multi-Criteria Infrastructure Health Index**

## 1. Overview

The **Pipeline Health Scoring Engine** (`app/services/pipeline_health_service.py`) calculates an explainable, normalized Health Index $H \in [0, 100]$ for any pipeline segment in the municipal water network.

The engine evaluates multi-modal streaming and historical sensor observations across acoustic emissions, pressure stability, flow mass balance, and environmental soil saturation, modulated by material-specific vulnerability multipliers.

---

## 2. Health Categorization Scale

| Health Index ($H$) | Classification | Operational Meaning | Recommended Protocol |
| :--- | :--- | :--- | :--- |
| **$90 - 100$** | `EXCELLENT` | Nominal hydraulic performance; baseline acoustic noise ($<45\text{ dB}$). | Routine background polling (30 days). |
| **$75 - 89$** | `GOOD` | Normal operational aging; minor diurnal pressure fluctuation ($<0.3\text{ bar}$). | Standard monitoring (14 days). |
| **$50 - 74$** | `FAIR` | Measurable hydraulic/acoustic anomaly; moderate pressure drop or noise spikes. | Elevate sensor sampling; non-urgent survey. |
| **$25 - 49$** | `POOR` | Severe instability; persistent acoustic hiss ($>65\text{ dB}$), soil moisture saturation. | Schedule autonomous crawler inspection (48h). |
| **$0 - 24$** | `CRITICAL` | Imminent burst/rupture hazard; acute pressure loss ($>1.0\text{ bar}$), active fissure. | Immediate autonomous rover dispatch (24h). |

---

## 3. Mathematical Health Index Formulation

The health index starts from an optimal baseline of $100$ and applies bounded deductions:
\[
H = \max\left(0.0,\, \min\left(100.0,\, 100.0 - \Delta_{\text{total}} \cdot \omega_{\text{mat}}\right)\right)
\]
where:
\[
\Delta_{\text{total}} = \Delta_{\text{ac}} + \Delta_{\text{pr}} + \Delta_{\text{fl}} + \Delta_{\text{env}} + \Delta_{\text{hist}}
\]

### 3.1 Acoustic Stability Penalty ($\Delta_{\text{ac}}$)
Evaluates sound pressure levels and transient noise bursts:
\[
\Delta_{\text{ac\_spl}} = \begin{cases}
22.0 & \text{if } \text{SPL}_{\text{mean}} \ge 75\text{ dB} \\
12.0 & \text{if } \text{SPL}_{\text{mean}} \ge 60\text{ dB} \\
5.0  & \text{if } \text{SPL}_{\text{mean}} \ge 50\text{ dB} \\
0.0  & \text{otherwise}
\end{cases}
\]
\[
\Delta_{\text{ac\_anom}} = \min(15.0,\, N_{\text{spikes}} \times 2.5)
\]
\[
\Delta_{\text{ac}} = \Delta_{\text{ac\_spl}} + \Delta_{\text{ac\_anom}}
\]

### 3.2 Pressure Stability Penalty ($\Delta_{\text{pr}}$)
Evaluates deviation from design nominal pressure and hydraulic transients (water hammer):
\[
\Delta P = \max(0.0,\, P_{\text{nominal}} - P_{\text{mean}})
\]
\[
\Delta_{\text{pr\_drop}} = \begin{cases}
25.0 & \text{if } \Delta P \ge 1.0\text{ bar} \\
14.0 & \text{if } \Delta P \ge 0.5\text{ bar} \\
0.0  & \text{otherwise}
\end{cases}
\]
\[
\Delta_{\text{pr\_instab}} = \begin{cases} 10.0 & \text{if } \sigma_P \ge 0.35\text{ bar} \\ 0.0 & \text{otherwise} \end{cases}
\]
\[
\Delta_{\text{pr}} = \Delta_{\text{pr\_drop}} + \Delta_{\text{pr\_instab}} + \min(12.0,\, N_{\text{dips}} \times 2.0)
\]

### 3.3 Flow Imbalance Penalty ($\Delta_{\text{fl}}$)
Evaluates mass-balance discrepancy relative to expected throughput:
\[
\Delta_{\text{fl}} = \begin{cases}
15.0 & \text{if } \text{Imbalance} \ge 20\% \\
8.0  & \text{if } \text{Imbalance} \ge 10\% \\
0.0  & \text{otherwise}
\end{cases}
\]

### 3.4 Moisture & Environmental Penalty ($\Delta_{\text{env}}$)
Evaluates soil dielectric moisture saturation around pipe trenching:
\[
\Delta_{\text{env}} = \begin{cases}
18.0 & \text{if } \text{Moisture}_{\text{mean}} \ge 50\% \\
8.0  & \text{if } \text{Moisture}_{\text{mean}} \ge 30\% \\
0.0  & \text{otherwise}
\end{cases}
\]

### 3.5 Material Multiplier ($\omega_{\text{mat}}$)
Conduit structural vulnerability scaling:
- **Pre-stressed Concrete Cylinder Pipe (PCCP)**: $\omega_{\text{mat}} = 1.15$ (Vulnerable to sudden catastrophic wire breaks)
- **Ductile Iron (Class 54)**: $\omega_{\text{mat}} = 1.10$ (Subject to graphitization and pitting)
- **HDPE / PVC**: $\omega_{\text{mat}} = 0.90$ (High corrosion resistance, ductile failure mode)

---

## 4. Confidence & Data Coverage Decoupling

Data quality confidence is explicitly decoupled from the health score:
- **Data Coverage Metric**:
  \[
  \text{Coverage} = \min\left(100.0,\, \frac{N_{\text{samples}}}{60} \times 100\right)
  \]
- **Confidence Metric**:
  - $\ge 80\%$ coverage $\implies \text{Confidence} = 0.95$
  - $\ge 50\%$ coverage $\implies \text{Confidence} = 0.85$
  - $< 50\%$ coverage $\implies \text{Confidence} = 0.65$
- Segments with insufficient history carry explicit warnings preventing unverified assumptions of structural integrity.

---

## 5. Simulation Provenance

All health assessments carry:
- `is_simulated: true`
- `source: "VIRTUAL_SIMULATION_ENGINE"`

