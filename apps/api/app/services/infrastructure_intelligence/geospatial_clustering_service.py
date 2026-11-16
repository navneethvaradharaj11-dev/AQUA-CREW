"""
AQUA CREW — Geospatial Incident Clustering Service (Task 11 / 11.5)
Performs density-based spatial clustering on pipeline incidents and leak detections
using Haversine geodesic distance metrics with antimeridian normalization,
3D spherical Cartesian centroid calculations, and coordinate validation.
"""
from typing import List, Dict, Any, Optional, Tuple
import math
import uuid
from datetime import datetime, timezone

from app.models.ai_detection import AiDetectionModel
from app.models.pipeline_segment import PipelineSegmentModel


class GeospatialClusteringService:
    EARTH_RADIUS_M = 6371000.0  # WGS-84 mean volumetric radius in meters
    DEFAULT_EPS_M = 350.0       # Spatial proximity threshold (350 meters)
    MIN_SAMPLES = 2             # Minimum incidents to form a dense cluster

    @classmethod
    def validate_coordinate(cls, lat: float, lng: float) -> Tuple[bool, str]:
        """
        Validates GPS coordinate bounds.
        Latitude must be in [-90.0, 90.0], Longitude must be in [-180.0, 180.0].
        """
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            return False, "Coordinates must be numeric"
        if math.isnan(lat) or math.isnan(lng):
            return False, "Coordinates cannot be NaN"
        if lat < -90.0 or lat > 90.0:
            return False, f"Latitude {lat} out of range [-90, 90]"
        if lng < -180.0 or lng > 180.0:
            return False, f"Longitude {lng} out of range [-180, 180]"
        return True, "Valid"

    @classmethod
    def haversine_distance_m(cls, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        Calculates great-circle distance between two GPS coordinates in meters.
        Includes antimeridian crossing normalization (wraps longitude delta to [-pi, pi]).
        """
        # Validate coordinates, clamp if near precision limits
        lat1 = max(-90.0, min(90.0, lat1))
        lat2 = max(-90.0, min(90.0, lat2))

        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        
        # Longitude difference normalized to [-pi, pi] to handle antimeridian crossing
        raw_delta_lambda = math.radians(lng2 - lng1)
        delta_lambda = (raw_delta_lambda + math.pi) % (2.0 * math.pi) - math.pi

        a = (
            math.sin(delta_phi / 2.0) ** 2 +
            math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
        )
        # Numerical guard against precision floating point overflow
        a = max(0.0, min(1.0, a))
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return cls.EARTH_RADIUS_M * c

    @classmethod
    def calculate_spherical_centroid(cls, points: List[Dict[str, Any]]) -> Tuple[float, float]:
        """
        Computes the true geometric centroid on a sphere using 3D Cartesian coordinates:
        x = cos(lat) * cos(lng)
        y = cos(lat) * sin(lng)
        z = sin(lat)
        Correctly computes centroid across the 180th meridian (antimeridian) and near poles.
        """
        if not points:
            return 0.0, 0.0
        if len(points) == 1:
            return points[0]["latitude"], points[0]["longitude"]

        x_sum = 0.0
        y_sum = 0.0
        z_sum = 0.0
        count = len(points)

        for p in points:
            phi = math.radians(p["latitude"])
            lam = math.radians(p["longitude"])
            x_sum += math.cos(phi) * math.cos(lam)
            y_sum += math.cos(phi) * math.sin(lam)
            z_sum += math.sin(phi)

        x_mean = x_sum / count
        y_mean = y_sum / count
        z_mean = z_sum / count

        hyp = math.sqrt(x_mean * x_mean + y_mean * y_mean)
        if hyp > 1e-9:
            centroid_lat = math.degrees(math.atan2(z_mean, hyp))
            centroid_lng = math.degrees(math.atan2(y_mean, x_mean))
        else:
            # Polar singularity
            centroid_lat = 90.0 if z_mean >= 0 else -90.0
            centroid_lng = 0.0

        return round(centroid_lat, 6), round(centroid_lng, 6)

    @classmethod
    def cluster_incidents(
        cls,
        incidents: List[Dict[str, Any]],
        eps_m: float = DEFAULT_EPS_M,
        min_samples: int = MIN_SAMPLES,
    ) -> List[Dict[str, Any]]:
        """
        DBSCAN-style spatial clustering implementation for incident points.
        Each incident must have:
        'id', 'latitude', 'longitude', 'segment_id', 'severity', 'material' (optional)
        """
        if not incidents:
            return []

        # 1. Filter and sanitize valid coordinates
        valid_incidents = []
        for p in incidents:
            lat = p.get("latitude")
            lng = p.get("longitude")
            if lat is not None and lng is not None:
                is_valid, _ = cls.validate_coordinate(lat, lng)
                if is_valid:
                    valid_incidents.append(p)

        n = len(valid_incidents)
        if n == 0:
            return []

        # 2. Build adjacency distance matrix using geodesic Haversine
        neighbors: List[List[int]] = []
        for i in range(n):
            i_neighbors = []
            for j in range(n):
                dist = cls.haversine_distance_m(
                    valid_incidents[i]["latitude"],
                    valid_incidents[i]["longitude"],
                    valid_incidents[j]["latitude"],
                    valid_incidents[j]["longitude"],
                )
                if dist <= eps_m:
                    i_neighbors.append(j)
            neighbors.append(i_neighbors)

        visited = [False] * n
        cluster_labels = [-1] * n  # -1 = unassigned / noise
        current_cluster_id = 0

        for i in range(n):
            if visited[i]:
                continue
            visited[i] = True
            i_neighbors = neighbors[i]

            if len(i_neighbors) < min_samples:
                # Mark as singleton/noise initially
                continue
            else:
                cluster_labels[i] = current_cluster_id
                queue = list(i_neighbors)
                idx = 0
                while idx < len(queue):
                    neighbor_idx = queue[idx]
                    idx += 1
                    if not visited[neighbor_idx]:
                        visited[neighbor_idx] = True
                        n_neighbors = neighbors[neighbor_idx]
                        if len(n_neighbors) >= min_samples:
                            for nn in n_neighbors:
                                if nn not in queue:
                                    queue.append(nn)
                    if cluster_labels[neighbor_idx] == -1:
                        cluster_labels[neighbor_idx] = current_cluster_id
                current_cluster_id += 1

        # Helper to safely parse string or numeric severities
        def _parse_severity(val: Any) -> float:
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                v_upper = val.upper()
                if "CRIT" in v_upper:
                    return 0.95
                if "HIGH" in v_upper:
                    return 0.75
                if "MED" in v_upper:
                    return 0.50
                if "LOW" in v_upper:
                    return 0.25
            return 0.50

        # Singleton promotion only if min_samples <= 1
        if min_samples <= 1:
            for i in range(n):
                sev_val = _parse_severity(valid_incidents[i].get("severity", 0.0))
                if cluster_labels[i] == -1 and sev_val >= 0.70:
                    cluster_labels[i] = current_cluster_id
                    current_cluster_id += 1

        # Aggregate cluster geometries and statistics
        clusters = []
        for cid in range(current_cluster_id):
            member_indices = [idx for idx, clabel in enumerate(cluster_labels) if clabel == cid]
            if not member_indices:
                continue

            member_pts = [valid_incidents[idx] for idx in member_indices]
            count = len(member_pts)
            mean_lat, mean_lng = cls.calculate_spherical_centroid(member_pts)

            # Calculate radius using geodesic distance from centroid to furthest member
            max_dist = 0.0
            for p in member_pts:
                d = cls.haversine_distance_m(mean_lat, mean_lng, p["latitude"], p["longitude"])
                if d > max_dist:
                    max_dist = d
            radius_m = max(150.0, round(max_dist, 1))

            # Calculate severity and dominant material safely handling numeric or string severity
            avg_severity = sum(_parse_severity(p.get("severity", 0.5)) for p in member_pts) / count
            materials: Dict[str, int] = {}
            affected_segments = set()
            for p in member_pts:
                mat = p.get("material", "Unknown")
                materials[mat] = materials.get(mat, 0) + 1
                seg_id = p.get("segment_id")
                if seg_id:
                    affected_segments.add(seg_id)

            dominant_mat = max(materials.items(), key=lambda x: x[1])[0] if materials else "Ductile Iron"

            # Hotspot intensity: density + severity composite (0.0 to 1.0)
            density_factor = min(1.0, count / 5.0)
            hotspot_intensity = round(0.50 * avg_severity + 0.50 * density_factor, 2)

            # Determine cluster risk level
            if hotspot_intensity >= 0.75 or count >= 3:
                risk_level = "CRITICAL"
            elif hotspot_intensity >= 0.55 or count >= 2:
                risk_level = "HIGH"
            elif hotspot_intensity >= 0.35:
                risk_level = "MODERATE"
            else:
                risk_level = "LOW"

            cluster_uuid = f"CLUS-{cid+1:02d}-{uuid.uuid4().hex[:4].upper()}"
            clusters.append({
                "id": cluster_uuid,
                "cluster_name": f"Hotspot Cluster #{cid + 1} ({dominant_mat})",
                "zone_id": f"ZONE-{cid+1:02d}",
                "centroid_lat": mean_lat,
                "centroid_lng": mean_lng,
                "radius_m": radius_m,
                "incident_count": count,
                "dominant_material": dominant_mat,
                "average_severity": round(avg_severity, 2),
                "cluster_risk_level": risk_level,
                "affected_segment_ids": list(affected_segments),
                "hotspot_intensity": hotspot_intensity,
                "is_active": True,
            })

        return clusters
