# AQUA CREW — TASK 14: OBJECTIVE & CONSTRAINT MATHEMATICAL MODEL

## 1. Mathematical Formulation of Multi-Objective Optimization

The AQUA CREW Network Optimization Engine formulates water distribution network operations as a constrained non-linear multi-objective optimization problem:

$$\min_{\mathbf{x} \in \Omega} \mathbf{F}(\mathbf{x}) = \left[ f_{\text{leak}}(\mathbf{x}),\, f_{\text{energy}}(\mathbf{x}),\, f_{\text{press}}(\mathbf{x}),\, f_{\text{demand}}(\mathbf{x}),\, f_{\text{cost}}(\mathbf{x}) \right]^T$$

subject to hydraulic continuity, energy conservation, and infrastructure safety constraints:

$$\mathbf{g}(\mathbf{x}) \le \mathbf{0}, \quad \mathbf{h}(\mathbf{x}) = \mathbf{0}$$

where $\mathbf{x}$ represents the vector of continuous and discrete decision variables:
- $s_p \in [s_{\min}, s_{\max}]$: Relative speed ratio for variable speed pump $p \in \mathcal{P}$.
- $P_{\text{set}, v} \in [P_{v,\min}, P_{v,\max}]$: Downstream pressure setpoint for pressure reducing valve $v \in \mathcal{V}$.
- $u_{p,t} \in \{0, 1\}$: Binary status (on/off) of pump $p$ at time interval $t$.

---

## 2. Objective Function Definitions

### 2.1 Water-Loss Minimization ($f_{\text{leak}}$)
Background leakage across all pipe junctions and burst orifices is modeled using Torricelli's orifice equation and the FAVAD (Fixed and Variable Area Discharges) principle:

$$q_{\text{leak}, j}(t) = C_d A_j \sqrt{\frac{2 P_j(t)}{\rho}} = \alpha_j \left( \frac{P_j(t)}{\rho g} \right)^{\beta_j}$$

For standard network junctions, $\beta_j \approx 0.5$ (orifice flow) to $1.15$ (elastic pipe fractures). Over a simulation horizon $T$:

$$f_{\text{leak}}(\mathbf{x}) = \sum_{t=1}^{T} \sum_{j \in \mathcal{J}} q_{\text{leak}, j}(t) \cdot \Delta t \quad \left[\text{m}^3\right]$$

### 2.2 Electrical Energy Minimization ($f_{\text{energy}}$)
Hydraulic power transferred to the fluid by pump $p$ delivering flow $Q_p$ against head $H_p$ is:

$$P_{\text{hyd}, p}(t) = \rho g Q_p(t) H_p(t) \quad [\text{W}]$$

Accounting for variable speed drive (VFD), electric motor, and pump impeller efficiencies ($\eta_{\text{wire-to-water}} = \eta_{\text{vfd}} \eta_{\text{motor}} \eta_{\text{hyd}}$):

$$P_{\text{elec}, p}(t) = \frac{\rho g Q_p(t) H_p(t)}{\eta_p(Q_p(t), s_p(t))} \quad [\text{kW}]$$

Total electrical energy consumed over duration $T$:

$$f_{\text{energy}}(\mathbf{x}) = \sum_{t=1}^{T} \sum_{p \in \mathcal{P}} P_{\text{elec}, p}(t) \cdot \Delta t \quad [\text{kWh}]$$

### 2.3 Pressure Quality & Stability ($f_{\text{press}}$)
Excessive pressure causes pipe fatigue and elevates leakage rates, while deficient pressure breaches regulatory standards. The pressure objective penalizes deviation from target nominal pressure $P_{\text{target}}$ (standard: $3.5\text{ bar}$):

$$f_{\text{press}}(\mathbf{x}) = \frac{1}{|\mathcal{J}| T} \sum_{t=1}^{T} \sum_{j \in \mathcal{J}} \left( \frac{|P_j(t) - P_{\text{target}}|}{P_{\text{target}}} \right)^2$$

### 2.4 Demand Satisfaction Fulfillment ($f_{\text{demand}}$)
In Pressure-Dependent Demand (PDA) mode, delivered demand $d_{\text{act}, j}(t)$ is governed by junction pressure:

$$d_{\text{act}, j}(t) = \begin{cases} 
0 & \text{if } P_j(t) < P_{\min} \\
d_{\text{req}, j}(t) \sqrt{\frac{P_j(t) - P_{\min}}{P_{\text{req}} - P_{\min}}} & \text{if } P_{\min} \le P_j(t) < P_{\text{req}} \\
d_{\text{req}, j}(t) & \text{if } P_j(t) \ge P_{\text{req}}
\end{cases}$$

The demand penalty function strictly penalizes unserved consumer demand:

$$f_{\text{demand}}(\mathbf{x}) = \max\left(0,\, 1.0 - \frac{\sum_{t=1}^T \sum_{j \in \mathcal{J}} d_{\text{act}, j}(t)}{\sum_{t=1}^T \sum_{j \in \mathcal{J}} d_{\text{req}, j}(t)}\right)$$

### 2.5 Operational Cost ($f_{\text{cost}}$)
When time-of-use or flat electricity tariff $c_e(t)$ (\$/kWh) is provided:

$$f_{\text{cost}}(\mathbf{x}) = \sum_{t=1}^{T} \sum_{p \in \mathcal{P}} P_{\text{elec}, p}(t) \cdot c_e(t) \cdot \Delta t \quad [\text{USD}]$$

*Zero-Substitution Rule*: When $c_e(t)$ is missing or null, $f_{\text{cost}}$ is omitted and `cost_data_available` is set to `False`.

---

## 3. Objective Normalization & Scalar Scoring

To synthesize a scalar objective function for search heuristics and candidate ranking, each component is normalized against the nominal unoptimized baseline solution $\mathbf{x}_{\text{base}}$:

$$J(\mathbf{x}) = w_{\text{leak}} \frac{f_{\text{leak}}(\mathbf{x})}{f_{\text{leak}}(\mathbf{x}_{\text{base}})} + w_{\text{energy}} \frac{f_{\text{energy}}(\mathbf{x})}{f_{\text{energy}}(\mathbf{x}_{\text{base}})} + w_{\text{press}} f_{\text{press}}(\mathbf{x}) + w_{\text{demand}} \cdot 100 \cdot f_{\text{demand}}(\mathbf{x}) + w_{\text{cost}} \frac{f_{\text{cost}}(\mathbf{x})}{f_{\text{cost}}(\mathbf{x}_{\text{base}})}$$

If any hydraulic or structural constraints are breached, an infeasibility penalty is compounded:

$$J_{\text{penalized}}(\mathbf{x}) = J(\mathbf{x}) + 100.0 \cdot N_{\text{violations}}$$

### Standard Objective Profiles & Weight Vectors

| Profile Name | $w_{\text{leak}}$ | $w_{\text{energy}}$ | $w_{\text{press}}$ | $w_{\text{demand}}$ | $w_{\text{cost}}$ | Primary Optimization Target |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| `BALANCED_OPERATION` | 0.25 | 0.25 | 0.25 | 0.25 | 0.00 | Balanced performance across all parameters |
| `ENERGY_EFFICIENCY` | 0.15 | 0.50 | 0.20 | 0.15 | 0.00 | Minimize kWh consumption while meeting service thresholds |
| `LEAKAGE_REDUCTION` | 0.50 | 0.15 | 0.20 | 0.15 | 0.00 | Maximum pressure reduction to curtail background loss |
| `PRESSURE_STABILITY` | 0.15 | 0.15 | 0.50 | 0.20 | 0.00 | Minimize DMA pressure variance and surge risk |

---

## 4. Hydraulic & Structural Constraints

Every candidate solution must strictly satisfy all physical constraints:

1. **Minimum Service Pressure**:
   $$\forall j \in \mathcal{J}, \forall t \in [0, T]: \quad P_j(t) \ge P_{\text{service},\min} \quad (\text{Standard: } 1.5\text{ bar} / 15.3\text{ m})$$

2. **Maximum Allowable Structural Pressure**:
   $$\forall j \in \mathcal{J}, \forall t \in [0, T]: \quad P_j(t) \le P_{\text{pipe},\max} \quad (\text{Standard: } 8.5\text{ bar} / 86.7\text{ m})$$

3. **Maximum Pipe Flow Velocity**:
   $$\forall l \in \mathcal{L}, \forall t \in [0, T]: \quad |v_l(t)| \le v_{\max} \quad (\text{Standard: } 7.0\text{ m/s})$$

4. **Storage Tank Operational Limits**:
   $$\forall k \in \mathcal{K}, \forall t \in [0, T]: \quad y_{\min, k} \le y_k(t) \le y_{\max, k} \quad (\text{Standard: } 1.5\text{ m} \le y_k \le 12.0\text{ m})$$

5. **Pump Switching Frequency**:
   $$\sum_{t=1}^{T-1} |u_{p,t+1} - u_{p,t}| \le S_{\max, p} \quad (\text{Standard: } \le 4\text{ switches/24h})$$

