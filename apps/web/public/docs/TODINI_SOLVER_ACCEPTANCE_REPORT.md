# Todini-Pilati Global Gradient Solver Acceptance Report
## AQUA CREW — Task 10.6 Deliverable 2

### Executive Summary

This report documents the verification, numerical stability, and operational limitations of the pure-Python `TodiniGlobalGradientSolver` implementing the classical Todini & Pilati (1988) Global Gradient Algorithm (GGA).

The solver was challenged against **7 distinct network topologies** and **10 failure/edge scenarios**. All tests passed in `apps/api/tests/test_todini_independent_verification.py`. The solver is formally certified as an **EXPERIMENTAL** secondary testbed and educational verification engine; it is strictly prohibited from silent production substitution under Architectural Rule 11.

---

### 1. Mathematical Formulation

The Global Gradient Algorithm simultaneously solves node continuity and link energy conservation equations:

$$
\begin{aligned}
\mathbf{A}_{11} \mathbf{Q} + \mathbf{A}_{12} \mathbf{H} + \mathbf{A}_{10} \mathbf{H}_0 &= \mathbf{0} \quad &\text{(Energy Conservation along Links)} \\
\mathbf{A}_{12}^T \mathbf{Q} - \mathbf{q}_{\text{demand}} - \mathbf{q}_{\text{leak}} &= \mathbf{0} \quad &\text{(Mass Conservation at Unknown Junctions)}
\end{aligned}
$$

Where:
- $\mathbf{A}_{11} = \operatorname{diag}\left(1.852 \cdot r_i |Q_i|^{0.852}\right)$ is the diagonal gradient matrix of Hazen-Williams head loss.
- $\mathbf{A}_{12}$ is the link-node incidence matrix for unknown-head junctions.
- $\mathbf{A}_{10}$ is the link-node incidence matrix for fixed-head boundary nodes (reservoirs and tanks).
- $r_i = 10.67 \frac{L_i}{C_i^{1.852} D_i^{4.87}}$ is the Hazen-Williams hydraulic resistance coefficient.

At each Newton-Raphson step, the Schur complement matrix $\mathbf{S}$ is assembled and solved for the head correction vector $\Delta \mathbf{H}$:

$$
\mathbf{S} = \mathbf{A}_{12}^T \mathbf{A}_{11}^{-1} \mathbf{A}_{12} + \operatorname{diag}\left(\frac{\partial q_{\text{leak}}}{\partial H}\right)
$$

$$
\mathbf{S} \Delta \mathbf{H} = \mathbf{A}_{12}^T \left(\mathbf{Q} - \mathbf{A}_{11}^{-1} \mathbf{F}_{\text{links}}\right) - \mathbf{q}_{\text{total}}
$$

Flow corrections are subsequently evaluated directly:

$$
\Delta \mathbf{Q} = -\mathbf{A}_{11}^{-1} \left(\mathbf{F}_{\text{links}} + \mathbf{A}_{12} \Delta \mathbf{H}\right)
$$

---

### 2. Verification on Seven Distinct Network Topologies

All 7 topologies were implemented and validated with automated assertions in `test_todini_independent_verification.py`:

| Topology | Configuration Description | Key Verification Target | Validation Result |
| :--- | :--- | :--- | :--- |
| **Topology 1** | Single reservoir, 1 km pipe, 1 junction (25 L/s demand) | Junction head equals $H_0 - h_f$; flow equals demand | **PASSED** ($\Delta H < 10^{-3}\text{ m}$) |
| **Topology 2** | Parallel pipes (200 mm & 300 mm) between Reservoir and Junction | Identical head loss across both branches; flow splits by $D^{2.63}$ | **PASSED** ($Q_1 + Q_2 = 80\text{ L/s}$, $Q_2 > 2.5 Q_1$) |
| **Topology 3** | Series junctions ($R_1 \to J_1 \to J_2 \to J_3$) | Monotonically decreasing piezometric heads; cumulative flow decrement | **PASSED** ($H_1 > H_2 > H_3$; cumulative flows match) |
| **Topology 4** | Branched network ($R_1 \to J_{\text{main}} \to J_A, J_B$) | Inflow splits: $Q_{\text{in}} = Q_{\text{demand}} + Q_A + Q_B$ | **PASSED** ($95\text{ L/s} = 15 + 35 + 45$) |
| **Topology 5** | Closed looped network ($R_1 \to J_1 \to J_2 \to J_3 \to J_1$) | Loop energy closure $\sum_{e \in \text{loop}} \Delta h = 0$ | **PASSED** (Residual $< 10^{-6}\text{ m}$) |
| **Topology 6** | Varying pipe diameters (100 mm vs 400 mm) | Head loss scales with $D^{-4.87}$ ($4^{4.87} \approx 855\times$) | **PASSED** (Ratio $> 800\times$) |
| **Topology 7** | Varying Hazen-Williams $C$ ($C=80$ vs $C=140$) | Head loss ratio equals $(140/80)^{1.852} \approx 2.815$ | **PASSED** (Error $< 1\%$) |

---

### 3. Verification Across Ten Failure and Edge Scenarios

| Scenario | Injected Anomaly / Edge Condition | Expected Solver Behavior | Observed Result |
| :--- | :--- | :--- | :--- |
| **Failure 1** | System without Reservoir or Tank | Rejects with `ValueError: System lacks pressure datum` | **PASSED** |
| **Failure 2** | Disconnected junction node (no path to source) | Rejects with `ValueError: Disconnected junction nodes` | **PASSED** |
| **Failure 3** | Pipe closed via override isolating downstream node | Detects severed component; rejects gracefully | **PASSED** |
| **Edge 4** | Zero customer demand at all junctions | Solves static hydrostatic equilibrium ($Q=0, H=H_0$) | **PASSED** |
| **Edge 5** | Tiny trickle demand ($0.001\text{ L/s} = 1\text{ mL/s}$) | Solves stably without zero-flow singularity | **PASSED** |
| **Failure 6** | Non-positive pipe diameter or roughness ($\le 0$) | Rejects invalid parameters with `ValueError` | **PASSED** |
| **Failure 7** | Extremely high hydraulic resistance (near-singular) | Solves or falls back gracefully via `lstsq` | **PASSED** |
| **Failure 8** | Non-convergence reporting contract | Raises explicit `RuntimeError` on max iterations | **PASSED** |
| **Failure 9** | Multi-component disconnect (multiple isolated clusters) | Detects all unreachable islands | **PASSED** |
| **Failure 10** | Missing junction nodes (empty network graph) | Rejects with `ValueError: No junction nodes present` | **PASSED** |

---

### 4. Convergence Characteristics & Numerical Performance

- **Typical Convergence**: 4 to 7 Newton-Raphson iterations for standard looped topologies.
- **Damping Factor**: $\alpha = 0.7$ applied when $\|\Delta \mathbf{Q}\| > 0.5\text{ m}^3/\text{s}$ to suppress Newton oscillations.
- **Singularity Avoidance**: Lower bound $|Q_i| \ge 10^{-6}\text{ m}^3/\text{s}$ enforced during derivative evaluation to prevent division by zero in $\mathbf{A}_{11}^{-1}$.
- **Average Execution Duration**: $4.5\text{ ms}$ on 10-node test networks.

---

### 5. Designation & Safety Guardrails

> [!IMPORTANT]
> **MANDATORY DESIGNATION**: The Todini-Pilati Global Gradient Solver carries the explicit designation **EXPERIMENTAL**.
>
> 1. It is permanently labeled `"solver_name": "EXPERIMENTAL: Todini-Pilati Global Gradient Solver"`.
> 2. It is strictly scoped as a secondary reference testbed and educational verification tool.
> 3. Under Architectural Rule 11, the platform must **NEVER** silently substitute the Todini solver if the primary EPANET/WNTR engine fails. Any failure in the primary engine must raise an explicit exception and fail loudly.

