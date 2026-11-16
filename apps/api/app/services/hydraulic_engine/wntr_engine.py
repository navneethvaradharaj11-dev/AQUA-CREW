"""
WNTR / EPANET Hydraulic Simulation Engine Adapter (Task 10)
Integrates EPA Water Network Tool for Resilience (WNTR) and EPANET 2.2 solver
supporting extended-period simulation, pressure-dependent demand (PDD),
Torricelli orifice leaks, booster pumps, control valves, and storage tanks.
"""
from typing import Dict, Any, List, Optional
import time
import math
from datetime import datetime, timezone

try:
    import wntr
    HAS_WNTR = True
except ImportError:
    HAS_WNTR = False

from app.services.hydraulic_engine.base_engine import HydraulicEngineBase
from app.services.hydraulic_engine.simulation_results import (
    HydraulicSimulationResult,
    NodeResult,
    LinkResult,
    TimeStepResult,
)
from app.services.hydraulic_engine.todini_solver import TodiniGlobalGradientSolver


DEFAULT_DIURNAL_PATTERN = [
    0.65, 0.55, 0.50, 0.55, 0.70, 0.95,  # 00:00 - 05:00 Early morning low
    1.25, 1.45, 1.35, 1.15, 1.05, 1.00,  # 06:00 - 11:00 Morning peak
    1.10, 1.15, 1.05, 1.00, 1.10, 1.25,  # 12:00 - 17:00 Midday moderate
    1.40, 1.35, 1.20, 1.00, 0.85, 0.70,  # 18:00 - 23:00 Evening peak
]


class WNTREngine(HydraulicEngineBase):
    """
    High-fidelity hydraulic solver powered by WNTR and EPANET 2.2.
    Translates AQUA CREW digital twin topologies and executes physical simulations.
    """

    def __init__(self, network_data: Dict[str, Any]):
        self.network_data = network_data
        self.overrides: Dict[str, Any] = {}
        self.wn = None

    def build_network(self, network_data: Optional[Dict[str, Any]] = None) -> None:
        if network_data:
            self.network_data = network_data

        if not HAS_WNTR:
            return

        wn = wntr.network.WaterNetworkModel()

        # Diurnal pattern
        pattern_vals = self.network_data.get("diurnal_pattern", DEFAULT_DIURNAL_PATTERN)
        wn.add_pattern("DIURNAL", pattern_vals)

        nodes = self.network_data.get("nodes", {})
        links = self.network_data.get("links", {})

        # Add Nodes (Reservoirs, Tanks, Junctions)
        for nid, node in nodes.items():
            ntype = node.get("node_type", "JUNCTION").upper()
            elev = float(node.get("elevation_m", 15.0))

            if ntype == "RESERVOIR":
                base_head = float(node.get("base_head_m", elev + 50.0))
                wn.add_reservoir(nid, base_head=base_head)
            elif ntype == "TANK":
                init_lvl = float(node.get("initial_level_m", 5.0))
                min_lvl = float(node.get("min_level_m", 1.0))
                max_lvl = float(node.get("max_level_m", 12.0))
                diam = float(node.get("diameter_m", 15.0))
                wn.add_tank(
                    nid,
                    elevation=elev,
                    init_level=init_lvl,
                    min_level=min_lvl,
                    max_level=max_lvl,
                    diameter=diam,
                )
            else:  # JUNCTION
                # Base demand in m3/s (converted from L/s)
                base_dem_m3s = float(node.get("base_demand_lps", 0.0)) / 1000.0
                wn.add_junction(
                    nid,
                    elevation=elev,
                    base_demand=base_dem_m3s,
                    demand_pattern="DIURNAL",
                )

        # Add Links (Pipes, Pumps, Valves)
        for lid, link in links.items():
            ltype = link.get("link_type", "PIPE").upper()
            u = link.get("start_node_id")
            v = link.get("end_node_id")
            status = link.get("current_status", "OPEN").upper()

            if ltype == "PUMP":
                curve_id = f"PUMP_CURVE_{lid}"
                # Add default 3-point pump curve (flow in m3/s, head in m)
                wn.add_curve(curve_id, "HEAD", [(0.0, 65.0), (0.15, 58.0), (0.35, 45.0)])
                pump = wn.add_pump(lid, u, v, pump_type="HEAD", pump_parameter=curve_id)
                if status == "CLOSED":
                    pump.initial_status = wntr.network.LinkStatus.Closed

            elif ltype == "VALVE":
                # Add PRV or FCV valve
                setting = float(link.get("valve_setting", 3.5)) * 10.197  # bar to meters of head
                valve = wn.add_valve(
                    lid,
                    u,
                    v,
                    diameter=float(link.get("diameter_mm", 300.0)) / 1000.0,
                    valve_type="PRV",
                    initial_setting=setting,
                    initial_status=wntr.network.LinkStatus.Closed if status == "CLOSED" else wntr.network.LinkStatus.Active,
                )

            else:  # PIPE
                length_m = max(1.0, float(link.get("length_m", 500.0)))
                diam_m = max(0.05, float(link.get("diameter_mm", 300.0)) / 1000.0)
                roughness = max(50.0, float(link.get("roughness", 140.0)))
                minor_loss = float(link.get("minor_loss", 0.0))

                pipe = wn.add_pipe(
                    lid,
                    u,
                    v,
                    length=length_m,
                    diameter=diam_m,
                    roughness=roughness,
                    minor_loss=minor_loss,
                )
                if status == "CLOSED":
                    pipe.initial_status = wntr.network.LinkStatus.Closed

        self.wn = wn

    def apply_overrides(self, overrides: Dict[str, Any]) -> None:
        self.overrides = overrides or {}
        if not self.wn:
            return

        # 1. Demand multipliers
        multiplier = float(self.overrides.get("demand_multiplier", 1.0))
        if multiplier != 1.0:
            for _, junc in self.wn.junctions():
                for d in junc.demand_timeseries_list:
                    if hasattr(d, "base_value"):
                        d.base_value *= multiplier
                    elif hasattr(d, "base"):
                        d.base *= multiplier

        # 2. Pipe overrides (Burst / Isolation)
        pipe_overrides = self.overrides.get("pipe_overrides", {})
        for pid, pdata in pipe_overrides.items():
            if pid in self.wn.link_name_list:
                link = self.wn.get_link(pid)
                if pdata.get("status") == "CLOSED":
                    link.initial_status = wntr.network.LinkStatus.Closed

        # 3. Pump overrides (Trip / Shutdown)
        pump_overrides = self.overrides.get("pump_overrides", {})
        for pmid, pdata in pump_overrides.items():
            if pmid in self.wn.link_name_list:
                pump = self.wn.get_link(pmid)
                if pdata.get("status") == "CLOSED" or pdata.get("speed", 1.0) == 0.0:
                    pump.initial_status = wntr.network.LinkStatus.Closed

        # 4. Leak overrides
        # [{"node_id": "...", "area_m2": 0.001, "discharge_coeff": 0.75}]
        leaks = self.overrides.get("leaks", [])
        for leak in leaks:
            nid = leak.get("node_id")
            if nid and nid in self.wn.node_name_list:
                node = self.wn.get_node(nid)
                if isinstance(node, wntr.network.elements.Junction):
                    area = float(leak.get("area_m2", 0.0008))
                    cd = float(leak.get("discharge_coeff", 0.75))
                    node.add_leak(self.wn, area=area, discharge_coeff=cd, start_time=0)

    def run_simulation(
        self,
        duration_hours: int = 24,
        timestep_minutes: int = 60,
        demand_model: str = "PDA"
    ) -> HydraulicSimulationResult:
        if not HAS_WNTR:
            # Fall back to pure-Python Todini solver
            solver = TodiniGlobalGradientSolver(self.network_data)
            return solver.solve(
                duration_hours=duration_hours,
                timestep_minutes=timestep_minutes,
                demand_multiplier=float(self.overrides.get("demand_multiplier", 1.0)),
                leak_overrides=self.overrides.get("leaks", []),
                pipe_overrides=self.overrides.get("pipe_overrides", {}),
                pump_overrides=self.overrides.get("pump_overrides", {}),
            )

        # Build network and apply overrides
        self.build_network()
        self.apply_overrides(self.overrides)

        # Configure time options
        self.wn.options.time.duration = duration_hours * 3600
        self.wn.options.time.hydraulic_timestep = timestep_minutes * 60

        start_time = time.perf_counter()
        solver_name = "WNTR / EPANET 2.2 Pressure-Driven Simulation Engine"

        try:
            if demand_model.upper() == "DDA":
                sim = wntr.sim.EpanetSimulator(self.wn)
                solver_name = "EPANET 2.2 Demand-Driven Simulation Engine"
            else:
                self.wn.options.hydraulic.demand_model = "PDD"
                self.wn.options.hydraulic.minimum_pressure = 0.5 * 10.197  # 0.5 bar to m
                self.wn.options.hydraulic.required_pressure = 1.5 * 10.197  # 1.5 bar to m
                sim = wntr.sim.WNTRSimulator(self.wn)
                solver_name = "WNTR / EPANET 2.2 Pressure-Driven Simulation Engine"

            results = sim.run_sim()
            converged = True
        except Exception as ex:
            # Per Rule 11 & Section 6: Never silently substitute a solver on failure
            raise RuntimeError(f"Hydraulic solver ({demand_model}) execution failed: {str(ex)}")

        exec_duration = (time.perf_counter() - start_time) * 1000.0

        # Process results
        # Extract t=0 or first available timestamp for steady-state snapshot
        t0 = results.node["pressure"].index[0]

        nodes_dict = self.network_data.get("nodes", {})
        links_dict = self.network_data.get("links", {})

        node_results = {}
        total_demand_lps = 0.0
        total_leak_lps = 0.0
        pressure_deficit_count = 0
        pressures_bar = []

        for nid, n_meta in nodes_dict.items():
            ntype = n_meta.get("node_type", "JUNCTION")
            elev = float(n_meta.get("elevation_m", 15.0))

            if nid in results.node["pressure"].columns:
                p_head = float(results.node["pressure"].loc[t0, nid])
                p_bar = p_head * 0.0980665
                p_psi = p_bar * 14.5038
                h_m = float(results.node["head"].loc[t0, nid])
            else:
                p_bar = 0.0
                p_psi = 0.0
                h_m = elev

            if ntype == "JUNCTION":
                pressures_bar.append(p_bar)

            act_dem_lps = 0.0
            if "demand" in results.node and nid in results.node["demand"].columns:
                act_dem_lps = float(results.node["demand"].loc[t0, nid]) * 1000.0

            leak_lps = 0.0
            if "leak_demand" in results.node and nid in results.node["leak_demand"].columns:
                leak_lps = float(results.node["leak_demand"].loc[t0, nid]) * 1000.0

            if ntype == "JUNCTION":
                total_demand_lps += max(0.0, act_dem_lps)
            total_leak_lps += leak_lps

            min_p = float(n_meta.get("min_pressure_bar", 1.5))
            if ntype == "JUNCTION":
                is_deficit = p_bar < min_p
                if is_deficit:
                    pressure_deficit_count += 1
                    status = "DEFICIT" if p_bar >= 0.5 else "CRITICAL_LOW"
                else:
                    status = "NORMAL"

                if leak_lps > 2.0:
                    status = "BURST"
                elif leak_lps > 0.1:
                    status = "LEAK"
            else:
                is_deficit = False
                status = "NORMAL"

            node_results[nid] = NodeResult(
                node_id=nid,
                name=n_meta.get("name", nid),
                node_type=ntype,
                pressure_bar=round(p_bar, 3),
                pressure_psi=round(p_psi, 2),
                head_m=round(h_m, 2),
                elevation_m=round(elev, 2),
                actual_demand_lps=round(act_dem_lps, 3),
                expected_demand_lps=round(float(n_meta.get("base_demand_lps", 0.0)), 3),
                leak_flow_lps=round(leak_lps, 3),
                pressure_deficit=is_deficit,
                status=status,
            )

        link_results = {}
        for lid, link in links_dict.items():
            ltype = link.get("link_type", "PIPE")
            diam_m = float(link.get("diameter_mm", 300.0)) / 1000.0
            length_m = float(link.get("length_m", 500.0))

            q_flow_lps = 0.0
            if "flowrate" in results.link and lid in results.link["flowrate"].columns:
                q_flow_lps = float(results.link["flowrate"].loc[t0, lid]) * 1000.0

            area_m2 = math.pi * ((diam_m / 2.0) ** 2)
            velocity = abs(q_flow_lps / 1000.0) / area_m2 if area_m2 > 0 else 0.0

            # Approximate head loss
            c_hw = float(link.get("roughness", 140.0))
            hl_m = 10.67 * (length_m / ((c_hw ** 1.852) * (diam_m ** 4.87))) * ((abs(q_flow_lps) / 1000.0) ** 1.852)
            unit_hl = (hl_m / length_m) * 1000.0 if length_m > 0 else 0.0

            direction = "FORWARD" if q_flow_lps >= 0 else "REVERSE"
            if abs(q_flow_lps) < 1e-4:
                direction = "ZERO"

            l_status = link.get("current_status", "OPEN")
            if abs(q_flow_lps) > 120.0:
                l_status = "BURST"

            link_results[lid] = LinkResult(
                link_id=lid,
                name=link.get("name", lid),
                link_type=ltype,
                flow_lps=round(q_flow_lps, 3),
                velocity_mps=round(velocity, 3),
                headloss_m=round(hl_m, 3),
                unit_headloss_m_per_km=round(unit_hl, 3),
                friction_factor=c_hw,
                direction=direction,
                status=l_status,
                pipeline_segment_id=link.get("pipeline_segment_id"),
            )

        # Extended period timestep metrics
        timesteps = []
        for step_idx, step_time in enumerate(results.node["pressure"].index):
            offset_h = step_time / 3600.0
            node_p_step = {}
            deficit_step = []

            for nid in nodes_dict.keys():
                if nid in results.node["pressure"].columns:
                    p = float(results.node["pressure"].loc[step_time, nid]) * 0.0980665
                    node_p_step[nid] = round(p, 3)
                    if p < float(nodes_dict[nid].get("min_pressure_bar", 1.5)):
                        deficit_step.append(nid)

            link_f_step = {}
            for lid in links_dict.keys():
                if "flowrate" in results.link and lid in results.link["flowrate"].columns:
                    link_f_step[lid] = round(float(results.link["flowrate"].loc[step_time, lid]) * 1000.0, 3)

            timesteps.append(
                TimeStepResult(
                    step_index=step_idx,
                    time_offset_hours=round(offset_h, 2),
                    timestamp_iso=f"+{int(offset_h):02d}:00",
                    demand_multiplier=DEFAULT_DIURNAL_PATTERN[step_idx % len(DEFAULT_DIURNAL_PATTERN)],
                    total_supply_lps=round(total_demand_lps + total_leak_lps, 2),
                    total_demand_lps=round(total_demand_lps, 2),
                    total_leakage_lps=round(total_leak_lps, 2),
                    min_pressure_bar=round(min(node_p_step.values()) if node_p_step else 0.0, 3),
                    max_pressure_bar=round(max(node_p_step.values()) if node_p_step else 0.0, 3),
                    pressure_deficit_nodes=deficit_step,
                    node_pressures=node_p_step,
                    link_flows=link_f_step,
                )
            )

        total_supply_lps = total_demand_lps + total_leak_lps
        water_loss_pct = (total_leak_lps / total_supply_lps * 100.0) if total_supply_lps > 0 else 0.0

        min_p = min(pressures_bar) if pressures_bar else 0.0
        max_p = max(pressures_bar) if pressures_bar else 0.0
        avg_p = sum(pressures_bar) / len(pressures_bar) if pressures_bar else 0.0

        return HydraulicSimulationResult(
            scenario_id=self.network_data.get("scenario_id", "SCEN-WNTR-01"),
            network_id=self.network_data.get("network_id", "NET-01"),
            converged=converged,
            iterations=1,
            execution_duration_ms=exec_duration,
            solver_name="WNTR / EPANET 2.2 Pressure-Driven Simulation Engine",
            total_supply_lps=round(total_supply_lps, 3),
            total_demand_lps=round(total_demand_lps, 3),
            total_leakage_lps=round(total_leak_lps, 3),
            water_loss_percentage=round(water_loss_pct, 2),
            min_pressure_bar=round(min_p, 3),
            max_pressure_bar=round(max_p, 3),
            avg_pressure_bar=round(avg_p, 3),
            pressure_deficit_count=pressure_deficit_count,
            nodes=node_results,
            links=link_results,
            timesteps=timesteps,
        )
