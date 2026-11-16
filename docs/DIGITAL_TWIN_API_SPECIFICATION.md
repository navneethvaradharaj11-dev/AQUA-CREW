# AQUA CREW — Digital Twin REST API Specification
## Version 1 REST API Contract & Payloads (Task 10)

---

### Base Path
All endpoints are versioned and mounted under:
```
/api/v1/digital-twin
```

---

### 1. Network & Topology Endpoints

#### 1.1 `GET /api/v1/digital-twin/networks`
List all registered hydraulic water networks.
- **Response `200 OK`**:
```json
[
  {
    "id": "NET-METRO-01",
    "name": "Metro Central Water Supply & Hydraulic Distribution Network",
    "description": "Comprehensive digital twin model of metropolitan water grid...",
    "headloss_formula": "H-W",
    "flow_units": "LPS",
    "demand_model": "PDA",
    "is_active": true,
    "created_at": "2026-11-15T19:00:00Z"
  }
]
```

#### 1.2 `GET /api/v1/digital-twin/networks/{network_id}/topology`
Retrieve complete GeoJSON FeatureCollection and tabular solver node/link datasets.
- **Response `200 OK`**:
```json
{
  "network": {
    "id": "NET-METRO-01",
    "name": "Metro Central Water Supply & Hydraulic Distribution Network",
    "headloss_formula": "H-W",
    "flow_units": "LPS",
    "demand_model": "PDA"
  },
  "nodes_count": 8,
  "links_count": 8,
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "id": "NODE-RES-01",
        "geometry": { "type": "Point", "coordinates": [-74.0060, 40.7220] },
        "properties": {
          "feature_type": "NODE",
          "name": "Northern Aqueduct Supply Reservoir R1",
          "node_type": "RESERVOIR",
          "elevation_m": 25.0,
          "base_head_m": 85.0,
          "min_pressure_bar": 2.0
        }
      }
    ]
  },
  "solver_data": { ... }
}
```

---

### 2. Scenario Management Endpoints

#### 2.1 `GET /api/v1/digital-twin/scenarios`
Query parameters: `network_id` (optional, default `"NET-METRO-01"`).
- **Response `200 OK`**: Array of `SimulationScenario` objects.

#### 2.2 `POST /api/v1/digital-twin/scenarios`
Create a custom what-if scenario.
- **Request Body**:
```json
{
  "network_id": "NET-METRO-01",
  "name": "Custom High-Demand Scenario",
  "scenario_type": "HIGH_DEMAND",
  "description": "Evaluates 1.4x demand surge",
  "duration_hours": 24,
  "time_step_minutes": 60,
  "solver_mode": "PDA",
  "parameters_override": {
    "demand_multiplier": 1.40
  }
}
```
- **Response `200 OK`**:
```json
{
  "id": "SCEN-A81E92B4",
  "name": "Custom High-Demand Scenario",
  "scenario_type": "HIGH_DEMAND",
  "status": "PENDING",
  "message": "Simulation scenario created successfully."
}
```

#### 2.3 `POST /api/v1/digital-twin/scenarios/{scenario_id}/run`
Execute physical simulation for scenario.
- **Request Body**: Optional `{ overrides: { ... } }`
- **Response `200 OK`**:
```json
{
  "run_id": "RUN-9F3C182A",
  "scenario_id": "SCEN-BURST-PIPE-02",
  "execution_timestamp": "2026-11-15T19:02:40Z",
  "execution_duration_ms": 14.8,
  "converged": true,
  "total_demand_m3": 358.2,
  "total_leakage_m3": 142.5,
  "water_loss_percentage": 28.4,
  "min_pressure_bar": 1.15,
  "max_pressure_bar": 5.82,
  "pressure_deficit_nodes_count": 2,
  "summary": {
    "solver_name": "WNTR / EPANET 2.2 Pressure-Driven Simulation Engine",
    "total_supply_lps": 139.0,
    "total_demand_lps": 99.5,
    "total_leakage_lps": 39.5,
    "avg_pressure_bar": 3.74
  },
  "is_simulated": true,
  "source": "VIRTUAL_SIMULATION_ENGINE"
}
```

#### 2.4 `GET /api/v1/digital-twin/runs/{run_id}`
Returns complete serialized node pressures, link flows, head losses, and 24h diurnal time steps.

---

### 3. Comparison & What-If Endpoints

#### 3.1 `POST /api/v1/digital-twin/scenarios/compare`
- **Request Body**:
```json
{
  "baseline_scenario_id": "SCEN-BASELINE-01",
  "comparison_scenario_id": "SCEN-BURST-PIPE-02"
}
```
- **Response `200 OK`**:
```json
{
  "comparison_id": "CMP-91A2BC34",
  "baseline_scenario_id": "SCEN-BASELINE-01",
  "comparison_scenario_id": "SCEN-BURST-PIPE-02",
  "delta_total_leakage_m3": 142.5,
  "delta_water_loss_pct": 28.4,
  "delta_min_pressure_bar": -2.70,
  "affected_nodes_count": 3,
  "high_risk_links_count": 2,
  "nodes": {
    "NODE-JUNC-02": {
      "node_id": "NODE-JUNC-02",
      "name": "Metro Central Commercial Distribution Node J2",
      "baseline_pressure_bar": 4.35,
      "comparison_pressure_bar": 1.15,
      "delta_pressure_bar": -3.20,
      "pressure_drop_pct": 73.6,
      "baseline_leak_lps": 0.0,
      "comparison_leak_lps": 39.5,
      "deficit_introduced": true
    }
  },
  "links": { ... },
  "is_simulated": true,
  "source": "VIRTUAL_SIMULATION_ENGINE"
}
```

#### 3.2 `POST /api/v1/digital-twin/simulate-leak`
- **Request Body**:
```json
{
  "network_id": "NET-METRO-01",
  "target_node_id": "NODE-JUNC-04",
  "leak_area_cm2": 6.5,
  "discharge_coeff": 0.75
}
```
- **Response `200 OK`**: Returns `{ scenario: { ... }, run: { ... }, comparison: { ... } }`.

#### 3.3 `GET /api/v1/digital-twin/equipment-status`
Returns live status for active Booster Pumps, Storage Tanks, and PRVs.

#### 3.4 `POST /api/v1/digital-twin/handoff-rover-dispatch`
Packages Digital Twin hydraulic anomaly into an autonomous rover inspection recommendation.
- **Request Body**:
```json
{
  "scenario_id": "SCEN-BURST-PIPE-02",
  "target_node_id": "NODE-JUNC-02",
  "operator_id": "OP-CENTRAL-01",
  "notes": "Emergency investigation for simulated burst on Trunk Main B"
}
```
- **Response `200 OK`**:
```json
{
  "recommendation_id": "REC-DTWIN-9821A",
  "status": "RECOMMENDED",
  "scenario_id": "SCEN-BURST-PIPE-02",
  "target_node_id": "NODE-JUNC-02",
  "target_coordinates": [-74.011, 40.7115],
  "assigned_rover_id": "ROV-AQUA-01",
  "assigned_rover_name": "Proteus Mk.IV Pipeline Inspector",
  "suitability_score": 94.5,
  "inspection_urgency": "CRITICAL_BURST_INVESTIGATION",
  "operator_approval_required": true,
  "notes": "Emergency investigation for simulated burst on Trunk Main B",
  "message": "Digital Twin hydraulic anomaly successfully packaged into autonomous rover inspection mission recommendation. Awaiting human operator approval.",
  "is_simulated": true,
  "source": "VIRTUAL_SIMULATION_ENGINE"
}
```

