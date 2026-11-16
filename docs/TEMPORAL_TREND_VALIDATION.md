# Temporal Deterioration & Trend Analysis Validation (Task 11.5)

## 1. Executive Summary & Objective

Accurate calculation of pipeline deterioration velocity ($\frac{dV}{dt}$, expressed in score points per day) is critical for shifting municipal maintenance from reactive leak repair to predictive infrastructure management.

Prior to Task 11.5, temporal trends were calculated assuming equally-spaced observation intervals, causing significant velocity errors when telemetry records arrived irregularly or in clustered bursts.

Task 11.5 redesigned and validated the **Risk Trend Service** (`risk_trend_service.py`), implementing:
1. Continuous-time Ordinary Least Squares (OLS) linear regression over irregular timestamp series.
2. Robust aggregation of duplicate timestamps at identical epochs.
3. Strict data sufficiency rules to prevent spurious slopes from narrow observation windows.
4. Quantitative trend categorization (`DETERIORATING`, `STABLE`, `IMPROVING`) and rapid degradation alerting.

```
+-----------------------------------------------------------------------------------------+
|                              TEMPORAL TREND VALIDATION MATRIX                           |
+--------------------------+-----------------------+--------------------------------------+
| Capability               | Task 11 Initial State | Task 11.5 Audited & Verified State   |
+--------------------------+-----------------------+--------------------------------------+
| Regression Basis         | Equal-step assumption | Continuous elapsed days ($t_i - t_0$)|
| Duplicate Timestamps     | Distorted slope       | Pre-averaged at identical epochs     |
| Minimum Observation Span | Unchecked             | Minimum $\ge 1.0$ hour required      |
| Sample Count Threshold   | $N \ge 1$             | $N \ge 2$ distinct epochs required   |
| Goodness-of-Fit Metric   | None                  | Pearson $R^2$ coefficient calculated |
| Rapid Degradation Flag   | Arbitrary             | Calibrated threshold $> 0.15$ pts/day|
+--------------------------+-----------------------+--------------------------------------+
```

---

## 2. Ordinary Least Squares (OLS) Mathematical Formulation

### 2.1 Elapsed Time Mapping & Duplicate Averaging

Given a historical series of $M$ timestamped risk observations $\mathcal{O} = \{(T_1, V_1), (T_2, V_2), \dots, (T_M, V_M)\}$:

1. **Epoch Grouping**: Identical timestamps ($T_i = T_j$) are grouped into unique time buckets $t_k$. The score for bucket $k$ is computed as the arithmetic mean of all readings at that exact second:
   $$v_k = \frac{1}{|B_k|} \sum_{m \in B_k} V_m$$
2. **Elapsed Days Normalization**: Epochs are sorted chronologically $\{t_0, t_1, \dots, t_{N-1}\}$:
   $$\tau_k = \frac{t_k - t_0}{86,400.0\text{ seconds}} \quad (\text{Elapsed decimal days from baseline})$$

### 2.2 Closed-Form Linear Regression

The linear trend model $v(\tau) = \beta_0 + \beta_1 \tau$ is solved analytically via Gauss-Markov OLS:

$$\bar{\tau} = \frac{1}{N} \sum_{k=0}^{N-1} \tau_k, \quad \bar{v} = \frac{1}{N} \sum_{k=0}^{N-1} v_k$$

$$SS_{\tau\tau} = \sum_{k=0}^{N-1} (\tau_k - \bar{\tau})^2$$
$$SS_{\tau v} = \sum_{k=0}^{N-1} (\tau_k - \bar{\tau})(v_k - \bar{v})$$
$$SS_{vv} = \sum_{k=0}^{N-1} (v_k - \bar{v})^2$$

The deterioration rate (slope in vulnerability points per day) is:
$$\beta_1 = \frac{SS_{\tau v}}{SS_{\tau\tau}}$$

The intercept is:
$$\beta_0 = \bar{v} - \beta_1 \bar{\tau}$$

The coefficient of determination $R^2 \in [0.0, 1.0]$ measures the linear goodness-of-fit:
$$R^2 = \frac{(SS_{\tau v})^2}{SS_{\tau\tau} \cdot SS_{vv}}$$

---

## 3. Data Sufficiency & Singularity Guardrails

To prevent misleading trend projections from sparse or clustered data, `calculate_ols_slope` enforces strict pre-flight gates:

1. **Minimum Epoch Count**:
   If $N < 2$, linear regression is mathematically undetermined. The service returns:
   $$\text{slope} = \text{None}, \quad \text{data\_sufficiency} = \text{"INSUFFICIENT\_DATA"}, \quad R^2 = \text{None}$$
2. **Minimum Timespan Window**:
   $$\Delta t = t_{N-1} - t_0$$
   If $\Delta t < 3,600.0\text{ seconds}$ ($1.0\text{ hour}$), calculating a daily rate introduces massive extrapolation error (e.g., a $0.1$ point fluctuation over 5 minutes extrapolates to an absurd $28.8\text{ points/day}$). The service rejects the series as `INSUFFICIENT_DATA`.
3. **Zero Variance Guardrail**:
   If $SS_{\tau\tau} < 10^{-12}$ (all points clustered at identical time) or $SS_{vv} < 10^{-12}$ (flat line), slope is clamped to $0.00\text{ pts/day}$.

---

## 4. Trend Direction & Operational Classification

The daily deterioration slope $\beta_1$ maps to utility maintenance categories:

| Deterioration Slope Range ($\beta_1$) | Trend Direction | Operational Meaning | Action Trigger |
|---|---|---|---|
| $\beta_1 > +0.15\text{ pts/day}$ | `DETERIORATING` | **Rapid Structural Degradation** | Immediate Priority Inspection Flag |
| $+0.02 < \beta_1 \le +0.15\text{ pts/day}$ | `DETERIORATING` | **Progressive Aging / Wear** | Scheduled Preventive Patrol (48–72h) |
| $-0.02 \le \beta_1 \le +0.02\text{ pts/day}$ | `STABLE` | **Nominal Baseline Operation** | Periodic Routine Monitoring |
| $\beta_1 < -0.02\text{ pts/day}$ | `IMPROVING` | **Post-Repair Recovery** | Verification Rover Clearance Patrol |

---

## 5. Automated Verification Results

The automated regression test suite (`test_infrastructure_intelligence_validation.py`) verified three critical temporal scenarios:

### Test Case 1: Irregular Timestamp Regression
- **Input Series**:
  - $t_0$: Day $0$, Score $= 50.0$
  - $t_1$: Day $3$, Score $= 51.5$
  - $t_2$: Day $10$, Score $= 55.0$
- **Expected Theoretical Rate**: $\frac{55.0 - 50.0}{10\text{ days}} = 0.500\text{ pts/day}$
- **Calculated Result**: $\beta_1 = 0.500\text{ pts/day}$, $R^2 = 1.000$, Sufficiency = `HIGH`
- **Result**: **PASSED**

### Test Case 2: Duplicate Timestamp Pre-Averaging
- **Input Series**:
  - $t_0$: Day $0$, Score $= 50.0$
  - $t_0$: Day $0$, Score $= 52.0$ (Duplicate timestamp, averaged to $51.0$)
  - $t_1$: Day $10$, Score $= 56.0$
- **Expected Theoretical Rate**: $\frac{56.0 - 51.0}{10\text{ days}} = 0.500\text{ pts/day}$
- **Calculated Result**: $\beta_1 = 0.500\text{ pts/day}$, Sufficiency = `MODERATE`
- **Result**: **PASSED**

### Test Case 3: Insufficient Data Filtering
- **Input Series A**: Single observation at $t_0 \rightarrow$ Returns `(None, "INSUFFICIENT_DATA", None)`
- **Input Series B**: Two observations separated by $15\text{ minutes}$ ($< 1\text{ hour}$) $\rightarrow$ Returns `(None, "INSUFFICIENT_DATA", None)`
- **Result**: **PASSED** (Both edge cases safely handled without spurious slopes)

---

## 6. Multi-Horizon Extrapolations (24h, 7d, 30d)

Using the validated slope $\beta_1$, projected vulnerability score deltas are computed:
$$\Delta V_{24\text{h}} = \beta_1 \cdot 1.0\text{ days}$$
$$\Delta V_{7\text{d}} = \beta_1 \cdot 7.0\text{ days}$$
$$\Delta V_{30\text{d}} = \beta_1 \cdot 30.0\text{ days}$$

Projected scores are strictly bounded within $[0.0, 100.0]$ and feed directly into the Multi-Horizon Infrastructure Prediction Service.

