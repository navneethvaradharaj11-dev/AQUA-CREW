"""
Todini-Pilati Global Gradient Algorithm (GGA) Hydraulic Network Solver (Task 10)
Pure-Python / NumPy implementation of the classical Global Gradient Algorithm for
pressurized water distribution networks using Hazen-Williams friction losses and
pressure-dependent Torricelli orifice leakage models.
"""
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import math
import time

from app.services.hydraulic_engine.simulation_results import (
    HydraulicSimulationResult,
    NodeResult,
    LinkResult,
    TimeStepResult,
)


class TodiniGlobalGradientSolver:
    """
    EXPERIMENTAL: Classical Todini-Pilati Global Gradient Solver.
    Solves mass conservation at nodes and energy conservation along links simultaneously
    via Newton-Raphson iteration on the Schur complement using Hazen-Williams friction.
    Intended for secondary validation and benchmarking against EPANET 2.2.
    """

    def __init__(self, network_data: Dict[str, Any]):
        self.network_data = network_data
        self.nodes = network_data.get("nodes", {})
        self.links = network_data.get("links", {})
        self.overrides = {}

    def apply_overrides(self, overrides: Dict[str, Any]) -> None:
        self.overrides = overrides or {}

    def solve(
        self,
        duration_hours: int = 24,
        timestep_minutes: int = 60,
        demand_multiplier: float = 1.0,
        leak_overrides: Optional[List[Dict[str, Any]]] = None,
        pipe_overrides: Optional[Dict[str, Any]] = None,
        pump_overrides: Optional[Dict[str, Any]] = None,
        raise_on_failure: bool = False,
    ) -> HydraulicSimulationResult:
        import networkx as nx

        start_time = time.perf_counter()

        # Identify fixed head nodes (reservoirs / tanks) vs unknown head junctions
        fixed_nodes = []
        unknown_nodes = []
        node_id_to_idx = {}
        fixed_id_to_idx = {}

        for nid, node in self.nodes.items():
            if node["node_type"] in ("RESERVOIR", "TANK"):
                fixed_id_to_idx[nid] = len(fixed_nodes)
                fixed_nodes.append(nid)
            else:
                node_id_to_idx[nid] = len(unknown_nodes)
                unknown_nodes.append(nid)

        N = len(unknown_nodes)
        N0 = len(fixed_nodes)

        # Validation Rule 1: Must have fixed-head boundary node
        if N0 == 0:
            msg = "Hydraulic solver error: No fixed-head boundary node (Reservoir or Tank) found. System lacks pressure datum."
            if raise_on_failure:
                raise ValueError(msg)
            return HydraulicSimulationResult(
                scenario_id=self.network_data.get("scenario_id", "SCEN-ERROR"),
                network_id=self.network_data.get("network_id", "NET-01"),
                converged=False,
                iterations=0,
                execution_duration_ms=0.0,
                solver_name="EXPERIMENTAL: Todini-Pilati Global Gradient Solver [FAILED]",
                total_supply_lps=0.0,
                total_demand_lps=0.0,
                total_leakage_lps=0.0,
                water_loss_percentage=0.0,
                min_pressure_bar=0.0,
                max_pressure_bar=0.0,
                avg_pressure_bar=0.0,
                pressure_deficit_count=0,
                nodes={},
                links={},
            )

        # Validation Rule 2: Must have unknown-head junctions
        if N == 0:
            msg = "Hydraulic solver error: No junction nodes present to solve."
            if raise_on_failure:
                raise ValueError(msg)

        # Links (pipes, pumps, valves)
        active_links = []
        g = nx.Graph()
        for nid in self.nodes.keys():
            g.add_node(nid)

        for lid, link in self.links.items():
            # Check if overridden closed
            status = link.get("current_status", "OPEN")
            if pipe_overrides and lid in pipe_overrides:
                status = pipe_overrides[lid].get("status", status)
            if link["link_type"] == "PUMP" and pump_overrides and lid in pump_overrides:
                status = pump_overrides[lid].get("status", status)

            active_links.append((lid, link, status))
            if status not in ("CLOSED", "CV_CLOSED"):
                g.add_edge(link["start_node_id"], link["end_node_id"])

        # Validation Rule 3: Graph connectivity to water sources
        disconnected = []
        for j_id in unknown_nodes:
            has_path = any(nx.has_path(g, j_id, f_id) for f_id in fixed_nodes)
            if not has_path:
                disconnected.append(j_id)

        if disconnected:
            msg = f"Hydraulic solver error: Disconnected junction nodes detected: {disconnected}. Nodes have no hydraulic path to a reservoir or storage tank."
            if raise_on_failure:
                raise ValueError(msg)
            return HydraulicSimulationResult(
                scenario_id=self.network_data.get("scenario_id", "SCEN-ERROR"),
                network_id=self.network_data.get("network_id", "NET-01"),
                converged=False,
                iterations=0,
                execution_duration_ms=0.0,
                solver_name="EXPERIMENTAL: Todini-Pilati Global Gradient Solver [DISCONNECTED_TOPOLOGY]",
                total_supply_lps=0.0,
                total_demand_lps=0.0,
                total_leakage_lps=0.0,
                water_loss_percentage=0.0,
                min_pressure_bar=0.0,
                max_pressure_bar=0.0,
                avg_pressure_bar=0.0,
                pressure_deficit_count=len(disconnected),
                nodes={},
                links={},
            )

        M = len(active_links)

        # Baseline heads for fixed nodes
        H0 = np.zeros(N0)
        for i, nid in enumerate(fixed_nodes):
            node = self.nodes[nid]
            if node.get("base_head_m") is not None:
                H0[i] = node["base_head_m"]
            elif node.get("initial_level_m") is not None:
                H0[i] = node["elevation_m"] + node["initial_level_m"]
            else:
                H0[i] = node.get("elevation_m", 0.0) + 50.0

        # Unknown elevations & demands
        Z = np.array([self.nodes[nid]["elevation_m"] for nid in unknown_nodes])
        base_demands_lps = np.array([self.nodes[nid]["base_demand_lps"] for nid in unknown_nodes])
        # Demand in m3/s
        q_demands = (base_demands_lps * demand_multiplier) / 1000.0

        # Build incidence matrices A12 (links x unknown nodes) and A10 (links x fixed nodes)
        A12 = np.zeros((M, N))
        A10 = np.zeros((M, N0))

        # Link parameters
        pipe_lengths = np.zeros(M)
        pipe_diams_m = np.zeros(M)
        pipe_rough = np.zeros(M)
        link_types = []
        pump_heads = np.zeros(M)
        is_pump = np.zeros(M, dtype=bool)

        for m, (lid, link, status) in enumerate(active_links):
            u = link["start_node_id"]
            v = link["end_node_id"]
            link_types.append(link["link_type"])

            if u in node_id_to_idx:
                A12[m, node_id_to_idx[u]] = 1.0
            elif u in fixed_id_to_idx:
                A10[m, fixed_id_to_idx[u]] = 1.0

            if v in node_id_to_idx:
                A12[m, node_id_to_idx[v]] = -1.0
            elif v in fixed_id_to_idx:
                A10[m, fixed_id_to_idx[v]] = -1.0

            raw_diam = float(link.get("diameter_mm", 300.0))
            raw_rough = float(link.get("roughness", 140.0))
            raw_len = float(link.get("length_m", 500.0))

            if raw_diam <= 0 or raw_rough <= 0 or raw_len <= 0:
                msg = f"Hydraulic solver error: Invalid physical properties for link {lid}: diameter_mm={raw_diam}, roughness={raw_rough}, length_m={raw_len} must all be strictly positive."
                if raise_on_failure:
                    raise ValueError(msg)
                return HydraulicSimulationResult(
                    scenario_id=self.network_data.get("scenario_id", "SCEN-ERROR"),
                    network_id=self.network_data.get("network_id", "NET-01"),
                    converged=False,
                    iterations=0,
                    execution_duration_ms=0.0,
                    solver_name="EXPERIMENTAL: Todini-Pilati Global Gradient Solver [INVALID_PARAMETERS]",
                    total_supply_lps=0.0,
                    total_demand_lps=0.0,
                    total_leakage_lps=0.0,
                    water_loss_percentage=0.0,
                    min_pressure_bar=0.0,
                    max_pressure_bar=0.0,
                    avg_pressure_bar=0.0,
                    pressure_deficit_count=0,
                    nodes={},
                    links={},
                )

            pipe_lengths[m] = max(1.0, raw_len)
            pipe_diams_m[m] = max(0.05, raw_diam / 1000.0)
            pipe_rough[m] = max(50.0, raw_rough)

            if link["link_type"] == "PUMP" and status not in ("CLOSED", "CV_CLOSED"):
                is_pump[m] = True
                pump_speed = float(link.get("pump_speed", 1.0))
                pump_curve = link.get("pump_curve_coeffs")
                if isinstance(pump_curve, dict) and "h0" in pump_curve:
                    pump_heads[m] = float(pump_curve["h0"]) * (pump_speed ** 2)
                elif link.get("pump_head_m") is not None:
                    pump_heads[m] = float(link["pump_head_m"]) * (pump_speed ** 2)
                else:
                    pump_heads[m] = 45.0 * (pump_speed ** 2)

        # Hazen-Williams resistance constant: r = 10.67 * L / (C^1.852 * D^4.87)
        r_hw = 10.67 * pipe_lengths / ((pipe_rough ** 1.852) * (pipe_diams_m ** 4.87))

        # Initial link flows Q in m3/s (reasonable initial guess)
        Q = np.full(M, 0.05)
        # Initial heads H in meters
        H = np.full(N, np.mean(H0) if N0 > 0 else 50.0)

        # Leak orifices mapping
        # leak format: [{"node_id": "...", "area_m2": 0.001, "discharge_coeff": 0.75}]
        active_leaks = {}
        if leak_overrides:
            for lk in leak_overrides:
                active_leaks[lk["node_id"]] = {
                    "area": float(lk.get("area_m2", 0.001)),
                    "cd": float(lk.get("discharge_coeff", 0.75)),
                }

        # Newton-Raphson iteration
        max_iter = 50
        tol = 1e-4
        converged = False
        iteration = 0

        for iteration in range(1, max_iter + 1):
            # Compute head losses h_f and derivatives dh_f/dQ
            abs_Q = np.abs(Q)
            abs_Q = np.maximum(abs_Q, 1e-6)  # Avoid singularity near 0

            # h_f = r * Q * |Q|^0.852
            h_f = r_hw * Q * (abs_Q ** 0.852)
            # Subtract pump head boost
            h_f[is_pump] -= pump_heads[is_pump]

            # g_prime = dh_f / dQ = 1.852 * r * |Q|^0.852
            g_prime = 1.852 * r_hw * (abs_Q ** 0.852)
            g_prime[is_pump] = 1e-2  # Small non-zero gradient for pump

            # Handle closed pipes
            for m, (lid, link, status) in enumerate(active_links):
                if status == "CLOSED":
                    g_prime[m] = 1e9
                    h_f[m] = 1e9 * Q[m]

            # A11 is diagonal matrix of g_prime
            A11_inv_diag = 1.0 / g_prime

            # Leak discharges at unknown nodes
            q_leaks = np.zeros(N)
            dq_leak_dH = np.zeros(N)
            for j, nid in enumerate(unknown_nodes):
                if nid in active_leaks:
                    lk = active_leaks[nid]
                    P_head = max(0.0, H[j] - Z[j])
                    if P_head > 0.0:
                        # Q_leak = Cd * A * sqrt(2 * g * P_head)
                        q_l = lk["cd"] * lk["area"] * math.sqrt(2.0 * 9.81 * P_head)
                        q_leaks[j] = q_l
                        dq_leak_dH[j] = 0.5 * q_l / P_head

            # Effective demands at nodes
            q_total_demand = q_demands + q_leaks

            # Residual for node continuity: F_nodes = A12^T * Q - q_total_demand
            F_nodes = np.dot(A12.T, Q) - q_total_demand

            # Energy residual along links: F_links = A12 * H + A10 * H0 + h_f
            F_links = np.dot(A12, H) + np.dot(A10, H0) + h_f

            # Schur Complement Matrix: S = A12^T * A11^-1 * A12 + diag(dq_leak_dH)
            # S is (N x N)
            A11_inv_A12 = A12 * A11_inv_diag[:, np.newaxis]
            S = np.dot(A12.T, A11_inv_A12)
            if np.any(dq_leak_dH > 0):
                S += np.diag(dq_leak_dH)

            # Right hand side for head increment:
            # rhs = A12^T * (Q - A11^-1 * F_links) - q_total_demand
            rhs = np.dot(A12.T, Q - A11_inv_diag * F_links) - q_total_demand

            try:
                dH = np.linalg.solve(S, rhs)
            except np.linalg.LinAlgError:
                dH = np.linalg.lstsq(S, rhs, rcond=None)[0]

            # Update link flows: dQ = - A11^-1 * (F_links + A12 * dH)
            dQ = - A11_inv_diag * (F_links + np.dot(A12, dH))

            # Damping to guarantee robust convergence
            alpha = 1.0
            if np.max(np.abs(dQ)) > 0.5:
                alpha = 0.7

            H += alpha * dH
            Q += alpha * dQ

            # Convergence check
            norm_dQ = np.max(np.abs(dQ))
            norm_dH = np.max(np.abs(dH))
            if norm_dQ < tol and norm_dH < tol:
                converged = True
                break

        if not converged and raise_on_failure:
            raise RuntimeError(
                f"Todini Global Gradient solver failed to converge within {max_iter} iterations (Residual ||dQ||={norm_dQ:.2e}, ||dH||={norm_dH:.2e})."
            )

        exec_duration = (time.perf_counter() - start_time) * 1000.0

        # Assemble node results
        node_results = {}
        total_demand_lps = 0.0
        total_leak_lps = 0.0
        pressure_deficit_count = 0

        pressures_bar = []

        for j, nid in enumerate(unknown_nodes):
            n_meta = self.nodes[nid]
            h_m = float(H[j])
            elev = float(Z[j])
            p_head = h_m - elev
            p_bar = p_head * 0.0980665
            p_psi = p_bar * 14.5038
            pressures_bar.append(p_bar)

            act_dem_lps = float(q_demands[j] * 1000.0)
            leak_lps = float(q_leaks[j] * 1000.0)
            total_demand_lps += act_dem_lps
            total_leak_lps += leak_lps

            min_p = n_meta.get("min_pressure_bar", 1.5)
            is_deficit = p_bar < min_p
            if is_deficit:
                pressure_deficit_count += 1

            status = "NORMAL"
            if p_bar < 0.5:
                status = "CRITICAL_LOW"
            elif is_deficit:
                status = "DEFICIT"
            elif leak_lps > 2.0:
                status = "BURST"
            elif leak_lps > 0.1:
                status = "LEAK"

            node_results[nid] = NodeResult(
                node_id=nid,
                name=n_meta.get("name", nid),
                node_type=n_meta.get("node_type", "JUNCTION"),
                pressure_bar=round(p_bar, 3),
                pressure_psi=round(p_psi, 2),
                head_m=round(h_m, 2),
                elevation_m=round(elev, 2),
                actual_demand_lps=round(act_dem_lps, 3),
                expected_demand_lps=round(n_meta.get("base_demand_lps", 0.0) * demand_multiplier, 3),
                leak_flow_lps=round(leak_lps, 3),
                pressure_deficit=is_deficit,
                status=status,
            )

        for i, nid in enumerate(fixed_nodes):
            n_meta = self.nodes[nid]
            h_m = float(H0[i])
            elev = float(n_meta.get("elevation_m", 0.0))
            p_bar = (h_m - elev) * 0.0980665
            pressures_bar.append(p_bar)

            node_results[nid] = NodeResult(
                node_id=nid,
                name=n_meta.get("name", nid),
                node_type=n_meta.get("node_type", "RESERVOIR"),
                pressure_bar=round(p_bar, 3),
                pressure_psi=round(p_bar * 14.5038, 2),
                head_m=round(h_m, 2),
                elevation_m=round(elev, 2),
                actual_demand_lps=0.0,
                expected_demand_lps=0.0,
                leak_flow_lps=0.0,
                pressure_deficit=False,
                status="NORMAL",
            )

        # Assemble link results
        link_results = {}
        for m, (lid, link, status) in enumerate(active_links):
            q_flow_lps = float(Q[m] * 1000.0)
            area_m2 = math.pi * ((pipe_diams_m[m] / 2.0) ** 2)
            velocity = abs(Q[m]) / area_m2
            hl_m = float(abs(h_f[m]))
            unit_hl = (hl_m / pipe_lengths[m]) * 1000.0  # m / km

            direction = "FORWARD" if q_flow_lps >= 0 else "REVERSE"
            if abs(q_flow_lps) < 1e-4:
                direction = "ZERO"

            l_status = status
            if abs(q_flow_lps) > 120.0:
                l_status = "BURST"

            link_results[lid] = LinkResult(
                link_id=lid,
                name=link.get("name", lid),
                link_type=link.get("link_type", "PIPE"),
                flow_lps=round(q_flow_lps, 5),
                velocity_mps=round(velocity, 3),
                headloss_m=round(hl_m, 3),
                unit_headloss_m_per_km=round(unit_hl, 3),
                friction_factor=round(float(pipe_rough[m]), 1),
                direction=direction,
                status=l_status,
                pipeline_segment_id=link.get("pipeline_segment_id"),
            )

        # Calculate network supply
        total_supply_lps = total_demand_lps + total_leak_lps
        water_loss_pct = (total_leak_lps / total_supply_lps * 100.0) if total_supply_lps > 0 else 0.0

        min_p = min(pressures_bar) if pressures_bar else 0.0
        max_p = max(pressures_bar) if pressures_bar else 0.0
        avg_p = sum(pressures_bar) / len(pressures_bar) if pressures_bar else 0.0

        solver_name = (
            "EXPERIMENTAL: Todini-Pilati Global Gradient Solver (Python / Hazen-Williams)"
            if converged
            else "EXPERIMENTAL: Todini-Pilati Global Gradient Solver [NON_CONVERGED]"
        )

        return HydraulicSimulationResult(
            scenario_id=self.network_data.get("scenario_id", "SCEN-TODINI-01"),
            network_id=self.network_data.get("network_id", "NET-01"),
            converged=converged,
            iterations=iteration,
            execution_duration_ms=exec_duration,
            solver_name=solver_name,
            total_supply_lps=total_supply_lps,
            total_demand_lps=total_demand_lps,
            total_leakage_lps=total_leak_lps,
            water_loss_percentage=water_loss_pct,
            min_pressure_bar=min_p,
            max_pressure_bar=max_p,
            avg_pressure_bar=avg_p,
            pressure_deficit_count=pressure_deficit_count,
            nodes=node_results,
            links=link_results,
            timesteps=[],
        )

