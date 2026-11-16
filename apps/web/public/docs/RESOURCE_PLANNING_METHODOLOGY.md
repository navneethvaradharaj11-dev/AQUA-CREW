# AQUA CREW — RESOURCE PLANNING METHODOLOGY
## Virtual Rover Fleet Suitability, Thermal Safety & Operational Scheduling (Task 12 - Phase 7)

```
========================================================================================
AQUA CREW PLATFORM — RESOURCE PLANNING & FLEET SUITABILITY SPECIFICATION
Milestone: TASK 12 — Unified Operational Intelligence & Decision Support Platform
Engine: operational_resource_planning_service.py
Safety Gates: Battery >= 20.0%, Motor Temperature < 65.0°C
Hardware Policy: Real-world physical actuators permanently disabled.
========================================================================================
```

---

## 1. Fleet Resource Planning Overview

Autonomous subterranean pipe inspection requires deploying specialized crawler rovers into pressurized or dewatered conduits. Deploying an unready or battery-depleted robot into an underground distribution main risks **subterranean stranding**, loss of telemetry contact, and severe operational blockage.

`OperationalResourcePlanningService` evaluates every virtual rover in the AQUA CREW fleet against candidate inspection targets, calculating deterministic suitability scores while strictly enforcing hard physical safety interlocks.

---

## 2. Hard Robotic Safety Interlocks

Before any suitability score is computed, candidate rovers must pass three binary safety gates:

```mermaid
flowchart TD
    R[Candidate Virtual Rover] --> G1{Battery Reserve >= 20.0%?}
    G1 -- No --> RJ1["INELIGIBLE\n(BATTERY_INSUFFICIENT)"]
    G1 -- Yes --> G2{Motor Temp < 65.0°C?}
    G2 -- No --> RJ2["INELIGIBLE\n(MOTOR_OVERHEATED)"]
    G2 -- Yes --> G3{Operating State in [IDLE, STANDBY]?}
    G3 -- No --> RJ3["INELIGIBLE\n(ROVER_UNAVAILABLE)"]
    G3 -- Yes --> ELIG["ELIGIBLE FOR DISPATCH\n(Compute Suitability Score)"]
```

1. **Battery Reserve Gate ($\text{SoC} \ge 20.0\%$)**:
   - Subterranean locomotion and active payload acoustic hydrophones consume significant battery power (~$0.8\%$ per 100 meters traversed).
   - If a rover's state of charge falls below $20.0\%$, the engine marks it ineligible with the error:
     `"BATTERY_INSUFFICIENT: Current charge X% is below safety limit (20.0%)"`.
2. **Thermal Safety Gate ($T_{\text{motor}} < 65.0^\circ\text{C}$)**:
   - High mechanical resistance in silted or tuberculated conduits causes motor thermal rise.
   - Operating above $65.0^\circ\text{C}$ risks motor coil breakdown. Any rover with $T_{\text{motor}} \ge 65.0^\circ\text{C}$ is rejected with:
     `"MOTOR_OVERHEATED: Motor temperature X°C exceeds threshold (65.0°C)"`.
3. **Availability Gate**:
   - Rovers currently in `BUSY`, `IN_MISSION`, `MAINTENANCE`, or `OFFLINE` states cannot receive concurrent assignments.

---

## 3. Mathematical Formulation of Rover Suitability

For all eligible rovers, the multi-factor suitability score $S_{\text{rover}} \in [0.0, 100.0]$ is computed as:

$$S_{\text{rover}} = 0.40 \cdot B + 0.35 \cdot F_{\text{dist}} + 0.15 \cdot F_{\text{thermal}} + 0.10 \cdot F_{\text{ready}}$$

Where:
- $B \in [20.0, 100.0]$: Current battery state of charge.
- $F_{\text{dist}} = \max\left(0.0, \; 100.0 - \frac{d}{50.0}\right)$: Geodesic proximity factor ($d$ = distance in meters from rover base station to target segment). 100 points at 0m, decaying to 0 points at 5,000m.
- $F_{\text{thermal}} = \max\left(0.0, \; \frac{65.0 - T_{\text{motor}}}{65.0 - 20.0} \cdot 100.0\right)$: Thermal headroom factor (100 points at nominal $20^\circ\text{C}$, decaying to 0 points at $65^\circ\text{C}$).
- $F_{\text{ready}} = 100.0$: Baseline diagnostic readiness bonus.

---

## 4. Resource Availability & Inventory Handling

In strict compliance with the Project Development Rules: **Do not invent technicians, crews, equipment or inventory records.**

Where physical workforce, maintenance crew rosters, or spare parts inventory data do not exist, the platform explicitly marks the features as unavailable:

```json
{
  "workforce_status": "NOT_AVAILABLE (Software Simulation Mode)",
  "inventory_status": "NOT_AVAILABLE (Software Simulation Mode)"
}
```

The system presents only verified, running virtual rover fleet assets and their live telemetric parameters.

---

## 5. Non-Automated Dispatch Protocol

Even when a rover achieves a suitability score of $95.0+$ and is classified as `READY_FOR_DISPATCH`, the platform **never executes an automatic launch**. All mission creation is held in `PENDING_APPROVAL` status, requiring an explicit operator sign-off via the Task 08 / Task 12 approval workflow.

