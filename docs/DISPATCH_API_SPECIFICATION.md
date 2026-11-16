# AQUA CREW — Autonomous Mission Planning & Rover Dispatch API Specification
**Task 08 Technical Documentation — REST API Contracts & WebSocket Events**

## 1. Overview

This document specifies the REST API contracts and WebSocket event streams introduced in **Task 08 — Autonomous Mission Planning & Intelligent Rover Dispatch System**.

All endpoints are hosted under the versioned base path:
`http://localhost:8000/api/v1`

All responses are serialized in JSON format and include explicit simulation provenance fields:
```json
{
  "is_simulated": true,
  "source": "VIRTUAL_SIMULATION_ENGINE"
}
```

---

## 2. Mission Planning & Recommendation Endpoints

### 2.1 Generate Mission Recommendation
- **Endpoint**: `POST /api/v1/missions/plan`
- **Description**: Generates an explainable mission recommendation for a given AI leak detection. Performs priority scoring, shortest-path pipeline routing, and battery feasibility checks.
- **Request Body**:
  ```json
  {
    "detection_id": "ai-det-sp-01"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "id": "rec-f82b7c41",
    "detection_id": "ai-det-sp-01",
    "pipeline_segment_id": "pipe-seg-spine-01",
    "recommended_rover_id": "rover-01",
    "recommended_rover_name": "HydroScout Alpha",
    "priority_score": 100.0,
    "priority_category": "CRITICAL",
    "status": "PENDING_APPROVAL",
    "route_distance_m": 724.5,
    "estimated_duration_s": 905.6,
    "estimated_energy_pct": 2.8,
    "battery_reserve_after_pct": 89.2,
    "destination_lat": 40.7135,
    "destination_lng": -74.0055,
    "localization_uncertainty_m": 15.0,
    "waypoints": [
      [-74.0060, 40.7128],
      [-74.0055, 40.7135]
    ],
    "segments_traversed": ["pipe-seg-spine-01"],
    "contributing_factors": {
      "risk_score": 35.0,
      "classification_score": 25.0,
      "water_loss_score": 20.0,
      "criticality_score": 12.0,
      "pressure_score": 8.0
    },
    "explanation": "Critical priority: Severe acoustic emissions and rapid pressure drop on arterial trunk main.",
    "is_simulated": true,
    "source": "VIRTUAL_SIMULATION_ENGINE"
  }
  ```

---

### 2.2 List Mission Recommendations
- **Endpoint**: `GET /api/v1/missions/recommendations`
- **Query Parameters**:
  - `priority` (string, optional): Filter by `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`.
  - `status` (string, optional): Filter by `PENDING_APPROVAL`, `APPROVED`, `REJECTED`, `CANCELLED`.
  - `limit` (integer, default: 50): Maximum items to return.
- **Response (200 OK)**: Array of `MissionRecommendation` objects.

---

### 2.3 Inspect Recommendation
- **Endpoint**: `GET /api/v1/missions/recommendations/{id}`
- **Response (200 OK)**: Full `MissionRecommendation` object.
- **Error (404 Not Found)**: If recommendation ID does not exist.

---

### 2.4 Approve Mission Recommendation
- **Endpoint**: `POST /api/v1/missions/recommendations/{id}/approve`
- **Description**: Operator approval gate. Transitions recommendation status to `APPROVED`, creates formal `MissionModel` record, transitions the recommended rover to `INSPECTING`, and initializes route telemetry.
- **Request Body**:
  ```json
  {
    "operator_id": "operator-nav",
    "operator_notes": "Acoustic signatures cross-verified against trunk pressure telemetry. Dispatch approved."
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "recommendation_id": "rec-f82b7c41",
    "status": "APPROVED",
    "assigned_mission_id": "msn-3e819b12",
    "assigned_rover_id": "rover-01",
    "approved_by": "operator-nav",
    "approved_at": "2026-11-15T23:30:00Z",
    "is_simulated": true,
    "source": "VIRTUAL_SIMULATION_ENGINE"
  }
  ```

---

### 2.5 Reject Mission Recommendation
- **Endpoint**: `POST /api/v1/missions/recommendations/{id}/reject`
- **Description**: Operator rejection gate. Transitions recommendation to `REJECTED`. Rejection reason is mandatory for auditable compliance.
- **Request Body**:
  ```json
  {
    "rejection_reason": "Scheduled trunk maintenance already in progress by field technicians.",
    "operator_notes": "Bypassing autonomous inspection per work order WO-4412."
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "recommendation_id": "rec-f82b7c41",
    "status": "REJECTED",
    "rejection_reason": "Scheduled trunk maintenance already in progress by field technicians.",
    "is_simulated": true
  }
  ```

---

### 2.6 Recalculate Recommendation
- **Endpoint**: `POST /api/v1/missions/recommendations/{id}/recalculate`
- **Description**: Re-evaluates routing, rover availability, and battery feasibility with real-time fleet coordinates and telemetric state.
- **Response (200 OK)**: Updated `MissionRecommendation` object.

---

## 3. Mission Execution & Tracking Endpoints

### 3.1 Get Mission Route
- **Endpoint**: `GET /api/v1/missions/{id}/route`
- **Description**: Returns the topological polyline waypoints, total route distance, and target segment for an active or completed mission.
- **Response (200 OK)**:
  ```json
  {
    "mission_id": "msn-3e819b12",
    "target_segment_id": "pipe-seg-spine-01",
    "assigned_rover_id": "rover-01",
    "route_distance_m": 724.5,
    "waypoint_count": 8,
    "waypoints": [
      [-74.0060, 40.7128],
      [-74.0055, 40.7135]
    ],
    "is_simulated": true
  }
  ```

---

### 3.2 Get Mission Progress
- **Endpoint**: `GET /api/v1/missions/{id}/progress`
- **Description**: Returns live progress percentage, inspected meters, completed waypoints, and estimated time to completion.
- **Response (200 OK)**:
  ```json
  {
    "mission_id": "msn-3e819b12",
    "status": "IN_PROGRESS",
    "progress_percentage": 42.5,
    "inspected_distance_m": 307.9,
    "total_distance_m": 724.5,
    "completed_waypoints": 3,
    "total_waypoints": 8,
    "start_time": "2026-11-15T23:30:15Z",
    "estimated_completion_time": "2026-11-15T23:45:20Z",
    "is_simulated": true
  }
  ```

---

### 3.3 Get Mission Audit Events
- **Endpoint**: `GET /api/v1/missions/{id}/events`
- **Description**: Returns all lifecycle and telemetry audit events logged for the specified mission.

---

## 4. Rover Dispatch Evaluation Endpoints

### 4.1 Evaluate Eligible Rovers
- **Endpoint**: `GET /api/v1/dispatch/eligible-rovers`
- **Query Parameters**:
  - `target_segment_id` (string, optional)
  - `target_lat` (float, optional)
  - `target_lng` (float, optional)
- **Response (200 OK)**: Array of `RoverSuitability` objects including battery reserve projections, distance, and disqualification reasons.

---

### 4.2 Evaluate Mission Priority
- **Endpoint**: `POST /api/v1/dispatch/evaluate`
- **Request Body**: Accepts raw or partial leak telemetry to calculate explainable priority score ($0-100$).

---

## 5. WebSocket Event Stream

The WebSocket endpoint `ws://localhost:8000/ws` broadcasts the following Task 08 events in real time:

| Event Type | Payload Attributes | Trigger Condition |
| :--- | :--- | :--- |
| `MISSION_RECOMMENDED` | `recommendation_id`, `priority_category`, `recommended_rover_id`, `route_distance_m` | Emitted when AI detection is converted to mission proposal |
| `MISSION_APPROVED` | `recommendation_id`, `mission_id`, `assigned_rover_id`, `approved_by` | Emitted when human operator verifies and approves dispatch |
| `MISSION_REJECTED` | `recommendation_id`, `rejection_reason` | Emitted when operator dismisses recommendation |
| `MISSION_STARTED` | `mission_id`, `rover_id`, `route_distance_m` | Emitted when virtual rover initiates trajectory crawl |
| `MISSION_PROGRESS` | `mission_id`, `progress_percentage`, `inspected_distance_m`, `battery_percentage` | Emitted every 1-second simulation tick during traversal |
| `MISSION_COMPLETED` | `mission_id`, `inspected_distance_m`, `duration_s` | Emitted when rover reaches destination inspection zone |

