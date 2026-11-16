# Geospatial Accuracy & Clustering Audit Report (Task 11.5)

## 1. Executive Summary & Geospatial Challenge

Geospatial calculations in municipal water distribution systems must maintain mathematical accuracy over complex real-world spherical geometries. Standard planar Euclidean approximations ($\Delta x^2 + \Delta y^2$) introduce distortion, while naïve spherical formulas fail catastrophically across the 180th meridian (antimeridian wrap) and near poles.

Task 11.5 executed an independent mathematical and algorithmic audit of the **Geospatial Incident Clustering Service** (`geospatial_clustering_service.py`) and **Spatial Analysis Service** (`spatial_analysis_service.py`).

```
+-----------------------------------------------------------------------------------------+
|                               GEOSPATIAL ACCURACY AUDIT MATRIX                          |
+--------------------------+-----------------------+--------------------------------------+
| Subsystem                | Task 11 Initial State | Task 11.5 Audited & Verified State   |
+--------------------------+-----------------------+--------------------------------------+
| Longitude Wrap (±180°)   | Δλ = 359.98° (Error)  | ((Δλ + π) mod 2π) - π (222m accurate)|
| Centroid Calculation     | Simple arithmetic mean| 3D Spherical Cartesian Vector Mean   |
| Coordinate Validation    | Unchecked             | Bounds check [-90,90], [-180,180],NaN|
| Conduit Distance Metric  | Midpoint only         | Polyline vertex-to-cluster minimum   |
| Map Visualization        | SVG Schematic Only    | MapLibre WebGL Live GIS + SVG toggle |
| 10 Clustering Datasets   | Partially tested      | 10/10 automated tests passing (100%) |
+--------------------------+-----------------------+--------------------------------------+
```

---

## 2. Spherical Geodesic Mathematics & Haversine Distance

### 2.1 The Great-Circle Haversine Formula

Given two coordinates $P_1(\phi_1, \lambda_1)$ and $P_2(\phi_2, \lambda_2)$ in radians on a spherical Earth with mean volumetric radius $R = 6,371,000.0\text{ m}$:

$$\Delta\phi = \phi_2 - \phi_1$$
$$\Delta\lambda_{\text{wrapped}} = ((\lambda_2 - \lambda_1 + \pi) \pmod{2\pi}) - \pi$$

$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1) \cdot \cos(\phi_2) \cdot \sin^2\left(\frac{\Delta\lambda_{\text{wrapped}}}{2}\right)$$

$$c = 2 \cdot \operatorname{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$
$$d(P_1, P_2) = R \cdot c$$

### 2.2 Proof of Antimeridian Singularity Resolution

Consider two sensor stations placed across the 180th meridian:
- Point $A$: $(0.00^\circ\text{ N}, +179.999^\circ\text{ E})$
- Point $B$: $(0.00^\circ\text{ N}, -179.999^\circ\text{ W})$

#### Without Longitude Wrapping (Naïve Difference):
$$\Delta\lambda = -179.999^\circ - 179.999^\circ = -359.998^\circ \approx -6.28315\text{ rad}$$
$$d_{\text{naïve}} = R \cdot \pi \cdot 2 \approx 20,015,000\text{ m} \quad (\text{Halfway around the globe!})$$

#### With Antimeridian Normalization ($((\Delta\lambda + \pi) \pmod{2\pi}) - \pi$):
$$\Delta\lambda_{\text{raw}} = -359.998^\circ$$
$$\Delta\lambda_{\text{wrapped}} = +0.002^\circ \approx 0.0000349\text{ rad}$$
$$d_{\text{accurate}} = 6,371,000 \cdot 0.0000349066 = 222.38\text{ meters}$$

**Verification Test**: `test_clustering_06_antimeridian_crossing` verifies that $d(A, B) = 222.4\text{ m} \le \epsilon (350\text{ m})$, correctly clustering Point A and Point B into a single incident hotspot.

---

## 3. 3D Spherical Cartesian Centroid Averaging

### 3.1 The Failure of Planar Arithmetic Averaging

Taking the arithmetic mean of latitudes and longitudes yields catastrophic errors across the 180th meridian:
$$\lambda_{\text{mean}} = \frac{+179.9^\circ + (-179.9^\circ)}{2} = \frac{0.0^\circ}{2} = 0.0^\circ \quad (\text{Greenwich Prime Meridian!})$$
A cluster located in the Pacific Ocean is erroneously projected onto London, United Kingdom.

### 3.2 3D Spherical Cartesian Formulation

The audited service converts every coordinate $(\phi_i, \lambda_i)$ to a unit Cartesian vector on the sphere:

$$x_i = \cos(\phi_i) \cdot \cos(\lambda_i)$$
$$y_i = \cos(\phi_i) \cdot \sin(\lambda_i)$$
$$z_i = \sin(\phi_i)$$

The vector mean is computed across all $N$ member points:
$$\bar{x} = \frac{1}{N} \sum_{i=1}^N x_i, \quad \bar{y} = \frac{1}{N} \sum_{i=1}^N y_i, \quad \bar{z} = \frac{1}{N} \sum_{i=1}^N z_i$$

The true spherical centroid is recovered using standard four-quadrant arctangents:
$$\text{hyp} = \sqrt{\bar{x}^2 + \bar{y}^2}$$
$$\phi_{\text{centroid}} = \operatorname{atan2}(\bar{z}, \text{hyp})$$
$$\lambda_{\text{centroid}} = \operatorname{atan2}(\bar{y}, \bar{x})$$

**Verification Test**: `test_clustering_07_spherical_centroid_across_antimeridian` verifies:
$$\phi_{\text{centroid}} = 0.0000^\circ\text{ N}, \quad \lambda_{\text{centroid}} = \pm 180.0000^\circ\text{ (Exact)}$$

---

## 4. Density-Based Clustering (DBSCAN Parameters)

The DBSCAN algorithm operates with deterministic spatial parameters tailored to urban pipeline telemetry:
- **Spatial Reachability ($\epsilon$)**: $350.0\text{ meters}$. Represents the physical propagation distance of acoustic pressure transients in municipal distribution pipes.
- **Core Sample Threshold ($\text{MinPts}$)**: $2\text{ incidents}$. Two distinct acoustic or moisture detections within $350\text{ m}$ establish a statistically significant leak hotspot.
- **Cluster Radius**:
  $$r_{\text{cluster}} = \max\left(150.0\text{ m}, \max_{p \in \text{Cluster}} d(\text{Centroid}, p)\right)$$
- **Hotspot Intensity Index**:
  $$I = 0.50 \cdot \bar{S}_{\text{severity}} + 0.50 \cdot \min\left(1.0, \frac{N}{5.0}\right)$$

---

## 5. Verification of 10 Geographic Datasets

All 10 validation datasets pass in automated testing:

| Dataset ID | Description | Input Coordinates | Expected Outcome | Actual Result | Status |
|---|---|---|---|---|---|
| **DS-01** | Points within $\epsilon$ | $(40.7128, -74.0060)$, $(40.7146, -74.0060)$ [$\approx 200\text{m}$] | 1 Cluster ($N=2$) | 1 Cluster ($N=2$) | **PASSED** |
| **DS-02** | Points outside $\epsilon$ | $(40.7128, -74.0060)$, $(40.7218, -74.0060)$ [$\approx 1000\text{m}$] | 0 Clusters (Noise) | 0 Clusters (Noise) | **PASSED** |
| **DS-03** | Three nearby points | 3 coordinates within $150\text{ m}$ of downtown | 1 Cluster ($N=3$) | 1 Cluster ($N=3$) | **PASSED** |
| **DS-04** | Isolated noise point | 2 nearby points + 1 point $5\text{ km}$ away | 1 Cluster ($N=2$) | 1 Cluster ($N=2$, noise excluded) | **PASSED** |
| **DS-05** | Duplicate coordinates | Identical lat/lng reported by multiple sensors | 1 Cluster, $r \ge 50\text{m}$ | 1 Cluster ($N=2$) | **PASSED** |
| **DS-06** | Antimeridian crossing | $(0.0, +179.999)$, $(0.0, -179.999)$ | 1 Cluster ($N=2, d=222\text{m}$) | 1 Cluster ($N=2$) | **PASSED** |
| **DS-07** | Antimeridian centroid | $(0.0, +179.9)$, $(0.0, -179.9)$ | Centroid at $\pm 180.0^\circ$ | Centroid $\pm 180.00^\circ$ | **PASSED** |
| **DS-08** | High-latitude polar | $(89.9^\circ\text{ N}, 0.0^\circ)$, $(89.9^\circ\text{ N}, 1.0^\circ)$ | 1 Cluster ($d < 250\text{m}$) | 1 Cluster ($N=2$) | **PASSED** |
| **DS-09** | Invalid coordinates | Latitude $95.0^\circ$, `NaN`, Longitude $200.0^\circ$ | Rejected (`is_valid=False`) | `is_valid=False` for all | **PASSED** |
| **DS-10** | Empty dataset | Empty incident array `[]` | Clean `[]` without error | Empty list `[]` returned | **PASSED** |

---

## 6. Polyline-to-Cluster Geodesic Distance Evaluation

Prior to Task 11.5, conduit distance to clusters was approximated using only the segment's geographic midpoint $(\bar{\phi}, \bar{\lambda})$. For long transmission mains ($L > 2000\text{ m}$), a cluster near one endpoint was falsely estimated as being $1000\text{ m}$ away.

Task 11.5 updated `calculate_distance_to_nearest_cluster` in `spatial_analysis_service.py`:
$$d_{\text{conduit}} = \min_{v \in \text{PolylineVertices}, c \in \text{Clusters}} d_{\text{Haversine}}(v, \text{Centroid}_c)$$

This guarantees accurate proximity evaluations even for curved or elongated transmission pipelines.

---

## 7. Frontend MapLibre GIS Integration

The user interface in `InfrastructureIntelligenceView.tsx` now supports dual-mode visualization:
1. **Interactive MapLibre WebGL GIS Engine**:
   - Renders live vector basemaps (Carto Dark) with full pan, tilt, pitch, and zoom.
   - Live layer toggles: Primary/Secondary Pipelines, Pressure Zones, Incident Hotspots, and Autonomous Rover units.
   - Interactive pipeline feature selection: Clicking any pipe on the WebGL canvas dynamically opens the granular Vulnerability Deep-Dive drawer.
   - Live Cursor Coordinate HUD: Real-time latitude, longitude, and zoom feedback.
2. **Schematic Vector Canvas**:
   - High-contrast 2D architectural schematic displaying hydraulic spines, cluster radii, and rover positioning for rapid operational overview.

