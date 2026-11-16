"""
AQUA CREW — Request Size Limit Middleware
Guards against volumetric Denial-of-Service and memory exhaustion by enforcing a strict
content length limit (default 10 MB).
"""
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from datetime import datetime, timezone

MAX_REQUEST_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int = MAX_REQUEST_SIZE_BYTES):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        content_length = request.headers.get("Content-Length")
        if content_length:
            try:
                length = int(content_length)
                if length > self.max_bytes:
                    request_id = getattr(request.state, "request_id", None)
                    return JSONResponse(
                        status_code=413,
                        content={
                            "success": False,
                            "error": {
                                "code": "PAYLOAD_TOO_LARGE",
                                "message": f"Request payload exceeds maximum allowed size of {self.max_bytes // (1024 * 1024)}MB.",
                                "details": [{"content_length": length, "max_allowed": self.max_bytes}],
                                "request_id": request_id,
                            },
                            "request_id": request_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )
            except ValueError:
                pass

        return await call_next(request)

