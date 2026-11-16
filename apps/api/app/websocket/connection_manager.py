"""
AQUA CREW — Production WebSocket Connection Manager (Task 17)
Manages active telemetry subscriber clients, connection quotas, IP limits,
frame size security limits, topic subscriptions, and heartbeat tracking.
"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set, Dict, Any, Optional, Tuple, List
from collections import defaultdict
import json
import logging
import time
from datetime import datetime, timezone
import asyncio

logger = logging.getLogger("aqua_crew.websocket")

MAX_WS_CONNECTIONS = 100
MAX_WS_PER_IP = 10
MAX_WS_MESSAGE_SIZE = 65536  # 64 KB
IDLE_TIMEOUT_SECONDS = 60.0

DEFAULT_TOPICS = {"telemetry", "simulations", "incidents", "missions", "repairs"}


class ConnectionManager:
    def __init__(
        self,
        max_connections: int = MAX_WS_CONNECTIONS,
        max_per_ip: int = MAX_WS_PER_IP,
        max_message_size: int = MAX_WS_MESSAGE_SIZE,
        idle_timeout: float = IDLE_TIMEOUT_SECONDS,
    ):
        self.active_connections: Set[WebSocket] = set()
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self.ip_counts: Dict[str, int] = defaultdict(int)
        self.max_connections = max_connections
        self.max_per_ip = max_per_ip
        self.max_message_size = max_message_size
        self.idle_timeout = idle_timeout
        self.topic_subscribers: Dict[str, Set[WebSocket]] = defaultdict(set)

    def can_accept(self, client_ip: str) -> Tuple[bool, str, int]:
        """
        Validates whether connection can be accepted under global and per-IP quotas.
        Returns (is_allowed, rejection_reason, websocket_close_code).
        """
        if len(self.active_connections) >= self.max_connections:
            return False, "Maximum active WebSocket connections limit reached", 1013
        if self.ip_counts[client_ip] >= self.max_per_ip:
            return False, f"Maximum concurrent WebSocket connections per IP ({self.max_per_ip}) exceeded", 1008
        return True, "", 0

    async def connect(
        self,
        websocket: WebSocket,
        client_ip: str = "127.0.0.1",
        user_id: Optional[str] = None,
        role: Optional[str] = None,
        initial_topics: Optional[List[str]] = None,
    ) -> None:
        """
        Accepts and registers incoming client WebSocket connection with metadata and quota tracking.
        """
        await websocket.accept()
        now = time.time()
        self.active_connections.add(websocket)
        self.ip_counts[client_ip] += 1

        topics = set(initial_topics or DEFAULT_TOPICS)
        self.connection_metadata[websocket] = {
            "client_ip": client_ip,
            "user_id": user_id,
            "role": role or "VIEWER",
            "connected_at": now,
            "last_active": now,
            "subscriptions": topics,
        }

        for topic in topics:
            self.topic_subscribers[topic].add(websocket)

        logger.info(
            f"WebSocket client connected from {client_ip} (user: {user_id or 'anonymous'}). "
            f"Active subscribers: {len(self.active_connections)}"
        )

        # Send initial handshake welcome packet
        await self.send_personal_message(
            {
                "type": "CONNECTION_ESTABLISHED",
                "message": "Connected to AQUA CREW Real-Time Fleet Telemetry Stream",
                "client_ip": client_ip,
                "role": role or "VIEWER",
                "subscribed_topics": list(topics),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_simulated": True,
                "provenance": "VIRTUAL_SIMULATION_BACKEND",
            },
            websocket,
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Unregisters client connection upon disconnect and updates IP quotas.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            meta = self.connection_metadata.pop(websocket, None)
            if meta:
                ip = meta.get("client_ip", "127.0.0.1")
                self.ip_counts[ip] = max(0, self.ip_counts[ip] - 1)
                for topic in meta.get("subscriptions", set()):
                    self.topic_subscribers[topic].discard(websocket)

            logger.info(f"WebSocket client disconnected. Remaining subscribers: {len(self.active_connections)}")

    def update_activity(self, websocket: WebSocket) -> None:
        """
        Refreshes last active timestamp on receipt of valid client frame.
        """
        if websocket in self.connection_metadata:
            self.connection_metadata[websocket]["last_active"] = time.time()

    def subscribe(self, websocket: WebSocket, topic: str) -> bool:
        if websocket not in self.connection_metadata:
            return False
        self.connection_metadata[websocket]["subscriptions"].add(topic)
        self.topic_subscribers[topic].add(websocket)
        return True

    def unsubscribe(self, websocket: WebSocket, topic: str) -> bool:
        if websocket not in self.connection_metadata:
            return False
        self.connection_metadata[websocket]["subscriptions"].discard(topic)
        self.topic_subscribers[topic].discard(websocket)
        return True

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> None:
        """
        Sends message to an individual WebSocket connection.
        """
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.warning(f"Error sending direct WebSocket message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any], topic: Optional[str] = None) -> None:
        """
        Safely broadcasts JSON payload to active subscriber clients.
        If topic is specified, only delivers to clients subscribed to that channel.
        Automatically prunes disconnected clients.
        """
        if not self.active_connections:
            return

        targets = (
            list(self.topic_subscribers.get(topic, set()))
            if topic
            else list(self.active_connections)
        )

        if not targets:
            return

        payload = json.dumps(message, default=str)
        dead_connections = set()

        for connection in targets:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logger.debug(f"Failed to send to client; queuing for removal: {e}")
                dead_connections.add(connection)

        for dead in dead_connections:
            self.disconnect(dead)

    async def prune_idle_connections(self) -> int:
        """
        Prunes idle connections that have not transmitted heartbeats within idle_timeout.
        """
        now = time.time()
        to_prune = []
        for ws, meta in list(self.connection_metadata.items()):
            if now - meta.get("last_active", now) > self.idle_timeout:
                to_prune.append(ws)

        for ws in to_prune:
            try:
                await ws.close(code=1000, reason="Connection closed due to heartbeat idle timeout")
            except Exception:
                pass
            self.disconnect(ws)

        return len(to_prune)

    @property
    def client_count(self) -> int:
        return len(self.active_connections)

    def reset(self):
        """Reset state (for test suites)."""
        self.active_connections.clear()
        self.connection_metadata.clear()
        self.ip_counts.clear()
        self.topic_subscribers.clear()


ws_manager = ConnectionManager()
