"""
Telemetry Endpoints Tests
"""
def test_get_latest_telemetry(client):
    response = client.get("/api/v1/telemetry/latest")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] == 5
    assert len(data["rovers"]) == 5


def test_get_telemetry_health(client):
    response = client.get("/api/v1/telemetry/health")
    assert response.status_code == 200
    health = response.json()
    assert "active_rovers" in health
    assert "total_rovers" in health
    assert "average_battery_pct" in health
    assert health["is_simulated"] is True


def test_get_telemetry_history(client):
    response = client.get("/api/v1/telemetry/history?page=1&page_size=10")
    assert response.status_code == 200
    hist = response.json()
    assert hist["success"] is True
    assert "count" in hist
    assert "records" in hist

