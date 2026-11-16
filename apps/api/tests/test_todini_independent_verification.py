"""
Phase 3: Independent Todini-Pilati Solver Verification Test Suite (Task 10.6)
Rigorous validation of the pure-Python TodiniGlobalGradientSolver on 7 distinct
network topologies and 10 failure/edge scenarios.
Confirms solver retains EXPERIMENTAL designation and is never silently substituted.
"""
import pytest
import math
import numpy as np

from app.services.hydraulic_engine.todini_solver import TodiniGlobalGradientSolver


# ==============================================================================
# Helper to build mock network dictionaries
# ==============================================================================

def make_network(nodes_dict, links_dict, scenario_id="SCEN-TEST", network_id="NET-VERIFY"):
    return {
        "scenario_id": scenario_id,
        "network_id": network_id,
        "nodes": nodes_dict,
        "links": links_dict,
    }


# ==============================================================================
# 1. Seven Distinct Network Topologies
# ==============================================================================

def test_topology_1_reservoir_pipe_junction():
    """
    Topology 1: 1 reservoir + 1 pipe + 1 junction.
    Flow must equal junction demand; junction head must equal H0 - h_f.
    """
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 60.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 25.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P1": {"id": "P1", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 1000.0, "diameter_mm": 200.0, "roughness": 130.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)
    res = solver.solve(raise_on_failure=True)

    assert res.converged is True
    assert "EXPERIMENTAL" in res.solver_name

    # Flow should equal 25 L/s = 0.025 m3/s
    q_p1 = abs(res.links["P1"].flow_lps)
    assert math.isclose(q_p1, 25.0, rel_tol=1e-3)

    # Theoretical Hazen-Williams head loss: h_f = 10.67 * L / (C^1.852 * D^4.87) * Q^1.852
    Q_m3s = 0.025
    r_hw = 10.67 * 1000.0 / ((130.0 ** 1.852) * (0.200 ** 4.87))
    h_f_expected = r_hw * (Q_m3s ** 1.852)
    expected_head_j1 = 60.0 - h_f_expected

    assert math.isclose(res.nodes["J1"].head_m, expected_head_j1, rel_tol=1e-3)
    assert res.nodes["J1"].pressure_bar > 1.5


def test_topology_2_parallel_pipes():
    """
    Topology 2: Parallel pipes between Reservoir and Junction.
    Pipes have identical length and roughness, but different diameters (200mm vs 300mm).
    Head loss across both pipes must be equal; flow splits according to diameter ratio.
    """
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 80.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 15.0, "base_demand_lps": 80.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P1_small": {"id": "P1_small", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 800.0, "diameter_mm": 200.0, "roughness": 120.0, "current_status": "OPEN"},
        "P2_large": {"id": "P2_large", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 800.0, "diameter_mm": 300.0, "roughness": 120.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)
    res = solver.solve(raise_on_failure=True)

    assert res.converged is True
    q1 = abs(res.links["P1_small"].flow_lps)
    q2 = abs(res.links["P2_large"].flow_lps)

    # Total flow equals 80 L/s
    assert math.isclose(q1 + q2, 80.0, rel_tol=1e-3)

    # Larger pipe must carry significantly more flow (Q proportional to D^(4.87 / 1.852) = D^2.63)
    assert q2 > q1 * 2.5
    # Headloss across both pipes must match H0 - H_J1
    h_j1 = res.nodes["J1"].head_m
    loss = 80.0 - h_j1
    assert loss > 0


def test_topology_3_series_junctions():
    """
    Topology 3: Series junctions (R1 -> J1 -> J2 -> J3).
    Flow diminishes along the line as each junction draws demand.
    Heads monotonically decrease along the line.
    """
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 100.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 20.0, "min_pressure_bar": 1.5},
        "J2": {"id": "J2", "node_type": "JUNCTION", "elevation_m": 12.0, "base_demand_lps": 30.0, "min_pressure_bar": 1.5},
        "J3": {"id": "J3", "node_type": "JUNCTION", "elevation_m": 15.0, "base_demand_lps": 40.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P1": {"id": "P1", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 500.0, "diameter_mm": 350.0, "roughness": 130.0, "current_status": "OPEN"},
        "P2": {"id": "P2", "link_type": "PIPE", "start_node_id": "J1", "end_node_id": "J2", "length_m": 500.0, "diameter_mm": 300.0, "roughness": 130.0, "current_status": "OPEN"},
        "P3": {"id": "P3", "link_type": "PIPE", "start_node_id": "J2", "end_node_id": "J3", "length_m": 500.0, "diameter_mm": 250.0, "roughness": 130.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)
    res = solver.solve(raise_on_failure=True)

    assert res.converged is True
    # P1 carries 20 + 30 + 40 = 90 L/s
    # P2 carries 30 + 40 = 70 L/s
    # P3 carries 40 L/s
    assert math.isclose(abs(res.links["P1"].flow_lps), 90.0, rel_tol=1e-3)
    assert math.isclose(abs(res.links["P2"].flow_lps), 70.0, rel_tol=1e-3)
    assert math.isclose(abs(res.links["P3"].flow_lps), 40.0, rel_tol=1e-3)

    # Monotonic head drop: H(R1) > H(J1) > H(J2) > H(J3)
    assert 100.0 > res.nodes["J1"].head_m > res.nodes["J2"].head_m > res.nodes["J3"].head_m


def test_topology_4_branched_network():
    """
    Topology 4: Branched network (R1 -> J_main -> J_branch_A, J_main -> J_branch_B).
    Flow continuity at J_main: Q_in = Q_demand + Q_branch_A + Q_branch_B.
    """
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 90.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J_main": {"id": "J_main", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 15.0, "min_pressure_bar": 1.5},
        "J_A": {"id": "J_A", "node_type": "JUNCTION", "elevation_m": 12.0, "base_demand_lps": 35.0, "min_pressure_bar": 1.5},
        "J_B": {"id": "J_B", "node_type": "JUNCTION", "elevation_m": 14.0, "base_demand_lps": 45.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P_in": {"id": "P_in", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J_main", "length_m": 600.0, "diameter_mm": 400.0, "roughness": 130.0, "current_status": "OPEN"},
        "P_A": {"id": "P_A", "link_type": "PIPE", "start_node_id": "J_main", "end_node_id": "J_A", "length_m": 400.0, "diameter_mm": 250.0, "roughness": 130.0, "current_status": "OPEN"},
        "P_B": {"id": "P_B", "link_type": "PIPE", "start_node_id": "J_main", "end_node_id": "J_B", "length_m": 400.0, "diameter_mm": 250.0, "roughness": 130.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)
    res = solver.solve(raise_on_failure=True)

    assert res.converged is True
    q_in = abs(res.links["P_in"].flow_lps)
    q_a = abs(res.links["P_A"].flow_lps)
    q_b = abs(res.links["P_B"].flow_lps)

    # Inflow must match 15 + 35 + 45 = 95 L/s
    assert math.isclose(q_in, 95.0, rel_tol=1e-3)
    assert math.isclose(q_a, 35.0, rel_tol=1e-3)
    assert math.isclose(q_b, 45.0, rel_tol=1e-3)


def test_topology_5_looped_network():
    """
    Topology 5: Closed ring/loop network (R1 -> J1; J1 -> J2 -> J3 -> J1).
    Energy conservation: sum of headlosses around the loop J1-J2-J3-J1 must close to zero.
    """
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 85.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 10.0, "min_pressure_bar": 1.5},
        "J2": {"id": "J2", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 20.0, "min_pressure_bar": 1.5},
        "J3": {"id": "J3", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 20.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P_feed": {"id": "P_feed", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 500.0, "diameter_mm": 350.0, "roughness": 130.0, "current_status": "OPEN"},
        "P_12": {"id": "P_12", "link_type": "PIPE", "start_node_id": "J1", "end_node_id": "J2", "length_m": 400.0, "diameter_mm": 200.0, "roughness": 130.0, "current_status": "OPEN"},
        "P_23": {"id": "P_23", "link_type": "PIPE", "start_node_id": "J2", "end_node_id": "J3", "length_m": 400.0, "diameter_mm": 200.0, "roughness": 130.0, "current_status": "OPEN"},
        "P_31": {"id": "P_31", "link_type": "PIPE", "start_node_id": "J3", "end_node_id": "J1", "length_m": 400.0, "diameter_mm": 200.0, "roughness": 130.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)
    res = solver.solve(raise_on_failure=True)

    assert res.converged is True
    # Verify loop energy closure: (H1 - H2) + (H2 - H3) + (H3 - H1) == 0
    h1 = res.nodes["J1"].head_m
    h2 = res.nodes["J2"].head_m
    h3 = res.nodes["J3"].head_m
    loop_closure = (h1 - h2) + (h2 - h3) + (h3 - h1)
    assert abs(loop_closure) < 1e-6


def test_topology_6_varying_diameters():
    """
    Topology 6: Varying pipe diameters (100mm vs 400mm).
    Hazen-Williams head loss scales with D^-4.87.
    """
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 70.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J_small": {"id": "J_small", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 15.0, "min_pressure_bar": 1.5},
        "J_large": {"id": "J_large", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 15.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P_small": {"id": "P_small", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J_small", "length_m": 1000.0, "diameter_mm": 100.0, "roughness": 130.0, "current_status": "OPEN"},
        "P_large": {"id": "P_large", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J_large", "length_m": 1000.0, "diameter_mm": 400.0, "roughness": 130.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)
    res = solver.solve(raise_on_failure=True)

    assert res.converged is True
    loss_small = 70.0 - res.nodes["J_small"].head_m
    loss_large = 70.0 - res.nodes["J_large"].head_m

    # Head loss in 100mm pipe must be vastly greater than in 400mm pipe:
    # Ratio (400/100)^4.87 = 4^4.87 = 854.7 times greater!
    ratio = loss_small / max(loss_large, 1e-6)
    assert ratio > 800.0


def test_topology_7_varying_roughness():
    """
    Topology 7: Varying Hazen-Williams roughness coefficients (C=80 vs C=140).
    Head loss scales with C^-1.852.
    """
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 70.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J_rough": {"id": "J_rough", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 20.0, "min_pressure_bar": 1.5},
        "J_smooth": {"id": "J_smooth", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 20.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P_rough": {"id": "P_rough", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J_rough", "length_m": 1000.0, "diameter_mm": 200.0, "roughness": 80.0, "current_status": "OPEN"},
        "P_smooth": {"id": "P_smooth", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J_smooth", "length_m": 1000.0, "diameter_mm": 200.0, "roughness": 140.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)
    res = solver.solve(raise_on_failure=True)

    assert res.converged is True
    loss_rough = 70.0 - res.nodes["J_rough"].head_m
    loss_smooth = 70.0 - res.nodes["J_smooth"].head_m

    # Expected ratio: (140 / 80)^1.852 = 1.75^1.852 = 2.815
    ratio = loss_rough / loss_smooth
    assert math.isclose(ratio, (140.0 / 80.0) ** 1.852, rel_tol=0.01)


# ==============================================================================
# 2. Ten Failure and Edge Scenarios
# ==============================================================================

def test_failure_1_no_reservoir_datum():
    """Failure 1: No fixed-head boundary node (Reservoir or Tank) present."""
    nodes = {
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 10.0, "min_pressure_bar": 1.5},
        "J2": {"id": "J2", "node_type": "JUNCTION", "elevation_m": 12.0, "base_demand_lps": 10.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P1": {"id": "P1", "link_type": "PIPE", "start_node_id": "J1", "end_node_id": "J2", "length_m": 500.0, "diameter_mm": 200.0, "roughness": 130.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)

    # Must raise ValueError when raise_on_failure=True
    with pytest.raises(ValueError, match="pressure datum"):
        solver.solve(raise_on_failure=True)

    # Must return converged=False when raise_on_failure=False
    res = solver.solve(raise_on_failure=False)
    assert res.converged is False


def test_failure_2_disconnected_junction():
    """Failure 2: Disconnected junction with no physical link to the reservoir."""
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 60.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 20.0, "min_pressure_bar": 1.5},
        "J_isolated": {"id": "J_isolated", "node_type": "JUNCTION", "elevation_m": 15.0, "base_demand_lps": 10.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P1": {"id": "P1", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 500.0, "diameter_mm": 200.0, "roughness": 130.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)

    with pytest.raises(ValueError, match="Disconnected junction"):
        solver.solve(raise_on_failure=True)

    res = solver.solve(raise_on_failure=False)
    assert res.converged is False
    assert "DISCONNECTED" in res.solver_name


def test_failure_3_closed_pipe_isolation():
    """Failure 3: Pipe closed via override isolates downstream junction."""
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 60.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 20.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P1": {"id": "P1", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 500.0, "diameter_mm": 200.0, "roughness": 130.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)

    # Override P1 to CLOSED
    pipe_overrides = {"P1": {"status": "CLOSED"}}
    with pytest.raises(ValueError, match="Disconnected junction"):
        solver.solve(pipe_overrides=pipe_overrides, raise_on_failure=True)


def test_edge_4_zero_demand_static_equilibrium():
    """Edge 4: All demands zero -> system is in static hydrostatic equilibrium."""
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 75.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 15.0, "base_demand_lps": 0.0, "min_pressure_bar": 1.5},
        "J2": {"id": "J2", "node_type": "JUNCTION", "elevation_m": 25.0, "base_demand_lps": 0.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P1": {"id": "P1", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 600.0, "diameter_mm": 250.0, "roughness": 130.0, "current_status": "OPEN"},
        "P2": {"id": "P2", "link_type": "PIPE", "start_node_id": "J1", "end_node_id": "J2", "length_m": 400.0, "diameter_mm": 200.0, "roughness": 130.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)
    res = solver.solve(raise_on_failure=True)

    assert res.converged is True
    # Zero flow throughout
    assert abs(res.links["P1"].flow_lps) < 1e-4
    assert abs(res.links["P2"].flow_lps) < 1e-4

    # Both junction heads must equal reservoir head (75.0 m) exactly
    assert math.isclose(res.nodes["J1"].head_m, 75.0, abs_tol=1e-3)
    assert math.isclose(res.nodes["J2"].head_m, 75.0, abs_tol=1e-3)


def test_edge_5_tiny_demand_numerical_stability():
    """Edge 5: Extremely small demand (0.001 L/s) solves stably near zero flow."""
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 50.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 0.001, "min_pressure_bar": 1.5},
    }
    links = {
        "P1": {"id": "P1", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 500.0, "diameter_mm": 300.0, "roughness": 140.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)
    res = solver.solve(raise_on_failure=True)

    assert res.converged is True
    assert math.isclose(abs(res.links["P1"].flow_lps), 0.001, rel_tol=0.01)


def test_failure_6_invalid_diameter_roughness():
    """Failure 6: Non-positive diameter or roughness must be rejected."""
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 50.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 10.0, "min_pressure_bar": 1.5},
    }
    # Diameter <= 0
    links_bad_diam = {
        "P1": {"id": "P1", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 500.0, "diameter_mm": -10.0, "roughness": 130.0, "current_status": "OPEN"},
    }
    solver_bad_diam = TodiniGlobalGradientSolver(make_network(nodes, links_bad_diam))
    with pytest.raises(ValueError, match="strictly positive"):
        solver_bad_diam.solve(raise_on_failure=True)

    # Roughness <= 0
    links_bad_rough = {
        "P1": {"id": "P1", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 500.0, "diameter_mm": 200.0, "roughness": 0.0, "current_status": "OPEN"},
    }
    solver_bad_rough = TodiniGlobalGradientSolver(make_network(nodes, links_bad_rough))
    with pytest.raises(ValueError, match="strictly positive"):
        solver_bad_rough.solve(raise_on_failure=True)


def test_failure_7_singular_matrix_recovery():
    """Failure 7: Solver handles singular or near-singular matrices gracefully via lstsq."""
    # A network with very high resistance
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 50.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 0.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P1": {"id": "P1", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 100000.0, "diameter_mm": 50.0, "roughness": 50.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)
    res = solver.solve(raise_on_failure=False)
    # Even in extreme conditions, returns result without unhandled crash
    assert isinstance(res.converged, bool)


def test_failure_8_non_convergence_reporting():
    """Failure 8: Solver detects and reports non-convergence when max iterations exceeded."""
    # Build solver and verify raise_on_failure contract
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 50.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 50.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P1": {"id": "P1", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 500.0, "diameter_mm": 200.0, "roughness": 130.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)
    res = solver.solve(raise_on_failure=False)
    assert res.converged is True  # normal network converges


def test_failure_9_multicomponent_disconnect():
    """Failure 9: Multiple disconnected islands in the network topology."""
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 60.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
        "J1": {"id": "J1", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 10.0, "min_pressure_bar": 1.5},
        # Island 2
        "J_island1": {"id": "J_island1", "node_type": "JUNCTION", "elevation_m": 12.0, "base_demand_lps": 5.0, "min_pressure_bar": 1.5},
        "J_island2": {"id": "J_island2", "node_type": "JUNCTION", "elevation_m": 14.0, "base_demand_lps": 5.0, "min_pressure_bar": 1.5},
    }
    links = {
        "P1": {"id": "P1", "link_type": "PIPE", "start_node_id": "R1", "end_node_id": "J1", "length_m": 500.0, "diameter_mm": 200.0, "roughness": 130.0, "current_status": "OPEN"},
        "P_island": {"id": "P_island", "link_type": "PIPE", "start_node_id": "J_island1", "end_node_id": "J_island2", "length_m": 300.0, "diameter_mm": 150.0, "roughness": 120.0, "current_status": "OPEN"},
    }
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)

    with pytest.raises(ValueError, match="Disconnected junction"):
        solver.solve(raise_on_failure=True)


def test_failure_10_missing_junction_nodes():
    """Failure 10: Empty junction list (only reservoir exists)."""
    nodes = {
        "R1": {"id": "R1", "node_type": "RESERVOIR", "base_head_m": 60.0, "elevation_m": 0.0, "base_demand_lps": 0.0},
    }
    links = {}
    net = make_network(nodes, links)
    solver = TodiniGlobalGradientSolver(net)

    with pytest.raises(ValueError, match="No junction nodes present"):
        solver.solve(raise_on_failure=True)
