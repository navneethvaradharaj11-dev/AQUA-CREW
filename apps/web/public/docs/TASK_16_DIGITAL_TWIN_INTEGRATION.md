# AQUA CREW — TASK 16 DIGITAL TWIN INTEGRATION
## Hydraulic Perturbation Simulation, Pressure Restoration & Energy Conservation

---

## 1. Digital Twin Architecture & Simulation Mechanics

The Digital Twin Repair Simulator (`DigitalTwinRepairSimulator`) links the physical pipe assessment directly to the platform's WNTR/EPANET hydraulic simulation engine (established in Tasks 10–10.6). Rather than evaluating repairs in isolation, every proposed repair plan triggers a coupled **Pre-Repair Baseline vs Post-Repair Scenario** simulation across the municipal distribution network.

```
+----------------------------------------------------------------------------------------------------+
|                               DIGITAL TWIN SIMULATION PIPELINE                                     |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [Pipe Damage & Leak Rate]                                                                         |
|            |                                                                                       |
|            v                                                                                       |
|  +-----------------------------------+     +-----------------------------------+                   |
|  |       PRE-REPAIR SCENARIO         |     |       POST-REPAIR SCENARIO        |                   |
|  | - EPANET Pressure-Dependent Emitter |    | - Emitter Leakage Removed (0 lph) |                   |
|  | - Depressed Node Pressures (bar)  |     | - Restored Pressure Gradient (bar)|                   |
|  | - Elevated Pump Head & Energy     |     | - Optimized Pump VFD Setpoints    |                   |
|  +-----------------------------------+     +-----------------------------------+                   |
|            |                                                 |                                     |
|            +-----------------------+-------------------------+                                     |
|                                    v                                                               |
|                  +-----------------------------------+                                             |
|                  |     DELTA COMPARISON ENGINE       |                                             |
|                  | - Pressure Restoration: +0.65 bar |                                             |
|                  | - Water Loss Cut: -98.2%          |                                             |
|                  | - Energy Conserved: -12.4 kWh/day |                                             |
|                  | - Benefit Score: 87.5 / 100       |                                             |
|                  +-----------------------------------+                                             |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Mathematical Formulations & Hydraulic Metrics

### 2.1 Pressure Restoration Formulation ($\Delta P$)

Prior to repair, water leaking under pressure acts as an uncontrolled pressure-dependent emitter. In EPANET/WNTR, emitter outflow is governed by the orifice equation:

$$q_{\text{emitter}} = C_{\text{emitter}} \cdot p^\gamma$$

Where $\gamma \approx 0.5$ for turbulent orifice flow through pipe cracks. This artificial discharge induces a localized hydraulic drawdown, depressing node service pressure.

Post-repair simulation sets the defect emitter coefficient to zero ($C_{\text{emitter}} = 0$). The resulting pressure restoration ($\Delta P$) is measured in bars at adjacent junction nodes:

$$\Delta P = P_{\text{post}} - P_{\text{pre}} \quad (\text{bar})$$

In typical municipal distribution sectors (e.g. EPANET Net1 baseline):
$$P_{\text{pre}} \approx 3.75 \text{ bar} \quad \longrightarrow \quad P_{\text{post}} \approx 4.25 \text{ bar} \quad (\Delta P = +0.50 \text{ bar})$$

### 2.2 Leakage Reduction Metric ($R_{\text{leak}}$)

Daily volumetric water loss ($V_{\text{leak}}$) is converted from liters per hour ($Q_{\text{leak, lph}}$) into cubic meters per day:

$$V_{\text{pre, segment}} = \frac{Q_{\text{pre, lph}} \times 24.0}{1000.0} \quad (\text{m}^3/\text{day})$$

Following standard mechanical clamp or spool replacement, residual segment leakage drops by approximately $98\%$:

$$V_{\text{post, segment}} = V_{\text{pre, segment}} \times 0.02 \quad (\text{m}^3/\text{day})$$

Total network leakage accounting for nominal background leakage ($V_{\text{bg}} = 0.5\text{ m}^3/\text{day}$) yields:

$$V_{\text{pre, net}} = V_{\text{bg}} + V_{\text{pre, segment}}$$
$$V_{\text{post, net}} = V_{\text{bg}} + V_{\text{post, segment}}$$

The percentage leakage reduction is:

$$R_{\text{leak}} = \frac{V_{\text{pre, net}} - V_{\text{post, net}}}{V_{\text{pre, net}}} \times 100\% \approx 92\% - 98\%$$

### 2.3 Pump Energy Savings ($\Delta E_{\text{pump}}$)

Uncontrolled leakage forces distribution pump stations to run at elevated speeds or higher duty cycles to maintain target pressure at peripheral demand nodes. Pump hydraulic power ($W_{\text{pump}}$) in kilowatts is given by:

$$W_{\text{pump}} = \frac{\rho \cdot g \cdot Q_{\text{pump}} \cdot H_{\text{pump}}}{1000 \cdot \eta_{\text{pump}}}$$

Where:
- $\rho = 1000 \text{ kg/m}^3$ (water density).
- $g = 9.81 \text{ m/s}^2$ (gravitational acceleration).
- $Q_{\text{pump}}$ is total system flow ($\text{m}^3/\text{s}$).
- $H_{\text{pump}}$ is dynamic pump head ($\text{m}$).
- $\eta_{\text{pump}}$ is wire-to-water efficiency ($\sim 75\%$).

Eliminating leakage reduces both $Q_{\text{pump}}$ and required head $H_{\text{pump}}$. Daily energy consumption drops:

$$\Delta E_{\text{pump}} = E_{\text{post}} - E_{\text{pre}} \quad (\text{kWh/day})$$

Because $E_{\text{post}} < E_{\text{pre}}$, $\Delta E_{\text{pump}}$ is negative, indicating energy savings ($\approx -10.0 \text{ to } -35.0 \text{ kWh/day}$).

### 2.4 Demand Satisfaction Index ($DSI$)

The simulation validates that repair operations preserve consumer delivery pressure across all downstream nodes:

$$DSI = \frac{\sum_{i=1}^{N_{\text{nodes}}} \min\left(1.0, \; \frac{P_i}{P_{\text{req}}}\right)}{N_{\text{nodes}}} \times 100\%$$

Where $P_{\text{req}} = 20.0\text{ PSI} \; (1.4\text{ bar})$ is the mandatory minimum municipal service pressure. Post-repair $DSI$ is maintained at $100.0\%$.

### 2.5 Hydraulic Benefit Score ($B_{\text{hydraulic}} \in [0, 100]$)

The overall digital twin benefit score balances water conservation, pressure recovery, and energy efficiency:

$$B_{\text{hydraulic}} = 0.50 \cdot R_{\text{leak}} + 0.30 \cdot \min\left(100.0, \; \frac{\Delta P}{1.0} \times 100\right) + 0.20 \cdot \min\left(100.0, \; \frac{|\Delta E_{\text{pump}}|}{20.0} \times 100\right)$$

---

## 3. Digital Twin Scenario Association

Every repair plan generated in Task 16 is explicitly tied to a registered digital twin scenario record:
- `scenario_id`: Unique identifier (e.g. `SCEN-REPAIR-PIPE-SEC-01-XXXX`).
- `baseline_scenario_id`: Foreign key to pre-repair baseline state.
- `hydraulic_solver`: `WNTR_EPANET_2_2` hydraulic simulation kernel.
- `pre_repair_leakage_m3`: Pre-repair daily water loss volume.
- `post_repair_leakage_m3`: Post-repair projected daily water loss volume.
- `pressure_restoration_bar`: Localized hydraulic pressure uplift.
- `pump_energy_savings_kwh_day`: Daily electrical energy conserved.
- `is_simulated`: `True` (Mandatory simulation flag).

