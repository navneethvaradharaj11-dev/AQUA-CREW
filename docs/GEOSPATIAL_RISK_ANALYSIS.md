# AQUA CREW — Geospatial Risk Analysis Specification
## Density-Based Spatial Clustering, Geodesic Distance Metrics & Zone Analysis (Task 11)

```
========================================================================================
AQUA CREW PLATFORM — GEOSPATIAL RISK ANALYSIS & HOTSPOT CLUSTERING
Document ID: AC-T11-GEO-2026-V1
Classification: Municipal Spatial Hydrology & Geodesic Clustering Specification
Simulation Mode: Software-Only Virtual Infrastructure Simulation
Provenance: VIRTUAL_SIMULATION_ENGINE (is_simulated: true)
========================================================================================
```

---

## 1. Overview & Purpose

Metropolitan water infrastructure failures do not occur uniformly at random across a city. Physical pipe ruptures, joint dislocations, and acoustic anomalies exhibit pronounced spatial clustering driven by common environmental factors:
- Subsurface geotechnical movement and variable soil moisture.
- Localized hydraulic pressure surges at dead-ends and pressure zone boundaries.
- Corrosive ground conditions (e.g. saline marine groundwater near coastal terminals).
- Historical manufacturing batches of vulnerable conduit materials (e.g. unlined cast iron laid in the 1950s).

The **Geospatial Risk Analysis Module** applies density-based spatial clustering (DBSCAN) to identify incident hotspots, aggregates network vulnerability across operational geographic zones, and generates weighted heatmap surfaces for real-time GIS rendering.

---

## 2. Geodesic Distance Computation: The Haversine Metric

Because municipal water grids span tens of square kilometers across spherical planetary coordinates, planar Euclidean distance introduces unacceptable latitude-dependent distortion. The AQUA CREW engine strictly employs the **Haversine great-circle distance**:

$$\Delta\phi = \phi_2 - \phi_1, \quad \Delta\lambda = \lambda_2 - \lambda_1$$
$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)$$
$$c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)$$
$$d(\mathbf{p}_1, \mathbf{p}_2) = R \cdot c$$

Where:
- $\phi_1, \phi_2$ are latitudes in radians.
- $\lambda_1, \lambda_2$ are longitudes in radians.
- $R = 6,371,000.0\text{ meters}$ (WGS-84 mean volumetric Earth radius).

---

## 3. Density-Based Spatial Clustering (DBSCAN) Methodology

### 3.1. Algorithmic Parameterization

The clustering engine groups incident points $P = \{\mathbf{p}_1, \mathbf{p}_2, \dots, \mathbf{p}_n\}$ into coherent geographic clusters based on two hyperparameters:

1. **Neighborhood Radius ($\epsilon$)**:
   $$\epsilon = 350.0\text{ meters}$$
   Represents the physical dissipation radius within which pipe bursts share common hydraulic transients or geotechnical ground conditions.

2. **Core Sample Threshold ($\text{MinPts}$)**:
   $$\text{MinPts} = 2\text{ incidents}$$
   Two or more spatially proximate AI leak alerts constitute an operational incident cluster. Standalone critical incidents with severity $\ge 0.70$ are preserved as single-incident micro-hotspots to prevent omission from operator queues.

### 3.2. Cluster Metrics Formulation

For each identified cluster $C_k = \{\mathbf{p}_i \mid \mathbf{p}_i \in C_k\}$ containing $N_k$ points:

#### 1. Cluster Centroid $(\bar{\phi}_k, \bar{\lambda}_k)$:
$$\bar{\phi}_k = \frac{1}{N_k} \sum_{i=1}^{N_k} \phi_i, \quad \bar{\lambda}_k = \frac{1}{N_k} \sum_{i=1}^{N_k} \lambda_i$$

#### 2. Dynamic Cluster Radius ($r_k$):
$$r_k = \max\left(150.0, \max_{i} d((\bar{\phi}_k, \bar{\lambda}_k), (\phi_i, \lambda_i))\right)$$
A minimum floor of $150.0\text{ meters}$ ensures that spatial uncertainty and acoustic localization error margins are encapsulated.

#### 3. Hotspot Intensity ($I_k \in [0.0, 1.0]$):
$$I_k = 0.50 \cdot \bar{S}_k + 0.50 \cdot \min\left(1.0, \frac{N_k}{5.0}\right)$$
Where $\bar{S}_k = \frac{1}{N_k} \sum_{i=1}^{N_k} \text{severity}_i$.

#### 4. Cluster Risk Tier:
$$\text{RiskLevel}(C_k) = \begin{cases}
\text{CRITICAL} & I_k \ge 0.75 \text{ or } N_k \ge 3 \\
\text{HIGH} & I_k \ge 0.55 \text{ or } N_k \ge 2 \\
\text{MODERATE} & I_k \ge 0.35 \\
\text{LOW} & I_k < 0.35
\end{cases}$$

---

## 4. Operational Geographic Risk Zones

To support municipal operations, pipeline segments are partitioned into discrete geographic zones corresponding to pressure boundaries and urban land-use:

```
+--------------------------------------------------------------------------------------------------+
| ZONE ID   | ZONE NAME                              | NOMINAL PSI | CHARACTERISTICS               |
+--------------------------------------------------------------------------------------------------+
| ZONE-PZ01 | Metro Central High-Pressure Corridor   | 65.0 psi    | Downtown commercial arterial  |
| ZONE-PZ02 | Eastern Industrial Sector              | 60.0 psi    | Heavy industrial demand       |
| ZONE-PZ03 | Northern Residential Zone              | 52.0 psi    | Diurnal residential peaking   |
| ZONE-PZ04 | Harbor Utility Terminal                | 58.0 psi    | Coastal, saline groundwater   |
+--------------------------------------------------------------------------------------------------+
```

### Zone Aggregation Metrics:
For each zone $Z$, the engine aggregates:
- **Total Conduit Length**: $L_Z = \sum_{s \in Z} \frac{\text{length}(s)}{1000.0}\text{ km}$.
- **Average Vulnerability Index**: $\bar{V}_Z = \frac{1}{|Z|} \sum_{s \in Z} V(s)$.
- **Critical Asset Concentration**: $N_{\text{crit}} = \sum_{s \in Z} \mathbb{I}(V(s) \ge 80.0)$.
- **Active Hotspot Count**: Total incident clusters intersecting pipelines within zone $Z$.

---

## 5. Heatmap Generation & GIS Surface Interpolation

To visualize continuous spatial risk on the Command Center map without discrete gaps, the `SpatialAnalysisService` generates high-resolution weighted coordinate sets:

1. **Pipeline Vertices**: Coordinates along each pipeline geometry are sampled and assigned weights $w = \frac{V(s)}{100.0}$.
2. **Cluster Centroids**: Cluster centroids are injected with amplified weights $w_c = \min(1.0, I_k \cdot 1.2)$ with point type `CLUSTER_HOTSPOT`.
3. **Frontend Presentation**: The web GIS rendering layer consumes this normalized array `[{lat, lng, weight, segment_id, risk_level, score}]` to render high-contrast radial density gradients.

