import json
import logging
import time
from collections import defaultdict, deque
from threading import Lock
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import settings

logger = logging.getLogger("resumeiq.api")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            _log("error", request, request_id, duration_ms, status_code=500)
            raise
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        _log("request", request, request_id, duration_ms, status_code=response.status_code)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        if settings.app_env.lower() == "production":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    """Process-local guardrail; deploy a shared gateway/Redis limiter for multiple replicas."""

    protected_prefixes = ("/api/v1/auth/", "/api/v1/resumes/upload", "/api/v1/analysis")

    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith(self.protected_prefixes):
            now = time.monotonic()
            key = f"{request.client.host if request.client else 'unknown'}:{request.url.path}"
            with self._lock:
                bucket = self._requests[key]
                cutoff = now - settings.rate_limit_window_seconds
                while bucket and bucket[0] <= cutoff:
                    bucket.popleft()
                if len(bucket) >= settings.rate_limit_requests:
                    return JSONResponse(status_code=429, content={"detail": "Too many requests", "request_id": getattr(request.state, "request_id", None)})
                bucket.append(now)
        return await call_next(request)


def _log(event: str, request: Request, request_id: str, duration_ms: float, *, status_code: int) -> None:
    logger.info(json.dumps({"event": event, "request_id": request_id, "method": request.method, "path": request.url.path, "status_code": status_code, "duration_ms": duration_ms}))
