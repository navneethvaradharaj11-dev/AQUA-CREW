"""
AQUA CREW — Request ID Correlation Middleware
Assigns or propagates a unique X-Request-ID header across every HTTP transaction.
Attaches request_id to request.state.request_id for downstream logging and audit tracing.
"""
import uuid
import re
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from app.core.metrics import metrics_collector

_REQUEST_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming_id = request.headers.get("X-Request-ID")
        if incoming_id and _REQUEST_ID_REGEX.match(incoming_id):
            request_id = incoming_id
        else:
            request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        # Record request telemetry in metrics
        try:
            metrics_collector.record_http_request(request.method, request.url.path, response.status_code)
        except Exception:
            pass

        return response
