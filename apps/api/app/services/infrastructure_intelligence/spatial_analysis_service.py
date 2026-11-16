"""
AQUA CREW — Spatial Analysis & Geographic Zone Service (Task 11)
Aggregates pipeline vulnerability metrics across operational geographic zones,
calculates cluster proximity, and generates geospatial risk heatmaps.
"""
from typing import List, Dict, Any, Optional
import json
import math
from datetime import datetime, timezone

from app.services.infrastructure_intelligence.geospatial_clustering_service import GeospatialClusteringService
from app.models.pipeline_segment import PipelineSegmentModel
from app.models.infrastructure_intelligence import GeographicRiskZoneModel


class SpatialAnalysisService:
    # Standard Metropolitan Zone Definitions
    ZONE_DEFINITIONS = {
        "PZ-01": {
            "code": "ZONE-PZ01",
            "name": "Metro Central High-Pressure Corridor",
            "description": "Primary high-pressure arterial spine servicing downtown commercial and civic core.",
            "nominal_pressure_psi": 65.0,
            "bounds": {
                "type": "Polygon",
                "coordinates": [[
                    [-74.020, 40.700],
                    [-73.990, 40.700],
                    [-73.990, 40.725],
                    [-74.020, 40.725],
                    [-74.020, 40.700],
                ]]
            }
        },
        "PZ-02": {
            "code": "ZONE-PZ02",
            "name": "Eastern Industrial Sector",
            "description": "Industrial feeder network with high daily flow variation and heavy manufacturing demand.",
            "nominal_pressure_psi": 60.0,
            "bounds": {
                "type": "Polygon",
                "coordinates": [[
                    [-74.005, 40.710],
                    [-73.990, 40.710],
                    [-73.990, 40.720],
                    [-74.005, 40.720],
                    [-74.005, 40.710],
                ]]
            }
        },
        "PZ-03": {
            "code": "ZONE-PZ03",
            "name": "Northern Residential Zone",
            "description": "Residential sub-branch with diurnal peaking and residential service connections.",
            "nominal_pressure_psi": 52.0,
            "bounds": {
                "type": "Polygon",
                "coordinates": [[
                    [-74.015, 40.718],
                    [-74.000, 40.718],
                    [-74.000, 40.730],
                    [-74.015, 40.730],
                    [-74.015, 40.718],
                ]]
            }
        },
        "PZ-04": {
            "code": "ZONE-PZ04",
            "name": "Harbor Utility Terminal",
            "description": "Coastal distribution grid with elevated saline groundwater and marine proximity.",
            "nominal_pressure_psi": 58.0,
            "bounds": {
                "type": "Polygon",
                "coordinates": [[
                    [-74.020, 40.700],
                    [-74.005, 40.700],
                    [-74.005, 40.712],
                    [-74.020, 40.712],
                    [-74.020, 40.700],
                ]]
            }
        },
    }

    @classmethod
    def get_segment_midpoint(cls, segment: PipelineSegmentModel) -> Optional[Tuple[float, float]]:
        """
        Extracts (latitude, longitude) of the pipeline segment midpoint.
        """
        raw_c = segment.coordinates_json
        if not raw_c:
            return None
        try:
            coords = json.loads(raw_c) if isinstance(raw_c, str) else raw_c
            if coords and len(coords) > 0:
                mid = coords[len(coords) // 2]
                return (mid[1], mid[0])  # lat, lng
        except Exception:
            return None
        return None

    @classmethod
    def calculate_distance_to_nearest_cluster(
        cls,
        segment: PipelineSegmentModel,
        clusters: List[Dict[str, Any]],
    ) -> float:
        """
        Calculates minimum geodesic distance in meters from any vertex along the pipeline conduit
        geometry to the nearest cluster centroid, ensuring spatial accuracy across extended mains.
        """
        if not clusters:
            return 9999.0

        raw_c = segment.coordinates_json
        if not raw_c:
            return 9999.0

        try:
            coords = json.loads(raw_c) if isinstance(raw_c, str) else raw_c
        except Exception:
            return 9999.0

        if not coords:
            return 9999.0

        min_dist = 9999.0
        for c in clusters:
            c_lat = c["centroid_lat"]
            c_lng = c["centroid_lng"]
            for pt in coords:
                # GeoJSON coordinates standard: [longitude, latitude]
                pt_lng, pt_lat = pt[0], pt[1]
                dist = GeospatialClusteringService.haversine_distance_m(pt_lat, pt_lng, c_lat, c_lng)
                if dist < min_dist:
                    min_dist = dist

        return round(min_dist, 1)

    @classmethod
    def aggregate_zones(
        cls,
        segments: List[PipelineSegmentModel],
        vulnerability_profiles: Dict[str, Dict[str, Any]],
        clusters: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Aggregates vulnerability and cluster statistics per geographic zone.
        """
        zone_buckets: Dict[str, List[PipelineSegmentModel]] = {}
        for s in segments:
            pz = s.pressure_zone_id or "PZ-01"
            if pz not in zone_buckets:
                zone_buckets[pz] = []
            zone_buckets[pz].append(s)

        results = []
        for pz, seg_list in zone_buckets.items():
            meta = cls.ZONE_DEFINITIONS.get(pz, {
                "code": f"ZONE-{pz}",
                "name": f"Pressure Zone {pz}",
                "description": f"Municipal utility sector for pressure zone {pz}.",
                "nominal_pressure_psi": 60.0,
                "bounds": {"type": "Polygon", "coordinates": []},
            })

            scores = []
            critical_count = 0
            total_len_m = 0.0

            for s in seg_list:
                total_len_m += (s.length_m or 0.0)
                profile = vulnerability_profiles.get(s.id)
                if profile:
                    score = profile.get("vulnerability_score", 0.0)
                    scores.append(score)
                    if score > 80.0:
                        critical_count += 1

            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
            from app.services.infrastructure_intelligence.vulnerability_scoring_service import VulnerabilityScoringService
            dominant_risk = VulnerabilityScoringService.get_vulnerability_level(avg_score)

            # Count clusters within or affecting this zone
            zone_clusters_count = 0
            for c in clusters:
                affected = set(c.get("affected_segment_ids", []))
                if any(s.id in affected for s in seg_list):
                    zone_clusters_count += 1

            results.append({
                "id": f"zone_{meta['code'].lower()}",
                "zone_code": meta["code"],
                "zone_name": meta["name"],
                "description": meta["description"],
                "total_segments": len(seg_list),
                "total_length_km": round(total_len_m / 1000.0, 2),
                "avg_vulnerability_score": avg_score,
                "dominant_risk_level": dominant_risk,
                "critical_segment_count": critical_count,
                "active_clusters_count": zone_clusters_count,
                "avg_pressure_psi": meta["nominal_pressure_psi"],
                "bounds_json": json.dumps(meta["bounds"]),
                "is_simulated": True,
                "source": "VIRTUAL_SIMULATION_ENGINE",
            })

        return results

    @classmethod
    def generate_heatmap_points(
        cls,
        segments: List[PipelineSegmentModel],
        vulnerability_profiles: Dict[str, Dict[str, Any]],
        clusters: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Generates weighted geospatial points along pipeline segments and cluster centroids
        for map heatmap layers.
        """
        heatmap_points = []

        # 1. Pipeline segment path points
        for s in segments:
            profile = vulnerability_profiles.get(s.id, {})
            score = profile.get("vulnerability_score", 30.0)
            risk_level = profile.get("vulnerability_level", "LOW")
            weight = round(max(0.1, min(1.0, score / 100.0)), 2)

            raw_c = s.coordinates_json
            if raw_c:
                try:
                    coords = json.loads(raw_c) if isinstance(raw_c, str) else raw_c
                    for pt in coords:
                        heatmap_points.append({
                            "latitude": pt[1],
                            "longitude": pt[0],
                            "weight": weight,
                            "segment_id": s.id,
                            "risk_level": risk_level,
                            "score": score,
                            "point_type": "PIPELINE_VERTEX",
                        })
                except Exception:
                    pass

        # 2. Add cluster centroid points with heightened weight
        for c in clusters:
            c_weight = round(max(0.4, min(1.0, c.get("hotspot_intensity", 0.7) * 1.2)), 2)
            heatmap_points.append({
                "latitude": c["centroid_lat"],
                "longitude": c["centroid_lng"],
                "weight": c_weight,
                "segment_id": c.get("affected_segment_ids", [""])[0] if c.get("affected_segment_ids") else "",
                "risk_level": c.get("cluster_risk_level", "HIGH"),
                "score": round(c_weight * 100.0, 1),
                "point_type": "CLUSTER_HOTSPOT",
            })

        return heatmap_points

