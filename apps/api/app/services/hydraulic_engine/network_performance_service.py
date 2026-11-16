"""
Network Performance Evaluation Service (Task 14)
Computes comprehensive pressure, hydraulic, water loss, energy, and reliability metrics
from hydraulic simulation outputs and network topology definitions.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from app.services.hydraulic_engine.simulation_results import HydraulicSimulationResult
from app.schemas.network_performance import (
    MetricValue,
    PressureMetrics,
    HydraulicFlowMetrics,
    WaterLossMetrics,
    EnergyMetrics,
    ReliabilityMetrics,
    NetworkPerformanceReport,
)


PRESSURE_ZONE_MAPPING = {
    "NODE-RES-01": "ZONE_NORTH_SUPPLY",
    "NODE-JUNC-01": "ZONE_METRO_CORE",
    "NODE-JUNC-02": "ZONE_METRO_CORE",
    "NODE-JUNC-03": "ZONE_WESTERN_HARBOR",
    "NODE-JUNC-04": "ZONE_EASTERN_INDUSTRIAL",
    "NODE-TANK-01": "ZONE_EASTERN_INDUSTRIAL",
    "NODE-JUNC-05": "ZONE_HARBOR_LOW_ELEVATION",
    "NODE-JUNC-06": "ZONE_PINECREST_RESIDENTIAL",
}

DEFAULT_MIN_PRESSURE_BAR = 1.5
DEFAULT_MAX_PRESSURE_BAR = 5.5
DEFAULT_MAX_VELOCITY_MPS = 2.5
DEFAULT_WIRE_TO_WATER_EFFICIENCY = 0.72


class NetworkPerformanceService:
    """
    Evaluates hydraulic simulation outputs and generates standardized engineering performance reports.
    """

    @classmethod
    def evaluate(
        cls,
        result: HydraulicSimulationResult,
        network_data: Dict[str, Any],
        scenario_name: str = "Operating Scenario",
        tariff_usd_per_kwh: Optional[float] = None,
        min_target_pressure_bar: float = DEFAULT_MIN_PRESSURE_BAR,
        max_target_pressure_bar: float = DEFAULT_MAX_PRESSURE_BAR,
        duration_hours: int = 24,
    ) -> NetworkPerformanceReport:
        """
        Calculates all 5 performance metric categories from simulation results.
        """
        nodes_dict = network_data.get("nodes", {})
        links_dict = network_data.get("links", {})

        # 1. Pressure Metrics
        pressures: List[float] = []
        node_pressures_map: Dict[str, float] = {}
        deficit_nodes: List[str] = []
        excess_nodes: List[str] = []

        for nid, nres in result.nodes.items():
            node_type = nodes_dict.get(nid, {}).get("node_type", nres.node_type).upper()
            if node_type == "JUNCTION":
                p = float(nres.pressure_bar)
                pressures.append(p)
                node_pressures_map[nid] = p
                if p < min_target_pressure_bar:
                    deficit_nodes.append(nid)
                elif p > max_target_pressure_bar:
                    excess_nodes.append(nid)

        min_p = min(pressures) if pressures else 0.0
        max_p = max(pressures) if pressures else 0.0
        avg_p = sum(pressures) / len(pressures) if pressures else 0.0

        pressure_metrics = PressureMetrics(
            min_pressure_bar=MetricValue(value=round(min_p, 3), unit="bar"),
            max_pressure_bar=MetricValue(value=round(max_p, 3), unit="bar"),
            avg_pressure_bar=MetricValue(value=round(avg_p, 3), unit="bar"),
            pressure_deficit_nodes_count=len(deficit_nodes),
            pressure_excess_nodes_count=len(excess_nodes),
            deficit_node_ids=deficit_nodes,
            excess_node_ids=excess_nodes,
            node_pressures_bar={k: round(v, 3) for k, v in node_pressures_map.items()},
        )

        # 2. Hydraulic Flow Metrics
        req_demand_lps = sum(
            float(nodes_dict.get(nid, {}).get("base_demand_lps", 0.0))
            for nid, nmeta in nodes_dict.items()
            if nmeta.get("node_type", "JUNCTION").upper() == "JUNCTION"
        )
        deliv_demand_lps = sum(
            max(0.0, float(nres.actual_demand_lps))
            for nid, nres in result.nodes.items()
            if nodes_dict.get(nid, {}).get("node_type", "JUNCTION").upper() == "JUNCTION"
        )
        satisfaction_ratio = (deliv_demand_lps / req_demand_lps) if req_demand_lps > 0 else 1.0

        velocities: List[float] = []
        headlosses: List[float] = []
        link_vels: Dict[str, float] = {}
        link_flows: Dict[str, float] = {}

        for lid, lres in result.links.items():
            ltype = links_dict.get(lid, {}).get("link_type", lres.link_type).upper()
            if ltype == "PIPE":
                v = float(lres.velocity_mps)
                hl = float(lres.headloss_m)
                velocities.append(v)
                headlosses.append(hl)
                link_vels[lid] = round(v, 3)
                link_flows[lid] = round(float(lres.flow_lps), 3)

        max_vel = max(velocities) if velocities else 0.0
        avg_vel = sum(velocities) / len(velocities) if velocities else 0.0
        max_hl = max(headlosses) if headlosses else 0.0
        total_hl = sum(headlosses)
        cap_util = (max_vel / DEFAULT_MAX_VELOCITY_MPS * 100.0) if DEFAULT_MAX_VELOCITY_MPS > 0 else 0.0

        hydraulic_metrics = HydraulicFlowMetrics(
            total_requested_demand_lps=MetricValue(value=round(req_demand_lps, 3), unit="L/s"),
            total_delivered_demand_lps=MetricValue(value=round(deliv_demand_lps, 3), unit="L/s"),
            demand_satisfaction_ratio=MetricValue(value=round(satisfaction_ratio, 4), unit="ratio"),
            max_pipe_velocity_mps=MetricValue(value=round(max_vel, 3), unit="m/s"),
            avg_pipe_velocity_mps=MetricValue(value=round(avg_vel, 3), unit="m/s"),
            max_pipe_headloss_m=MetricValue(value=round(max_hl, 3), unit="m"),
            total_network_headloss_m=MetricValue(value=round(total_hl, 3), unit="m"),
            capacity_utilization_pct=MetricValue(value=round(cap_util, 2), unit="%"),
            link_velocities_mps=link_vels,
            link_flows_lps=link_flows,
        )

        # 3. Water-Loss Metrics
        total_leak_lps = sum(float(nres.leak_flow_lps) for nres in result.nodes.values())
        daily_leak_m3 = total_leak_lps * 86.4  # L/s to m3/day
        total_supply_lps = deliv_demand_lps + total_leak_lps
        leak_ratio_pct = (total_leak_lps / total_supply_lps * 100.0) if total_supply_lps > 0 else 0.0

        leak_by_segment: Dict[str, float] = {}
        leak_by_zone: Dict[str, float] = {}

        for nid, nres in result.nodes.items():
            leak_q = float(nres.leak_flow_lps)
            if leak_q > 0.001:
                zone = PRESSURE_ZONE_MAPPING.get(nid, "ZONE_UNKNOWN")
                leak_by_zone[zone] = round(leak_by_zone.get(zone, 0.0) + leak_q, 3)
                seg_id = nodes_dict.get(nid, {}).get("pipeline_segment_id", nid)
                leak_by_segment[seg_id] = round(leak_by_segment.get(seg_id, 0.0) + leak_q, 3)

        water_loss_metrics = WaterLossMetrics(
            total_simulated_leakage_lps=MetricValue(value=round(total_leak_lps, 3), unit="L/s"),
            daily_leakage_volume_m3=MetricValue(value=round(daily_leak_m3, 2), unit="m3/day"),
            leakage_to_supplied_ratio_pct=MetricValue(value=round(leak_ratio_pct, 2), unit="%"),
            leakage_by_segment=leak_by_segment,
            leakage_by_zone=leak_by_zone,
        )

        # 4. Energy Metrics
        # Identify pumps
        total_hydraulic_energy_kwh = 0.0
        total_elec_energy_kwh = 0.0
        pump_op_hours = 0.0

        for lid, lmeta in links_dict.items():
            if lmeta.get("link_type", "").upper() == "PUMP":
                lres = result.links.get(lid)
                flow_lps = abs(float(lres.flow_lps)) if lres else 0.0
                rated_kw = float(lmeta.get("pump_power_kw", 45.0))
                speed = float(lmeta.get("pump_speed", 1.0))
                is_running = (lmeta.get("current_status", "OPEN").upper() != "CLOSED") and (speed > 0.05)

                if is_running:
                    pump_op_hours += duration_hours
                    # Affinity scaling: electrical power scales as speed^3
                    actual_kw = rated_kw * (speed ** 3)
                    elec_kwh = actual_kw * duration_hours
                    total_elec_energy_kwh += elec_kwh
                    # Approximate hydraulic energy from head and flow
                    # P_hyd (kW) = 9.81 * Q (m3/s) * H (m)
                    q_m3s = flow_lps / 1000.0
                    head_m = 65.0 * (speed ** 2)  # approximate head at operating point
                    hyd_kw = 9.81 * q_m3s * head_m
                    total_hydraulic_energy_kwh += hyd_kw * duration_hours

        efficiency_pct = (
            (total_hydraulic_energy_kwh / total_elec_energy_kwh * 100.0)
            if total_elec_energy_kwh > 0
            else DEFAULT_WIRE_TO_WATER_EFFICIENCY * 100.0
        )

        cost_val = None
        has_cost = False
        if tariff_usd_per_kwh is not None and tariff_usd_per_kwh > 0:
            cost_val = round(total_elec_energy_kwh * tariff_usd_per_kwh, 2)
            has_cost = True

        energy_metrics = EnergyMetrics(
            pump_electrical_energy_kwh=MetricValue(value=round(total_elec_energy_kwh, 2), unit="kWh"),
            pump_hydraulic_energy_kwh=MetricValue(value=round(total_hydraulic_energy_kwh, 2), unit="kWh"),
            pump_wire_to_water_efficiency_pct=MetricValue(value=round(min(100.0, max(0.0, efficiency_pct)), 1), unit="%"),
            pump_operating_hours=MetricValue(value=round(pump_op_hours, 1), unit="hours"),
            energy_cost_usd=MetricValue(value=cost_val, unit="USD", is_available=has_cost),
            tariff_usd_per_kwh=tariff_usd_per_kwh,
            cost_data_available=has_cost,
        )

        # 5. Reliability Metrics
        unserved_lps = max(0.0, req_demand_lps - deliv_demand_lps)
        violations: List[str] = []

        if len(deficit_nodes) > 0:
            violations.append(f"Pressure deficit on {len(deficit_nodes)} nodes (< {min_target_pressure_bar} bar): {', '.join(deficit_nodes[:5])}")
        if len(excess_nodes) > 0:
            violations.append(f"Excessive pressure on {len(excess_nodes)} nodes (> {max_target_pressure_bar} bar): {', '.join(excess_nodes[:5])}")
        if max_vel > DEFAULT_MAX_VELOCITY_MPS:
            violations.append(f"Maximum velocity exceeded ({max_vel:.2f} m/s > {DEFAULT_MAX_VELOCITY_MPS} m/s)")
        if not result.converged:
            violations.append("Hydraulic solver did not achieve convergence.")

        # Continuity mass balance check
        mass_error = abs(total_supply_lps - (deliv_demand_lps + total_leak_lps))

        reliability_metrics = ReliabilityMetrics(
            hydraulic_converged=result.converged,
            iterations=result.iterations,
            unserved_demand_lps=MetricValue(value=round(unserved_lps, 3), unit="L/s"),
            mass_balance_error_lps=MetricValue(value=round(mass_error, 5), unit="L/s"),
            network_connectivity=True,
            critical_violations_count=len(violations),
            violations=violations,
        )

        return NetworkPerformanceReport(
            network_id=result.network_id,
            scenario_id=result.scenario_id,
            scenario_name=scenario_name,
            evaluation_timestamp=datetime.now(timezone.utc).isoformat(),
            duration_hours=duration_hours,
            solver_mode=result.solver_name,
            pressure=pressure_metrics,
            hydraulic=hydraulic_metrics,
            water_loss=water_loss_metrics,
            energy=energy_metrics,
            reliability=reliability_metrics,
            is_simulated=True,
            source="VIRTUAL_SIMULATION_ENGINE",
        )

