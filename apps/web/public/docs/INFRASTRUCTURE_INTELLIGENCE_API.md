# AQUA CREW — Infrastructure Intelligence REST API Specification
## Comprehensive Endpoint Reference & Schema Definitions (Task 11)

```
========================================================================================
AQUA CREW PLATFORM — REST API SPECIFICATION: INFRASTRUCTURE INTELLIGENCE
Document ID: AC-T11-API-2026-V1
Base URL: /api/v1/infrastructure-intelligence
Classification: Backend OpenAPI 3.1 & Pydantic Schema Reference
Simulation Mode: Software-Only Virtual Infrastructure Simulation
Provenance: VIRTUAL_SIMULATION_ENGINE (is_simulated: true)
========================================================================================
```

---

## 1. Overview

The Infrastructure Intelligence API provides unified, programmatic access to pipeline vulnerability profiles, spatial incident clustering, operational geographic zones, temporal deterioration velocity, multi-horizon forecasts, and prioritized inspection dispatch queues.

All responses adhere to strict JSON contracts, include simulation provenance flags (`is_simulated: true`, `source: "VIRTUAL_SIMULATION_ENGINE"`), and support OpenAPI 3.1 specifications.

---

## 2. Endpoint Summary Table

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/overview` | High-level executive intelligence summary for dashboard cards. |
| `POST` | `/assess` | Triggers complete recalculation of the intelligence pipeline. |
| `GET` | `/segments` | Paginated list of pipeline vulnerability profiles with filtering. |
| `GET` | `/segments/{segment_id}` | Granular 4-factor deep-dive profile for a specific conduit. |
| `GET` | `/risk-assessments` | Multi-horizon risk assessments and primary drivers. |
| `GET` | `/heatmap` | Weighted coordinate array for GIS heatmap rendering. |
| `GET` | `/clusters` | Active DBSCAN incident clusters with centroids and radii. |
| `GET` | `/zones` | Operational geographic risk zones and aggregated metrics. |
| `GET` | `/trends` | Temporal deterioration velocity and 24h/7d/30d deltas. |
| `GET` | `/predictions` | Multi-horizon future risk projections. |
| `GET` | `/inspection-priorities` | Ranked inspection queue with status filtering. |
| `POST` | `/inspection-priorities/{id}/acknowledge` | Operator acknowledges an inspection target. |
| `POST` | `/inspection-priorities/{id}/dismiss` | Operator dismisses an inspection target with justification. |
| `POST` | `/inspection-priorities/{id}/request-inspection` | Generates autonomous rover inspection mission recommendation. |

---

## 3. Granular Endpoint Specifications

### 3.1. Executive Overview
`GET /api/v1/infrastructure-intelligence/overview`

#### Response `200 OK`:
```json
{
  "total_segments_analyzed": 5,
  "critical_segments_count": 1,
  "high_risk_segments_count": 1,
  "moderate_risk_segments_count": 2,
  "low_risk_segments_count": 1,
  "average_network_vulnerability": 54.2,
  "network_deterioration_rate": 0.16,
  "deteriorating_segments_count": 2,
  "active_clusters_count": 2,
  "pending_inspections_count": 3,
  "highest_risk_segment": {
    "id": "PIPE-SEC-4B-92",
    "name": "Metro Central Main Trunk Line B",
    "score": 84.5,
    "level": "CRITICAL",
    "material": "Ductile Iron (Class 54)"
  },
  "highest_risk_zone": {
    "code": "ZONE-PZ01",
    "name": "Metro Central High-Pressure Corridor",
    "avg_score": 68.2,
    "critical_count": 1
  },
  "last_updated": "2026-11-16T09:30:00Z",
  "is_simulated": true,
  "source": "VIRTUAL_SIMULATION_ENGINE"
}
```

---

### 3.2. List Vulnerability Profiles
`GET /api/v1/infrastructure-intelligence/segments`

#### Query Parameters:
- `risk_level` (string, optional): `VERY_LOW`, `LOW`, `MODERATE`, `HIGH`, `CRITICAL`
- `zone` (string, optional): e.g. `PZ-01`
- `trend` (string, optional): `DETERIORATING`, `STABLE`, `IMPROVING`
- `limit` (int, default: 50, max: 100)
- `offset` (int, default: 0)

#### Response `200 OK`:
```json
{
  "total": 5,
  "limit": 50,
  "offset": 0,
  "items": [
    {
      "id": "vuln_PIPE-SEC-4B-92",
      "pipeline_segment_id": "PIPE-SEC-4B-92",
      "segment_name": "Metro Central Main Trunk Line B",
      "material": "Ductile Iron (Class 54)",
      "diameter_mm": 600,
      "length_m": 1850.0,
      "pressure_zone_id": "PZ-01",
      "category": "primary",
      "vulnerability_score": 84.5,
      "vulnerability_level": "CRITICAL",
      "hydraulic_score": 82.0,
      "structural_score": 80.0,
      "incident_score": 92.0,
      "environmental_score": 85.0,
      "contributing_factors": {
        "hydraulic": {
          "score": 82.0,
          "weight": 0.30,
          "weighted_contribution": 24.6,
          "reasons": ["High nominal operating pressure (65 psi)"]
        }
      },
      "confidence": 0.92,
      "data_completeness_pct": 95.0,
      "uncertainty_margin": 3.5,
      "deterioration_rate_per_day": 0.26,
      "trend_direction": "DETERIORATING",
      "active_incident_count": 2,
      "midpoint_lat": 40.7128,
      "midpoint_lng": -74.0060,
      "assessed_at": "2026-11-16T09:30:00Z",
      "is_simulated": true
    }
  ]
}
```

---

### 3.3. Segment Deep Dive
`GET /api/v1/infrastructure-intelligence/segments/{segment_id}`

#### Response `200 OK`:
Returns comprehensive profile including 4-factor contributing factors, predictive forecasts, and associated inspection queue items.

---

### 3.4. Spatial Incident Clusters
`GET /api/v1/infrastructure-intelligence/clusters`

#### Response `200 OK`:
```json
[
  {
    "id": "CLUS-01-METRO",
    "cluster_name": "Hotspot Cluster #1 (Ductile Iron Main)",
    "zone_id": "ZONE-PZ01",
    "centroid_lat": 40.7128,
    "centroid_lng": -74.0060,
    "radius_m": 220.0,
    "incident_count": 2,
    "dominant_material": "Ductile Iron (Class 54)",
    "average_severity": 0.82,
    "cluster_risk_level": "CRITICAL",
    "affected_segment_ids": ["PIPE-SEC-4B-92"],
    "hotspot_intensity": 0.85,
    "is_active": true,
    "is_simulated": true
  }
]
```

---

### 3.5. Inspection Priorities Queue
`GET /api/v1/infrastructure-intelligence/inspection-priorities?status=PENDING`

#### Response `200 OK`:
```json
[
  {
    "id": "INSP-SEC4B",
    "pipeline_segment_id": "PIPE-SEC-4B-92",
    "segment_name": "Metro Central Main Trunk Line B",
    "priority_score": 88.5,
    "priority_level": "CRITICAL_IMMEDIATE",
    "status": "PENDING",
    "target_latitude": 40.7128,
    "target_longitude": -74.0060,
    "reasons": [
      "Critical vulnerability index (84.5/100)",
      "Rapid degradation rate (+0.26 pts/day)",
      "Located directly within active incident hotspot (120m)"
    ],
    "suggested_action": "Immediate acoustic crawling patrol and acoustic leak pinpointing",
    "assigned_rover_id": null,
    "mission_recommendation_id": null,
    "reviewed_by": null,
    "reviewed_at": null,
    "is_simulated": true
  }
]
```

---

### 3.6. Request Rover Inspection Dispatch
`POST /api/v1/infrastructure-intelligence/inspection-priorities/{priority_id}/request-inspection`

#### Request Body:
```json
{
  "operator_name": "OPERATOR_CHIEF",
  "preferred_rover_id": "ROV-01",
  "notes": "Target joint acoustic survey across first 400 meters"
}
```

#### Response `200 OK`:
```json
{
  "status": "DISPATCHED",
  "priority_record_id": "INSP-SEC4B",
  "pipeline_segment_id": "PIPE-SEC-4B-92",
  "mission_recommendation_id": "REC-2026-4B819E",
  "assigned_rover_id": "ROV-01",
  "assigned_rover_name": "AquaRover Alpha (Crawler)",
  "planned_route_distance_m": 1250.0,
  "operator_approval_required": true,
  "recommendation_status": "PENDING_APPROVAL",
  "message": "Inspection mission recommendation generated for rover AquaRover Alpha (Crawler). Operator approval required to launch."
}
```

