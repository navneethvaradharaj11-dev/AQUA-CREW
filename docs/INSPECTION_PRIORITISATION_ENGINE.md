# AQUA CREW — Inspection Prioritisation Engine
## Intelligent Inspection Queue, Operator Review & Autonomous Rover Handoff (Task 11)

```
========================================================================================
AQUA CREW PLATFORM — INSPECTION PRIORITISATION & FLEET DISPATCH ENGINE
Document ID: AC-T11-INSP-2026-V1
Classification: Autonomous Inspection Queue & Human-in-the-Loop Dispatch
Simulation Mode: Software-Only Virtual Infrastructure Simulation
Provenance: VIRTUAL_SIMULATION_ENGINE (is_simulated: true)
========================================================================================
```

---

## 1. Overview & Objective

In a metropolitan water network spanning hundreds of kilometers of underground conduit, autonomous inspection rovers are a finite, high-value resource. Uncoordinated or ad-hoc dispatch leads to depleted rover batteries, delayed response to critical leaks, and inefficient coverage of low-risk pipes.

The **Inspection Prioritisation Engine** dynamically prioritizes inspection targets by synthesizing:
1. Current pipeline vulnerability ($V \in [0, 100]$).
2. Structural degradation velocity ($d\text{Risk}/dt$).
3. Proximity to active geospatial incident hotspots ($d_{\min}$).
4. Asset criticality and failure consequence ($D$, network hierarchy).

Crucially, it establishes an **explainable queue** with full operator workflow states (`PENDING`, `ACKNOWLEDGED`, `DISPATCHED`, `DISMISSED`) and automates rover mission planning while strictly retaining the human authorization gate.

---

## 2. Priority Scoring Formula

The overall inspection priority score $P(s) \in [0.0, 100.0]$ is computed as:

$$P(s) = 0.40 \cdot V(s) + 0.25 \cdot W_{\text{det}}(s) + 0.20 \cdot W_{\text{prox}}(s) + 0.15 \cdot W_{\text{crit}}(s)$$

### 2.1. Component Weights & Definitions

#### 1. Vulnerability Contribution (40% Weight):
Provides baseline physical vulnerability $V(s) \in [0, 100]$.

#### 2. Deterioration Velocity Weight ($W_{\text{det}}$ — 25% Weight):
$$W_{\text{det}}(s) = \begin{cases}
92.0 & \alpha(s) \ge 0.25\text{ pts/day (rapid degradation)} \\
65.0 & 0.12 \le \alpha(s) < 0.25\text{ pts/day (moderate wear)} \\
30.0 & \alpha(s) < 0.12\text{ pts/day (nominal aging)}
\end{cases}$$

#### 3. Cluster Proximity Weight ($W_{\text{prox}}$ — 20% Weight):
$$W_{\text{prox}}(s) = \begin{cases}
95.0 & d_{\min} \le 150.0\text{ meters (within core hotspot)} \\
72.0 & 150.0\text{ m} < d_{\min} \le 400.0\text{ meters (hotspot buffer)} \\
45.0 & 400.0\text{ m} < d_{\min} \le 800.0\text{ meters} \\
20.0 & d_{\min} > 800.0\text{ meters (spatially isolated)}
\end{cases}$$

#### 4. Asset Criticality Consequence ($W_{\text{crit}}$ — 15% Weight):
$$W_{\text{crit}}(s) = \begin{cases}
90.0 & D \ge 600\text{ mm or Primary Transmission Trunk} \\
60.0 & 350\text{ mm} \le D < 600\text{ mm or Secondary Feeder} \\
40.0 & D < 350\text{ mm (Distribution Lateral)}
\end{cases}$$

---

## 3. Priority Levels & Operational Actions

The composite score $P(s)$ maps directly to standard utility priority categories:

```
+----------------------------------------------------------------------------------------------------+
| PRIORITY LEVEL       | SCORE RANGE | ACTION WINDOW | SUGGESTED OPERATIONAL ACTION                  |
+----------------------------------------------------------------------------------------------------+
| CRITICAL_IMMEDIATE   | 80.0 - 100  | < 24 Hours    | Immediate crawler rover acoustic pinpointing  |
| HIGH_PRIORITY        | 60.0 - 79.9 | < 48 Hours    | Autonomous rover sonar & visual inspection    |
| ROUTINE_SCHEDULED    | 40.0 - 59.9 | < 14 Days     | Preventive patrol & pressure sensor check     |
| MONITORING_ONLY      | < 40.0      | Continuous    | Telemetry monitoring; no physical patrol      |
+----------------------------------------------------------------------------------------------------+
```

---

## 4. Operator Review & Rover Dispatch Workflow

```
+-------------------------+
| Target Enters Queue     |  ---> State: PENDING
+-------------------------+
       |
       +---------------------------------------------+
       |                                             |
       v                                             v
[ Operator Acknowledges ]                  [ Operator Dismisses ]
       |                                             |
       v                                             v
 State: ACKNOWLEDGED                           State: DISMISSED
       |                                       (Notes & Reason Logged)
       v
[ Operator Clicks "Request Rover Inspection" ]
       |
       +---> 1. Verifies / Seeds AI Detection Record
       +---> 2. Invokes Task 08 MissionPlanningService
       +---> 3. Evaluates Rover Fleet Suitability (Battery >= 20%, Velocity)
       +---> 4. Calculates Dijkstra Pipeline Graph Waypoints
       +---> 5. Creates MissionRecommendationModel (PENDING_APPROVAL)
       +---> 6. Updates Queue Record to DISPATCHED
       |
       v
+----------------------------------------------------+
| HUMAN OPERATOR APPROVAL GATE                       |
| operator_approval_required: true                   |
| (Rover stays held until final launch authorization)|
+----------------------------------------------------+
```

---

## 5. De-Duplication & Idempotency Safeguards

To prevent queue pollution and duplicate dispatches:
1. **Segment-Level De-duplication**: The engine queries for existing `PENDING`, `ACKNOWLEDGED`, or `DISPATCHED` records for a segment before insertion. If an active record exists, its priority score and reasons are updated in-place without creating a new row.
2. **Atomic Dispatch Handshake**: Requesting an inspection links the existing `mission_recommendation_id` to prevent concurrent operators from generating multiple recommendations for the same pipeline conduit.

