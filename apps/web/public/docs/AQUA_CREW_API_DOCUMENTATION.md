# AQUA CREW — Comprehensive API Documentation
**Release:** v1.0.0-rc1  
**Base URL:** `http://localhost:8000/api/v1` (or `http://localhost/api/v1` via Gateway)  
**OpenAPI Specification:** Available interactively at `/docs` (Swagger UI) and `/redoc` (ReDoc)  

---

## 1. Authentication & Security Headers

All protected endpoints require an HTTP `Authorization` header containing an HMAC-SHA256 signed JSON Web Token (JWT):
```http
Authorization: Bearer <access_token>
```

### 1.1 Authentication Endpoints
- **`POST /api/v1/auth/login`**: Authenticate using OAuth2 Password Request Form (`username`, `password`).
  - *Response (200 OK):*
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "expires_in": 3600,
      "user": {
        "id": "u-001",
        "email": "admin@aquacrew.internal",
        "full_name": "System Administrator",
        "role": "SUPER_ADMIN"
      }
    }
    ```
- **`GET /api/v1/auth/me`**: Retrieve current authenticated user profile.

---

## 2. Unified Incident Management API

### 2.1 List & Filter Incidents
- **`GET /api/v1/incidents/`**
  - **Query Parameters:** `status` (optional), `severity` (optional), `skip` (default 0), `limit` (default 100).
  - *Response (200 OK):* Array of `UnifiedIncidentRead` objects.

### 2.2 Trigger Master 15-Step Incident Lifecycle Scenario
- **`POST /api/v1/incidents/scenarios/master-15-step`**
  - Executes the full end-to-end incident response lifecycle in a single call.
  - *Response (200 OK):*
    ```json
    {
      "scenario": "MASTER_15_STEP_E2E_ACCEPTED",
      "incident_id": "907be8c8-b19d-472d-94ae-cffcc9bb03cf",
      "incident_code": "INC-2026-001",
      "lifecycle_status": "RESOLVED",
      "total_steps_executed": 15,
      "estimated_loss_lph": 1850.0,
      "repair_cost_usd": 2450.0,
      "acoustic_confidence": 0.942,
      "twin_headloss_delta_m": 4.12
    }
    ```

### 2.3 Compile Final Incident Dossier Report
- **`GET /api/v1/incidents/{incident_id}/report`**
  - Compiles an auditable technical dossier with multi-source telemetry evidence, digital signatures, and timeline events.
  - *Response (200 OK):* Publication-grade JSON dossier report.

### 2.4 Hermetic Demonstration State Reset
- **`POST /api/v1/incidents/scenarios/demo-reset`**
  - Resets all demo scenario modifications back to baseline in < 5ms without schema drops.
  - *Response (200 OK):*
    ```json
    {
      "status": "DEMO_SCENARIOS_RESET_SUCCESSFUL",
      "timestamp": "2026-11-16T15:34:02Z",
      "cleared_scenario_incidents": 1,
      "reset_baseline_incidents": 4,
      "reset_rovers": 5
    }
    ```

---

## 3. Acoustic AI & Leak Detection API

- **`POST /api/v1/leak-detection/analyze`**: Extract acoustic spectral features and estimate leak probability.
  - *Request Body:*
    ```json
    {
      "pipeline_id": "p-001",
      "acoustic_samples": [0.012, 0.045, -0.021, 0.089, -0.054],
      "sampling_rate_hz": 44100
    }
    ```
  - *Response (200 OK):* Leak probability ($P(\text{leak})$), dominant frequency (Hz), spectral centroid, and estimated flow loss.

- **`POST /api/v1/leak-detection/cross-correlate`**: Compute Time Delay of Arrival ($\Delta t$) between two boundary hydrophone transducers.

---

## 4. Hydraulic Digital Twin API

- **`POST /api/v1/digital-twin/simulate`**: Execute Todini GGA hydraulic network balance.
  - *Request Body:* Network configuration and boundary conditions (tank levels, pump speeds).
  - *Response (200 OK):* Nodal pressure vector ($\mathbf{P}$), pipe flow velocities ($\mathbf{V}$), and headloss distribution ($\Delta \mathbf{H}$).
- **`POST /api/v1/digital-twin/burst-scenario`**: Simulate sudden pipe rupture and consumer pressure deficits.
- **`GET /api/v1/digital-twin/network-graph`**: Return GIS-compatible EPANET network topological graph.

---

## 5. Fleet & Autonomous Inspection API

- **`GET /api/v1/fleet/rovers/`**: Fetch telemetry and operational state for all 5 robotic rovers.
- **`POST /api/v1/inspection/dispatch`**: Autonomously dispatch optimal rover based on battery SoC, distance, and pipe velocity.
  - *Request Body:*
    ```json
    {
      "pipeline_id": "p-001",
      "target_distance_m": 120.0,
      "priority": "HIGH"
    }
    ```

---

## 6. Repair Planning & Management API

- **`POST /api/v1/repair-management/plans`**: Synthesize repair plan, bill of materials, and safety requirements.
- **`POST /api/v1/repair-management/verify`**: Dual-stage post-repair sign-off (acoustic listen + pressure hold).

---

## 7. IoT Device Registry & Telemetry API

- **`GET /api/v1/iot/devices`**: List registered edge transducers.
- **`POST /api/v1/iot/devices/{id}/calibrate`**: Apply 2-point calibration offsets and thermal drift polynomial coefficients.
- **`POST /api/v1/iot/telemetry/ingest`**: Ingest high-frequency pressure and acoustic packets (mean latency 0.007 ms).

---

## 8. WebSocket Real-Time Event Hub

- **Endpoint:** `ws://localhost:8000/ws/telemetry`
- **Supported Channels:**
  - `telemetry.pressure`: Real-time transducer readings.
  - `telemetry.rover`: Real-time rover coordinate and battery updates.
  - `incidents.lifecycle`: State transitions across the 15-step incident pipeline.

