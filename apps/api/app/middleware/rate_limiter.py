"""
AQUA CREW — Sliding Window Rate Limiting Middleware
Enforces IP-based rate limiting across all API endpoints with tightened limits on authentication.
Protects against automated brute-force attacks and volumetric request floods.
"""
import time
from collections import defaultdict
from typing import Dict, List, Tuple
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from datetime import datetime, timezone
import threading


class SlidingWindowRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        # client_ip -> list of epoch timestamps
        self._requests: Dict[str, List[float]] = defaultdict(list)
        # client_ip -> list of epoch timestamps for auth login
        self._auth_requests: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
        is_auth: bool = False,
    ) -> Tuple[bool, int]:
        """
        Returns (is_allowed, retry_after_seconds).
        """
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            store = self._auth_requests if is_auth else self._requests
            timestamps = store[key]

            # Prune timestamps older than window
            valid_timestamps = [t for t in timestamps if t > window_start]
            store[key] = valid_timestamps

            if len(valid_timestamps) >= max_requests:
                oldest_timestamp = valid_timestamps[0]
                retry_after = max(1, int(oldest_timestamp + window_seconds - now))
                return False, retry_after

            store[key].append(now)
            return True, 0

    def reset(self):
        with self._lock:
            self._requests.clear()
            self._auth_requests.clear()


rate_limiter_instance = SlidingWindowRateLimiter()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        default_limit: int = 120,
        auth_limit: int = 10,
        window_seconds: int = 60,
        enabled: bool = True,
    ):
        super().__init__(app)
        self.default_limit = default_limit
        self.auth_limit = auth_limit
        self.window_seconds = window_seconds
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for static/docs and health check endpoints
        path = request.url.path
        if (
            path in ["/", "/docs", "/redoc", "/openapi.json"]
            or path.startswith("/api/v1/health")
            or path.startswith("/health")
            or path == "/metrics"
            or path.startswith("/api/v1/metrics")
        ):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        # Forwarded header support if behind proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        is_auth_login = path.endswith("/auth/login")
        limit = self.auth_limit if is_auth_login else self.default_limit

        allowed, retry_after = rate_limiter_instance.is_allowed(
            key=client_ip,
            max_requests=limit,
            window_seconds=self.window_seconds,
            is_auth=is_auth_login,
        )

        if not allowed:
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(retry_after)},
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded. Too many requests from client IP '{client_ip}'.",
                        "details": [
                            {
                                "limit": limit,
                                "window_seconds": self.window_seconds,
                                "retry_after_seconds": retry_after,
                            }
                        ],
                        "request_id": request_id,
                    },
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

        return await call_next(request)

