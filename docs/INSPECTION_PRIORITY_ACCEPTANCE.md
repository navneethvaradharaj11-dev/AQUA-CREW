# Inspection Priority & Rover Dispatch Acceptance Report (Task 11.5)

## 1. Executive Summary & Audit Scope

The **Intelligent Inspection Prioritization Service** (`inspection_priority_service.py`) coordinates the handoff between high-level geospatial infrastructure intelligence and the autonomous rover fleet dispatch engine (Tasks 05, 06, and 08).

Task 11.5 conducted a rigorous acceptance audit to verify:
1. Mathematical correctness and monotonicity of the 4-factor Inspection Priority Ranking Formula.
2. Descending queue ordering across 15 distinct operational ranking scenarios.
3. Enforcement of the **Rover Battery Safety Gate** ($\ge 20.0\%$ minimum charge).
4. Full validation of Rover Dispatch **Scenarios A through E** (Creation, Rejection, Dismissal, Dispatch, and Duplicate Prevention).
5. Strict human-in-the-loop operator approval preservation (`operator_approval_required: true`).

```
+-----------------------------------------------------------------------------------------+
|                          INSPECTION DISPATCH ACCEPTANCE MATRIX                          |
+--------------------------+-----------------------+--------------------------------------+
| Subsystem                | Task 11 Initial State | Task 11.5 Audited & Verified State   |
+--------------------------+-----------------------+--------------------------------------+
| Priority Formulation     | Heuristic             | 40% Vuln + 25% Rate + 20% Prox + 15% D|
| 15 Ranking Scenarios     | Unverified            | 15/15 Scenarios monotonic pass       |
| Rover Battery Gate       | Not checked           | Rejects rovers with battery < 20.0%  |
| Duplicate Protection     | Allowed re-dispatch   | Raises DUPLICATE_DISPATCH_REJECTED   |
| Operator Approval Gate   | Optional              | Strictly ENFORCED (status: PENDING)  |
| Hardware Actuation       | Disabled              | Disabled (is_simulated: true)        |
+--------------------------+-----------------------+--------------------------------------+
```

---

## 2. Priority Scoring Mathematical Formulation

The composite inspection priority score $P \in [0.0, 100.0]$ is computed as:

$$P = w_V \cdot V + w_R \cdot S_{\text{rate}} + w_P \cdot S_{\text{prox}} + w_C \cdot S_{\text{conseq}}$$

Where:
- $w_V = 0.40$ (Vulnerability Index Weight)
- $w_R = 0.25$ (Deterioration Rate Velocity Weight)
- $w_P = 0.20$ (Hotspot Proximity Weight)
- $w_C = 0.15$ (Asset Consequence & Diameter Weight)

$$\sum w_k = 0.40 + 0.25 + 0.20 + 0.15 = 1.000$$

### Sub-Factor Scoring Details:

1. **Vulnerability Contribution ($40\%$)**:
   $$P_V = 0.40 \cdot V_0$$
2. **Deterioration Rate Contribution ($25\%$)**:
   $$S_{\text{rate}} = \min(100.0, \, \max(0.0, \, \beta_1 \cdot 200.0))$$
   $$P_R = 0.25 \cdot S_{\text{rate}}$$
   A pipe degrading at $+0.25\text{ pts/day}$ receives $S_{\text{rate}} = 50.0 \rightarrow P_R = 12.5\text{ pts}$.
3. **Hotspot Proximity Contribution ($20\%$)**:
   $$S_{\text{prox}} = \begin{cases}
   100.0 & \text{if } d \le 100\text{ m} \\
   75.0 & \text{if } 100\text{ m} < d \le 350\text{ m} \\
   40.0 & \text{if } 350\text{ m} < d \le 750\text{ m} \\
   10.0 & \text{if } d > 750\text{ m} \end{cases}$$
   $$P_P = 0.20 \cdot S_{\text{prox}}$$
4. **Asset Consequence & Diameter Contribution ($15\%$)**:
   $$S_{\text{conseq}} = \begin{cases}
   90.0 & \text{if } D \ge 600\text{ mm (Primary Trunk Main)} \\
   70.0 & \text{if } 400\text{ mm} \le D < 600\text{ mm} \\
   45.0 & \text{if } 200\text{ mm} \le D < 400\text{ mm} \\
   25.0 & \text{if } D < 200\text{ mm} \end{cases}$$
   $$P_C = 0.15 \cdot S_{\text{conseq}}$$

---

## 3. Priority Level Categorization & Action Mappings

The final priority score $P$ maps to four actionable operational tiers:

| Priority Score Range | Priority Level | Suggested Autonomous Rover Action | Response SLA |
|---|---|---|---|
| **$80.0 \le P \le 100.0$** | `CRITICAL_IMMEDIATE` | Immediate acoustic crawling patrol and acoustic leak pinpointing. | $< 12\text{ Hours}$ |
| **$60.0 \le P < 80.0$** | `HIGH_PRIORITY` | Scheduled autonomous rover sonar & visual inspection. | $< 48\text{ Hours}$ |
| **$40.0 \le P < 60.0$** | `ROUTINE_SCHEDULED` | Routine preventive rover patrol and pressure sensor validation. | Standard Sprint |
| **$0.0 \le P < 40.0$** | `MONITORING_ONLY` | Continuous virtual telemetry monitoring; no physical dispatch required. | Periodic Telemetry |

---

## 4. 15 Inspection Queue Ranking Scenarios

To prove the monotonic ranking behavior of the priority formula, 15 synthetic pipe assets with progressively increasing vulnerability, deterioration rate, proximity, and diameter were evaluated.

**Automated Verification**: `test_inspection_priority_formula_ranking` executed:
$$\forall i \in [0, 13]: \quad P_i \le P_{i+1}$$
**Result**: **PASSED**. Monotonic progression verified across all 15 scenarios.

---

## 5. Rover Battery Safety Gate ($\ge 20.0\%$)

Deploying an autonomous rover with insufficient battery risks dead-battery entrapment inside subterranean water conduits.

Task 11.5 implemented and validated an uncompromised battery gate in `request_inspection`:

```python
if rover.battery_percentage is not None and rover.battery_percentage < 20.0:
    raise AquaCrewException(
        status_code=400,
        code="ROVER_BATTERY_INSUFFICIENT",
        message=f"Rover '{rover.name}' ({rover.id}) has insufficient battery reserve ({rover.battery_percentage:.1f}% < 20.0%). Select an alternate rover.",
    )
```

In `InfrastructureIntelligenceView.tsx`, the UI reflects this safety constraint: rovers with $< 20.0\%$ battery are marked as `BLOCKED: Battery < 20%` and disabled in the dispatch dialog.

---

## 6. End-to-End Rover Dispatch Scenarios (A through E)

The full lifecycle of prioritized inspection dispatch was tested in `test_rover_dispatch_scenarios_a_through_e`:

```
+--------------------------------------------------------------------------------+
|                        ROVER DISPATCH WORKFLOW LIFECYCLE                       |
+--------------------------------------------------------------------------------+
|                                                                                |
|  [Vulnerability Scoring Engine]                                                |
|             |                                                                  |
|             v                                                                  |
|  SCENARIO A: Target Identified (Score >= 80)                                   |
|  Record created in DB (status: PENDING, level: CRITICAL_IMMEDIATE)             |
|             |                                                                  |
|             +-----------------------------------------+                        |
|             |                                         |                        |
|             v                                         v                        |
|  SCENARIO B: Battery Gate Check              SCENARIO C: Operator Dismissal    |
|  Rover < 20% Rejected                        Operator rejects recommendation   |
|  (ROVER_BATTERY_INSUFFICIENT)                (status: DISMISSED, reason saved) |
|             |                                                                  |
|             v (Rover >= 20% Selected)                                          |
|  SCENARIO D: Operator Approval & Dispatch                                      |
|  Mission recommendation created, rover assigned                                |
|  (status: DISPATCHED, operator_approval_required: true)                        |
|             |                                                                  |
|             v                                                                  |
|  SCENARIO E: Duplicate Request Prevention                                      |
|  Secondary dispatch on same active target rejected                             |
|  (DUPLICATE_DISPATCH_REJECTED)                                                 |
|                                                                                |
+--------------------------------------------------------------------------------+
```

### Scenario Execution Audit Log:

1. **Scenario A (Target Identification & Queue Entry)**:
   - Priority record generated for segment `PIPE-VAL-TEST-01` ($P = 85.0$, `CRITICAL_IMMEDIATE`).
   - Initial status verified as `PENDING`.
   - **Status: PASSED**.
2. **Scenario B (Depleted Rover Battery Gate)**:
   - Dispatch attempted using `ROV-DEPLETED` ($15.0\%$ battery).
   - System raised `AquaCrewException` with `code="ROVER_BATTERY_INSUFFICIENT"`.
   - Rover was prevented from mission assignment.
   - **Status: PASSED**.
3. **Scenario C (Operator Dismissal Flow)**:
   - Low-priority target ($P = 45.0$) reviewed by operator.
   - Operator called `dismiss_priority` with reason `"Operator verified false positive"`.
   - Database record transitioned to `DISMISSED` with timestamp and justification.
   - **Status: PASSED**.
4. **Scenario D (Operator Approval & Valid Dispatch)**:
   - High-priority target ($P = 85.0$) dispatched with `ROV-VAL-01` ($90.0\%$ battery).
   - `request_inspection` returned `status: "DISPATCHED"`, assigned rover `ROV-VAL-01`, and created mission recommendation.
   - Database record transitioned to `DISPATCHED`.
   - `operator_approval_required` confirmed as `True`.
   - **Status: PASSED**.
5. **Scenario E (Duplicate Dispatch Rejection)**:
   - Second call to `request_inspection` made on the already-dispatched target.
   - System raised `AquaCrewException` with `code="DUPLICATE_DISPATCH_REJECTED"`.
   - Duplicate rover assignment was blocked.
   - **Status: PASSED**.

---

## 7. Safety & Simulation Compliance

All inspection dispatches are software-simulated demonstrations:
- Database provenance: `source: "VIRTUAL_SIMULATION_ENGINE"`, `is_simulated: true`.
- Zero physical actuators or live pumps connected.
- Human operator sign-off strictly required before any rover movement commences.

