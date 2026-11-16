# AQUA CREW — Autonomous Mission Planning & Intelligent Rover Dispatch Architecture
**Task 08 — Architecture, Decision Systems, Geospatial Routing & Safety Specifications**

## 1. System Vision & Objective

AQUA CREW Task 08 establishes the autonomous decision-making and operational dispatch bridge between the **AI Leak Detection Subsystem (Task 07)** and the **Virtual Autonomous Rover Fleet (Tasks 05 & 06)**.

The system ingests AI-classified leak detections, evaluates multi-criteria mission priorities, calculates shortest-path trajectories across connected metropolitan pipeline graphs, scores eligible virtual rovers based on battery and sensor compatibility, generates explainable mission recommendations, and enforces strict **Human-in-the-Loop** operator verification prior to dispatching inspection missions.

> [!IMPORTANT]
> **SOFTWARE-ONLY SIMULATION PROVENANCE**: All rover trajectories, battery models, dispatch commands, and mission progress metrics are simulated in software. No physical hardware actuation (motors, valves, lasers, or mechanical repairs) is executed. Human operator approval is strictly enforced.

---

## 2. End-to-End Mission Planning & Dispatch Architecture

```
                  [AI Leak Detection Engine]
                   (Task 07: AiDetectionModel)
                              │
                              ▼
               ┌──────────────────────────────┐
               │    Mission Priority Engine   │
               │   (0–100 Explainable Score)  │
               └──────────────┬───────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
   ┌───────────────────────┐     ┌───────────────────────┐
   │ Pipeline Graph Router │     │ Rover Suitability     │
   │ (Dijkstra Traversal)  │     │ (Battery & Sensor)    │
   └───────────┬───────────┘     └───────────┬───────────┘
               │                             │
               └──────────────┬──────────────┘
                              ▼
               ┌──────────────────────────────┐
               │  Mission Recommendation Gen  │
               │  (Route, Rover, Energy, Est) │
               └──────────────┬───────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │ Human Operator Approval Gate │
               │  [Approve] / [Reject Reason] │
               └──────────────┬───────────────┘
                              │ (Approved)
                              ▼
               ┌──────────────────────────────┐
               │  Mission Service Assignment  │
               │ (MissionModel & Rover State) │
               └──────────────┬───────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │ Backend Simulation Engine    │
               │ (Kinematics, Progress, WS)   │
               └──────────────────────────────┘
```

---

## 3. Core Engine Components

### 3.1 Mission Priority Engine (`mission_priority_service.py`)
Calculates an explainable priority score ($0 \le P \le 100$) evaluating:
1. **Risk Severity**: CRITICAL (+35), HIGH (+25), MODERATE (+15), LOW (+5)
2. **AI Classification**: HIGH_LEAK_PROBABILITY (+25), MEDIUM (+18), LOW (+8)
3. **Estimated Water Loss**: $\ge 2,000 \text{ L/h}$ (+20), $\ge 1,000 \text{ L/h}$ (+15), $\ge 500 \text{ L/h}$ (+10), $>0$ (+5)
4. **Pipeline Criticality**: Primary Trunk Main (+12), Secondary Feeder (+8), Distribution (+4)
5. **Operating Pressure Deviation**: $<-1.0 \text{ bar}$ (+8), $<-0.5 \text{ bar}$ (+5)
6. **Localization Uncertainty Adjustment**: If uncertainty radius is wide ($>30\text{ m}$), flag for broad exploratory survey; if tight ($<15\text{ m}$), boost confidence factor.

**Priority Categories**:
- `CRITICAL`: 90–100
- `HIGH`: 70–89
- `MEDIUM`: 40–69
- `LOW`: 0–39

### 3.2 Pipeline Network Routing Engine (`pipeline_routing_service.py`)
- Models the underground pipeline network as an undirected topological graph $G = (V, E)$.
- **Vertices ($V$)**: Junctions, valves, pump stations, and pipe segment terminals.
- **Edges ($E$)**: Pipeline segments with attributes (length in meters, material, category, diameter).
- **Pathfinding**: Implements Dijkstra's algorithm to compute the shortest connected path along real pipeline geometry between the rover's initial position and the target leak coordinates.
- **Constraints**: Rovers cannot jump between disconnected pipelines; routing returns an explicit path-failure if no topological connection exists.

### 3.3 Rover Suitability & Energy Feasibility Engine (`rover_selection_service.py`)
- **State Eligibility**: Only rovers in `IDLE` state are eligible. Rovers in `OFFLINE`, `ERROR`, `EMERGENCY_STOP`, `RETURNING`, `CHARGING`, or actively executing another mission are excluded.
- **Energy Consumption Model**:
  \[
  E_{\text{total}} = E_{\text{travel\_out}} + E_{\text{inspect}} + E_{\text{return}}
  \]
  where:
  - $E_{\text{travel\_out}} = d_{\text{out\_km}} \times 1.8\% \text{ battery/km}$
  - $E_{\text{inspect}} = t_{\text{inspect\_hr}} \times 4.0\% \text{ battery/hr}$
  - $E_{\text{return}} = d_{\text{return\_km}} \times 1.8\% \text{ battery/km}$
  - $\text{Safety Reserve} = 20.0\%$ (Configurable parameter)
- A rover is only recommended if:
  \[
  \text{Current Battery} - E_{\text{total}} \ge \text{Safety Reserve}
  \]
- **Composite Suitability Score (0–100)** incorporates proximity, battery surplus, sensor payload compatibility, and motor thermal status.

### 3.4 Mission Recommendation & Approval Lifecycle
1. `PENDING_APPROVAL`: Recommendation created with optimal rover and planned route.
2. `APPROVED`: Human operator confirms dispatch; triggers formal mission creation in `MissionRepository` and transitions rover to `MOVING`/`INSPECTING`.
3. `REJECTED`: Operator rejects with documented reason; recommendation is closed without rover actuation.
4. `CANCELLED`: System or operator cancels prior to assignment.

---

## 4. Safety & Governance Safeguards
1. **Zero Autonomous Actuation**: Autonomous engines only formulate recommendations; physical dispatch requires human operator authorization.
2. **Duplicate Guard**: Only one active mission may target a given leak detection ID or pipeline segment.
3. **Single Mission Invariance**: A rover can only execute one active mission at a time.
4. **Thermal and Battery Interlocks**: Simulation engine halts or returns rovers exceeding $58^\circ\text{C}$ motor temperature or dropping below $12\%$ battery.
5. **Simulation Provenance**: Every record, recommendation, route, and event carries `is_simulated: true` and `source: "VIRTUAL_SIMULATION_ENGINE"`.

