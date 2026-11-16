"""
Telemetry & Kinematics Calculation Service
Implements Haversine distance, azimuth bearings, and LineString position interpolation.
"""
import math
from typing import List, Tuple, Dict, Any, Optional

EARTH_RADIUS_METERS = 6371000.0


def haversine_distance_meters(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Computes great-circle distance between two (lon, lat) points in meters.
    """
    lon1, lat1 = coord1
    lon2, lat2 = coord2

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return EARTH_RADIUS_METERS * c


def calculate_bearing_deg(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Computes initial forward azimuth in degrees (0-360) from coord1 to coord2.
    """
    lon1, lat1 = coord1
    lon2, lat2 = coord2

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = (math.cos(phi1) * math.sin(phi2) -
         math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda))
    theta = math.atan2(y, x)
    return (math.degrees(theta) + 360.0) % 360.0


def interpolate_route_position(
    coords: List[List[float]],
    current_distance_m: float,
    is_returning: bool = False
) -> Dict[str, Any]:
    """
    Interpolates longitude, latitude, and heading along a list of [lon, lat] coordinates.
    """
    if len(coords) < 2:
        lon, lat = coords[0] if coords else (0.0, 0.0)
        return {
            "longitude": lon,
            "latitude": lat,
            "heading_deg": 0.0,
            "fraction": 0.0,
            "total_length_m": 0.0,
        }

    # Compute sub-segment distances
    sub_dists = []
    cum_dists = [0.0]
    total_len = 0.0

    for i in range(len(coords) - 1):
        c1 = (coords[i][0], coords[i][1])
        c2 = (coords[i + 1][0], coords[i + 1][1])
        d = haversine_distance_meters(c1, c2)
        sub_dists.append(d)
        total_len += d
        cum_dists.append(total_len)

    total_len = max(total_len, 1.0)
    clamped_dist = max(0.0, min(total_len, current_distance_m))
    fraction = clamped_dist / total_len

    # Identify segment
    seg_idx = 0
    for i in range(len(cum_dists) - 1):
        if clamped_dist >= cum_dists[i] and clamped_dist <= cum_dists[i + 1]:
            seg_idx = i
            break

    c_start = coords[seg_idx]
    c_end = coords[min(seg_idx + 1, len(coords) - 1)]
    seg_start_dist = cum_dists[seg_idx]
    seg_length = sub_dists[seg_idx] if sub_dists[seg_idx] > 0 else 1.0

    t = max(0.0, min(1.0, (clamped_dist - seg_start_dist) / seg_length))

    lon = c_start[0] + t * (c_end[0] - c_start[0])
    lat = c_start[1] + t * (c_end[1] - c_start[1])

    bearing = calculate_bearing_deg((c_start[0], c_start[1]), (c_end[0], c_end[1]))
    if is_returning:
        bearing = (bearing + 180.0) % 360.0

    return {
        "longitude": round(lon, 6),
        "latitude": round(lat, 6),
        "heading_deg": round(bearing, 1),
        "fraction": round(fraction, 3),
        "total_length_m": round(total_len, 1),
    }

