# AQUA CREW — Backend Simulation Engine Specification
## Task 06: Authoritative Autonomous Kinematics & Safety Interlocks

### 1. Engine Overview

The backend simulation engine (`SimulationService` in `apps/api/app/services/simulation_service.py`) is the authoritative source of truth for the AQUA CREW virtual fleet.

- **Execution Model**: Async background event loop (`asyncio.create_task`).
- **Tick Interval**: Default $1000\text{ ms}$ (configurable via `AQUA_SIMULATION_TICK_INTERVAL_MS`).
- **Single Source of Truth**: When connected, the backend loop generates all kinematics, mission updates, and telemetry records, broadcasting them over WebSockets to client applications.

---

### 2. Autonomous Movement Algorithm

1. **Pipeline Traversal**: Every active rover is bound to a pipeline segment (`PIPE-SEC-4B-92`, `PIPE-IND-1A-04`, `PIPE-RES-3C-11`, `PIPE-HRB-02-19`, `PIPE-SEC-4A-10`).
2. **Haversine Distance**:
   $$d = 2R \cdot \text{asin}\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos\phi_1\cos\phi_2\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$
   Where $R = 6,371,000\text{ m}$.
3. **Position Interpolation**: Coordinates are interpolated along the LineString geometry:
   $$P(t) = P_{\text{start}} + t(P_{\text{end}} - P_{\text{start}}), \quad t \in [0, 1]$$
4. **Azimuth Heading**: Computed from coordinate tangents:
   $$\theta = \text{atan2}(\sin\Delta\lambda \cos\phi_2, \cos\phi_1\sin\phi_2 - \sin\phi_1\cos\phi_2\cos\Delta\lambda) \pmod{360^\circ}$$
   In `RETURNING` mode, heading is reversed by $+180^\circ$.

---

### 3. Kinematic Speeds by Operating State

- `MOVING`: Target speed $0.55\text{ m/s}$ (rapid transit).
- `INSPECTING`: Target speed $0.28\text{ m/s}$ (high-density acoustic listening).
- `RETURNING`: Target speed $0.85\text{ m/s}$ (accelerated transit to base).
- `IDLE`, `PAUSED`, `CHARGING`, `OFFLINE`, `ERROR`, `EMERGENCY_STOP`: Velocity $= 0.0\text{ m/s}$, Motor Current $= 0.0\text{ A}$.

---

### 4. Safety Interlocks

1. **Low-Battery Auto-Return**: If a rover's battery State of Charge drops to $\le 12.0\%$, the engine automatically transitions the rover to `RETURNING` and logs an interlock event.
2. **Motor Thermal Cut-Off**: If a rover's motor temperature reaches $\ge 58.0^\circ\text{C}$, the engine halts the motors ($0.0\text{ m/s}$) and transitions the rover to `PAUSED` for cool-down.
3. **Emergency Stop Halt**: When `EMERGENCY_STOP` is triggered, motor current is immediately cut to $0.0\text{ A}$ and velocity drops to $0.0\text{ m/s}$. The rover is interlocked until an administrative clear command (`RESET_ESTOP`) is signed with operator notes.

