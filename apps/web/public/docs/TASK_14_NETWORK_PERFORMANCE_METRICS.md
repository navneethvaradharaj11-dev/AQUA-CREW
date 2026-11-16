# AQUA CREW — TASK 14: Network Performance Evaluation Metrics

**Document ID**: `AC-OPT-14-02`  
**Classification**: Performance Engineering Standard & Metric Taxonomy  
**Status**: APPROVED  
**Author**: Principal Hydraulic Systems Engineer & Scientific Computing Group  
**Target Release**: AQUA CREW Core Platform v0.1.0 (Task 14)

---

## 1. Metric Taxonomy & Formulation

The `NetworkPerformanceService` evaluates water distribution networks across five distinct physical and operational dimensions:

$$\mathbf{M} = \{\mathcal{P}, \mathcal{H}, \mathcal{W}, \mathcal{E}, \mathcal{R}\}$$

Where:
- $\mathcal{P}$: Pressure Metrics
- $\mathcal{H}$: Hydraulic Flow & Capacity Metrics
- $\mathcal{W}$: Water-Loss & Leakage Metrics
- $\mathcal{E}$: Energy Consumption & Operational Cost Metrics
- $\mathcal{R}$: Reliability, Continuity & Constraint Compliance Metrics

Every metric is encapsulated within a structured `MetricValue` preserving:
1. `value`: Numerical scalar (or `None` if data is unconfigured).
2. `unit`: Explicit engineering unit (e.g. `bar`, `m3/day`, `kWh`, `USD`).
3. `is_available`: Boolean availability flag.
4. `source`: Provenance tag (`"VIRTUAL_SIMULATION_ENGINE"`).

> [!IMPORTANT]
> **Zero-Substitution Rule**: Unavailable metrics (such as operational cost when no electricity tariff is defined) are explicitly represented as `is_available = False` and `value = None`. The engine strictly forbids substituting unconfigured inputs with zero.

---

## 2. Category Specifications

### 2.1 Pressure Metrics ($\mathcal{P}$)
- **Minimum Pressure** ($P_{min}$): Lowest nodal pressure observed across all active demand junctions ($P_j = \min_{j \in \mathcal{J}} P_j$).
- **Maximum Pressure** ($P_{max}$): Highest junction pressure ($P_{max} = \max_{j \in \mathcal{J}} P_j$).
- **Average Pressure** ($P_{avg}$): Arithmetic mean junction pressure ($\frac{1}{N_{\mathcal{J}}} \sum_{j \in \mathcal{J}} P_j$).
- **Pressure Deficit Count**: Count of demand junctions failing regulatory minimum service pressure ($P_j < 1.5$ bar).
- **Pressure Excess Count**: Count of junctions exceeding maximum structural threshold ($P_j > 5.5$ bar).

### 2.2 Hydraulic Flow & Capacity Metrics ($\mathcal{H}$)
- **Requested Demand** ($\sum Q_{req}$): Total consumer demand requested across all municipal nodes.
- **Delivered Demand** ($\sum Q_{deliv}$): Actual volume delivered under Pressure-Dependent Demand (PDD) simulation.
- **Demand Satisfaction Ratio** ($S_D = \frac{\sum Q_{deliv}}{\sum Q_{req}}$): Fraction of requested demand fulfilled.
- **Max & Average Pipe Velocity** ($v = \frac{Q}{A}$): Velocity profile across all links. Maximum velocity constraint: $v \le 2.5$ m/s.
- **Capacity Utilization** ($U_{cap} = \frac{v_{max}}{2.5\text{ m/s}} \times 100\%$): Network capacity stress index.

### 2.3 Water-Loss Metrics ($\mathcal{W}$)
- **Total Simulated Leakage Rate** ($Q_{leak} = \sum_{j} q_{leak,j}$ in L/s).
- **Daily Leakage Volume** ($V_{leak,daily} = Q_{leak} \times 86.4\text{ m}^3/\text{day}$).
- **Leakage-to-Supplied Ratio** ($\frac{Q_{leak}}{Q_{deliv} + Q_{leak}} \times 100\%$).
- **Spatial Breakdown**: Leakage aggregated by GIS pipeline segment and hydraulic pressure zone.

### 2.4 Energy Metrics ($\mathcal{E}$)
- **Pump Electrical Energy** ($E_{elec} = \sum_{p} P_{p,rated} \cdot s_p^3 \cdot \Delta t$ in kWh): Affinity-scaled power consumption.
- **Pump Hydraulic Energy** ($E_{hyd} = \sum_{p} 9.81 \cdot Q_p \cdot H_p \cdot \Delta t$ in kWh).
- **Wire-to-Water Efficiency** ($\eta = \frac{E_{hyd}}{E_{elec}} \times 100\%$).
- **Energy Cost** ($C_{energy} = E_{elec} \times Tariff$): Calculated only when a verified tariff ($\$/\text{kWh}$) is provided.

### 2.5 Reliability Metrics ($\mathcal{R}$)
- **Hydraulic Convergence**: Boolean flag indicating numerical solver solution stability.
- **Mass Continuity Error** ($|\sum Q_{in} - \sum Q_{out}|$ in L/s).
- **Critical Violation Count**: Aggregate count of active pressure, velocity, and equipment violations.

