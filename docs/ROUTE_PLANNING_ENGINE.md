# AQUA CREW — Pipeline Network Routing Engine Specification
**Task 08 Technical Documentation — Topological Pathfinding & Waypoint Synthesis**

## 1. Architectural Overview

The **Pipeline Network Routing Engine** (`apps/api/app/services/pipeline_routing_service.py`) provides mathematically rigorous, graph-constrained navigation for virtual autonomous rovers across the metropolitan water pipeline infrastructure.

Unlike surface vehicles or aerial drones, pipeline inspection rovers are mechanically constrained to traverse within underground conduits. Direct straight-line Euclidean shortcuts are physically impossible and strictly disallowed by the system.

```
 [Rover Origin]
       │ (Nearest Pipe Entry Projection)
       ▼
  [Vertex V_a] ──(Edge E_1)── [Junction V_b] ──(Edge E_2)── [Junction V_c]
                                                                    │
                                                            (Edge E_3)
                                                                    │
                                                                    ▼
                                                            [Target Leak V_dest]
```

---

## 2. Mathematical Graph Formulation

The pipeline infrastructure is modeled as an undirected weighted topological multigraph:
\[
G = (V, E, W)
\]
where:
- **$V$ (Vertices / Nodes)**: Set of discrete pipeline junctions, endpoints, valve manifolds, and pump stations.
- **$E$ (Edges / Conduits)**: Set of physical pipe segments linking vertices. Each edge $e = (u, v)$ encapsulates underlying geometry as an ordered list of coordinate pairs $[(\text{lon}_1, \text{lat}_1), \dots, (\text{lon}_k, \text{lat}_k)]$.
- **$W(e)$ (Traversal Cost Weight)**: Scalar edge traversal cost derived from physical arc distance, conduit diameter, material resistance, and flow directionality.

### 2.1 Coordinate Quantization & Vertex Snapping
To bridge floating-point GPS coordinate discrepancies between adjacent pipeline segment endpoints in GeoJSON definitions, coordinates are normalized via precision-bounded quantization:
\[
\text{hash}(u) = \big(\text{round}(\text{lon}, 4),\, \text{round}(\text{lat}, 4)\big)
\]
A 4-decimal precision threshold corresponds to $\approx 11.1\text{ m}$ at the equator, ensuring that interconnected pipeline segments cleanly snap together at physical junctions (e.g., Spine Trunk A and Trunk Line B intersection at `[-74.0060, 40.7128]`).

---

## 3. Distance Metrics & Shortest Path Algorithm

### 3.1 Haversine Great-Circle Arc Distance
For any pair of spherical coordinates $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$ in radians, the geodesic distance $d$ across the Earth's mean radius ($R = 6,371,000\text{ m}$) is calculated via:
\[
a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)
\]
\[
c = 2 \cdot \arctan2\left(\sqrt{a}, \sqrt{1 - a}\right)
\]
\[
d = R \cdot c
\]

Segment total length $L(e)$ is computed by summing the successive Haversine distances along all internal polyline vertices:
\[
L(e) = \sum_{i=1}^{k-1} d(p_i, p_{i+1})
\]

### 3.2 Dijkstra Pathfinding Implementation
The routing engine employs Dijkstra's priority-queue algorithm with min-heap complexity $\mathcal{O}((|E| + |V|)\log |V|)$:

1. **Projection**: Find the closest pipeline vertex $v_{\text{start}} \in V$ to the rover's current coordinates $(\text{rover}_{\text{lat}}, \text{rover}_{\text{lng}})$.
2. **Target Resolution**: Find the closest vertex $v_{\text{dest}} \in V$ on the target pipeline segment containing the AI leak detection coordinates $(\text{leak}_{\text{lat}}, \text{leak}_{\text{lng}})$.
3. **Exploration**: Maintain tentative distance map $D[v]$ initialized to $\infty$, $D[v_{\text{start}}] = 0$.
4. **Relaxation**: For the current node $u$ with minimum distance, evaluate each adjacent neighbor $v$ connected via edge $e$:
   \[
   \text{If } D[u] + W(e) < D[v] \implies D[v] = D[u] + W(e),\quad \text{predecessor}[v] = u
   \]
5. **Backtracking**: Reconstruct the optimal sequence of traversed vertices and pipeline segments from $v_{\text{dest}}$ back to $v_{\text{start}}$.

---

## 4. Waypoint Generation & Uncertainty Buffer

When a path is resolved:
1. **Polyline Waypoint Sequence**: All intermediate geometry coordinates along the traversed segments are concatenated in sequence, matching the direction of travel.
2. **Estimated Travel Time**:
   \[
   T_{\text{travel}} = \frac{D_{\text{route}}}{v_{\text{cruise}}}
   \]
   where $v_{\text{cruise}} = 0.8\text{ m/s}$ (simulated nominal crawling speed in subterranean pipelines).
3. **Localization Uncertainty Buffer**: AI leak detections carry a spatial uncertainty radius $r_{\text{uncertainty}}$ (typically $10\text{ m}$ to $50\text{ m}$). The router retains this buffer to designate the target inspection zone for slow-speed acoustic sensor sweeping.

---

## 5. Disconnected Network & Routing Failure Handling

If $v_{\text{dest}}$ is unreachable from $v_{\text{start}}$ (e.g., isolated hydraulic distribution sector or severed pipe barrier):
- The algorithm detects `D[v_{\text{dest}}] == \infty`.
- The engine **refuses to construct a straight-line shortcut**.
- It returns an explicit routing failure object:
  ```json
  {
    "is_connected": false,
    "total_distance_m": 0.0,
    "waypoints": [],
    "segments_traversed": [],
    "error": "No connected pipeline topology exists between rover start position and target segment"
  }
  ```
- This triggers an operator alert recommending manual rover crane redeployment or selecting an alternate rover stationed within the isolated sector.

---

## 6. Simulation Provenance

All pipeline routing calculations are executed using virtual vector geometry. Every routing response carries:
- `is_simulated: true`
- `source: "VIRTUAL_SIMULATION_ENGINE"`

