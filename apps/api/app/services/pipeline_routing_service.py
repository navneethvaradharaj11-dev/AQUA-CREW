"""
AQUA CREW — Pipeline Network Routing Engine
Models metropolitan pipeline GeoJSON network as a topological graph.
Executes Dijkstra shortest-path pathfinding following actual connected underground pipe geometry.
"""
from typing import List, Dict, Any, Tuple, Optional
import math
import heapq
import json

from app.schemas.dispatch import PipelineRoute


def haversine_distance_m(coord1: List[float], coord2: List[float]) -> float:
    """
    Computes great-circle distance between two [lng, lat] points in meters.
    """
    lng1, lat1 = coord1[0], coord1[1]
    lng2, lat2 = coord2[0], coord2[1]
    r = 6371000.0  # Earth radius in meters

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def coord_to_key(coord: List[float]) -> str:
    """
    Quantizes coordinates to 4 decimal places (~11m resolution) for topological junction snapping.
    """
    return f"{coord[0]:.4f},{coord[1]:.4f}"


def key_to_coord(key: str) -> List[float]:
    parts = key.split(",")
    return [float(parts[0]), float(parts[1])]


class PipelineRoutingService:
    @classmethod
    def build_network_graph(cls, pipeline_records: List[Any]) -> Tuple[Dict[str, List[Tuple[str, float, str]]], Dict[str, List[float]]]:
        """
        Constructs adjacency graph from pipeline segment geometries.
        Graph: {node_key: [(neighbor_key, distance_m, segment_id), ...]}
        """
        adj: Dict[str, List[Tuple[str, float, str]]] = {}
        nodes: Dict[str, List[float]] = {}

        for seg in pipeline_records:
            seg_id = seg.id if hasattr(seg, "id") else seg["id"]
            raw_coords = seg.coordinates_json if hasattr(seg, "coordinates_json") else seg.get("coordinates", [])
            coords = json.loads(raw_coords) if isinstance(raw_coords, str) else raw_coords

            if not coords or len(coords) < 2:
                continue

            for i in range(len(coords) - 1):
                c1, c2 = coords[i], coords[i + 1]
                k1, k2 = coord_to_key(c1), coord_to_key(c2)

                dist = haversine_distance_m(c1, c2)
                nodes[k1] = c1
                nodes[k2] = c2

                if k1 not in adj:
                    adj[k1] = []
                if k2 not in adj:
                    adj[k2] = []

                adj[k1].append((k2, dist, seg_id))
                adj[k2].append((k1, dist, seg_id))

        return adj, nodes

    @classmethod
    def find_nearest_node(cls, coord: List[float], nodes: Dict[str, List[float]]) -> Tuple[str, float]:
        """
        Snaps an arbitrary coordinate to the closest pipeline junction/node in the graph.
        """
        best_node = None
        min_dist = float("inf")

        for k, c in nodes.items():
            d = haversine_distance_m(coord, c)
            if d < min_dist:
                min_dist = d
                best_node = k

        return best_node, min_dist

    @classmethod
    def calculate_route(
        cls,
        start_coord: List[float],
        target_coord: List[float],
        pipeline_records: List[Any],
        target_segment_id: Optional[str] = None,
        rover_speed_mps: float = 0.55,
        uncertainty_radius_m: Optional[float] = None,
    ) -> PipelineRoute:
        """
        Calculates shortest path along connected underground pipeline geometry using Dijkstra.
        """
        adj, nodes = cls.build_network_graph(pipeline_records)

        if not nodes:
            return PipelineRoute(
                start_coordinates=start_coord,
                destination_coordinates=target_coord,
                waypoints=[start_coord, target_coord],
                segments_traversed=[],
                total_distance_m=0.0,
                estimated_travel_time_s=0.0,
                is_connected=False,
                uncertainty_radius_m=uncertainty_radius_m,
            )

        start_node, _ = cls.find_nearest_node(start_coord, nodes)
        target_node, _ = cls.find_nearest_node(target_coord, nodes)

        if not start_node or not target_node:
            return PipelineRoute(
                start_coordinates=start_coord,
                destination_coordinates=target_coord,
                waypoints=[],
                segments_traversed=[],
                total_distance_m=0.0,
                estimated_travel_time_s=0.0,
                is_connected=False,
                uncertainty_radius_m=uncertainty_radius_m,
            )

        # Dijkstra Pathfinding: min-heap (dist, current_node, path, segments)
        heap = [(0.0, start_node, [start_node], [])]
        visited = set()
        best_path: Optional[List[str]] = None
        best_segments: List[str] = []
        total_dist_m = 0.0

        while heap:
            dist, curr, path, segs = heapq.heappop(heap)

            if curr in visited:
                continue
            visited.add(curr)

            if curr == target_node:
                best_path = path
                best_segments = segs
                total_dist_m = dist
                break

            for nxt, edge_dist, seg_id in adj.get(curr, []):
                if nxt not in visited:
                    nxt_segs = segs if (segs and segs[-1] == seg_id) else (segs + [seg_id])
                    heapq.heappush(heap, (dist + edge_dist, nxt, path + [nxt], nxt_segs))

        # Check if connected path found
        if not best_path:
            # Fallback if start and target were snapped to the same segment or disconnected
            return PipelineRoute(
                start_coordinates=start_coord,
                destination_coordinates=target_coord,
                waypoints=[start_coord],
                segments_traversed=[],
                total_distance_m=0.0,
                estimated_travel_time_s=0.0,
                is_connected=False,
                uncertainty_radius_m=uncertainty_radius_m,
            )

        # Reconstruct actual waypoints
        waypoints = [start_coord]
        for node_key in best_path:
            c = nodes[node_key]
            # Avoid immediate duplicate points
            if not waypoints or (waypoints[-1][0] != c[0] or waypoints[-1][1] != c[1]):
                waypoints.append(c)

        if waypoints[-1][0] != target_coord[0] or waypoints[-1][1] != target_coord[1]:
            waypoints.append(target_coord)

        # Ensure target segment is in segments traversed
        if target_segment_id and target_segment_id not in best_segments:
            best_segments.append(target_segment_id)

        # If start and target snapped to the same junction but coordinates differ, use direct distance
        if total_dist_m == 0.0:
            direct_dist = haversine_distance_m(start_coord, target_coord)
            if direct_dist > 0.0:
                total_dist_m = direct_dist

        # Compute travel duration
        speed = max(0.1, rover_speed_mps)
        est_duration_s = round(total_dist_m / speed, 1)

        return PipelineRoute(
            start_coordinates=start_coord,
            destination_coordinates=target_coord,
            waypoints=waypoints,
            segments_traversed=best_segments,
            total_distance_m=round(total_dist_m, 1),
            estimated_travel_time_s=est_duration_s,
            is_connected=True,
            uncertainty_radius_m=uncertainty_radius_m,
        )

