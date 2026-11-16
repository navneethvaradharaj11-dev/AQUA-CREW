# AQUA CREW — Database Schema Specification
## Task 06: Relational & Geospatial Data Architecture

### 1. Database Strategy: SQLite (Dev) to PostGIS (Production)

The AQUA CREW platform implements an environment-adaptive persistence architecture:
- **Local Development & Automated Testing**: SQLite (`sqlite:///./aqua_crew_dev.db`) managed via SQLAlchemy 2.x and Alembic. Requires zero external database server setup.
- **Production Metropolitan Deployment**: PostgreSQL 16+ with PostGIS 3.4+. Geometry columns (`GEOMETRY(LINESTRING, 4326)` for pipelines, `GEOMETRY(POINT, 4326)` for rover coordinates and sensors) provide high-performance spatial indexing (`GIST`) and topological queries.

---

### 2. Entity Relationship Diagram (ERD)

```
┌────────────────────────┐         ┌─────────────────────────┐
│     pipeline_segments  │         │         missions        │
├────────────────────────┤         ├─────────────────────────┤
│ id (PK)                │         │ id (PK)                 │
│ name                   │◄────┐   │ assigned_rover_id       │◄───┐
│ category               │     │   │ mission_type            │    │
│ length_m               │     │   │ progress_percentage     │    │
│ coordinates_json       │     │   │ status                  │    │
└────────────────────────┘     │   │ target_segment_id (FK)──┼────┘
                               │   └─────────────────────────┘
                               │
┌────────────────────────┐     │   ┌─────────────────────────┐
│         rovers         │     │   │    state_transitions    │
├────────────────────────┤     │   ├─────────────────────────┤
│ id (PK)                │     │   │ id (PK)                 │
│ name                   │     │   │ rover_id (FK)───────────┼────┐
│ status                 │     │   │ previous_state          │    │
│ operating_state        │     │   │ new_state               │    │
│ battery_percentage     │     │   │ timestamp               │    │
│ pipe_segment_id (FK)───┼─────┘   │ reason                  │    │
│ latitude, longitude    │         └─────────────────────────┘    │
└────────────────────────┘                                        │
           │                                                      │
           │ 1:N                                                  │
           ▼                                                      ▼
┌────────────────────────┐         ┌─────────────────────────┐
│   telemetry_records    │         │       audit_events      │
├────────────────────────┤         ├─────────────────────────┤
│ id (PK, AutoIncrement) │         │ id (PK)                 │
│ rover_id (FK)          │         │ event_type              │
│ timestamp              │         │ rover_id (FK)           │
│ latitude, longitude    │         │ mission_id (FK)         │
│ velocity_mps           │         │ details                 │
│ battery_pct            │         │ timestamp               │
│ motor_temp_c           │         └─────────────────────────┘
└────────────────────────┘
```

---

### 3. Table Schemas & Indexing

#### 3.1 `rovers`
Authoritative virtual rover fleet registry.
- `id` (VARCHAR(64), PK): Unique rover identifier (e.g. `ROV-AQUA-01`).
- `name` (VARCHAR(128)): Human-readable rover name (e.g. `Triton-1 Crawler`).
- `model` (VARCHAR(128)): Hardware model classification.
- `status` (VARCHAR(32), INDEX): Operational status (`ONLINE`, `ACTIVE`, `IDLE`, `WARNING`, `OFFLINE`).
- `operating_state` (VARCHAR(32), INDEX): State machine (`IDLE`, `MOVING`, `INSPECTING`, `PAUSED`, `RETURNING`, `CHARGING`, `OFFLINE`, `ERROR`, `EMERGENCY_STOP`).
- `connection_status` (VARCHAR(32)): Connectivity status (`ONLINE`, `DEGRADED`, `OFFLINE`).
- `battery_percentage` (FLOAT): Battery State of Charge ($0.0\dots100.0\%$).
- `distance_travelled_km` (FLOAT): Monotonically accumulating inspection distance.
- `assigned_mission_id` (VARCHAR(64), NULLABLE, INDEX): Currently assigned active mission.
- `pipe_segment_id` (VARCHAR(64), INDEX): Currently occupied pipeline segment.
- `latitude` (FLOAT): WGS84 Latitude.
- `longitude` (FLOAT): WGS84 Longitude.
- `velocity_mps` (FLOAT): Kinematic speed ($0.0\dots1.5\text{ m/s}$).
- `heading_deg` (FLOAT): Direction azimuth ($0.0^\circ\dots360.0^\circ$).
- `motor_temp_c` (FLOAT): Motor temperature.
- `internal_temp_c` (FLOAT): Internal ambient enclosure temperature.
- `signal_rssi_dbm` (FLOAT): RF telemetry signal strength.
- `acoustic_spl_db` (FLOAT): Payload acoustic noise reading.
- `dominant_freq_hz` (FLOAT): Frequency peak.
- `ground_moisture_pct` (FLOAT): Ground moisture percentage.
- `last_heartbeat` (TIMESTAMPTZ): Heartbeat timestamp in UTC.
- `is_simulated` (BOOLEAN): Simulation provenance flag (`TRUE`).

#### 3.2 `missions`
Inspection and intercept mission orders.
- `id` (VARCHAR(64), PK): Unique mission identifier (e.g. `MSN-2026-042`).
- `assigned_rover_id` (VARCHAR(64), NULLABLE, INDEX): Assigned rover.
- `mission_type` (VARCHAR(128)): Classification (`Acoustic Pipe Survey`, `Pressure Transient Test`, `Emergency Intercept`).
- `progress_percentage` (INTEGER): Mission route completion ($0\dots100\%$).
- `status` (VARCHAR(32), INDEX): Lifecycle status (`In Progress`, `Scheduled`, `Paused`, `Completed`, `Cancelled`).
- `target_segment_id` (VARCHAR(64), INDEX): Pipeline segment targeted.
- `waypoint_count` (INTEGER): Total route waypoints.
- `completed_waypoints` (INTEGER): Completed waypoints.
- `created_at` (TIMESTAMPTZ): Created timestamp in UTC.
- `updated_at` (TIMESTAMPTZ): Updated timestamp in UTC.

#### 3.3 `pipeline_segments`
Underground pipeline network geometry.
- `id` (VARCHAR(64), PK): Unique segment identifier (e.g. `PIPE-SEC-4B-92`).
- `name` (VARCHAR(256)): Segment display name.
- `category` (VARCHAR(64), INDEX): Tier (`primary`, `secondary`, `distribution`, `service`).
- `material` (VARCHAR(128)): Pipe material (Ductile Iron, Steel, HDPE, PVC).
- `diameter_mm` (INTEGER): Internal diameter.
- `length_m` (FLOAT): Total linear length.
- `coordinates_json` (TEXT): GeoJSON LineString coordinates array (`[[lon, lat], ...]`). In production, represented as `GEOMETRY(LINESTRING, 4326)`.

#### 3.4 `telemetry_records`
Time-series telemetry archive for analytics and playback.
- `id` (BIGINT, PK, AUTOINCREMENT)
- `rover_id` (VARCHAR(64), INDEX)
- `timestamp` (TIMESTAMPTZ, INDEX): Telemetry sample time in UTC.
- `latitude`, `longitude` (FLOAT)
- `velocity_mps`, `heading_deg` (FLOAT)
- `battery_pct`, `motor_temp_c`, `internal_temp_c` (FLOAT)
- `acoustic_spl_db`, `dominant_freq_hz`, `ground_moisture_pct` (FLOAT)
- `operating_state` (VARCHAR(32))

#### 3.5 `state_transitions`
Audit log of all autonomous rover state transitions.
- `id` (VARCHAR(64), PK): Unique transition ID (`TR-xxxx`).
- `rover_id` (VARCHAR(64), INDEX)
- `previous_state` (VARCHAR(32))
- `new_state` (VARCHAR(32))
- `timestamp` (TIMESTAMPTZ, INDEX)
- `reason` (VARCHAR(512))
- `triggered_by` (VARCHAR(64)): `OPERATOR`, `SAFETY_INTERLOCK`, `AUTONOMOUS_CONTROLLER`.

#### 3.6 `audit_events`
General system and mission event trail.
- `id` (VARCHAR(64), PK): Unique event ID (`EV-xxxx`).
- `event_type` (VARCHAR(64), INDEX)
- `rover_id` (VARCHAR(64), NULLABLE, INDEX)
- `mission_id` (VARCHAR(64), NULLABLE, INDEX)
- `details` (VARCHAR(1024))
- `timestamp` (TIMESTAMPTZ, INDEX)

---

### 4. Database Migrations with Alembic

Migrations are managed through Alembic:
```bash
# Generate revision from models
alembic revision --autogenerate -m "Migration description"

# Apply pending revisions
alembic upgrade head

# Rollback last revision
alembic downgrade -1
```

