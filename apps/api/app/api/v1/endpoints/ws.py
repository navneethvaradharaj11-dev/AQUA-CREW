"""
Real-Time Telemetry WebSocket Endpoint (/api/v1/ws/telemetry)
Task 13.6 & Task 17: Authenticated via cryptographic token (query param ?token=<jwt> or Authorization header)
Enforces connection quotas, per-IP rate limits, 64KB frame size limits, and topic subscriptions.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging
from app.websocket.connection_manager import ws_manager, MAX_WS_MESSAGE_SIZE
from app.core.security import decode_and_verify_token
from app.repositories.user_repository import UserRepository
from app.database.session import get_db_context
from app.config import settings

logger = logging.getLogger("aqua_crew.websocket")
router = APIRouter()


@router.websocket("")
@router.websocket("/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """
    Subscribes authenticated client to live backend-generated telemetry and simulation events.
    Enforces cryptographic token verification with code 1008 rejection.
    Enforces per-IP limits, 64KB max frame size, and topic subscriptions.
    """
    client_ip = websocket.client.host if websocket.client else "127.0.0.1"
    forwarded = websocket.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()

    # Pre-accept quota and rate limit verification
    can_accept, reason, close_code = ws_manager.can_accept(client_ip)
    if not can_accept:
        logger.warning(f"WebSocket rejected for {client_ip}: {reason}")
        await websocket.close(code=close_code, reason=reason)
        return

    query_token = websocket.query_params.get("token")
    auth_header = websocket.headers.get("authorization")
    token = None
    if query_token:
        token = query_token
    elif auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]

    user_id = None
    user_role = "VIEWER"

    if not token:
        if settings.REQUIRE_AUTH:
            logger.warning("WebSocket rejected: Missing token when REQUIRE_AUTH is true")
            await websocket.close(code=1008, reason="Authentication token required")
            return
    else:
        try:
            payload = decode_and_verify_token(token, expected_type="access")
            jti = payload.get("jti")
            db = get_db_context()
            try:
                if jti and UserRepository.is_token_revoked(db, jti):
                    logger.warning("WebSocket rejected: Token revoked")
                    await websocket.close(code=1008, reason="Token revoked")
                    return
                user_id = payload.get("sub")
                user = UserRepository.get_by_id(db, user_id)
                if not user or not user.is_active:
                    logger.warning("WebSocket rejected: User inactive or not found")
                    await websocket.close(code=1008, reason="User deactivated or not found")
                    return
                user_role = user.role
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"WebSocket rejected: Invalid token ({e})")
            await websocket.close(code=1008, reason=f"Authentication error: {e}")
            return

    await ws_manager.connect(websocket, client_ip=client_ip, user_id=user_id, role=user_role)
    try:
        while True:
            # Keep connection open, handle client-side ping/messages and frame size limits
            data = await websocket.receive_text()

            # Enforce 64 KB message size limit
            if len(data.encode("utf-8")) > MAX_WS_MESSAGE_SIZE:
                logger.warning(f"WebSocket client {client_ip} exceeded max frame size ({len(data)} bytes). Closing.")
                await websocket.close(code=1009, reason="Message size exceeds maximum 64KB limit")
                ws_manager.disconnect(websocket)
                return

            ws_manager.update_activity(websocket)

            try:
                msg = json.loads(data)
                msg_type = msg.get("type")
                if msg_type == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG", "timestamp": msg.get("timestamp")}))
                elif msg_type == "SUBSCRIBE":
                    topic = msg.get("topic")
                    if topic:
                        ws_manager.subscribe(websocket, topic)
                        await websocket.send_text(json.dumps({"type": "SUBSCRIPTION_CONFIRMED", "topic": topic}))
                elif msg_type == "UNSUBSCRIBE":
                    topic = msg.get("topic")
                    if topic:
                        ws_manager.unsubscribe(websocket, topic)
                        await websocket.send_text(json.dumps({"type": "UNSUBSCRIPTION_CONFIRMED", "topic": topic}))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        ws_manager.disconnect(websocket)


