"""
TASK 10.5 — Comprehensive Hydraulic Engineering Validation & Digital Twin Audit Suite
Tests EPANET Net1 benchmark accuracy, mass & energy conservation, Hazen-Williams friction,
Torricelli orifice dynamics, Todini-Pilati solver edge cases, baseline immutability,
and cross-task dispatch safety.
"""
import pytest
from fastapi.testclient import TestClient
import math
import copy

from app.main import app
from app.database.session import init_db, get_db
from app.services.hydraulic_engine.epanet_benchmark import EPANETBenchmarkValidator, HAS_WNTR
from app.services.hydraulic_engine.todini_solver import TodiniGlobalGradientSolver
from app.services.hydraulic_engine.wntr_engine import WNTREngine
from app.services.hydraulic_network_service import HydraulicNetworkService, DEFAULT_NETWORK_ID
from app.services.scenario_manager_service import ScenarioManagerService

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


# ==============================================================================
# 1. TRACEABLE BENCHMARK VALIDATION (EPANET Net1)
# ==============================================================================

@pytest.mark.skipif(not HAS_WNTR, reason="WNTR / EPANET engine required")
def test_epanet_net1_benchmark_precision():
    """
    Validates WNTR simulation against EPA EPANET 2.2 reference benchmark.
    Verifies that relative pressure and flow errors are below strict engineering tolerances (< 0.01%).
    """
    res = EPANETBenchmarkValidator.run_net1_benchmark()
    assert res["is_validated"] is True
    assert res["validation_status"] == "VALIDATED"
    assert res["is_simulated"] is True
    assert res["source"] == "VIRTUAL_SIMULATION_ENGINE"

    metrics = res["metrics"]
    # Relative pressure error must be negligible (< 0.001%)
    assert metrics["max_relative_error_pressure_pct"] < 0.001, (
        f"Pressure error too high: {metrics['max_relative_error_pressure_pct']}%"
    )
    # Absolute flow error must be below 1e-5 m3/s
    assert metrics["max_absolute_error_flow_m3s"] < 1e-5, (
        f"Flow error too high: {metrics['max_absolute_error_flow_m3s']} m3/s"
    )
    # Mass balance continuity residual must be zero (< 1e-4 m3/s)
    assert metrics["mass_balance_conserved"] is True
    assert metrics["mass_balance_residual_m3s"] < 1e-4

    # Closed-loop energy conservation (sum of headlosses along loop 11->12->22->21->11 = 0)
    assert metrics["energy_balance_conserved"] is True
    assert metrics["loop_headloss_closure_residual_m"] < 0.05  # within 5 cm


# ==============================================================================
# 2. PHYSICAL FORMULATION & CONSERVATION LAWS
# ==============================================================================

def test_conservation_of_mass():
    """
    Validates physical conservation of mass:
    Total Network Supply (m3/s) = Total Junction Demands (m3/s) + Leak Outflows (m3/s).
    """
    res = client.get(f"/api/v1/digital-twin/networks/{DEFAULT_NETWORK_ID}/topology")
    solver_data = res.json()["solver_data"]

    solver = TodiniGlobalGradientSolver(solver_data)
    sim_res = solver.solve(duration_hours=1, timestep_minutes=60, demand_multiplier=1.0)
    assert sim_res.converged is True

    # Check conservation: Supply - Demand - Leak = 0
    mass_residual = abs(sim_res.total_supply_lps - (sim_res.total_demand_lps + sim_res.total_leakage_lps))
    assert mass_residual < 0.1, f"Mass balance violation in network: residual {mass_residual:.4f} L/s"


def test_hazen_williams_headloss_formulation():
    """
    Validates pipe friction headloss against theoretical Hazen-Williams equation:
    h_f = 10.67 * (L / (C^1.852 * D^4.87)) * Q^1.852
    """
    # Sample pipe: L = 1000m, D = 0.3m (300mm), C = 130, Q = 0.05 m3/s (50 L/s)
    L = 1000.0
    D = 0.30
    C = 130.0
    Q = 0.05

    theoretical_hf = 10.67 * (L / ((C ** 1.852) * (D ** 4.87))) * (Q ** 1.852)
    assert theoretical_hf > 0.0

    # Execute single pipe in Todini solver structure
    test_network = {
        "network_id": "NET-TEST-HW",
        "nodes": {
            "N-SRC": {"id": "N-SRC", "node_type": "RESERVOIR", "elevation_m": 0.0, "base_head_m": 100.0, "base_demand_lps": 0.0},
            "N-DST": {"id": "N-DST", "node_type": "JUNCTION", "elevation_m": 0.0, "base_demand_lps": 50.0},
        },
        "links": {
            "P-01": {"id": "P-01", "name": "Test Pipe", "link_type": "PIPE", "start_node_id": "N-SRC", "end_node_id": "N-DST",
                     "length_m": L, "diameter_mm": 300.0, "roughness": C, "current_status": "OPEN"},
        },
    }
    solver = TodiniGlobalGradientSolver(test_network)
    sim_res = solver.solve(duration_hours=1, timestep_minutes=60, demand_multiplier=1.0)
    assert sim_res.converged is True

    simulated_hf = sim_res.links["P-01"].headloss_m
    relative_diff = abs(simulated_hf - theoretical_hf) / theoretical_hf
    assert relative_diff < 0.02, f"Hazen-Williams discrepancy: Sim={simulated_hf:.4f}m, Theory={theoretical_hf:.4f}m"


def test_torricelli_orifice_dynamics():
    """
    Validates Torricelli orifice leak discharge formulation:
    Q = Cd * A * sqrt(2 * ΔP / ρ)
    across multiple pressure and area regimes.
    """
    # Test case 1: P = 4.0 bar (400,000 Pa), A = 5 cm2, Cd = 0.75
    calc1 = EPANETBenchmarkValidator.verify_torricelli_orifice(
        pressure_bar=4.0, orifice_area_cm2=5.0, discharge_coeff=0.75
    )
    # Theoretical: v = sqrt(2 * 400000 / 1000) = sqrt(800) = 28.284 m/s
    # Q = 0.75 * 0.0005 * 28.284 = 0.010607 m3/s = 10.607 L/s
    assert math.isclose(calc1["theoretical_velocity_mps"], 28.284, rel_tol=1e-3)
    assert math.isclose(calc1["expected_flow_lps"], 10.607, rel_tol=1e-3)

    # Test case 2: Pipe Burst (P = 4.35 bar, A = 35 cm2, Cd = 0.80)
    calc2 = EPANETBenchmarkValidator.verify_torricelli_orifice(
        pressure_bar=4.35, orifice_area_cm2=35.0, discharge_coeff=0.80
    )
    # v = sqrt(2 * 435000 / 1000) = 29.496 m/s
    # Q = 0.80 * 0.0035 * 29.496 = 0.082588 m3/s = 82.588 L/s
    assert math.isclose(calc2["theoretical_velocity_mps"], 29.496, rel_tol=1e-3)
    assert math.isclose(calc2["expected_flow_lps"], 82.588, rel_tol=1e-3)


@pytest.mark.skipif(not HAS_WNTR, reason="WNTR engine required for PDA")
def test_pressure_dependent_demand_behavior():
    """
    Validates Wagner Pressure-Dependent Demand (PDD):
    When pressure is severely depressed, actual delivered demand decreases below required demand.
    """
    res = client.get(f"/api/v1/digital-twin/networks/{DEFAULT_NETWORK_ID}/topology")
    solver_data = res.json()["solver_data"]

    # 1. Nominal PDA run
    pda_engine = WNTREngine(solver_data)
    res_nom = pda_engine.run_simulation(duration_hours=1, timestep_minutes=60, demand_model="PDA")
    assert res_nom.converged is True

    # 2. Severely throttle source head to induce severe network pressure deficit
    throttled_data = copy.deepcopy(solver_data)
    for n in throttled_data["nodes"].values():
        if n["node_type"] == "RESERVOIR":
            n["base_head_m"] = 5.0  # severely drop reservoir head from 85m to 5m

    pda_engine_throttled = WNTREngine(throttled_data)
    res_deficit = pda_engine_throttled.run_simulation(duration_hours=1, timestep_minutes=60, demand_model="PDA")
    assert res_deficit.converged is True

    # Under severe deficit, delivered demand must be lower than nominal demand
    assert res_deficit.total_demand_lps < res_nom.total_demand_lps
    assert res_deficit.pressure_deficit_count > 0


# ==============================================================================
# 3. SOLVER HARDENING & EDGE CASE HANDLING
# ==============================================================================

def test_todini_solver_disconnected_network_exception():
    """
    Ensures Todini solver identifies disconnected topologies and raises explicit
    error when raise_on_failure=True, rather than silently failing.
    """
    disconnected_data = {
        "network_id": "NET-DISCONNECTED",
        "nodes": {
            "R-01": {"id": "R-01", "node_type": "RESERVOIR", "elevation_m": 0.0, "base_head_m": 80.0, "base_demand_lps": 0.0},
            "J-01": {"id": "J-01", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 20.0},
            "J-ISLAND": {"id": "J-ISLAND", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 15.0},
        },
        "links": {
            "P-01": {"id": "P-01", "name": "Connected Pipe", "link_type": "PIPE", "start_node_id": "R-01", "end_node_id": "J-01",
                     "length_m": 500.0, "diameter_mm": 300.0, "roughness": 130.0, "current_status": "OPEN"},
            # J-ISLAND has no connected pipes
        },
    }
    solver = TodiniGlobalGradientSolver(disconnected_data)
    with pytest.raises(ValueError, match="Disconnected junction nodes detected"):
        solver.solve(raise_on_failure=True)


def test_todini_solver_no_source_exception():
    """
    Ensures network without fixed-head source raises explicit ValueError.
    """
    sourceless_data = {
        "network_id": "NET-NO-SOURCE",
        "nodes": {
            "J-01": {"id": "J-01", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 20.0},
            "J-02": {"id": "J-02", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 20.0},
        },
        "links": {
            "P-01": {"id": "P-01", "link_type": "PIPE", "start_node_id": "J-01", "end_node_id": "J-02",
                     "length_m": 500.0, "diameter_mm": 300.0, "roughness": 130.0, "current_status": "OPEN"},
        },
    }
    solver = TodiniGlobalGradientSolver(sourceless_data)
    with pytest.raises(ValueError, match="No fixed-head boundary node"):
        solver.solve(raise_on_failure=True)


def test_todini_solver_zero_demand_condition():
    """
    Validates that network with zero consumer demand converges with zero pipe flow
    and hydrostatic heads matching boundary source head.
    """
    zero_demand_data = {
        "network_id": "NET-ZERO-DEMAND",
        "nodes": {
            "R-01": {"id": "R-01", "node_type": "RESERVOIR", "elevation_m": 0.0, "base_head_m": 60.0, "base_demand_lps": 0.0},
            "J-01": {"id": "J-01", "node_type": "JUNCTION", "elevation_m": 10.0, "base_demand_lps": 0.0},
        },
        "links": {
            "P-01": {"id": "P-01", "link_type": "PIPE", "start_node_id": "R-01", "end_node_id": "J-01",
                     "length_m": 400.0, "diameter_mm": 200.0, "roughness": 140.0, "current_status": "OPEN"},
        },
    }
    solver = TodiniGlobalGradientSolver(zero_demand_data)
    res = solver.solve(duration_hours=1, timestep_minutes=60, demand_multiplier=1.0)
    assert res.converged is True
    assert math.isclose(res.total_supply_lps, 0.0, abs_tol=1e-3)
    # Hydrostatic pressure at J-01: Head(60m) - Elevation(10m) = 50m head ~ 4.905 bar
    j1_pressure = res.nodes["J-01"].pressure_bar
    assert math.isclose(j1_pressure, 50.0 / 10.197, rel_tol=0.05)


def test_todini_solver_parallel_pipes():
    """
    Validates parallel pipe configuration:
    Flow divides between two parallel pipes of equal diameter and roughness equally.
    """
    parallel_data = {
        "network_id": "NET-PARALLEL",
        "nodes": {
            "R-01": {"id": "R-01", "node_type": "RESERVOIR", "elevation_m": 0.0, "base_head_m": 80.0, "base_demand_lps": 0.0},
            "J-01": {"id": "J-01", "node_type": "JUNCTION", "elevation_m": 0.0, "base_demand_lps": 40.0},
        },
        "links": {
            "P-01A": {"id": "P-01A", "link_type": "PIPE", "start_node_id": "R-01", "end_node_id": "J-01",
                      "length_m": 500.0, "diameter_mm": 250.0, "roughness": 130.0, "current_status": "OPEN"},
            "P-01B": {"id": "P-01B", "link_type": "PIPE", "start_node_id": "R-01", "end_node_id": "J-01",
                      "length_m": 500.0, "diameter_mm": 250.0, "roughness": 130.0, "current_status": "OPEN"},
        },
    }
    solver = TodiniGlobalGradientSolver(parallel_data)
    res = solver.solve(duration_hours=1, timestep_minutes=60, demand_multiplier=1.0)
    assert res.converged is True

    flow_a = res.links["P-01A"].flow_lps
    flow_b = res.links["P-01B"].flow_lps
    assert math.isclose(abs(flow_a), 20.0, rel_tol=0.05)
    assert math.isclose(abs(flow_b), 20.0, rel_tol=0.05)
    assert math.isclose(abs(flow_a) + abs(flow_b), 40.0, rel_tol=0.01)


# ==============================================================================
# 4. SCENARIO ISOLATION & IMMUTABILITY
# ==============================================================================

def test_baseline_immutability():
    """
    Validates Rule 6 & 12: Baseline scenario SCEN-BASELINE-01 is strictly immutable.
    Attempting to recreate or overwrite a baseline scenario raises ValueError.
    """
    db = next(get_db())
    # Ensure baseline is seeded
    ScenarioManagerService.seed_default_scenarios(db, DEFAULT_NETWORK_ID)

    with pytest.raises(ValueError, match="Baseline scenario is immutable"):
        ScenarioManagerService.create_scenario(
            db=db,
            network_id=DEFAULT_NETWORK_ID,
            name="Attempted Baseline Overwrite",
            scenario_type="BASELINE",
            description="Unauthorized modification",
            parameters_override={},
            is_baseline=True,
        )


def test_scenario_run_deep_copy_isolation():
    """
    Validates that running a severe what-if burst perturbation does not mutate
    or leak modified parameters into the baseline network solver data.
    """
    db = next(get_db())
    topo_before = HydraulicNetworkService.get_network_topology(db, DEFAULT_NETWORK_ID)
    j2_demand_before = topo_before["solver_data"]["nodes"]["NODE-JUNC-02"]["base_demand_lps"]

    # Execute severe leak injection
    ScenarioManagerService.simulate_leak_injection(
        db=db,
        network_id=DEFAULT_NETWORK_ID,
        target_node_id="NODE-JUNC-02",
        leak_area_cm2=25.0,
        discharge_coeff=0.85,
    )

    # Topology and solver_data must remain completely unchanged
    topo_after = HydraulicNetworkService.get_network_topology(db, DEFAULT_NETWORK_ID)
    j2_demand_after = topo_after["solver_data"]["nodes"]["NODE-JUNC-02"]["base_demand_lps"]
    assert j2_demand_before == j2_demand_after


# ==============================================================================
# 5. CROSS-TASK INTEGRATION & SAFETY AUDIT
# ==============================================================================

def test_digital_twin_rover_dispatch_human_approval():
    """
    Validates Rule 10: Rover dispatch from Digital Twin burst anomaly requires
    mandatory human operator approval.
    """
    handoff_payload = {
        "scenario_id": "SCEN-BURST-PIPE-02",
        "target_node_id": "NODE-JUNC-02",
        "operator_id": "OP-CENTRAL-01",
        "notes": "Burst investigated via Digital Twin PDA simulation",
    }
    response = client.post("/api/v1/digital-twin/handoff-rover-dispatch", json=handoff_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["operator_approval_required"] is True
    assert data["status"] == "RECOMMENDED"
    assert data["is_simulated"] is True
    assert data["source"] == "VIRTUAL_SIMULATION_ENGINE"


def test_rest_api_benchmarks_and_validation_status():
    """
    Validates that REST endpoints expose reproducible validation metrics,
    primary solver status, and analytical Torricelli verification.
    """
    # 1. Validation status
    status_res = client.get("/api/v1/digital-twin/validation-status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["audit_version"] == "TASK-10.5-HYDRAULIC-ENGINEERING-AUDIT"
    assert status_data["primary_solver"]["status"] == "VALIDATED"
    assert status_data["secondary_solver"]["status"] == "EXPERIMENTAL"
    assert status_data["operational_guardrails"]["human_approval_required_for_dispatch"] is True
    assert status_data["operational_guardrails"]["baseline_immutability"] is True

    # 2. Net1 benchmark endpoint
    net1_res = client.get("/api/v1/digital-twin/benchmark/net1")
    assert net1_res.status_code == 200
    net1_data = net1_res.json()
    assert net1_data["is_validated"] is True
    assert net1_data["nodes_count"] == 11
    assert net1_data["links_count"] == 13

    # 3. Torricelli verification endpoint
    torr_res = client.post(
        "/api/v1/digital-twin/benchmark/torricelli",
        json={"pressure_bar": 3.5, "orifice_area_cm2": 10.0, "discharge_coeff": 0.75},
    )
    assert torr_res.status_code == 200
    torr_data = torr_res.json()
    assert torr_data["expected_flow_lps"] > 10.0
    assert torr_data["is_simulated"] is True
