# AQUA CREW — Leak Localization & TDOA Methodology
**Task 07 — Acoustic Time-Difference-Of-Arrival & Pipeline Spatial Mapping**

## 1. Overview of Acoustic Leak Localization

Acoustic leak localization estimates the spatial position of a leak along a buried pipeline segment by analyzing the acoustic propagation delay between two acoustic measurement sensors (stationary hydrophones, accelerometers, or rover-mounted listening devices) situated at known ends or stations of the pipe segment.

> [!NOTE]
> In AQUA CREW Task 07, the localization engine operates in software simulation mode using mathematical acoustic models and pipeline GIS geometry.

---

## 2. Mathematical TDOA Principles

### 2.1 Acoustic Wave Velocity in Buried Water Pipes

The speed of acoustic wave propagation \(c\) in a water-filled pipe depends on fluid bulk modulus, pipe wall elasticity, and pipe diameter:

\[
c = \frac{c_0}{\sqrt{1 + \frac{K \cdot D}{E \cdot e}}}
\]

where:
- \(c_0 \approx 1,480 \text{ m/s}\) is the speed of sound in unconfined freshwater at 20°C.
- \(K \approx 2.15 \times 10^9 \text{ Pa}\) is the bulk modulus of water.
- \(D\) is the internal pipe diameter.
- \(E\) is the Young's modulus of elasticity of the pipe material (e.g., \(1.7 \times 10^{11} \text{ Pa}\) for ductile iron, \(3.0 \times 10^9 \text{ Pa}\) for PVC).
- \(e\) is the pipe wall thickness.

For typical urban distribution networks:
- Metallic pipes (Ductile Iron, Cast Iron, Steel): \(c \approx 1,100 \text{ to } 1,350 \text{ m/s}\)
- Plastic pipes (PVC, HDPE): \(c \approx 350 \text{ to } 600 \text{ m/s}\)

### 2.2 Time-Difference-of-Arrival (TDOA) Distance Equation

For two sensors separated by pipe distance \(L\), a leak located at distance \(d_1\) from Sensor 1 and \(d_2\) from Sensor 2 produces arrival times \(t_1\) and \(t_2\):

\[
\Delta t = t_1 - t_2 = \frac{d_1 - d_2}{c}
\]

Since \(d_1 + d_2 = L\):

\[
d_1 = \frac{L + c \cdot \Delta t}{2}
\]

---

## 3. Implementation in AQUA CREW

The localization engine is implemented in `apps/api/app/services/leak_localization_service.py`:

1. **Velocity Lookup**: Computes acoustic wave velocity according to pipeline material:
   - `ductile_iron` / `cast_iron`: 1,250 m/s
   - `steel`: 1,350 m/s
   - `pvc` / `hdpe`: 450 m/s
2. **Normalized Fraction (\(\alpha\))**:
   \[
   \alpha = \frac{d_1}{L} \in [0.0, 1.0]
   \]
3. **Geo-Coordinate Linear Interpolation**:
   Projects \(\alpha\) onto the segment's GeoJSON coordinate polylines:
   \[
   \text{Lat}_{\text{leak}} = \text{Lat}_{\text{start}} + \alpha (\text{Lat}_{\text{end}} - \text{Lat}_{\text{start}})
   \]
   \[
   \text{Lng}_{\text{leak}} = \text{Lng}_{\text{start}} + \alpha (\text{Lng}_{\text{end}} - \text{Lng}_{\text{start}})
   \]
4. **Uncertainty Radius Estimation**:
   The uncertainty radius \(\sigma_r\) scales inversely with acoustic Signal-to-Noise Ratio (\(\text{SNR}_{\text{dB}}\)):
   \[
   \sigma_r = \max\left(8.0, \frac{180.0}{\max(\text{SNR}_{\text{dB}}, 4.0)}\right) \text{ meters}
   \]

---

## 4. Quality Indicators & Fallbacks

To prevent misleading operators with false precision, AQUA CREW assigns explicit quality levels:

| Quality Flag | Criteria | UI Behavior |
|---|---|---|
| `HIGH` | SNR \(\ge 14 \text{ dB}\), pipe metadata complete | Displays exact pin and tight uncertainty circle (e.g. \(\pm 12 \text{ m}\)) |
| `MODERATE` | 8 dB \(\le\) SNR \(< 14 \text{ dB}\) | Displays pin with wider uncertainty ring (e.g. \(\pm 25 \text{ m}\)) |
| `LOW` | 4 dB \(\le\) SNR \(< 8 \text{ dB}\) | Displays warning: "Coarse localization only" |
| `SUPPRESSED` | SNR \(< 4 \text{ dB}\) or NORMAL flow | Coordinates suppressed to `null`. Prevents false pin on map. |

