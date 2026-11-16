# AQUA CREW — EVIDENCE-GROUNDED REASONING & CROSS-SYSTEM SYNTHESIS
## Task 13 Technical Methodology Document

### 1. The Core Engineering Challenge
In complex municipal water distribution networks, raw data is inherently heterogeneous, asynchronous, and occasionally contradictory:
- A high-frequency acoustic hydrophone may detect an intense leak signature, yet upstream and downstream pressure transmitters register negligible pressure drop.
- A spatial clustering algorithm may group three historical failures within 150 meters, yet the pipes are constructed of completely different materials and operate under distinct pressure zones.
- An ML survival model may predict a 78% failure risk within 7 days, yet physical visual inspection has never been performed.

Conventional LLM systems fail catastrophically in these scenarios by confabulating causes, smoothing over contradictions, or inventing plausible-sounding but unverified physical mechanisms. The **AQUA CREW Evidence-Grounded Reasoning Engine** enforces mathematical, physical, and ontological rigor.

---

### 2. Ontological Classification Matrix
Every evidence item processed by the decision engine is stamped with its verified ontological class:

```
[RAW TELEMETRY / SENSORS] --------> MEASURED (Hydrophones, Pressure, Moister Sensors)
[EPANET / HYDRAULIC TWIN] --------> SIMULATED (Torricelli Q = Cd*A*sqrt(2gh), Headloss)
[STATISTICAL AGGREGATION] ---------> DERIVED (Health Index 0-100, Vulnerability 0-100, CPI)
[ML SURVIVAL / FORECAST] ---------> PREDICTED (24h, 7d, 30d Failure Hazard Probabilities)
[HUMAN OPERATOR ACTIONS] ---------> OPERATOR_ENTERED (Approved / Rejected Decision Records)
[MISSING / UNCALIBRATED] ---------> UNKNOWN (Unmeasured Borehole Resistivity, Gaps)
```

#### Rule of Provenance Non-Substitution:
- The system **never** transforms a `SIMULATED` value into a `MEASURED` fact. For example, Torricelli simulated discharge ($184.2\text{ m}^3/\text{day}$) is always labeled as `SIMULATED ESTIMATE`, never as physical metered loss.
- The system **never** reports a `PREDICTED` failure probability ($78.4\%$) as an observed current failure.

---

### 3. Cross-System Contradiction Identification
The `MultiSourceReasoningService` systematically compares signals across subsystems to detect physical tensions:

#### Case Study: Acoustic Anomaly vs. Nominal Pressure Gradient
- **Signal A (Acoustic Stream - MEASURED / DERIVED)**: Hydrophone records continuous stationary narrow-band energy at 450–700 Hz, SPL 64.2 dB, anomaly score 0.88 (`HIGH_LEAK_PROBABILITY`).
- **Signal B (Hydraulic Pressure Stream - MEASURED)**: Upstream junction pressure is 58.4 psi, downstream is 57.2 psi (1.2 psi delta, well within nominal diurnal diurnal oscillation bounds).
- **Automated Tension Analysis**:
  - `Contradiction Identified`: High acoustic leak confidence co-occurs with normal hydraulic gradient.
  - `Physical Reconciliation Hypothesis`: The orifice diameter is small ($\approx 8\text{–}12\text{ mm}$), creating high-velocity supersonic jet cavitation noise without causing macroscopic volumetric pressure collapse in a high-capacity 600 mm arterial trunk.
  - `Confidence Scoring`: Acoustic hypothesis is supported ($0.91$), but macroscopic rupture is refuted ($0.12$).
  - `Action Recommendation`: Deploy autonomous crawler for localized near-field acoustic cross-correlation to pinpoint orifice coordinate without declaring an emergency main shutdown.

---

### 4. Distinguishing Supported Conclusions from Uncertain Hypotheses
The engine categorizes conclusions into two strict buckets:

| Supported Conclusions | Uncertain Hypotheses |
| :--- | :--- |
| **Criteria**: Corroborated by $\ge 2$ independent physical evidence streams with temporal synchrony $< 15$ minutes. | **Criteria**: Supported by only 1 sensory stream, or characterized by missing geotechnical parameters. |
| **Example**: Conduit `PIPE-SEC-4B-92` exhibits active localized pipe-wall discharge corroborated by acoustic SPL ($64.2\text{ dB}$) and subterranean moisture probe saturation ($38.4\%$). | **Example**: Whether the failure mechanism is circumferential cracking vs. joint packing slippage remains an uncertain hypothesis until near-field CCTV footage is collected. |

---

### 5. Evidence Gap Analysis & Sensor Blind Spots
When an operator requests decision support (e.g., *"What are we missing to make a confident repair decision?"*), the system does not improvise. It runs `analyze_evidence_gaps(segment_id)`:
1. **Direct Visual Imagery**: Checks if internal CCTV crawler footage exists. If missing, flags as `CRITICAL_DATA_GAP`.
2. **Sub-Meter Localization**: Evaluates whether acoustic correlation is from fixed manholes ($\pm 15\text{ m}$ uncertainty) vs. in-pipe acoustic crawler ($\pm 0.5\text{ m}$).
3. **Geotechnical Corrosivity**: Audits whether borehole soil resistivity, redox potential, and pH logs have been updated within the 24-month recency window.
4. **DMA Night-Flow Validation**: Checks whether physical district meter night flow isolation tests have verified the zero-consumption baseline.

The output explicitly instructs the operator: *"Authorize autonomous rover inspection to resolve Gaps #1 and #2 before mobilizing excavation contractors."*

