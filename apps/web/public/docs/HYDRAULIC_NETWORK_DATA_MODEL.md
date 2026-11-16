# AQUA CREW — Hydraulic Network Data Model Specification
## Physical Topology & Component Data Reference (Task 10)

---

### Executive Overview

The **AQUA CREW Hydraulic Network Data Model** provides the relational and graph schema required to transform GIS pipeline geometry into an engineering-grade water distribution network (WDN). It defines discrete hydraulic elements, boundary conditions, physical parameters, and operational states compatible with EPANET 2.2 and WNTR standards.

---

### 1. Database Entity-Relationship Architecture

```
+-------------------------------------------------------------+
|                   hydraulic_networks                        |
+-------------------------------------------------------------+
|  id (PK, String)                                            |
|  name (String)                                              |
|  headloss_formula (String: "H-W" | "D-W")                   |
|  flow_units (String: "LPS" | "GPM")                         |
|  demand_model (String: "PDA" | "DDA")                       |
|  is_active (Boolean)                                        |
|  is_simulated (Boolean)                                     |
+------------------------------+------------------------------+
                               | 1
                               |
            +------------------+------------------+
            | 1..*                                | 1..*
+-----------v-----------------+     +-------------v---------------+
|       hydraulic_nodes       |     |       hydraulic_links       |
+-----------------------------+     +-----------------------------+
| id (PK, String)             |     | id (PK, String)             |
| network_id (FK)             |     | network_id (FK)             |
| node_type (String)          |     | link_type (String)          |
| name (String)               |     | name (String)               |
| elevation_m (Float)         |     | start_node_id (FK)          |
| base_head_m (Float, Nullable|     | end_node_id (FK)            |
| base_demand_lps (Float)     |     | length_m (Float)            |
| emitter_coeff (Float)       |     | diameter_mm (Float)         |
| min_pressure_bar (Float)    |     | roughness (Float)           |
| nominal_pressure_bar (Float)|     | initial_status (String)     |
| initial_level_m (Float)     |     | current_status (String)     |
| min_level_m (Float)         |     | pipeline_segment_id (String)|
| max_level_m (Float)         |     | pump_power_kw (Float)       |
| diameter_m (Float)          |     | valve_type (String)         |
| longitude (Float)           |     | valve_setting (Float)       |
| latitude (Float)            |     | coordinates_json (Text)     |
+-----------------------------+     +-----------------------------+
```

---

### 2. Node Classification & Parameters

#### 2.1 Reservoirs (`node_type = "RESERVOIR"`)
Infinite-source boundary nodes supplying hydraulic potential energy:
- `base_head_m`: Total hydraulic grade line (HGL) at the reservoir water surface ($Z + P/\gamma_w$).
- Example: `NODE-RES-01` (Northern Aqueduct Supply Reservoir, base head $= 85.0\text{ m}$, elevation $= 25.0\text{ m}$).

#### 2.2 Storage Tanks (`node_type = "TANK"`)
Variable-head volumetric buffer reservoirs with dynamic water levels:
- `elevation_m`: Base elevation of the tank bottom.
- `initial_level_m`: Initial water column height ($h_{\text{tank}}(0)$).
- `min_level_m` / `max_level_m`: Operational physical limits.
- `diameter_m`: Equivalent cylindrical tank diameter.
- Example: `NODE-TANK-01` (Industrial Park Elevated Storage Tank $T_1$, base elev $= 24.0\text{ m}$, level $= 6.5\text{ m}$, max $= 12.0\text{ m}$, diameter $= 18.0\text{ m}$).

#### 2.3 Demand Junctions (`node_type = "JUNCTION"`)
Consumer withdrawal and pipe junction nodes:
- `base_demand_lps`: Mean baseline consumption in liters per second ($L/s$).
- `demand_pattern_id`: Diurnal hourly multiplier pattern curve (24 timesteps).
- `emitter_coeff`: Pressure-dependent leakage orifice emitter coefficient.
- `min_pressure_bar`: Regulatory minimum threshold (typically $1.5\text{ bar}$). If pressure drops below this, deficit alarms trip.
- Example: `NODE-JUNC-01` (Central Grand Avenue Spine Junction, elev $= 16.5\text{ m}$, base demand $= 22.0\text{ L/s}$).

---

### 3. Link Classification & Parameters

#### 3.1 Pipelines (`link_type = "PIPE"`)
Conduits transporting pressurized water:
- `length_m`: Measured conduit length in meters.
- `diameter_mm`: Internal pipe bore in millimeters.
- `roughness`: Dimensionless Hazen-Williams roughness coefficient $C$:
  - Ductile Iron (Class 54): $C = 130$
  - Concrete Cylinder: $C = 140$
  - High-Density Polyethylene (HDPE): $C = 150$
  - Epoxy-Lined Cast Iron: $C = 140$
- `pipeline_segment_id`: Foreign link to Task 04 / Task 07 / Task 09 GIS segment (`PipelineSegmentModel`).

#### 3.2 Booster Pumps (`link_type = "PUMP"`)
In-line mechanical energy generators:
- 3-point polynomial head curve:
  $$H_{\text{pump}}(Q) = 65.0 - 0.002 \cdot Q^2$$
- `pump_speed`: Speed multiplier (1.0 = nominal, 0.0 = stopped/tripped).
- `pump_power_kw`: Electric motor rating (e.g., $45.0\text{ kW}$).
- Example: `LINK-PUMP-BOOSTER-01` on Grand Avenue Spine Trunk Line A.

#### 3.3 Pressure Reducing Valves (`link_type = "VALVE"`, `valve_type = "PRV"`)
Active control devices throttling upstream head to maintain preset downstream pressure:
- `valve_setting`: Downstream target pressure in bar (e.g., $3.5\text{ bar}$).
- Example: `LINK-VALVE-HRB-PRV` controlling water delivery to the Harbor Utility Terminal.

---

### 4. GIS Pipeline to Hydraulic Topology Cross-Reference

| GIS Segment ID | Hydraulic Link ID | Start Node | End Node | Material | Diameter | Length |
|---|---|---|---|---|---|---|
| `PIPE-SEC-4A-10` | `LINK-PIPE-TRUNK-A` | `NODE-RES-01` | `NODE-JUNC-01` | Concrete | 750 mm | 1050 m |
| `PIPE-SEC-4B-92` | `LINK-PIPE-TRUNK-B1` | `NODE-JUNC-01` | `NODE-JUNC-02` | Ductile Iron | 600 mm | 620 m |
| `PIPE-SEC-4B-92` | `LINK-PIPE-TRUNK-B2` | `NODE-JUNC-02` | `NODE-JUNC-03` | Ductile Iron | 600 mm | 540 m |
| `PIPE-IND-1A-04` | `LINK-PIPE-IND-01` | `NODE-JUNC-01` | `NODE-JUNC-04` | HDPE | 400 mm | 820 m |
| `PIPE-IND-1A-04` | `LINK-PIPE-IND-TANK` | `NODE-JUNC-04` | `NODE-TANK-01` | HDPE | 350 mm | 350 m |
| `PIPE-RES-3C-11` | `LINK-PIPE-RES-01` | `NODE-RES-01` | `NODE-JUNC-06` | Ductile Iron | 350 mm | 940 m |
| `PIPE-HRB-02-19` | `LINK-VALVE-HRB-PRV` | `NODE-JUNC-01` | `NODE-JUNC-05` | Cast Iron | 300 mm | 980 m |

