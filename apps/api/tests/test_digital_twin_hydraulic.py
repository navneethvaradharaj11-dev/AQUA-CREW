"""
Comprehensive Unit & Integration Test Suite for Digital Twin & Hydraulic Simulation (Task 10)
Validates network topology, WNTR solver, Todini Global Gradient solver,
What-If scenarios, burst modeling, scenario comparisons, and rover dispatch handoff.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json

from app.main import app
from app.database.session import get_db, init_db
from app.services.hydraulic_network_service import HydraulicNetworkService, DEFAULT_NETWORK_ID
from app.services.scenario_manager_service import ScenarioManagerService
from app.services.hydraulic_engine.todini_solver import TodiniGlobalGradientSolver
from app.services.hydraulic_engine.wntr_engine import WNTREngine, HAS_WNTR


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_hydraulic_network_seeding_and_topology():
    """Verify hydraulic network seeding, node types, and GeoJSON topology."""
    response = client.get("/api/v1/digital-twin/networks")
    assert response.status_code == 200
    networks = response.json()
    assert len(networks) >= 1
    assert any(n["id"] == DEFAULT_NETWORK_ID for n in networks)

    # Topology
    topo_res = client.get(f"/api/v1/digital-twin/networks/{DEFAULT_NETWORK_ID}/topology")
    assert topo_res.status_code == 200
    topo = topo_res.json()
    assert topo["nodes_count"] >= 7
    assert topo["links_count"] >= 7
    assert topo["geojson"]["type"] == "FeatureCollection"
    assert len(topo["geojson"]["features"]) >= 14

    # Verify specialized assets present in features
    node_types = {f["properties"].get("node_type") for f in topo["geojson"]["features"] if f["properties"].get("feature_type") == "NODE"}
    assert "RESERVOIR" in node_types
    assert "JUNCTION" in node_types
    assert "TANK" in node_types

    link_types = {f["properties"].get("link_type") for f in topo["geojson"]["features"] if f["properties"].get("feature_type") == "LINK"}
    assert "PIPE" in link_types
    assert "PUMP" in link_types
    assert "VALVE" in link_types


def test_todini_global_gradient_solver():
    """Test pure-Python Todini-Pilati GGA solver directly."""
    # Obtain solver data
    res = client.get(f"/api/v1/digital-twin/networks/{DEFAULT_NETWORK_ID}/topology")
    solver_data = res.json()["solver_data"]

    solver = TodiniGlobalGradientSolver(solver_data)
    result = solver.solve(duration_hours=1, timestep_minutes=60, demand_multiplier=1.0)

    assert result.converged is True
    assert result.iterations >= 1
    assert result.total_supply_lps > 50.0  # Network supplies all junction demands
    assert result.min_pressure_bar > 0.0
    assert result.max_pressure_bar < 8.0

    # Verify link flows and velocities
    for lid, link in result.links.items():
        assert link.velocity_mps >= 0.0
        assert link.headloss_m >= 0.0


def test_wntr_hydraulic_engine():
    """Test WNTR / EPANET simulation engine."""
    if not HAS_WNTR:
        pytest.skip("WNTR not installed in test environment")

    res = client.get(f"/api/v1/digital-twin/networks/{DEFAULT_NETWORK_ID}/topology")
    solver_data = res.json()["solver_data"]

    engine = WNTREngine(solver_data)
    result = engine.run_simulation(duration_hours=24, timestep_minutes=60, demand_model="PDA")

    assert result.converged is True
    assert len(result.timesteps) >= 24
    assert result.total_demand_lps > 0.0
    assert result.water_loss_percentage >= 0.0

    # Verify node pressures
    for nid, node in result.nodes.items():
        assert node.pressure_bar >= 0.0
        assert node.head_m >= node.elevation_m


def test_scenarios_listing_and_baseline_execution():
    """Verify default scenarios are seeded and baseline scenario executes."""
    scens_res = client.get("/api/v1/digital-twin/scenarios")
    assert scens_res.status_code == 200
    scenarios = scens_res.json()
    assert len(scenarios) >= 5

    baseline = next(s for s in scenarios if s["id"] == "SCEN-BASELINE-01")
    assert baseline["is_baseline"] is True

    # Run baseline scenario
    run_res = client.post(f"/api/v1/digital-twin/scenarios/{baseline['id']}/run", json={})
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["converged"] is True
    assert run_data["water_loss_percentage"] == 0.0  # Baseline has 0 leaks
    assert run_data["pressure_deficit_nodes_count"] == 0


def test_pipe_burst_scenario():
    """Verify pipe burst scenario generates orifice leakage and pressure drops."""
    run_res = client.post("/api/v1/digital-twin/scenarios/SCEN-BURST-PIPE-02/run", json={})
    assert run_res.status_code == 200
    burst_run = run_res.json()
    assert burst_run["converged"] is True
    assert burst_run["total_leakage_m3"] > 0.0
    assert burst_run["water_loss_percentage"] > 10.0  # Significant loss during burst

    # Retrieve full run output
    run_id = burst_run["run_id"]
    detail_res = client.get(f"/api/v1/digital-twin/runs/{run_id}")
    assert detail_res.status_code == 200
    details = detail_res.json()
    assert details["nodes"]["NODE-JUNC-02"]["leak_flow_lps"] > 10.0


def test_scenario_comparison():
    """Verify differential comparison matrix between baseline and burst scenario."""
    compare_req = {
        "baseline_scenario_id": "SCEN-BASELINE-01",
        "comparison_scenario_id": "SCEN-BURST-PIPE-02",
    }
    cmp_res = client.post("/api/v1/digital-twin/scenarios/compare", json=compare_req)
    assert cmp_res.status_code == 200
    cmp_data = cmp_res.json()

    assert cmp_data["delta_total_leakage_m3"] > 0.0
    assert cmp_data["delta_water_loss_pct"] > 0.0
    assert cmp_data["affected_nodes_count"] >= 1
    assert "nodes" in cmp_data
    assert "links" in cmp_data

    # Node J2 should have an acute pressure drop
    j2 = cmp_data["nodes"]["NODE-JUNC-02"]
    assert j2["delta_pressure_bar"] < 0.0
    assert j2["delta_leak_lps"] > 10.0


def test_interactive_leak_injection():
    """Verify instant what-if leak injection endpoint."""
    leak_req = {
        "network_id": DEFAULT_NETWORK_ID,
        "target_node_id": "NODE-JUNC-04",
        "leak_area_cm2": 6.5,
        "discharge_coeff": 0.75,
    }
    leak_res = client.post("/api/v1/digital-twin/simulate-leak", json=leak_req)
    assert leak_res.status_code == 200
    leak_data = leak_res.json()
    assert "scenario" in leak_data
    assert "run" in leak_data
    assert "comparison" in leak_data
    assert leak_data["run"]["total_leakage_m3"] > 0.0


def test_equipment_status():
    """Verify live telemetry from booster pumps, PRVs, and elevated storage tanks."""
    eq_res = client.get("/api/v1/digital-twin/equipment-status")
    assert eq_res.status_code == 200
    eq = eq_res.json()

    assert len(eq["pumps"]) >= 1
    assert len(eq["valves"]) >= 1
    assert len(eq["tanks"]) >= 1

    pump = eq["pumps"][0]
    assert pump["status"] in ("OPEN", "ACTIVE")
    assert pump["power_kw"] > 0.0

    tank = eq["tanks"][0]
    assert tank["volume_pct"] > 0.0
    assert tank["level_m"] > 0.0


def test_rover_dispatch_handoff():
    """Verify cross-system handoff packaging digital twin burst to Task 08 dispatch."""
    handoff_req = {
        "scenario_id": "SCEN-BURST-PIPE-02",
        "target_node_id": "NODE-JUNC-02",
        "operator_id": "OP-SENIOR-99",
        "notes": "Emergency investigation for simulated burst on Trunk Main B",
    }
    h_res = client.post("/api/v1/digital-twin/handoff-rover-dispatch", json=handoff_req)
    assert h_res.status_code == 200
    h_data = h_res.json()

    assert h_data["status"] == "RECOMMENDED"
    assert h_data["inspection_urgency"] == "CRITICAL_BURST_INVESTIGATION"
    assert h_data["operator_approval_required"] is True
    assert h_data["target_node_id"] == "NODE-JUNC-02"
    assert h_data["assigned_rover_id"] is not None
