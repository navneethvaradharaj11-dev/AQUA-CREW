# AQUA CREW — TASK 19: KNOWN LIMITATIONS & FUTURE ROADMAP
## Operational Boundaries, Environmental Assumptions & Recommended Next Steps

---

### 1. Architectural & Simulation Boundaries

1. **Air-Gapped Hardware Boundary**:
   - The platform strictly enforces `HARDWARE_ACTUATION_ENABLED = False`. Physical PLC/SCADA commands are intentionally not executed. 
   - *Roadmap*: When physical pilot deployment is authorized, an external certified IEC 62443 physical security gateway must be provisioned with dual-key hardware tokens.

2. **Synthetic Waveform Calibration**:
   - Virtual acoustic sensors generate synthetic waveforms using standard frequency spectra (800–2500 Hz).
   - *Roadmap*: Future releases will support importing field acoustic `.wav` and raw accelerometer logs directly into the simulation sandbox.

3. **In-Memory Test Database vs Multi-Region PostgreSQL**:
   - Automated regression tests execute on in-memory SQLite with hermetic rollbacks.
   - *Roadmap*: Production deployment utilizes PostgreSQL with PostGIS extension for spatial queries and TimescaleDB for high-throughput sensor telemetry.

4. **Rover Physical Terrain Limitations**:
   - Virtual rover crawls model friction and pipe slope synthetically.
   - *Roadmap*: Incorporate multi-sensor SLAM and 3D LiDAR point cloud mesh generation for complex trunk geometries.

---

### 2. Operational Recommendations

1. **Periodic Calibration Audits**:
   - Continue running automated 90-day ISO 17025 sensor calibration audits to ensure AI confidence metrics remain accurate.
2. **Mandatory Dual Human Approvals**:
   - Retain the strict separation between Operator dispatch approval and certified Municipal Engineer repair sign-off.

