# AQUA CREW — Rover Selection & Battery Feasibility Algorithm Specification
**Task 08 Technical Documentation — Multi-Criteria Decision Analysis & Energy Modeling**

## 1. Executive Summary

The **Rover Selection Service** (`apps/api/app/services/rover_selection_service.py`) evaluates virtual autonomous rovers to identify the most suitable candidate for a planned pipeline inspection mission.

To ensure operational safety, the engine enforces strict gating constraints: rovers with insufficient battery capacity, non-idle operating states, elevated motor temperatures, or sensor payload incompatibilities are disqualified with transparent, auditable explanations.

---

## 2. Rover Eligibility Gating Criteria

Before computing numerical suitability scores, each candidate rover must pass binary gating filters:

| Constraint Parameter | Requirement | Disqualification Behavior |
| :--- | :--- | :--- |
| **Operational State** | Must equal `IDLE` | Disqualified if `INSPECTING`, `RETURNING`, `CHARGING`, `ERROR`, `OFFLINE`, or `EMERGENCY_STOP` |
| **Battery Safety Reserve** | Projected end-of-mission battery $\ge 20.0\%$ | Disqualified if energy consumption breaches reserve margin |
| **Motor Temperature** | $T_{\text{motor}} < 50.0^\circ\text{C}$ | Disqualified with thermal alert if motor is overheating |
| **Sensor Payload** | Acoustic & Visual payload active | Disqualified if acoustic listening sensors are offline |
| **Network Reachability** | Connected pipe topology exists | Disqualified if no connected pipeline path connects rover to leak |

---

## 3. Mathematical Battery & Energy Consumption Model

The energy consumption model accounts for transit to the target, slow-speed acoustic survey across the inspection zone, and return transit to the nearest docking hub:

\[
E_{\text{mission\_pct}} = E_{\text{transit\_out}} + E_{\text{inspection}} + E_{\text{transit\_return}}
\]

### 3.1 Component Formulations
1. **Outbound Transit Energy ($E_{\text{transit\_out}}$)**:
   \[
   E_{\text{transit\_out}} = \left(\frac{D_{\text{route\_m}}}{1000}\right) \times \kappa_{\text{travel}}
   \]
   where $\kappa_{\text{travel}} = 1.8\% \text{ battery per kilometer}$ at nominal cruising speed ($0.8\text{ m/s}$).

2. **Acoustic Inspection Energy ($E_{\text{inspection}}$)**:
   Inspection requires high-gain hydrophone amplification, active sonar pinging, and multi-spectral edge inference:
   \[
   T_{\text{inspect\_hr}} = \frac{D_{\text{inspect\_zone\_m}}}{v_{\text{crawl}} \times 3600}
   \]
   \[
   E_{\text{inspection}} = T_{\text{inspect\_hr}} \times \kappa_{\text{sensor}}
   \]
   where $\kappa_{\text{sensor}} = 4.0\% \text{ battery per hour}$ and $v_{\text{crawl}} = 0.2\text{ m/s}$.

3. **Inbound Return Transit Energy ($E_{\text{transit\_return}}$)**:
   \[
   E_{\text{transit\_return}} = \left(\frac{D_{\text{return\_m}}}{1000}\right) \times \kappa_{\text{travel}}
   \]
   *(Assuming return along the same pipeline route, $D_{\text{return\_m}} \approx D_{\text{route\_m}}$).*

4. **Safety Reserve Verification**:
   \[
   \text{Reserve}_{\text{final}} = \text{Battery}_{\text{current}} - E_{\text{mission\_pct}}
   \]
   \[
   \text{IsFeasible} = \begin{cases} 
   \text{True} & \text{if } \text{Reserve}_{\text{final}} \ge 20.0\% \\
   \text{False} & \text{if } \text{Reserve}_{\text{final}} < 20.0\% 
   \end{cases}
   \]

---

## 4. Multi-Criteria Suitability Scoring Function

For rovers satisfying all feasibility constraints, a composite suitability score $S \in [0, 100]$ is computed:

\[
S = w_{\text{dist}} \cdot S_{\text{dist}} + w_{\text{bat}} \cdot S_{\text{bat}} + w_{\text{temp}} \cdot S_{\text{temp}} + w_{\text{sensor}} \cdot S_{\text{sensor}}
\]

### 4.1 Weight Distribution
- $w_{\text{dist}} = 0.40$ (Proximity to target)
- $w_{\text{bat}} = 0.35$ (Post-mission battery safety margin)
- $w_{\text{temp}} = 0.15$ (Motor thermal headroom)
- $w_{\text{sensor}} = 0.10$ (Sensor calibration status)

### 4.2 Sub-Score Normalized Formulations
1. **Proximity Score ($S_{\text{dist}}$)**:
   \[
   S_{\text{dist}} = \max\left(0, 100 - \frac{D_{\text{route\_m}}}{50}\right)
   \]
   *(A rover $0\text{ m}$ away scores 100; a rover $5,000\text{ m}$ away scores 0).*

2. **Battery Reserve Score ($S_{\text{bat}}$)**:
   \[
   S_{\text{bat}} = \min\left(100, \frac{\text{Reserve}_{\text{final}} - 20.0\%}{80.0\% - 20.0\%} \times 100\right)
   \]

3. **Thermal Score ($S_{\text{temp}}$)**:
   \[
   S_{\text{temp}} = \max\left(0, \frac{50.0^\circ\text{C} - T_{\text{motor}}}{50.0^\circ\text{C} - 20.0^\circ\text{C}} \times 100\right)
   \]

4. **Sensor Calibration Score ($S_{\text{sensor}}$)**:
   Fixed at $100$ when acoustic sensors report valid calibration certificates, or scaled by sensor confidence index.

---

## 5. Candidate Ranking & Recommendation

The candidate rovers are sorted in descending order of suitability:
1. The highest-scoring eligible rover is assigned as `recommended_rover_id`.
2. Detailed breakdown of scoring factors, projected energy consumption, and battery reserves are recorded in the `MissionRecommendationModel`.
3. If no rovers meet the eligibility criteria, the recommendation status is flagged with a blocking alert explaining that fleet charging or repositioning is required.

---

## 6. Simulation Provenance

All rover telemetry, motor temperatures, and battery discharge rates are computed by the virtual simulation model. Every rover evaluation carries:
- `is_simulated: true`
- `source: "VIRTUAL_SIMULATION_ENGINE"`

