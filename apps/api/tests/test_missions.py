"""
Mission Lifecycle & Assignment Tests
"""
def test_list_missions(client):
    response = client.get("/api/v1/missions")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] >= 3
    mission_ids = [m["id"] for m in data["missions"]]
    assert "MSN-2026-042" in mission_ids
    assert "MSN-2026-044" in mission_ids


def test_get_mission_by_id(client):
    response = client.get("/api/v1/missions/MSN-2026-042")
    assert response.status_code == 200
    m = response.json()
    assert m["id"] == "MSN-2026-042"
    assert m["status"] == "In Progress"
    assert m["assignedRoverId"] == "ROV-AQUA-01"


def test_create_mission(client):
    new_mission = {
        "id": "MSN-2026-099",
        "mission_type": "Pressure Transient Test",
        "target_segment_id": "PIPE-SEC-4A-10",
        "waypoint_count": 20,
    }
    response = client.post("/api/v1/missions", json=new_mission)
    assert response.status_code == 200
    created = response.json()
    assert created["id"] == "MSN-2026-099"
    assert created["status"] == "Scheduled"
    assert created["targetSegmentId"] == "PIPE-SEC-4A-10"


def test_assign_mission_to_idle_rover_and_duplicate_guard(client):
    # ROV-AQUA-03 is IDLE. Assign MSN-2026-044 to it.
    assign_res = client.post(
        "/api/v1/missions/MSN-2026-044/assign",
        json={"rover_id": "ROV-AQUA-03"}
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["success"] is True

    # Rover 3 should now be INSPECTING
    r3 = client.get("/api/v1/rovers/ROV-AQUA-03").json()
    assert r3["operatingState"] == "INSPECTING"
    assert r3["assignedMissionId"] == "MSN-2026-044"

    # Attempting to assign another mission to Rover 3 (now busy) must be rejected
    busy_res = client.post(
        "/api/v1/missions/MSN-2026-042/assign",
        json={"rover_id": "ROV-AQUA-03"}
    )
    assert busy_res.status_code == 400
    assert busy_res.json()["error"]["code"] == "ROVER_NOT_IDLE"


def test_mission_lifecycle_pause_resume_cancel(client):
    # Pause mission
    pause_res = client.post("/api/v1/missions/MSN-2026-042/pause")
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "Paused"

    # Resume mission
    resume_res = client.post("/api/v1/missions/MSN-2026-042/resume")
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "In Progress"

    # Cancel mission
    cancel_res = client.post("/api/v1/missions/MSN-2026-042/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "Cancelled"

