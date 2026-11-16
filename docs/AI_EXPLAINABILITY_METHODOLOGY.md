# AQUA CREW — AI EXPLAINABILITY & TRANSPARENCY METHODOLOGY
## Task 13 Technical Methodology Document

### 1. The Anti-Fabrication Explainability Mandate
A pervasive pathology in modern conversational AI is the synthesis of artificial explainability metrics:
- An LLM prompted to explain a model prediction often invents plausible-sounding but completely fabricated SHAP values (e.g., claiming *"feature_x had a SHAP value of +0.342"* when SHAP was never computed).
- Generating synthetic confidence intervals or false feature importances creates legal liability and undermines engineering trust.

**AQUA CREW Rule of Explainability**:
> *Under no circumstances shall the Advanced AI Subsystem fabricate SHAP values, surrogate feature importances, or post-hoc regression coefficients. Explanations must be grounded entirely in verifiable, deterministic rule-based attributions, physical equations, and audited model metadata.*

---

### 2. Multi-Factor Infrastructure Vulnerability Explainability
When explaining a pipeline's vulnerability score (e.g. `84.5 / 100` on `PIPE-SEC-4B-92`), the system accesses the audited weights from Task 11:
$$\text{Vulnerability} = w_{\text{hyd}} \cdot S_{\text{hyd}} + w_{\text{str}} \cdot S_{\text{str}} + w_{\text{inc}} \cdot S_{\text{inc}} + w_{\text{env}} \cdot S_{\text{env}}$$
Where:
- Hydraulic Criticality ($30\%$ weight): $82.0 / 100$
- Structural Material Degradation ($25\%$ weight): $86.5 / 100$
- Spatial Incident Proximity ($25\%$ weight): $88.0 / 100$
- Environmental Corrosivity ($20\%$ weight): $78.5 / 100$

The assistant explains:
1. **Primary Score Driver**: Structural material degradation on 42-year-old pit-cast ductile iron pipe.
2. **Amplifier**: Transmission consequence scaling applied due to conduit diameter ($600\text{ mm} \ge 600\text{ mm}$).
3. **Data Completeness**: $85.0\%$, with an explicit uncertainty bound of $\pm 3.2$ points.
4. **Assumptions & Limitations**: Soil corrosivity was assumed neutral ($\text{pH } 7.0$) due to missing geotechnical borehole resistivity logs.

---

### 3. Predictive Failure Risk Explainability (7-Day Hazard)
When explaining why the model predicted a 7-day failure probability of $78.4\%$:
- **Model**: Gradient-Boosted Survival Hazard & Random Forest Classifier (`v1.0.0-rf-gradient-predictive`).
- **Verified Deterministic Feature Drivers**:
  1. **Asset Age & Material Lifecycle ($+28.2\%$)**: 42-year-old Ductile Iron pipe exceeding $80\%$ of design lifecycle without polyethylene protective wrap.
  2. **Operating Pressure Stress ($+24.5\%$)**: Sustained operating pressure of 65 psi with diurnal transient hydraulic surging ($\pm 14\text{ psi}$ oscillations).
  3. **Active Structural Degradation Velocity ($+16.1\%$)**: Wall thinning deterioration rate of $+0.26\text{ points/day}$ over the 90-day regression window.
  4. **Corrosive Soil Table Setting ($+9.6\%$)**: Conduit traverses coastal water table proximity zone.

Each percentage contribution is directly derived from the normalized physical properties and decision splits of the trained model, not invented by the language model.

---

### 4. Operational Recommendation Ranking Explainability
When explaining why an operational recommendation ranks #1 in the network:
- **Framework**: Task 12 Multi-Criteria Pareto Optimization (`v1.0.0-multi-criteria-pareto`).
- **Deterministic Component Breakdown**:
  - Incident Severity Weight ($25\%$): $88.0$
  - Vulnerability Profile Weight ($20\%$): $84.5$
  - Structural Health Deficit ($20\%$): $74.2$
  - Hydraulic Criticality ($15\%$): $82.0$
  - Service Criticality ($12\%$): $100.0$
  - Recurrence Factor ($8\%$): $40.0$
- **Resource Feasibility Gate**: Evaluated `AquaRover Alpha` availability (battery $92\%$, motor temp $28.4^\circ\text{C}$, distance $1,200\text{ m}$) as an operational constraint without artificially modifying the intrinsic risk score.
- **Safety Interlock**: Recommends dispatch, but holds execution in `PENDING_REVIEW` requiring certified operator approval.

