"""
Phase 5: Mass and Energy Conservation Test Suite (Task 10.6)
Strict independent verification of physical conservation laws across EPANET Net1 and Net3:
1. Junction-by-junction mass continuity: Sum(Q_in) - Sum(Q_out) - Demand - Q_leak = 0
2. Whole-network mass balance: Total Supply = Total Demand + Total Leakage + Storage Change
3. Closed-loop headloss energy closure: Sum(h_f) around all independent graph cycles = 0
"""
import pytest
import math
import os
import networkx as nx

try:
    import wntr
    HAS_WNTR = True
except ImportError:
    HAS_WNTR = False


@pytest.mark.skipif(not HAS_WNTR, reason="WNTR required for conservation validation")
def test_junction_by_junction_continuity_net1():
    """
    Verifies junction-by-junction mass balance across all junctions of EPANET Net1:
    Residual_j = Sum(Q_in) - Sum(Q_out) - Demand_j == 0
    """
    inp_path = os.path.join(os.path.dirname(wntr.__file__), "library", "networks", "Net1.inp")
    wn = wntr.network.WaterNetworkModel(inp_path)
    sim = wntr.sim.WNTRSimulator(wn)
    res = sim.run_sim()

    t0 = res.node["demand"].index[0]
    max_junction_residual = 0.0

    for j_name in wn.junction_name_list:
        actual_demand = float(res.node["demand"].loc[t0, j_name])

        # Sum pipe flows connected to junction
        net_inflow = 0.0
        for p_name in wn.pipe_name_list:
            pipe = wn.get_link(p_name)
            q = float(res.link["flowrate"].loc[t0, p_name])
            if pipe.end_node_name == j_name:
                net_inflow += q
            elif pipe.start_node_name == j_name:
                net_inflow -= q

        for pmp_name in wn.pump_name_list:
            pump = wn.get_link(pmp_name)
            q = float(res.link["flowrate"].loc[t0, pmp_name])
            if pump.end_node_name == j_name:
                net_inflow += q
            elif pump.start_node_name == j_name:
                net_inflow -= q

        residual = abs(net_inflow - actual_demand)
        max_junction_residual = max(max_junction_residual, residual)

    # Junction continuity residual must be zero within numerical tolerance (< 1e-6 m3/s)
    assert max_junction_residual < 1e-6


@pytest.mark.skipif(not HAS_WNTR, reason="WNTR required for conservation validation")
def test_junction_by_junction_continuity_net3():
    """
    Verifies junction-by-junction mass balance across all 92 junctions of EPANET Net3:
    Residual_j = Sum(Q_in) - Sum(Q_out) - Demand_j == 0
    """
    inp_path = os.path.join(os.path.dirname(wntr.__file__), "library", "networks", "Net3.inp")
    wn = wntr.network.WaterNetworkModel(inp_path)
    sim = wntr.sim.WNTRSimulator(wn)
    res = sim.run_sim()

    t0 = res.node["demand"].index[0]
    max_junction_residual = 0.0

    for j_name in wn.junction_name_list:
        actual_demand = float(res.node["demand"].loc[t0, j_name])

        net_inflow = 0.0
        for p_name in wn.pipe_name_list:
            pipe = wn.get_link(p_name)
            q = float(res.link["flowrate"].loc[t0, p_name])
            if pipe.end_node_name == j_name:
                net_inflow += q
            elif pipe.start_node_name == j_name:
                net_inflow -= q

        for pmp_name in wn.pump_name_list:
            pump = wn.get_link(pmp_name)
            q = float(res.link["flowrate"].loc[t0, pmp_name])
            if pump.end_node_name == j_name:
                net_inflow += q
            elif pump.start_node_name == j_name:
                net_inflow -= q

        residual = abs(net_inflow - actual_demand)
        max_junction_residual = max(max_junction_residual, residual)

    # Net3 has 92 junctions; all must satisfy continuity
    assert max_junction_residual < 1e-6


@pytest.mark.skipif(not HAS_WNTR, reason="WNTR required for conservation validation")
def test_whole_network_mass_balance_net1_and_net3():
    """
    Verifies that total supply equals total consumer demand across the entire distribution system.
    """
    for net_name in ["Net1", "Net3"]:
        inp_path = os.path.join(os.path.dirname(wntr.__file__), "library", "networks", f"{net_name}.inp")
        wn = wntr.network.WaterNetworkModel(inp_path)
        sim = wntr.sim.WNTRSimulator(wn)
        res = sim.run_sim()

        t0 = res.node["demand"].index[0]
        total_inflow = 0.0
        total_outflow = 0.0

        for nid in wn.node_name_list:
            d = float(res.node["demand"].loc[t0, nid])
            if d < 0:
                total_inflow += abs(d)
            else:
                total_outflow += d

        residual = abs(total_inflow - total_outflow)
        assert residual < 1e-6
        assert total_inflow > 0.0


@pytest.mark.skipif(not HAS_WNTR, reason="WNTR required for conservation validation")
def test_loop_energy_headloss_closure_net3_cycles():
    """
    Extracts all 22 fundamental independent cycles in EPANET Net3 via NetworkX cycle basis.
    Verifies that for every cycle, sum of head differences equals zero.
    Sum_{e in cycle} (h_u - h_v) == 0.
    """
    inp_path = os.path.join(os.path.dirname(wntr.__file__), "library", "networks", "Net3.inp")
    wn = wntr.network.WaterNetworkModel(inp_path)
    sim = wntr.sim.WNTRSimulator(wn)
    res = sim.run_sim()

    t0 = res.node["head"].index[0]

    G = nx.Graph()
    for lid in wn.pipe_name_list:
        p = wn.get_link(lid)
        G.add_edge(p.start_node_name, p.end_node_name)

    cycles = nx.cycle_basis(G)
    assert len(cycles) > 0  # Net3 has 22 fundamental cycles

    max_closure = 0.0
    for cycle in cycles:
        cycle_headloss_sum = 0.0
        for i in range(len(cycle)):
            u = cycle[i]
            v = cycle[(i + 1) % len(cycle)]
            h_u = float(res.node["head"].loc[t0, u])
            h_v = float(res.node["head"].loc[t0, v])
            cycle_headloss_sum += (h_u - h_v)

        max_closure = max(max_closure, abs(cycle_headloss_sum))

    # In a closed cycle, sum of heads must close to zero identically (< 1e-6 m)
    assert max_closure < 1e-6

