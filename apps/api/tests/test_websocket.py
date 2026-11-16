"""
WebSocket Real-Time Telemetry Tests
"""
import json


def test_websocket_telemetry_handshake_and_ping(client):
    with client.websocket_connect("/api/v1/ws/telemetry") as websocket:
        # Initial Handshake packet
        data = websocket.receive_text()
        msg = json.loads(data)
        assert msg["type"] == "CONNECTION_ESTABLISHED"
        assert msg["is_simulated"] is True
        assert msg["provenance"] == "VIRTUAL_SIMULATION_BACKEND"

        # Ping-Pong Heartbeat test
        websocket.send_text(json.dumps({"type": "PING", "timestamp": "2026-11-15T16:00:00Z"}))
        pong_data = websocket.receive_text()
        pong = json.loads(pong_data)
        assert pong["type"] == "PONG"
        assert pong["timestamp"] == "2026-11-15T16:00:00Z"

