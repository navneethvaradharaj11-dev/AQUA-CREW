# AQUA CREW — TASK 16 RESOURCE AND COST MODEL
## Itemized Material Intelligence, Equipment Allocation & Transparent Cost Model

---

## 1. Resource Planning Engine

The Resource Planning Engine (`ResourcePlanningEngine`) formulates complete, itemized Bills of Materials (BOM) and heavy equipment rosters tailored to the selected repair method, pipe diameter ($D_{\text{mm}}$), and pipe metallurgy.

### 1.1 Itemized Bill of Materials (BOM)

Every material item is validated against compatibility constraints:

| Category | Component Description | Sizing / Specification | Unit Cost (USD) | Compatibility Rule |
| :--- | :--- | :--- | :--- | :--- |
| `MATERIAL` | Full-Circle Stainless Steel Repair Clamp | Sized to pipe outer diameter ($D_{\text{OD}}$) | \$450.00 | Ductile Iron, Cast Iron, Steel, PVC |
| `MATERIAL` | EPDM Dielectric Insulating Gasket Bushing | Compatible with pipe nominal diameter | \$85.00 | Metallic-to-metallic isolation |
| `MATERIAL` | High-Tensile 316SS T-Head Bolt & Nut Set | 5/8" $\times$ 3.5" coated fasteners | \$65.00 per set | Torque specified per AWWA C230 |
| `MATERIAL` | High-Zinc Sacrificial Galvanic Anode Pack | 12 lb pre-packaged bentonite-gypsum backfill | \$180.00 each | Soil resistivity $< 2000 \; \Omega\cdot\text{cm}$ |
| `MATERIAL` | Class 52 Ductile Iron Replacement Spool Piece | Sized to $D_{\text{mm}}$, epoxy-lined | \$850.00 – \$1,800.00 | AWWA C151 / ANSI A21.51 |
| `MATERIAL` | Restrained Wide-Tolerance Mechanical Couplings | Pair of transition couplings | \$750.00 per pair | Plain-end pipe bridging |
| `MATERIAL` | High-Tack Petrolatum Anti-Corrosion Wrap | 100mm $\times$ 10m roll | \$70.00 per roll | External atmospheric/soil protection |
| `MATERIAL` | Ready-Mix Rapid Hardening Concrete | Class C 3000 PSI thrust restraint | \$220.00 per $\text{m}^3$ | Reaction blocks at fittings/valves |

### 1.2 Heavy Equipment & Machinery Roster

Equipment requirements are determined by excavation depth, trench safety, and handling requirements:

| Equipment Item | Function | Hourly Rate (USD) | Allocation Trigger |
| :--- | :--- | :--- | :--- |
| **Tracked Mini-Excavator (5 Ton)** | Precision urban trenching and pavement peeling | \$120.00 / hr | Clamp repairs, small excavations |
| **Heavy Tracked Excavator (20 Ton)** | Deep excavation and heavy spool lifting | \$220.00 / hr | Full pipe cut-and-replace, valves |
| **Aluminum Trench Shoring Box & Struts** | OSHA Subpart P cave-in protection | \$45.00 / hr | Any excavation depth $> 1.2\text{ m}$ |
| **Submersible Trash Dewatering Pump (3")** | Excavation water evacuation | \$35.00 / hr | Leaking pipes with water pooling |
| **Hydraulic Pipe Guillotine Saw** | Cold cut pipe severance without spark hazard | \$55.00 / hr | Spool piece replacement |
| **Calibrated Digital Torque Multiplier** | Precision bolt torque application (100–120 ft-lb) | \$25.00 / hr | Flange and coupling bolting |
| **Vacuum Excavation (Soft-Dig) Unit** | Non-destructive utility daylighting | \$185.00 / hr | High-density underground utility zones |
| **Mobile Boom Crane Truck** | Large diameter pipe & valve lifting | \$160.00 / hr | Components weighing $> 250\text{ kg}$ |

### 1.3 Certified Field Labor Model

Field labor costs reflect fully loaded municipal utility union rates including fringe benefits, insurance, and hazard allowances:

| Role | Required Certification | Hourly Wage (USD) |
| :--- | :--- | :--- |
| **Lead Repair Foreman** | AWWA Certified Distribution Operator Class IV | \$85.00 / hr |
| **Journeyman Pipefitter** | State Certified Pressure Piping Mechanic | \$65.00 / hr |
| **Heavy Equipment Operator** | NCCCO Certified Crane & Excavator Class A | \$75.00 / hr |
| **Welder / Joint Specialist** | AWS D1.1 Structural Welding Certified | \$70.00 / hr |
| **Safety Specialist** | OSHA Confined Space Supervisor (29 CFR 1910.146) | \$60.00 / hr |
| **Traffic Control Specialist** | ATSSA / DOT Certified Flagger | \$45.00 / hr |

The average blended crew hourly rate is:

$$R_{\text{labour, blended}} = \frac{\sum_{i=1}^{N_{\text{crew}}} R_i}{N_{\text{crew}}} \approx \$72.00 \text{ / hour}$$

---

## 2. Transparent Cost Calculation Engine

The Cost Estimation Engine (`CostEstimationEngine`) avoids black-box estimates by calculating every expense through explicit formulas and verifiable parameters across seven distinct cost components.

### 2.1 Seven Itemized Cost Components

1. **Materials Subtotal ($C_{\text{material}}$)**:
   $$C_{\text{material}} = \sum_{j \in \text{BOM}} Q_j \times P_{\text{unit}, j}$$

2. **Heavy Equipment Subtotal ($C_{\text{equipment}}$)**:
   $$C_{\text{equipment}} = \sum_{k \in \text{Equipment}} T_{\text{hours}} \times R_{\text{equip}, k}$$

3. **Certified Field Labor Subtotal ($C_{\text{labour}}$)**:
   $$C_{\text{labour}} = N_{\text{crew}} \times R_{\text{labour, blended}} \times T_{\text{duration}}$$

4. **Specialized Inspection & Diagnostic Allocation ($C_{\text{inspection}}$)**:
   Accounts for rover deployment, hydro-acoustic sensor processing, and digital twin pre-modeling:
   $$C_{\text{inspection}} = \$450.00 \quad \text{(Fixed Municipal Allocation)}$$

5. **Pre-Repair Treated Water Loss Valuation ($C_{\text{water\_loss}}$)**:
   Quantifies the economic cost of treated drinking water lost from anomaly detection until physical repair:
   $$V_{\text{day}} = \frac{Q_{\text{leak, lph}} \times 24}{1000} \quad (\text{m}^3/\text{day})$$
   $$C_{\text{water\_loss}} = V_{\text{day}} \times U_{\text{water}} \times D_{\text{response}}$$
   Where:
   - $U_{\text{water}} = \$1.85 / \text{m}^3$ (Average municipal treated water production cost).
   - $D_{\text{response}}$ is projected response window in days ($1.0$ day for `CRITICAL`, $3.0$ days for `HIGH`, $7.0$ days for `MODERATE`).

6. **Road Surface & Infrastructure Restoration ($C_{\text{restoration}}$)**:
   Restoration of asphalt paving, sub-base compaction, and curb concrete:
   $$C_{\text{restoration}} = A_{\text{trench}} \times R_{\text{paving}}$$
   - Clamp repair: $3\text{ m}^2$ trench $\to \$600.00$.
   - Full cut-and-replace: $8\text{ m}^2$ trench $\to \$2,800.00$.
   - Valve / joint repair: $5\text{ m}^2$ trench $\to \$1,100.00$.

7. **Engineering Contingency Allowance ($C_{\text{contingency}}$)**:
   A standard 10% contingency buffer for unforeseen subsurface utility interference, rock excavation, and groundwater pumping:
   $$C_{\text{subtotal}} = C_{\text{material}} + C_{\text{equipment}} + C_{\text{labour}} + C_{\text{inspection}} + C_{\text{water\_loss}} + C_{\text{restoration}}$$
   $$C_{\text{contingency}} = C_{\text{subtotal}} \times 0.10 \quad (10\%)$$

### 2.2 Total Cost & Uncertainty Bounds

The baseline total estimated repair cost ($C_{\text{total}}$) is:

$$C_{\text{total}} = C_{\text{subtotal}} + C_{\text{contingency}}$$

To account for market material fluctuations and subsurface site variance, symmetric $\pm 10\%$ uncertainty bounds are established:

$$C_{\text{lower}} = C_{\text{total}} \times 0.90 \quad (-10\%)$$
$$C_{\text{upper}} = C_{\text{total}} \times 1.10 \quad (+10\%)$$

---

## 3. Synthetic Financial Disclaimer

> [!WARNING]
> **SYNTHETIC ESTIMATE DISCLAIMER**:
> All financial projections, material costs, equipment rental fees, labor rates, and water loss valuations generated by this system are synthetic engineering estimates intended solely for operational decision support, resource planning, and digital twin simulation. They do not constitute an active commercial contract, binding quote, or guaranteed municipal expenditure. Actual field procurement and labor costs must be confirmed through authorized municipal procurement channels.

