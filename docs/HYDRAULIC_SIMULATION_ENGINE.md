# AQUA CREW — Hydraulic Simulation Engine Specification
## Solver Mathematics, Engine Architecture & Algorithms (Task 10)

---

### Executive Summary

The **AQUA CREW Hydraulic Simulation Engine** coordinates scientific numerical solvers to calculate the steady-state and extended-period hydraulic state of pressurized water distribution networks. The architecture pairs an industry-standard **EPANET 2.2 / WNTR Pressure-Dependent Demand (PDD)** engine with an embedded, zero-dependency **Todini-Pilati Global Gradient Solver** implemented in vectorized Python and NumPy.

---

### 1. Mathematical Solver Formulations

#### 1.1 Non-Linear Network Equations
The hydraulic state of a pipe network of $M$ links and $N$ unknown-head junction nodes is governed by the simultaneous system:
1. **Link Energy Conservation**:
   $$\mathbf{A}_{12} \mathbf{H} + \mathbf{A}_{10} \mathbf{H}_0 + \mathbf{h}_f(\mathbf{Q}) = \mathbf{0}$$
2. **Node Mass Conservation**:
   $$\mathbf{A}_{12}^T \mathbf{Q} - \mathbf{q}(\mathbf{H}) = \mathbf{0}$$

Where:
- $\mathbf{Q} \in \mathbb{R}^M$ is the vector of link volumetric flow rates ($m^3/s$).
- $\mathbf{H} \in \mathbb{R}^N$ is the vector of unknown nodal total heads ($m$).
- $\mathbf{H}_0 \in \mathbb{R}^{N_0}$ is the fixed head at reservoir boundary nodes ($m$).
- $\mathbf{h}_f(\mathbf{Q})$ is the non-linear friction and minor headloss vector.
- $\mathbf{A}_{12}$ and $\mathbf{A}_{10}$ are the incidence matrices.
- $\mathbf{q}(\mathbf{H})$ is the nodal withdrawal vector (including pressure-dependent leaks).

#### 1.2 Todini-Pilati Global Gradient Algorithm (GGA)
To solve this coupled non-linear system without inversion of non-diagonal link resistance, the engine computes Newton-Raphson increments using the Schur complement:

At iteration $k$:
1. Compute link gradient diagonal matrix $\mathbf{A}_{11} \in \mathbb{R}^{M \times M}$:
   $$A_{11, mm} = \frac{\partial h_{f, m}}{\partial Q_m} = 1.852 \cdot r_m \cdot |Q_m|^{0.852}$$
   Where $r_m = 10.67 \frac{L_m}{C_m^{1.852} D_m^{4.87}}$.
2. Form Schur complement matrix $\mathbf{S} \in \mathbb{R}^{N \times N}$:
   $$\mathbf{S} = \mathbf{A}_{12}^T \mathbf{A}_{11}^{-1} \mathbf{A}_{12} + \text{diag}\left(\frac{\partial Q_{\text{leak}, j}}{\partial H_j}\right)$$
3. Compute nodal head update $\mathbf{dH}$:
   $$\mathbf{S} \cdot \mathbf{dH} = \mathbf{A}_{12}^T \left(\mathbf{Q}^{(k)} - \mathbf{A}_{11}^{-1} \mathbf{F}_{\text{links}}\right) - \mathbf{q}(\mathbf{H}^{(k)})$$
4. Compute link flow update $\mathbf{dQ}$:
   $$\mathbf{dQ} = -\mathbf{A}_{11}^{-1} \left(\mathbf{F}_{\text{links}} + \mathbf{A}_{12} \mathbf{dH}\right)$$
5. Update state vectors with relaxation parameter $\alpha \in [0.7, 1.0]$:
   $$\mathbf{H}^{(k+1)} = \mathbf{H}^{(k)} + \alpha \mathbf{dH}$$
   $$\mathbf{Q}^{(k+1)} = \mathbf{Q}^{(k)} + \alpha \mathbf{dQ}$$

Convergence is achieved when $||\mathbf{dQ}||_\infty < 10^{-4}\text{ m}^3/\text{s}$ and $||\mathbf{dH}||_\infty < 10^{-4}\text{ m}$.

---

### 2. Pressure-Dependent Demand (PDD) & Leak Modeling

#### 2.1 Wagner-Fox-Skeeti PDD Function
Under normal operating pressures ($P_j \ge P_{\text{req}}$), consumer nodes receive 100% of their base demand. When pressure drops below required minimums due to trunk bursts:
$$q_j(P_j) = \begin{cases} 
0 & P_j \le P_{\text{min}} \\
D_j \cdot \left(\frac{P_j - P_{\text{min}}}{P_{\text{req}} - P_{\text{min}}}\right)^\beta & P_{\text{min}} < P_j < P_{\text{req}} \\
D_j & P_j \ge P_{\text{req}}
\end{cases}$$
Where $P_{\text{min}} = 0.5\text{ bar}$, $P_{\text{req}} = 1.5\text{ bar}$, and $\beta = 0.5$.

#### 2.2 Torricelli Orifice Leak Dynamics
Active pipeline fissures discharge fluid into the surrounding soil according to Torricelli's orifice equation:
$$Q_{\text{leak}} = C_d \cdot A_{\text{orifice}} \cdot \sqrt{2g \cdot \frac{P_j - P_{\text{ambient}}}{\rho g}}$$
For gauge pressure in meters of head ($h_p = H_j - Z_j$):
$$Q_{\text{leak}} = C_d \cdot A_{\text{orifice}} \cdot \sqrt{2g \cdot h_p}$$

---

### 3. Extended-Period Simulation (EPS) Diurnal Demand Tracking

Extended period simulations execute across a 24-hour operational cycle with 1-hour hydraulic intervals. Municipal consumption modulates baseline demand via diurnal coefficients:

```
Demand Multiplier
 1.6 |               *** (08:00 Peak: 1.45x)
 1.4 |             *     *                       *** (18:00 Peak: 1.40x)
 1.2 |            *       *                     *   *
 1.0 |-----------*---------*-------*-----------*-----*--------- Baseline (1.0x)
 0.8 |          *           *     * *         *       *
 0.6 | *       *             *   *   *       *         *
 0.4 |  * *** *               ***     * *** *           ***
     +--------------------------------------------------------
       00  02  04  06  08  10  12  14  16  18  20  22  24  Hour
```

At each timestep $t_k$, the engine:
1. Scales junction demands: $D_j(t_k) = D_{j, \text{base}} \times \text{multiplier}(t_k)$.
2. Updates dynamic tank water levels:
   $$h_{\text{tank}}(t_k + \Delta t) = h_{\text{tank}}(t_k) + \frac{Q_{\text{net, tank}}(t_k)}{A_{\text{tank}}} \Delta t$$
3. Re-solves non-linear network equations to convergence.
4. Records timestamped nodal pressures, link velocities, and headlosses.

