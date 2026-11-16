# AQUA CREW — AI-Powered Leak Detection & Acoustic Intelligence Architecture
## Document Reference: `docs/AI_LEAK_DETECTION_ARCHITECTURE.md`
### Architectural Boundary: Task 07 — AI Leak Detection, Signal Processing & Anomaly Classification

---

## 1. Executive Overview

The **AQUA CREW AI Leak Detection System** is an explainable, multi-stage analytical engine designed to detect, classify, localize, and prioritize potential water leaks across metropolitan pipeline networks. 

In strict adherence to the **Software-First Strategy**, all inputs derive from high-fidelity mathematical simulations and sensor models. All records, events, and API payloads carry explicit simulation provenance (`is_simulated: true`, `source: "VIRTUAL_SIMULATION_ENGINE"`). The architecture deliberately separates automated diagnostic intelligence from physical control: **AI models generate proposed detections and risk assessments for human operator review; no machine learning model or automated rule is permitted to actuate physical infrastructure**.

```
+----------------------------------------------------------------------------------------------------+
|                                    AQUA CREW AI DETECTION PIPELINE                                 |
|                                                                                                    |
|   +--------------------------------------------------------------------------------------------+   |
|   | 1. SENSOR INGESTION LAYER                                                                  |   |
|   |    Acoustic Mics | Pressure Sensors | Flow Meters | Moisture Sensors | Rover Acoustics     |   |
|   +----------------------------------------------+---------------------------------------------+   |
|                                                  | Raw Readings                                    |
|   +----------------------------------------------v---------------------------------------------+   |
|   | 2. SIGNAL PROCESSING ENGINE (NumPy / SciPy)                                                |   |
|   |    Bandpass Filter | Hanning Window | FFT Spectrum | RMS | Dominant Freq | Spectral Energy   |   |
|   +----------------------------------------------+---------------------------------------------+   |
|                                                  | Spectral & Waveform Metrics                     |
|   +----------------------------------------------v---------------------------------------------+   |
|   | 3. FEATURE ENGINEERING & NORMALIZATION                                                     |   |
|   |    Hydraulic Deviations (delta-P, delta-Q) | Soil Saturation | Pipe Structural Properties   |   |
|   +----------------------------------------------+---------------------------------------------+   |
|                                                  | Standardized Feature Vector (12 Dimensions)    |
|   +----------------------------------------------v---------------------------------------------+   |
|   | 4. MACHINE LEARNING INFERENCE                                                              |   |
|   |    A. Isolation Forest (Anomaly Score [-1.0, 1.0])                                         |   |
|   |    B. Random Forest / Logistic Regression Classifier                                       |   |
|   |       [NORMAL, LOW_LEAK_PROBABILITY, MEDIUM_LEAK_PROBABILITY, HIGH_LEAK_PROBABILITY]       |   |
|   +----------------------------------------------+---------------------------------------------+   |
|                                                  | Prediction + Calibrated Probabilities           |
|   +----------------------------------------------v---------------------------------------------+   |
|   | 5. SEVERITY & RISK ASSESSMENT (Rule-Based Matrix)                                          |   |
|   |    Flow Loss Est. + Pressure Drop + Sensor Reliability + Critical Infrastructure Proximity |   |
|   |    => Risk Categories: [LOW, MODERATE, HIGH, CRITICAL] + Human-Readable Explanations       |   |
|   +----------------------------------------------+---------------------------------------------+   |
|                                                  | Prioritized Detection                           |
|   +----------------------------------------------v---------------------------------------------+   |
|   | 6. TDOA LOCALIZATION & UNCERTAINTY                                                         |   |
|   |    Cross-Correlation Time Difference of Arrival (TDOA) along Pipeline LineString           |   |
|   |    => Coordinates [lat, lng] + Uncertainty Radius (meters) / Quality Warning               |   |
|   +----------------------------------------------+---------------------------------------------+   |
|                                                  | Complete AI Detection Record                    |
|   +----------------------------------------------v---------------------------------------------+   |
|   | 7. PERSISTENCE & DISPATCH                                                                  |   |
|   |    - SQLite/PostGIS Storage (`ai_detections`, `sensor_readings`)                           |   |
|   |    - Real-Time WebSocket Events (`/api/v1/ws/telemetry`)                                   |   |
|   |    - Integrated Incident Management (`/app/intelligence` -> `/app/fleet` Dispatch)         |   |
|   +--------------------------------------------------------------------------------------------+   |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Sensor Ingestion & Health Architecture

### Supported Sensor Modalities

| Modality | Physical Unit | Typical Range | Primary Indicator |
|---|---|---|---|
| **Acoustic Microphone** | Decibels ($\text{dB}$) / Amplitude | $20 - 110\text{ dB}$ | High-frequency hiss ($800 - 3500\text{ Hz}$) generated by orifice jet turbulence |
| **Pressure Sensor** | Bar ($\text{bar}$) | $1.5 - 8.5\text{ bar}$ | Localized hydraulic gradient drop downstream of orifice |
| **Flow Meter** | Cubic meters per hour ($\text{m}^3/\text{h}$) | $10 - 250\text{ m}^3/\text{h}$ | Differential mass balance discrepancies across pipeline boundaries |
| **Ground Moisture** | Volumetric Water Content ($\% \text{ VWC}$) | $5 - 85\%$ | Soil saturation anomalies surrounding buried pipeline beds |
| **Temperature** | Celsius ($^\circ\text{C}$) | $8 - 35^\circ\text{C}$ | Thermal gradient shifts caused by escaping potable water into soil |
| **Rover-Mounted Acoustic** | Decibels ($\text{dB}$) / Hydrophone | $15 - 120\text{ dB}$ | Mobile, high-proximity localized acoustic sweeps along pipe walls |

### Ingestion Pipeline Operations
1. **Schema Validation**: Validates all incoming payloads against `SensorReadingCreate` Pydantic models.
2. **Missing-Value Imputation**: Forward-fills intermittent sensor packet drops; flags consecutive gaps $> 3$ intervals as `DEGRADED_QUALITY`.
3. **Outlier Clamping**: Detects impossible sensor spikes (e.g. pressure $> 25\text{ bar}$ or negative flow) using 3-sigma statistical thresholds.
4. **Health State Machine**: Classifies sensor operational status into `HEALTHY`, `SUSPECT`, `CALIBRATING`, or `FAULT`.

---

## 3. Acoustic Signal Processing Engine

The signal processing engine ([`signal_processing_service.py`](file:///E:/BRIDGE%20ASSIGNMENTS/Aqua%20Crew/apps/api/app/services/signal_processing_service.py)) models synthetic acoustic waveforms sampled at $f_s = 8000\text{ Hz}$ across 7 operational regimes:
1. `NORMAL_FLOW`: Broad low-frequency laminar noise ($< 300\text{ Hz}$) with high signal stability.
2. `BACKGROUND_NOISE`: Urban surface traffic vibration and ambient seismic micro-tremors ($50 - 200\text{ Hz}$).
3. `MINOR_LEAK`: Incipient pinhole puncture producing moderate narrow-band resonance ($1200 - 1800\text{ Hz}$).
4. `MODERATE_LEAK`: Crack or joint separation emitting sustained wide-band acoustic hiss ($800 - 2800\text{ Hz}$).
5. `MAJOR_LEAK`: Full pipe breach characterized by massive turbulent roar, cavitation bursts, and significant low-to-mid energy.
6. `PRESSURE_TRANSIENT`: Water hammer or pump switching impulses characterized by sudden step decay.
7. `MECHANICAL_VIBRATION`: Discrete periodic harmonics ($50\text{ Hz}, 100\text{ Hz}$) from rotating machinery/pumps.

### Extracted Acoustic Metrics
- **Root Mean Square (RMS) Amplitude**: Overall signal power $\sqrt{\frac{1}{N} \sum x_i^2}$.
- **Signal-to-Noise Ratio (SNR)**: Decibel ratio of leak-band power to ambient baseline power.
- **Dominant Frequency**: Spectral peak calculated via discrete Fourier transform (FFT) $\arg\max_f |X(f)|$.
- **Spectral Centroid**: Centre of mass of the spectrum $\frac{\sum f \cdot |X(f)|}{\sum |X(f)|}$.
- **Spectral Bandwidth**: Spectral spread around centroid $\sqrt{\frac{\sum (f - \mu_c)^2 |X(f)|}{\sum |X(f)|}}$.
- **Spectral Energy Ratio**: Fraction of acoustic energy concentrated within the diagnostic leak band ($500 - 3000\text{ Hz}$).

---

## 4. Multi-Modal Feature Vector

Engineered features combine acoustic signatures, hydraulic discrepancies, soil environmental factors, and pipeline physical attributes:

$$\mathbf{x} = \begin{bmatrix}
\text{RMS Amplitude} \\
\text{Dominant Frequency (Hz)} \\
\text{Spectral Centroid (Hz)} \\
\text{Leak Band Energy Ratio} \\
\text{Pressure Drop } (\Delta P = P_{\text{expected}} - P_{\text{measured}}) \\
\text{Flow Rate Deviation } (\Delta Q = Q_{\text{in}} - Q_{\text{out}}) \\
\text{Ground Moisture Delta } (\Delta M = M_{\text{measured}} - M_{\text{baseline}}) \\
\text{Soil Temperature Delta } (\Delta T) \\
\text{Sensor Reliability Score } [0.0 - 1.0] \\
\text{Pipeline Diameter (mm)} \\
\text{Pipeline Material Index (Ductile Iron, Cast Iron, Steel, PVC, HDPE)} \\
\text{Nominal Operating Pressure (bar)}
\end{bmatrix}$$

---

## 5. Machine Learning Architecture

Two distinct, complementary ML capabilities are deployed:

### A. Unsupervised Anomaly Detection (`IsolationForest`)
- **Objective**: Identify abnormal sensor behavior without requiring prior leak class labels.
- **Algorithm**: `sklearn.ensemble.IsolationForest` trained on normal metropolitan baseline distributions.
- **Output**: Anomaly score scaled to $[0.0, 1.0]$ ($0.0 = \text{nominal}$, $1.0 = \text{extreme anomaly}$).

### B. Supervised Leak Classifier (`RandomForestClassifier` & `LogisticRegression`)
- **Objective**: Multi-class categorization into diagnostic tiers:
  1. `NORMAL`: Nominal flow, zero leak indication ($P(\text{leak}) < 0.20$).
  2. `LOW_LEAK_PROBABILITY`: Marginal anomaly; potential micro-leak or sensor drift ($0.20 \le P < 0.50$).
  3. `MEDIUM_LEAK_PROBABILITY`: Consistent acoustic hiss and minor pressure depression ($0.50 \le P < 0.80$).
  4. `HIGH_LEAK_PROBABILITY`: Pronounced acoustic turbulence, sharp pressure drop, moisture rise ($P \ge 0.80$).
- **Explainability**: Returns feature importance weights and SHAP-inspired linear attribution vectors explaining why a classification was produced.

---

## 6. Rule-Based Severity & Risk Matrix

To prevent black-box decision making, risk is computed via a transparent deterministic matrix:

$$\text{Risk Score} = 0.35 \cdot S_{\text{class}} + 0.25 \cdot S_{\Delta P} + 0.20 \cdot S_{\text{loss}} + 0.10 \cdot S_{\text{mat}} + 0.10 \cdot S_{\text{crit}}$$

- **LOW**: Pinhole seepage, negligible hydraulic impact, non-critical residential zone.
- **MODERATE**: Minor-to-medium leak on distribution line; inspection scheduled within 24 hours.
- **HIGH**: Significant water loss ($> 1500\text{ L/h}$) or primary trunk line pressure drop; rapid virtual rover dispatch recommended.
- **CRITICAL**: Major burst or structural joint failure with critical infrastructure proximity; immediate operator alert and high-priority inspection mission creation.

---

## 7. Acoustic Time-Difference-of-Arrival (TDOA) Localization

For pipeline segments equipped with dual acoustic transducers at sensor positions $S_1$ and $S_2$, the relative location of the acoustic emission source along the pipe length $L$ is determined by:

$$d_1 = \frac{L - c \cdot \Delta t}{2}$$

where:
- $L$: Distance between sensor stations along the pipeline segment (meters).
- $c$: Speed of sound in the fluid-pipe system ($c \approx 1100 - 1400\text{ m/s}$ for water in ductile iron/steel; $c \approx 350 - 550\text{ m/s}$ for PVC/plastic).
- $\Delta t$: Measured time difference of arrival derived from generalized cross-correlation with phase transform (GCC-PHAT):
  $$\Delta t = \arg\max_\tau \int_{-\infty}^{\infty} \frac{X_1(f) X_2^*(f)}{|X_1(f) X_2^*(f)|} e^{j 2 \pi f \tau} df$$

### Uncertainty & Quality Guardrails
- If $\text{SNR} < 6\text{ dB}$ or sensor cross-correlation peak $< 0.45$, the localization engine **refuses to return a fake coordinate**.
- Instead, it returns an explicit `uncertainty_meters: null` and `quality: "INSUFFICIENT_ACOUSTIC_COHERENCE"`, prompting manual rover verification rather than misleading field operators.

---

## 8. Human-in-the-Loop Operational Workflow

```
[Simulated Sensors]
        |
        v
[AI Processing & Anomaly Engine]
        |
        v
[Proposed AI Detection Record] (Status: PROPOSED / PENDING_REVIEW)
        |
        v
[Operator Dashboard: /app/intelligence]
        |
   +----+--------------------------+
   | Operator Rejects              | Operator Approves
   v                               v
[Mark False Positive]       [Promote to Active Incident]
                                   |
                                   v
                            [Auto-Create Inspection Mission]
                                   |
                                   v
                            [Dispatch Virtual Rover: ROV-AQUA-01]
```

**Guardrail Policy**: No physical actuator, valve closure, or pump shutdown can be initiated by the AI service. All actions require human operator confirmation.
