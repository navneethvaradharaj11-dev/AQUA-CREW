"""
Pressure Management and Zone Optimization Service (Task 14)
Analyzes nodal pressure distributions across hydraulic zones and optimizes
virtual Pressure-Reducing Valve (PRV) setpoints to stabilize pressure gradients and reduce pipe stress.
"""
from typing import Dict, Any, List, Optional, Tuple

from app.services.hydraulic_engine.simulation_results import HydraulicSimulationResult
from app.services.hydraulic_engine.network_performance_service import (
    PRESSURE_ZONE_MAPPING,
    DEFAULT_MIN_PRESSURE_BAR,
    DEFAULT_MAX_PRESSURE_BAR,
)


class PressureManagementService:
    """
    Evaluates pressure zone balance and determines optimal PRV settings.
    """

    @classmethod
    def analyze_zones(
        cls,
        sim_result: HydraulicSimulationResult,
        network_data: Dict[str, Any],
        min_threshold_bar: float = DEFAULT_MIN_PRESSURE_BAR,
        max_threshold_bar: float = DEFAULT_MAX_PRESSURE_BAR,
    ) -> Dict[str, Any]:
        """
        Groups nodal pressures by pressure zone and flags regional deficits/excesses.
        """
        zones_summary: Dict[str, Dict[str, Any]] = {}
        nodes_dict = network_data.get("nodes", {})

        for nid, nres in sim_result.nodes.items():
            if nodes_dict.get(nid, {}).get("node_type", "JUNCTION").upper() != "JUNCTION":
                continue

            zone_name = PRESSURE_ZONE_MAPPING.get(nid, "ZONE_DEFAULT")
            p = float(nres.pressure_bar)

            if zone_name not in zones_summary:
                zones_summary[zone_name] = {
                    "zone_name": zone_name,
                    "pressures": [],
                    "nodes": [],
                    "deficit_nodes": [],
                    "excess_nodes": [],
                }

            zones_summary[zone_name]["pressures"].append(p)
            zones_summary[zone_name]["nodes"].append(nid)
            if p < min_threshold_bar:
                zones_summary[zone_name]["deficit_nodes"].append(nid)
            elif p > max_threshold_bar:
                zones_summary[zone_name]["excess_nodes"].append(nid)

        # Compute zone aggregations
        report_zones = {}
        for z_name, z_data in zones_summary.items():
            p_list = z_data["pressures"]
            min_p = min(p_list) if p_list else 0.0
            max_p = max(p_list) if p_list else 0.0
            avg_p = sum(p_list) / len(p_list) if p_list else 0.0

            status = "STABLE"
            if len(z_data["deficit_nodes"]) > 0:
                status = "PRESSURE_DEFICIT"
            elif len(z_data["excess_nodes"]) > 0:
                status = "PRESSURE_EXCESS"

            report_zones[z_name] = {
                "zone_name": z_name,
                "node_count": len(z_data["nodes"]),
                "min_pressure_bar": round(min_p, 3),
                "max_pressure_bar": round(max_p, 3),
                "avg_pressure_bar": round(avg_p, 3),
                "deficit_count": len(z_data["deficit_nodes"]),
                "excess_count": len(z_data["excess_nodes"]),
                "status": status,
                "nodes": z_data["nodes"],
                "deficit_nodes": z_data["deficit_nodes"],
                "excess_nodes": z_data["excess_nodes"],
            }

        return report_zones

    @classmethod
    def evaluate_prv_impact(
        cls,
        prv_id: str,
        target_downstream_bar: float,
        network_data: Dict[str, Any],
        min_service_bar: float = DEFAULT_MIN_PRESSURE_BAR,
    ) -> Tuple[bool, str]:
        """
        Validates whether proposed PRV setting maintains minimum service pressure downstream.
        """
        if target_downstream_bar < min_service_bar:
            return False, f"Proposed PRV setting ({target_downstream_bar:.2f} bar) violates minimum regulatory service pressure ({min_service_bar:.2f} bar)."
        if target_downstream_bar > 6.0:
            return False, f"Proposed PRV setting ({target_downstream_bar:.2f} bar) exceeds maximum pressure threshold (6.0 bar)."

        explanation = (
            f"Modulating {prv_id} setpoint to {target_downstream_bar:.2f} bar throttles excess hydraulic head "
            f"in low-elevation zones while maintaining required minimum service pressure ({min_service_bar:.2f} bar)."
        )
        return True, explanation

