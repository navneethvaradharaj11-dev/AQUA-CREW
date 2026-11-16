# AQUA CREW — OPERATIONAL AI ASSISTANT SPECIFICATION
## Task 13 Technical Guide & Query Reference

### 1. The 12 Core Platform Questions
The Operational AI Assistant is engineered to answer 12 foundational water distribution and robotics questions with strict factual grounding:

#### 1. "Which pipeline currently has the highest inspection priority and why?"
- **Response Structure**: Names the conduit, composite priority score, priority tier (`CRITICAL`), recommended action, and the 3 principal physical drivers (active acoustic leak anomaly, 600mm arterial consequence, and degradation velocity). States resource allocation feasibility and human approval mandate.

#### 2. "Why is PIPE-SEC-4B-92 classified as critical?"
- **Response Structure**: Decomposes the 4 corroborating evidence streams (acoustic hydrophone score 0.88, Torricelli loss 184.2 m³/day, degradation velocity +0.26 pts/day, spatial cluster proximity 120m). Identifies missing soil resistivity logs and states uncertainty margin (±3.2 points).

#### 3. "Are there contradictions in the evidence for this segment?"
- **Response Structure**: Identifies physical tensions between sensory channels. Specifically highlights elevated acoustic cavitation noise (0.88) co-occurring with nominal macroscopic pressure drop (1.2 psi delta). Reconciles via small orifice jet dynamics.

#### 4. "Which rovers are available and eligible to inspect this pipeline?"
- **Response Structure**: Evaluates fleet telemetry against safety gates: minimum battery $\ge 20.0\%$ (anti-stranding rule) and motor coil temperature $< 65.0^\circ\text{C}$. Lists `AquaRover Alpha` (92% battery) and `AquaRover Beta` (78.5% battery). Notes physical workforce inventory is in simulation mode.

#### 5. "What are the tradeoffs between inspecting pipeline A vs pipeline B today?"
- **Response Structure**: Compares arterial trunk `PIPE-SEC-4B-92` against feeder `PIPE-HRB-02-19`. Highlights that inspecting Trunk B first mitigates maximum volumetric water loss (184.2 m³/day vs terminal feeder pressure drop).

#### 6. "Summarize the operational situation across the network today."
- **Response Structure**: Reports overall network health score (79.4 / 100), network urgency (`CRITICAL`), active acoustic leaks (2), critical conduits (1), pending operator recommendations (3), and available rovers (2). Recommends immediate review of recommendation `REC-SEC4B-92`.

#### 7. "What hydraulic impact would a rupture on this segment have?"
- **Response Structure**: Cites Torricelli orifice discharge ($Q = C_d A \sqrt{2gh}$, $C_d = 0.62$). Details simulated water loss ($184.2\text{ m}^3/\text{day}$, $8.5\text{ L/s}$), pressure deficit delta (0.85 bar), and 6 affected downstream junctions (~8,500 consumers). States financial cost is strictly omitted to prevent fabricated monetary savings.

#### 8. "What evidence supports the leak hypothesis versus sensor anomaly?"
- **Response Structure**: Side-by-side comparative table evaluating acoustic spectral centroid (narrow-band 580 Hz cavitation vs wide-band electrical hum), subterranean moisture probe saturation (38.4%), and hydraulic flow telemetry. Scores true leak likelihood at 87.4%.

#### 9. "What are we missing to make a confident repair decision?"
- **Response Structure**: Identifies 4 evidentiary gaps: direct internal optical CCTV footage, near-field sub-meter acoustic localization, geotechnical soil resistivity, and physical DMA night-flow calibration. Recommends rover inspection before contractor mobilization.

#### 10. "Can the system dispatch a rover to inspect this leak immediately?"
- **Response Structure**: **"NO. The system CANNOT dispatch a rover autonomously or immediately without human authorization."** Details actuator software isolation, mandatory human-in-the-loop review, and provides navigation instructions to authorize the mission in the Command Center.

#### 11. "What caused the model to predict a 7-day failure risk of 78%?"
- **Response Structure**: Cites the Random Forest & Gradient Boosted hazard model (`v1.0.0-rf-gradient-predictive`). Lists deterministic feature drivers: pipe age (+28.2%), operating pressure stress (+24.5%), wall degradation velocity (+16.1%), and corrosive soil exposure (+9.6%).

#### 12. "What should an operator investigate next?"
- **Response Structure**: Provides an ordered action plan: Primary Priority (authorize `REC-SEC4B-92` for AquaRover Alpha), Secondary Priority (sonar survey on Harbor lateral), and Sensor Gap Mitigation (temporary IoT pressure loggers on Southern Feeder).

---

### 2. Typed Context Retrieval Architecture
The assistant does not execute text-to-SQL. Instead, `OperationalContextRetrievalService` implements typed retrieval:
- `detect_query_intent(query)`: Maps query syntax to one of the 12 platform operational intents.
- `extract_target_segment_id(query, db)`: Extracts pipeline segment IDs via regex and database matching.
- `retrieve_context_for_query(...)`: Fetches typed dictionaries of segments, recommendations, rovers, and multi-source evidence.

---

### 3. Interactive UI & Evidence Inspector Drawer
The Next.js 14 frontend (`/app/ai-assistant`) features:
1. **Interactive Evidence Badges**: Every citation in an assistant message is clickable, stamped with its ontological color:
   - `MEASURED` (Emerald)
   - `SIMULATED` (Cyan)
   - `DERIVED` (Purple)
   - `PREDICTED` (Amber)
   - `OPERATOR_ENTERED` (Blue)
2. **Side Evidence Inspector Drawer**: Slides out to display the raw database record, source module, metric value, confidence rating, and simulation provenance tag.
3. **Dedicated Operational Intelligence Tabs**:
   - `Tradeoff Comparison`: Interactive pipeline selector with side-by-side metric tables.
   - `Network Summary`: Metric cards, executive narrative, and unresolved risk lists.
   - `Evidence Gap Analysis`: Data completeness meters and recommended sensory installations.

