# AQUA CREW — HYDRAULIC UNITS, ASSUMPTIONS & ENGINEERING LIMITATIONS
**Task 10.5 — Technical Reference Manual: Units, Conversions, Physical Constants & Model Bounds**

---

## 1. System of Units & Conversion Standards

AQUA CREW adopts the **International System of Units (SI)** as its primary scientific computation standard, while providing calibrated conversions to municipal utility units (bar, L/s, m³/hr, psi) in all user-facing dashboards and REST contracts.

### 1.1 Physical Quantities & Dimensions

| Hydraulic Variable | Physical Dimension | Internal Solver Base Unit | Dashboard Display Unit | Mathematical Conversion |
| :--- | :--- | :--- | :--- | :--- |
| **Nodal Gauge Pressure** | $M L^{-1} T^{-2}$ | $\text{m}$ (water head) / $\text{Pa}$ | $\text{bar}$ | $1\text{ bar} = 10^5\text{ Pa} \approx 10.197\text{ m H}_2\text{O}$ |
| **Volumetric Flow Rate** | $L^3 T^{-1}$ | $\text{m}^3/\text{s}$ | $\text{L/s}$ | $1\text{ m}^3/\text{s} = 1000.0\text{ L/s} = 3600.0\text{ m}^3/\text{hr}$ |
| **Pipe Flow Velocity** | $L T^{-1}$ | $\text{m/s}$ | $\text{m/s}$ | $v = \frac{4 Q}{\pi D^2}$ |
| **Pipe Diameter** | $L$ | $\text{m}$ | $\text{mm}$ | $1\text{ m} = 1000.0\text{ mm}$ |
| **Pipe Length** | $L$ | $\text{m}$ | $\text{m}$ / $\text{km}$ | $1\text{ km} = 1000.0\text{ m}$ |
| **Hydraulic Head Loss** | $L$ | $\text{m}$ | $\text{m}$ / $\text{m/km}$ | $h_f = H_{\text{start}} - H_{\text{end}}$ |
| **Orifice Rupture Area**| $L^2$ | $\text{m}^2$ | $\text{cm}^2$ | $1\text{ cm}^2 = 10^{-4}\text{ m}^2 = 100.0\text{ mm}^2$ |
| **Storage Tank Volume** | $L^3$ | $\text{m}^3$ | $\text{m}^3$ / $\%$ fill | $V = \frac{\pi D^2}{4} \cdot h_{\text{level}}$ |

### 1.2 Pressure Unit Equivalencies
$$\begin{aligned}
1.0\text{ bar} &= 100.0\text{ kPa} = 100,000\text{ Pa} \\
1.0\text{ bar} &= 10.197162\text{ m of head } (\text{at } 20^\circ\text{C}) \\
1.0\text{ bar} &= 14.5038\text{ psi} \\
1.0\text{ m of head} &= 0.0980665\text{ bar} = 9.80665\text{ kPa} = 1.4223\text{ psi}
\end{aligned}$$

---

## 2. Fundamental Physical Constants & Fluid Properties

All hydraulic equations assume clean, potable municipal water at standard environmental temperature and pressure:

| Parameter | Symbol | Reference Value | Units | Justification / Source |
| :--- | :--- | :--- | :--- | :--- |
| **Fluid Temperature** | $T$ | $20.0$ | $^\circ\text{C}$ | Nominal municipal drinking water temperature |
| **Fluid Density** | $\rho$ | $1000.0$ | $\text{kg/m}^3$ | Standard freshwater density at $20^\circ\text{C}$ |
| **Gravitational Acceleration** | $g$ | $9.81$ | $\text{m/s}^2$ | Standard surface gravity datum |
| **Kinematic Viscosity** | $\nu$ | $1.004 \times 10^{-6}$ | $\text{m}^2/\text{s}$ | Water kinematic viscosity at $20^\circ\text{C}$ |
| **Bulk Modulus of Elasticity** | $K_w$ | $2.15 \times 10^9$ | $\text{Pa}$ | Incompressible assumption valid for steady/quasi-steady analysis |

---

## 3. Engineering Assumptions & Limitations

### 3.1 Flow Conditions & Friction Formulation
1. **Steady / Extended-Period Simulation (EPS)**: Hydraulic states represent quasi-steady snapshots (hydraulic timesteps: $60\text{ minutes}$). Transient water hammer, cavitation shockwaves, and acoustic wave propagation are handled in Task 07 signal processing rather than macroscopic network gradient solvers.
2. **Hazen-Williams Validity Bounds**:
   - The Hazen-Williams formula is applicable strictly to water at normal temperatures ($5^\circ\text{C} - 25^\circ\text{C}$) under turbulent flow regimes ($\text{Re} > 4000$).
   - It is not recommended for laminar flows or non-Newtonian slurries.
3. **Pipe Roughness Coefficients ($C$)**:
   - New Ductile Iron (Cement-lined): $C = 140$
   - Clean Welded Steel: $C = 130$
   - Unlined Cast Iron (Aged): $C = 100 - 110$
   - Polyvinyl Chloride (PVC / HDPE): $C = 150$

### 3.2 Leakage & Orifice Discharge Bounds
1. **Torricelli Efflux Coefficient ($C_d$)**:
   - Calibrated default: $C_d = 0.75$.
   - Valid range for sub-surface pipeline ruptures: $0.60 \le C_d \le 0.85$.
   - $C_d$ accounts for vena contracta flow contraction and local viscous shear around jagged pipe edges.
2. **Soil Backpressure & Immersion**:
   - The standard model assumes discharge into atmospheric or unsaturated permeable soil ($\Delta P = P_{\text{internal}} - P_{\text{atm}}$).
   - In fully waterlogged, saturated clay backfill, effective discharge may experience backpressure attenuation.

### 3.3 Pressure Thresholds & Operational Limits
- **Nominal Municipal Pressure**: $2.5\text{ bar} \le P \le 5.0\text{ bar}$ ($25\text{ m} - 51\text{ m}$ head).
- **Minimum Service Pressure (Tap Deficit)**: $P_{\text{req}} = 1.5\text{ bar}$ ($15.3\text{ m}$ head). Nodes dropping below $1.5\text{ bar}$ trigger `DEFICIT` alarms.
- **Zero Tap Delivery Threshold**: $P_{\min} = 0.5\text{ bar}$ ($5.1\text{ m}$ head). Below this pressure, Wagner PDD terminates consumer withdrawal ($d = 0$).
- **Maximum Pressure (Overpressure Threshold)**: $P_{\max} = 6.0\text{ bar}$ ($61.2\text{ m}$ head). Nodes exceeding this trigger `OVERPRESSURE` warnings to prevent joint blowouts.
- **Velocity Erosion & Water Hammer Guardrail**: Maximum permissible pipe flow velocity is $2.0\text{ m/s}$. Velocities above $2.0\text{ m/s}$ trigger `is_high_risk: true` in scenario comparison matrices.

---

## 4. Diurnal Demand Pattern Multipliers

Municipal water consumption exhibits characteristic human circadian patterns. The certified 24-hour baseline diurnal pattern multiplier applied in AQUA CREW is:

```
Hour (24h)   Multiplier   Operational Description
00:00        0.65         Nighttime minimum base load
01:00        0.55         Minimum nocturnal consumption
02:00        0.50         Municipal diurnal low (optimal leak acoustic window)
03:00        0.55         Nighttime baseline
04:00        0.70         Early riser industrial startup
05:00        0.95         Morning transition
06:00        1.25         Morning peak residential surge
07:00        1.45         Morning peak maximum (breakfast, showers)
08:00        1.35         Sustained morning high
09:00        1.15         Commercial sector transition
10:00        1.05         Nominal business hours
11:00        1.00         Nominal base level (1.00x)
12:00        1.10         Lunch surge
13:00        1.15         Afternoon commercial demand
14:00        1.05         Midday plateau
15:00        1.00         Nominal base level
16:00        1.10         Late afternoon transition
17:00        1.25         Evening return from work
18:00        1.40         Evening residential peak (cooking, washing)
19:00        1.35         Sustained evening peak
20:00        1.20         Evening relaxation
21:00        1.00         Late evening tapering
22:00        0.85         Night transition
23:00        0.70         Night transition
```

