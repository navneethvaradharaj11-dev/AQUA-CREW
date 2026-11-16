"""
Hydraulic Network Data Adapter (Task 10)
Translates between database models, GIS pipeline segments, and solver network representations.
"""
from typing import Dict, List, Any, Optional
import json
import math

from app.models.digital_twin import HydraulicNetworkModel, HydraulicNodeModel, HydraulicLinkModel


class NetworkAdapter:
    """
    Serializes and validates network topologies, converting database entities
    into structured dictionary graph formats suitable for hydraulic solvers.
    """

    @staticmethod
    def to_solver_dict(
        network: HydraulicNetworkModel,
        nodes: List[HydraulicNodeModel],
        links: List[HydraulicLinkModel]
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive solver-ready dictionary representation of the network.
        """
        nodes_dict = {}
        for n in nodes:
            nodes_dict[n.id] = {
                "id": n.id,
                "name": n.name,
                "node_type": n.node_type,
                "elevation_m": float(n.elevation_m),
                "base_head_m": float(n.base_head_m) if n.base_head_m is not None else None,
                "base_demand_lps": float(n.base_demand_lps),
                "demand_pattern_id": n.demand_pattern_id,
                "emitter_coeff": float(n.emitter_coeff),
                "min_pressure_bar": float(n.min_pressure_bar),
                "nominal_pressure_bar": float(n.nominal_pressure_bar),
                "initial_level_m": float(n.initial_level_m) if n.initial_level_m is not None else None,
                "min_level_m": float(n.min_level_m) if n.min_level_m is not None else None,
                "max_level_m": float(n.max_level_m) if n.max_level_m is not None else None,
                "diameter_m": float(n.diameter_m) if n.diameter_m is not None else None,
                "longitude": float(n.longitude),
                "latitude": float(n.latitude),
            }

        links_dict = {}
        for l in links:
            pump_curves = None
            if l.pump_curve_coeffs_json:
                try:
                    pump_curves = json.loads(l.pump_curve_coeffs_json)
                except Exception:
                    pump_curves = None

            coords = []
            if l.coordinates_json:
                try:
                    coords = json.loads(l.coordinates_json)
                except Exception:
                    coords = []

            links_dict[l.id] = {
                "id": l.id,
                "name": l.name,
                "link_type": l.link_type,
                "start_node_id": l.start_node_id,
                "end_node_id": l.end_node_id,
                "length_m": float(l.length_m),
                "diameter_mm": float(l.diameter_mm),
                "roughness": float(l.roughness),
                "minor_loss": float(l.minor_loss),
                "initial_status": l.initial_status,
                "current_status": l.current_status,
                "pipeline_segment_id": l.pipeline_segment_id,
                "pump_curve_coeffs": pump_curves,
                "pump_speed": float(l.pump_speed) if l.pump_speed is not None else 1.0,
                "pump_power_kw": float(l.pump_power_kw) if l.pump_power_kw is not None else 45.0,
                "valve_type": l.valve_type,
                "valve_setting": float(l.valve_setting) if l.valve_setting is not None else None,
                "coordinates": coords,
            }

        return {
            "network_id": network.id,
            "name": network.name,
            "description": network.description,
            "headloss_formula": network.headloss_formula,
            "flow_units": network.flow_units,
            "demand_model": network.demand_model,
            "nodes": nodes_dict,
            "links": links_dict,
        }

    @staticmethod
    def calculate_distance_m(coord1: List[float], coord2: List[float]) -> float:
        """Haversine distance between two [lon, lat] coordinates in meters."""
        lon1, lat1 = coord1
        lon2, lat2 = coord2
        R = 6371000.0  # Earth radius in meters
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2.0) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

