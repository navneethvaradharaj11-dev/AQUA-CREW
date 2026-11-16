"""
Phase 6: Leak Ground-Truth Verification Test Suite (Task 10.6)
Validates simulated vs theoretical Torricelli orifice discharge across 6 independent leak regimes:
1. Pinhole: 1 cm2
2. Moderate: 5 cm2
3. Major: 15 cm2
4. Severe/Burst: 35 cm2
5. Low-pressure regime (1.8 bar)
6. High-pressure regime (5.2 bar)
Verifies absence of double-counting between customer demand and emitter leakage.
"""
import pytest
import math
import os

try:
    import wntr
    HAS_WNTR = True
except ImportError:
    HAS_WNTR = False

from app.services.hydraulic_engine.wntr_engine import WNTREngine
from app.services.hydraulic_engine.epanet_benchmark import EPANETBenchmarkValidator


def build_test_network(head_m: float = 50.0, customer_demand_lps: float = 10.0):
    """Helper to build a clean single-pipe water network model in WNTR."""
    wn = wntr.network.WaterNetworkModel()
    wn.add_pattern("pat1", [1.0])
    wn.add_reservoir("R1", base_head=head_m)
    wn.add_junction("J1", elevation=10.0, base_demand=customer_demand_lps / 1000.0, demand_pattern="pat1")
    wn.add_pipe("P1", "R1", "J1", length=500.0, diameter=0.300, roughness=130.0)
    return wn


@pytest.mark.skipif(not HAS_WNTR, reason="WNTR required for leak ground truth")
@pytest.mark.parametrize(
    "area_cm2,label",
    [
        (1.0, "Pinhole (1 cm2)"),
        (5.0, "Moderate (5 cm2)"),
        (15.0, "Major (15 cm2)"),
        (35.0, "Burst (35 cm2)"),
    ],
)
def test_leak_regimes_orifice_discharge_accuracy(area_cm2: float, label: str):
    """
    Verifies that across leak sizes from 1 cm2 to 35 cm2, simulated emitter discharge
    matches the analytical Torricelli equation Q = Cd * A * sqrt(2 * g * P_head).
    """
    area_m2 = area_cm2 * 1e-4
    cd = 0.75

    wn = build_test_network(head_m=50.0, customer_demand_lps=15.0)
    j1 = wn.get_node("J1")
    j1.add_leak(wn, area=area_m2, discharge_coeff=cd, start_time=0)

    sim = wntr.sim.WNTRSimulator(wn)
    res = sim.run_sim()

    t0 = res.node["pressure"].index[0]
    p_head = float(res.node["pressure"].loc[t0, "J1"])
    sim_leak_m3s = float(res.node["leak_demand"].loc[t0, "J1"])

    # Theoretical Torricelli: Q = Cd * A * sqrt(2 * g * h)
    theor_leak_m3s = cd * area_m2 * math.sqrt(2.0 * 9.81 * p_head)

    # Difference must be practically zero (< 1e-5 m3/s = 0.01 L/s)
    abs_diff = abs(sim_leak_m3s - theor_leak_m3s)
    assert abs_diff < 1e-5, f"{label} discharge mismatch: sim={sim_leak_m3s:.6f}, theor={theor_leak_m3s:.6f}"

    # Also verify through EPANETBenchmarkValidator
    p_bar = p_head * 0.0980665
    bench = EPANETBenchmarkValidator.verify_torricelli_orifice(
        pressure_bar=p_bar,
        orifice_area_cm2=area_cm2,
        discharge_coeff=cd,
    )
    assert math.isclose(bench["expected_flow_m3s"], theor_leak_m3s, rel_tol=0.01)


@pytest.mark.skipif(not HAS_WNTR, reason="WNTR required")
def test_low_pressure_regime_1_8_bar():
    """
    Verifies leak behavior in low-pressure network regime (1.8 bar ~ 18.35 m head).
    """
    # Reservoir head set so J1 pressure settles around 1.8 bar (18.35 m)
    # J1 elevation = 10.0 m -> Total Head = 28.35 m
    wn = build_test_network(head_m=28.35, customer_demand_lps=5.0)
    area_m2 = 5.0 * 1e-4
    cd = 0.75

    j1 = wn.get_node("J1")
    j1.add_leak(wn, area=area_m2, discharge_coeff=cd, start_time=0)

    sim = wntr.sim.WNTRSimulator(wn)
    res = sim.run_sim()

    t0 = res.node["pressure"].index[0]
    p_head = float(res.node["pressure"].loc[t0, "J1"])
    p_bar = p_head * 0.0980665

    assert 1.6 <= p_bar <= 2.0  # low pressure regime ~ 1.8 bar

    sim_leak_lps = float(res.node["leak_demand"].loc[t0, "J1"]) * 1000.0
    theor_leak_lps = cd * area_m2 * math.sqrt(2.0 * 9.81 * p_head) * 1000.0

    assert math.isclose(sim_leak_lps, theor_leak_lps, rel_tol=1e-3)


@pytest.mark.skipif(not HAS_WNTR, reason="WNTR required")
def test_high_pressure_regime_5_2_bar():
    """
    Verifies leak behavior in high-pressure network regime (5.2 bar ~ 53.0 m head).
    """
    # J1 elevation = 10.0 m -> Total Head = 63.0 m
    wn = build_test_network(head_m=63.0, customer_demand_lps=5.0)
    area_m2 = 5.0 * 1e-4
    cd = 0.75

    j1 = wn.get_node("J1")
    j1.add_leak(wn, area=area_m2, discharge_coeff=cd, start_time=0)

    sim = wntr.sim.WNTRSimulator(wn)
    res = sim.run_sim()

    t0 = res.node["pressure"].index[0]
    p_head = float(res.node["pressure"].loc[t0, "J1"])
    p_bar = p_head * 0.0980665

    assert 5.0 <= p_bar <= 5.4  # high pressure regime ~ 5.2 bar

    sim_leak_lps = float(res.node["leak_demand"].loc[t0, "J1"]) * 1000.0
    theor_leak_lps = cd * area_m2 * math.sqrt(2.0 * 9.81 * p_head) * 1000.0

    assert math.isclose(sim_leak_lps, theor_leak_lps, rel_tol=1e-3)


@pytest.mark.skipif(not HAS_WNTR, reason="WNTR required")
def test_no_double_counting_between_demand_and_leak():
    """
    Strictly verifies that customer base demand is NEVER conflated with emitter leakage.
    Total Inflow = Actual Customer Demand + Emitter Leakage.
    """
    customer_demand_lps = 20.0
    wn = build_test_network(head_m=50.0, customer_demand_lps=customer_demand_lps)

    # Add 10 cm2 leak
    j1 = wn.get_node("J1")
    j1.add_leak(wn, area=10.0 * 1e-4, discharge_coeff=0.75, start_time=0)

    sim = wntr.sim.WNTRSimulator(wn)
    res = sim.run_sim()

    t0 = res.node["pressure"].index[0]
    cust_d_lps = float(res.node["demand"].loc[t0, "J1"]) * 1000.0
    leak_d_lps = float(res.node["leak_demand"].loc[t0, "J1"]) * 1000.0
    pipe_flow_lps = abs(float(res.link["flowrate"].loc[t0, "P1"])) * 1000.0

    # 1. Customer demand equals exactly 20.0 L/s
    assert math.isclose(cust_d_lps, 20.0, rel_tol=1e-3)

    # 2. Leak demand is positive non-zero
    assert leak_d_lps > 15.0

    # 3. Pipe flow equals sum of customer demand and leak demand
    assert math.isclose(pipe_flow_lps, cust_d_lps + leak_d_lps, rel_tol=1e-4)


@pytest.mark.skipif(not HAS_WNTR, reason="WNTR required")
def test_monotonic_pressure_drop_with_leak_size():
    """
    Verifies that larger leaks cause monotonically greater pressure drops at the node.
    """
    pressures = []
    leak_sizes = [0.0, 1.0, 5.0, 15.0, 35.0]  # cm2

    for lk_cm2 in leak_sizes:
        wn = build_test_network(head_m=50.0, customer_demand_lps=10.0)
        if lk_cm2 > 0:
            j1 = wn.get_node("J1")
            j1.add_leak(wn, area=lk_cm2 * 1e-4, discharge_coeff=0.75, start_time=0)

        sim = wntr.sim.WNTRSimulator(wn)
        res = sim.run_sim()
        t0 = res.node["pressure"].index[0]
        p = float(res.node["pressure"].loc[t0, "J1"])
        pressures.append(p)

    # Monotonically strictly decreasing: P(0) > P(1) > P(5) > P(15) > P(35)
    for i in range(len(pressures) - 1):
        assert pressures[i] > pressures[i + 1], f"Pressure did not drop from size {leak_sizes[i]} to {leak_sizes[i+1]}"

