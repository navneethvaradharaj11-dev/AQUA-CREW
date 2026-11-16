"""
Rover Fleet & Command Execution Tests
"""
def test_list_rovers(client):
    response = client.get("/api/v1/rovers")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] == 5
    assert len(data["rovers"]) == 5
    rover_ids = [r["id"] for r in data["rovers"]]
    assert "ROV-AQUA-01" in rover_ids
    assert "ROV-AQUA-03" in rover_ids


def test_get_rover_by_id(client):
    response = client.get("/api/v1/rovers/ROV-AQUA-01")
    assert response.status_code == 200
    rover = response.json()
    assert rover["id"] == "ROV-AQUA-01"
    assert rover["name"] == "Triton-1 Crawler"
    assert "currentLocation" in rover
    assert rover["currentLocation"]["pipeSegmentId"] == "PIPE-SEC-4B-92"
    assert rover["batteryPercentage"] == 86.0


def test_get_rover_not_found(client):
    response = client.get("/api/v1/rovers/ROV-NON-EXISTENT")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ROVER_NOT_FOUND"


def test_rover_pause_and_resume_commands(client):
    # ROV-AQUA-01 starts in INSPECTING
    pause_res = client.post(
        "/api/v1/rovers/ROV-AQUA-01/commands",
        json={"command": "PAUSE", "reason": "Test pause command"}
    )
    assert pause_res.status_code == 200
    assert pause_res.json()["new_state"] == "PAUSED"

    # Verify state via GET
    rover_res = client.get("/api/v1/rovers/ROV-AQUA-01")
    assert rover_res.json()["operatingState"] == "PAUSED"

    # Resume rover
    resume_res = client.post(
        "/api/v1/rovers/ROV-AQUA-01/commands",
        json={"command": "RESUME", "reason": "Test resume command"}
    )
    assert resume_res.status_code == 200
    assert resume_res.json()["new_state"] == "INSPECTING"


def test_rover_emergency_stop_and_reset(client):
    # Trigger Emergency Stop
    estop_res = client.post(
        "/api/v1/rovers/ROV-AQUA-02/commands",
        json={"command": "EMERGENCY_STOP", "reason": "Obstacle in pipeline"}
    )
    assert estop_res.status_code == 200
    assert estop_res.json()["new_state"] == "EMERGENCY_STOP"

    # Verify velocity and motor current cut to 0
    rover_res = client.get("/api/v1/rovers/ROV-AQUA-02")
    assert rover_res.json()["operatingState"] == "EMERGENCY_STOP"
    assert rover_res.json()["kinematics"]["velocityMps"] == 0.0

    # Illegal direct resume from EMERGENCY_STOP must be rejected (HTTP 400)
    illegal_res = client.post(
        "/api/v1/rovers/ROV-AQUA-02/commands",
        json={"command": "RESUME", "reason": "Premature resume"}
    )
    assert illegal_res.status_code == 400
    assert illegal_res.json()["error"]["code"] == "INVALID_STATE_TRANSITION"

    # Administrative reset
    reset_res = client.post(
        "/api/v1/rovers/ROV-AQUA-02/commands",
        json={"command": "RESET_ESTOP", "reason": "Safety perimeter verified"}
    )
    assert reset_res.status_code == 200
    assert reset_res.json()["new_state"] == "IDLE"


def test_rover_events_history(client):
    res = client.post(
        "/api/v1/rovers/ROV-AQUA-01/commands",
        json={"command": "PAUSE", "reason": "Pre-check pause"}
    )
    assert res.status_code == 200
    response = client.get("/api/v1/rovers/ROV-AQUA-01/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
    assert events[0]["rover_id"] == "ROV-AQUA-01"
    assert events[0]["is_simulated"] is True
