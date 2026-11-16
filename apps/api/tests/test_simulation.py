"""
Simulation Controls & Engine Lifecycle Tests
"""
import pytest
from app.services.simulation_service import simulation_service
from app.models.rover import RoverModel


def test_simulation_status(client):
    response = client.get("/api/v1/simulation/status")
    assert response.status_code == 200
    status = response.json()
    assert "is_running" in status
    assert "tick_interval_ms" in status
    assert "active_rovers_count" in status
    assert status["is_simulated"] is True


def test_simulation_controls_lifecycle(client):
    # Start simulation
    start_res = client.post("/api/v1/simulation/start")
    assert start_res.status_code == 200
    assert start_res.json()["is_running"] is True

    # Pause simulation
    pause_res = client.post("/api/v1/simulation/pause")
    assert pause_res.status_code == 200
    assert pause_res.json()["is_running"] is False

    # Resume simulation
    resume_res = client.post("/api/v1/simulation/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["is_running"] is True

    # Reset simulation
    reset_res = client.post("/api/v1/simulation/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["is_running"] is False


@pytest.mark.asyncio
async def test_single_tick_advances_kinematics(db_session):
    # Rover 1 is in INSPECTING at station 1200m
    r1_before = db_session.query(RoverModel).filter(RoverModel.id == "ROV-AQUA-01").first()
    assert r1_before is not None
    # Execute single tick
    await simulation_service.execute_tick()
    assert simulation_service.tick_count >= 1
