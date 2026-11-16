# Material & Diameter Engineering Assumptions (Task 11.5)

## 1. Executive Summary & Purpose

In municipal water infrastructure asset management, physical pipe attributes—specifically **construction material** and **internal diameter**—are the primary determinants of structural deterioration rates and failure consequence.

This document formalizes the empirical engineering assumptions, peer-reviewed literature benchmarks, diameter consequence curves, and missing data fallback behaviors implemented within the **AQUA CREW Multi-Factor Vulnerability Scoring Engine** (`vulnerability_scoring_service.py`).

> [!IMPORTANT]
> **Engineering Transparency & Methodology Honesty**:
> These material and diameter weights are **deterministic, physics-informed empirical heuristics** calibrated against American Water Works Association (AWWA) standards and Water Research Foundation (WRF) municipal break records. They must **never** be misrepresented to operators as black-box deep learning failure probabilities.

---

## 2. Industry Literature Benchmarks & Material Provenance

The material vulnerability coefficients in AQUA CREW are derived from peer-reviewed water industry research:

1. **AWWA Manual of Water Supply Practices M28** (*Rehabilitation of Water Mains*):
   - Documents graphitic corrosion rates in unlined cast iron pipes manufactured before 1960.
   - Highlights circumferential beam breakage modes in small-diameter cast iron versus longitudinal splitting in large ductile iron.
2. **Water Research Foundation (WRF) Project 4307** (*Water Main Break Rates in the USA and Canada: A Comprehensive Study*):
   - Analyzed over 170,000 miles of water mains across 298 municipal utilities.
   - Established average annual break rates per 100 miles of pipe:
     - Cast Iron: **24.4 breaks / 100 miles / year** (Highest vulnerability)
     - Asbestos Cement: **13.2 breaks / 100 miles / year**
     - Ductile Iron: **5.5 breaks / 100 miles / year**
     - PVC / HDPE: **2.6 breaks / 100 miles / year** (Lowest vulnerability)
3. **EPA Aging Water Infrastructure Research Program (EPA/600/R-10/078)**:
   - Validated non-destructive acoustic inspection intervals based on material degradation curves.

---

## 3. Calibrated Material Vulnerability Matrix

The scoring engine maps sanitized material descriptors to baseline structural vulnerability scores $S_{\text{mat}} \in [0.0, 100.0]$:

| Pipe Material Classification | Baseline Vulnerability Score | Degradation Mechanisms & Vulnerability Factors | Recommended Inspection Cadence |
|---|---|---|---|
| **Cast Iron (Pit Cast / Sand Cast, Unlined)** | **82.0 / 100** | External anaerobic pitting corrosion, graphitization (iron leached away leaving brittle graphite matrix), high circumferential fracture risk under traffic shock. | 12–24 Months (Acoustic Crawling) |
| **Cast Iron (Epoxy Lined / Cement Mortar)** | **75.0 / 100** | Reduced internal tuberculation; exterior wall remains vulnerable to corrosive groundwater and soil sulfides. | 24–36 Months |
| **Prestressed Concrete Cylinder Pipe (PCCP)** | **68.0 / 100** | Prestressing wire corrosion, hydrogen embrittlement, catastrophic instantaneous barrel rupture under surge pressure. | 24 Months (Electromagnetic / Sonar) |
| **Asbestos Cement (Transite)** | **65.0 / 100** | Calcium leaching in soft water, fiber embrittlement, wall softening and micro-fracturing. | 36 Months |
| **Ductile Iron (Class 54, Modern Lined)** | **52.0 / 100** | High tensile yield strength ($420\text{ MPa}$), ductile deformation mode, localized galvanic pitting at damaged polywrap sleeves. | 48–60 Months |
| **Mild Carbon Steel (Mortar Lined/Coated)** | **45.0 / 100** | Weld seam corrosion, high pressure tolerance but vulnerable to soil electro-chemical currents if cathodic protection fails. | 48 Months |
| **Polyvinyl Chloride (PVC Schedule 40/80)** | **30.0 / 100** | Immune to galvanic and chemical corrosion; susceptible to cyclic fatigue from pressure transients and brittle cold-weather shear. | 72 Months |
| **High-Density Polyethylene (HDPE PE4710)** | **25.0 / 100** | Zero corrosion, heat-fused monolithic joints (zero bell/spigot leaks), high strain tolerance ($> 1000\%$), surge resilience. | 84–120 Months |
| **Unclassified / Missing Material** | **50.0 / 100** | **Neutral Default Baseline**. Triggers data completeness penalty ($10\%$) and expands uncertainty margin ($\pm 8.0\text{ pts}$). | Immediate Attribute Verification |

---

## 4. Diameter Consequence & Hydraulic Impact Curves

Pipe diameter $D$ directly dictates **burst consequence** (volumetric discharge rate, flood damage to street grade, pressure zone collapse) and **mechanical vulnerability**:

$$\Delta S_{\text{dia}} = \begin{cases}
+12.0 & \text{if } D \ge 600\text{ mm} \quad (\text{Catastrophic Municipal Consequence}) \\
+6.0 & \text{if } 400\text{ mm} \le D < 600\text{ mm} \quad (\text{Secondary Arterial Consequence}) \\
0.0 & \text{if } 200\text{ mm} < D < 400\text{ mm} \quad (\text{Nominal Distribution Range}) \\
+8.0 & \text{if } D \le 200\text{ mm} \quad (\text{Localized Shear & Soil Overburden Vulnerability})
\end{cases}$$

### Engineering Justification:

1. **Large Transmission Mains ($D \ge 600\text{ mm}$)**:
   - Carries municipal transmission discharge flows exceeding $0.50\text{ m}^3/\text{s}$ ($8,000\text{ GPM}$).
   - A single full-bore rupture can depressurize an entire pressure zone, trigger boil-water notices, flood electrical substations, and cause massive street subsidence.
   - Consequence weight $+12.0$ elevates transmission corridors to priority inspection status even when historical leaks are sparse.
2. **Small Distribution Laterals ($D \le 200\text{ mm}$)**:
   - Consequence of rupture is localized.
   - However, physical beam strength is proportionally lower: small pipes suffer beam failure from differential soil settlement, frost heave, and urban heavy axle traffic overburden.
   - Structural vulnerability weight $+8.0$ reflects higher break frequency per unit length.

---

## 5. Handling Incomplete & Corrupted Metadata

Municipal GIS databases frequently contain incomplete pipe records for historic conduits installed prior to digital cataloging.

The AQUA CREW scoring engine enforces robust, non-crashing guardrails:

```
[Incoming Segment Payload]
            |
            v
[validate_segment_inputs()]
            |
            +--> Is material missing / empty?
            |      YES: MatScore = 50.0, Completeness -= 10%, Uncertainty += 3.5 pts
            |      NO:  Lookup AWWA calibrated score
            |
            +--> Is diameter <= 0 or > 3000 mm?
            |      YES: Dia = 300 mm, Completeness -= 10%, Uncertainty += 3.5 pts
            |      NO:  Calculate exact diameter curve
            |
            +--> Is length <= 0 or > 50,000 m?
            |      YES: Length = 500.0 m, Completeness -= 10%
            |      NO:  Use surveyed length
            |
            +--> Is nominal pressure negative or > 250 psi?
                   YES: Pressure = 60.0 psi, Completeness -= 10%
                   NO:  Use operating pressure head
```

### Automated Validation Evidence:
- `test_scenario_08_incomplete_data_missing_material` confirms that uncatalogued segments receive base $50.0$ structural score with `data_completeness_pct <= 50%` and `uncertainty_margin >= 5.0 pts`.
- `test_scenario_15_invalid_parameter_conditions` confirms that negative diameters ($-500\text{ mm}$) and negative pressures ($-50\text{ psi}$) are sanitized without uncaught runtime exceptions, strictly clamping the final score within $[0.0, 100.0]$.

---

## 6. Conclusion & Maintenance Protocol

The material and diameter models provide an objective, traceable foundation for vulnerability scoring. When physical pipe replacements occur (e.g. replacing Cast Iron with HDPE), the platform recalculation immediately reduces structural vulnerability from $82.0$ to $25.0$, updating the inspection queue and rover deployment schedules in real time.

