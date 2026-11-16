# AQUA CREW — ADVANCED AI & EVIDENCE-GROUNDED DECISION INTELLIGENCE ARCHITECTURE
## Task 13 Technical Architecture Document

### 1. Executive Summary & Design Mission
The **Advanced AI & Evidence-Grounded Decision Intelligence Subsystem** serves as the central cognitive synthesis layer of the AQUA CREW platform. It interprets and harmonizes heterogeneous evidentiary streams spanning acoustic hydrophone leak detections (Task 07), predictive asset degradation hazards (Task 09), hydraulic digital twin simulation dynamics (Task 10), geospatial vulnerability clusters (Task 11), and operational prioritization workflows (Task 12).

The core mission of Task 13 is to empower human water utility operators and municipal engineers with transparent, verifiable, evidence-grounded natural-language decision support while strictly eliminating generative hallucinations, fabricated machine learning metrics, and unauthorized autonomous equipment actuation.

---

### 2. High-Level Architectural Flowchart
```
+---------------------------------------------------------------------------------------------------------+
|                                    AQUA CREW APPLICATION UI                                             |
|        Next.js 14 Assistant View (/app/ai-assistant) | Evidence Inspector Drawer | Tradeoff Comparison  |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                   REST HTTP /api/v1/advanced-ai/*
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                                    INPUT SECURITY & SANITIZATION                                        |
|   - Adversarial Prompt Injection Defense (regex pattern screening & token bounding)                     |
|   - Safety Interlock Refusal: Blocks SQL execution, actuator commands & approval bypasses               |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                               TYPED OPERATIONAL CONTEXT RETRIEVAL                                       |
|   - Intent Classification (12 core operational intents mapped without dynamic SQL generation)            |
|   - Entity Resolution (segment IDs, rover units, DMA zones, cluster coordinates)                        |
|   - Structured Subsystem Retrieval (GIS, AI Detections, WNTR Runs, Vulnerability Profiles, Rovers)       |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                               MULTI-SOURCE REASONING & ONTOLOGY                                         |
|   - Strict 6-Class Ontological Segregation:                                                             |
|       * MEASURED: Hydrophone acoustics, pressure sensors, physical pipe specs                           |
|       * SIMULATED: WNTR/EPANET digital twin flows, headloss deltas, Torricelli loss                    |
|       * DERIVED: Health indices, multi-factor vulnerability scores, Pareto priorities                   |
|       * PREDICTED: 24h, 7d, 30d survival failure hazard forecasts                                       |
|       * OPERATOR_ENTERED: Operator authorization decisions, override notes                              |
|       * UNKNOWN: Uncalibrated or missing sensors                                                       |
|   - Physical Tension & Contradiction Detection (Acoustic Anomaly vs. Nominal Pressure Gradient)         |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                                 LLM INFERENCE & PROVIDER ABSTRACTION                                    |
|   - Configured Primary Provider: NVIDIA NIM (Llama 3.1 70B Instruct / Mixtral 8x22B)                   |
|   - OpenAI-Compatible Endpoint Support (GPT-4o, Custom fine-tuned models)                               |
|   - Fallback Engine: Deterministic Grounded Decision Engine (100% offline reliability, zero hallucination) |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                               OUTPUT CLAIM VALIDATION & AUDIT LOGGING                                   |
|   - Fact Verification against Structured Evidence Context                                               |
|   - Currency / Financial Fabrication Prevention (Strictly flags unmodelled monetary savings)            |
|   - Actuator Safeguard Enforcement (Verifies real-world hardware lockout statements)                    |
|   - Tamper-Evident Audit Persistence: ai_conversations, ai_messages, ai_response_evidences, audits       |
+---------------------------------------------------------------------------------------------------------+
```

---

### 3. Ontological Segregation Framework
A foundational constraint of the AQUA CREW platform is the complete provenance separation of data types:
1. **`MEASURED`**: Physical telemetric measurements collected directly by calibrated hardware (hydrophones, acoustic pressure transmitters, soil moisture probes).
2. **`SIMULATED`**: Numerical outputs calculated by scientific engineering engines (WNTR/EPANET hydraulic solver, Torricelli orifice discharge equations, virtual rover kinematic engines).
3. **`DERIVED`**: Deterministic statistical aggregations, Ordinary Least Squares (OLS) regression slopes, and multi-criteria composite priority indices.
4. **`PREDICTED`**: Temporal forecasts generated by trained machine learning models (Gradient-Boosted survival hazard curves, Random Forest 7-day failure risk projections).
5. **`OPERATOR_ENTERED`**: Authorizations, supervisor sign-offs, and override rationales explicitly submitted by human operators.
6. **`UNKNOWN`**: Sensor channels with expired calibrations, unmeasured geotechnical parameters, or incomplete telemetry records.

The AI Assistant is strictly barred from presenting a `PREDICTED` forecast as a `MEASURED` fact, or presenting a `SIMULATED` water loss estimate as a metered physical billing loss.

---

### 4. Integration with Subsystems (Tasks 01–12)
| Subsystem Module | Data Retrieved & Interpreted | Evidence Classification |
| :--- | :--- | :--- |
| **Task 04 (GIS Pipelines)** | Diameter, material, length, pressure zone, nominal pressure | `MEASURED` |
| **Task 05/06 (Virtual Rovers)** | Battery %, motor temperature, operational state, coordinates | `SIMULATED` |
| **Task 07 (AI Leak Detection)** | Anomaly score, classification, SNR, spectral centroid, frequency | `DERIVED` / `MEASURED` |
| **Task 08 (Autonomous Dispatch)** | Mission routes, waypoint plans, feasibility scores, dispatch status | `DERIVED` / `SIMULATED` |
| **Task 09 (Predictive Maintenance)** | Structural health score (0-100), 24h/7d/30d failure probabilities | `DERIVED` / `PREDICTED` |
| **Task 10 (Digital Twin Hydraulics)** | Torricelli leak rate (L/s), headloss delta, junction pressure drops | `SIMULATED` |
| **Task 11 (Geospatial Risk)** | Multi-factor vulnerability score (0-100), spatial cluster radius | `DERIVED` |
| **Task 12 (Operational Intelligence)** | Composite Priority Score, recommended action, operator approval status | `DERIVED` / `OPERATOR_ENTERED` |

---

### 5. Architectural Guarantees & Non-Negotiable Safeguards
- **Zero Raw Database / SQL Access**: The AI Assistant interacts with backend state exclusively through typed Pydantic retrieval services (`OperationalContextRetrievalService`). It cannot dynamically synthesize SQL queries or access the underlying SQLite/PostgreSQL engine.
- **Permanent Actuator Lockdown**: Real-world actuators, pump starters, and isolation valve motorized gearboxes are permanently disabled in software architecture (`hardware_actuators_disabled: true`).
- **Human-in-the-Loop Interlock**: Natural-language requests to "dispatch a rover immediately" or "open a valve" are met with a deterministic safety refusal explaining that all robotic missions must be reviewed and authorized by a human supervisor in the Command Center.
- **Simulation Traceability**: Every generated message, response schema, and audit record carries `is_simulated: true` and `source: "VIRTUAL_SIMULATION_ENGINE"`.

