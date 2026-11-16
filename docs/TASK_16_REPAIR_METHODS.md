# AQUA CREW — TASK 16 REPAIR METHODS
## Standardized Repair Methods, Engineering Constraints & Standards Compliance

---

## 1. Overview of Standardized Repair Methods

The Repair Method Engine (`RepairMethodEngine`) evaluates 8 industry-standard repair methods for every damage assessment. Each method is verified against pipe diameter, pipe wall material, dynamic hydraulic pressure, defect geometry, and required professional engineering sign-offs.

```
+----------------------------------------------------------------------------------------------------+
|                                    8 STANDARDIZED REPAIR METHODS                                   |
+----------------------------------------------------------------------------------------------------+
| 1. CLAMP_REPAIR                   | Full-circle split-sleeve mechanical repair clamp                |
| 2. JOINT_REPAIR_REPLACEMENT       | Mechanical bell-joint leak clamp / restrained coupling          |
| 3. PIPE_SECTION_REPLACEMENT       | Full conduit section cut-and-replace spool piece               |
| 4. INTERNAL_LINING_REHABILITATION | Cured-in-Place Pipe (CIPP) structural inversion                |
| 5. CORROSION_PROTECTION           | Sacrificial zinc anode cathodic protection + dielectric wrap    |
| 6. VALVE_REPLACEMENT              | Resilient-seated gate valve / PRV control assembly replacement  |
| 7. PRESSURE_MANAGEMENT            | Hydraulic PRV setpoint modulation & dynamic transient relief    |
| 8. FURTHER_INSPECTION_REQUIRED    | Targeted secondary crawler verification (Safe fallback)        |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Engineering Standards & Constraint Matrix

Each repair method conforms to established municipal water engineering standards:

| Repair Method | Compatible Materials | Diameter Range ($D$) | Max Pressure | Verified Engineering Standard Reference | Required Approvals |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`CLAMP_REPAIR`** | Ductile Iron, Cast Iron, Carbon Steel, PVC, Asbestos Cement | 50 – 600 mm | 175 PSI (12 bar) | **AWWA C230** (Standard for Stainless-Steel Full-Circle Repair Clamps) — Sec. 4.2 | Certified Distribution Operator Level II, Operations Supervisor |
| **`JOINT_REPAIR_REPLACEMENT`** | Ductile Iron, Cast Iron, Pre-stressed Concrete, Steel | 75 – 1200 mm | 250 PSI (17 bar) | **AWWA C219** (Bolted, Sleeve-Type Couplings for Plain-End Pipe) — Sec. 3.1 | Mechanical Systems Engineer, Operations Supervisor |
| **`PIPE_SECTION_REPLACEMENT`** | All Standard Pipe Materials (Ductile, Cast, Steel, PVC, HDPE) | 50 – 2000 mm | 350 PSI (24 bar) | **AWWA C600** (Installation of Ductile-Iron Water Mains and Their Appurtenances) — Sec. 5.3 | Registered Professional Engineer (PE), Water Quality Assurance Officer |
| **`INTERNAL_LINING_REHABILITATION`** | Ductile Iron, Cast Iron, Steel, Asbestos Cement | 150 – 1200 mm | 200 PSI (14 bar) | **ASTM F1216** (Standard Practice for Rehabilitation of Existing Pipelines by Inverted CIPP) | Principal Materials Engineer, Environmental Compliance Officer |
| **`CORROSION_PROTECTION`** | Ductile Iron, Cast Iron, Carbon Steel | 50 – 2000 mm | 350 PSI (24 bar) | **NACE SP0169 / AWWA C210** (Control of External Corrosion on Underground Metallic Piping) | NACE Certified CP Specialist, Asset Integrity Engineer |
| **`VALVE_REPLACEMENT`** | All Standard Pipe Materials | 50 – 900 mm | 250 PSI (17 bar) | **AWWA C509 / C515** (Resilient-Seated Gate Valves for Water Supply Service) | Hydraulic Distribution Engineer, Operations Supervisor |
| **`PRESSURE_MANAGEMENT`** | All Standard Pipe Materials | 50 – 2000 mm | 350 PSI (24 bar) | **IWA Water Loss Specialist Group** (Guidelines on Dynamic Pressure Reduction) | Lead Hydraulic Modeler, Distribution Chief Operator |
| **`FURTHER_INSPECTION_REQUIRED`** | All Standard Pipe Materials | 50 – 2000 mm | 350 PSI (24 bar) | **NASSCO PACP Version 7.0** (Pipeline Assessment Certification Program) | Chief Asset Integrity Engineer |

---

## 3. Detailed Technical Profiles

### 3.1 Clamp Repair (`CLAMP_REPAIR`)
- **Engineering Description**: Stainless-steel full-circle wrap clamp featuring a waffle-patterned NBR or EPDM elastomeric gasket that bridges localized circumferential cracks or pinholes.
- **Operational Constraints**:
  - Requires minimum 150 mm sound, uncorroded pipe on either side of defect.
  - Cannot bridge longitudinal splits exceeding 50 mm in length.
  - Line pressure must remain $\le 175$ PSI; forbidden on high-pressure arterial transmission mains.
- **Advantages**:
  - Rapid deployment with under 4 hours typical installation time.
  - Can often be installed under residual service pressure without full dewatering.
  - Minimal excavation footprint ($3\text{ m}^2$).
- **Disadvantages & Risks**:
  - Localized repair only; does not restore structural beam strength to degraded pipe.
  - Potential gasket relaxation under ground thermal cycles.

### 3.2 Joint Repair / Replacement (`JOINT_REPAIR_REPLACEMENT`)
- **Engineering Description**: Bolted split-bell encapsulation sleeve or flexible restrained mechanical coupling that clamps over leaking bell-and-spigot lead joints or push-on elastomeric gaskets.
- **Operational Constraints**:
  - Requires full $360^\circ$ excavation around pipe bell.
  - Joint deflection must not exceed $5^\circ$.
- **Advantages**:
  - Accommodates ongoing thermal expansion and ground movement.
  - High pressure rating up to 250 PSI.

### 3.3 Pipe Section Replacement (`PIPE_SECTION_REPLACEMENT`)
- **Engineering Description**: Full structural cut-and-replace operation where the compromised pipe length is excised using hydraulic guillotine saws and replaced with a new epoxy-lined ductile iron spool piece secured with restrained flexible couplings.
- **Operational Constraints**:
  - Complete line isolation and sector dewatering mandatory.
  - Full roadway closure and trench shoring box required.
- **Advantages**:
  - 100% structural renewal with design life exceeding 75 years.
  - Eliminates all local structural flaws and restores hydraulic capacity.

### 3.4 Internal Lining Rehabilitation (`INTERNAL_LINING_REHABILITATION`)
- **Engineering Description**: Trenchless rehabilitation utilizing Cured-in-Place Pipe (CIPP) polymeric inversion or spray-applied structural polyurea lining.
- **Operational Constraints**:
  - Requires overland temporary consumer bypass water piping.
  - Pipe internal surface must undergo high-pressure water jet descaling prior to inversion.
- **Advantages**:
  - Trenchless installation eliminating road excavation between access pits.
  - Restores Hazen-Williams roughness coefficient ($C$-factor) to 140.
  - Spans continuous lengths exceeding 100 meters.

### 3.5 Corrosion Protection (`CORROSION_PROTECTION`)
- **Engineering Description**: Installation of pre-packaged high-potential sacrificial zinc or magnesium anodes welded to the pipe barrel via pin brazing, complemented with petrolatum wax dielectric tape wrapping.
- **Operational Constraints**:
  - Soil resistivity survey required; triggered when soil resistivity is $< 2000 \; \Omega\cdot\text{cm}$.
- **Advantages**:
  - Halts active galvanic oxidation and pit propagation.
  - Low capital cost; extends residual service life by 25+ years.

### 3.6 Valve Replacement (`VALVE_REPLACEMENT`)
- **Engineering Description**: Replacement of defective, seized, or cavitation-damaged resilient-seated gate valves, butterfly valves, or pressure-reducing valves (PRVs).
- **Operational Constraints**:
  - Requires boundary secondary valve isolation and concrete thrust block re-pouring.
- **Advantages**:
  - Restores 100% drip-tight sector partitioning and emergency isolation capability.

### 3.7 Pressure Management (`PRESSURE_MANAGEMENT`)
- **Engineering Description**: Non-invasive hydraulic mitigation modulating upstream PRV pilot controls or variable frequency drive (VFD) pump setpoints to lower dynamic zone pressure by 15–25 PSI.
- **Operational Constraints**:
  - Must maintain minimum 25 PSI residual pressure at high-elevation consumer nodes for fireflow safety.
- **Advantages**:
  - Zero excavation; immediately cuts water loss rate by 30–50% within minutes via SCADA / digital twin.

### 3.8 Further Inspection Required (`FURTHER_INSPECTION_REQUIRED`)
- **Engineering Description**: Automated safety fallback dispatching in-pipe acoustic rovers, CCTV crawlers, or ultrasonic thickness gauges.
- **Trigger Conditions**:
  - Incomplete evidence ($C_{\text{evid}} < 50\%$).
  - Undetermined severity level (`UNDETERMINED`).
  - Unclassified damage category (`UNKNOWN_DAMAGE`).

---

## 4. Feasibility Scoring Algorithm

The feasibility score ($F_m \in [0, 100]$) for each repair method $m$ is evaluated across:
1. **Material Compatibility**: Penalized if pipe material does not match certified coupling metallurgy.
2. **Pressure Safety Margin**: If $P_{\text{nominal}} > P_{\text{max}, m}$, feasibility is penalized to $20.0$, rejecting the method on safety grounds.
3. **Diameter Thresholds**: If $D_{\text{mm}} < D_{\text{min}, m}$ or $D_{\text{mm}} > D_{\text{max}, m}$, score drops below viable threshold.
4. **Defect Geometry Matching**: Bursts favor section replacement ($F = 98.0$); localized leaks favor clamps ($F = 92.0$); severe corrosion favors CIPP lining ($F = 90.0$).

The method with the highest feasibility score is designated as the **Primary Recommended Method**, while the second-highest compliant method is designated as the **Secondary Alternative Method**.

