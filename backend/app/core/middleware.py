from __future__ import annotations

import asyncio
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Request, Response, status

from app.core.errors import build_error_response

RequestHandler = Callable[[Request], Awaitable[Response]]


class InMemoryRateLimiter:
    def __init__(self, *, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        window_start = now - self.window_seconds

        async with self._lock:
            bucket = self._requests[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()

            if len(bucket) >= self.max_requests:
                return False

            bucket.append(now)
            return True


def request_context_middleware() -> Callable[[Request, RequestHandler], Awaitable[Response]]:
    async def middleware(request: Request, call_next: RequestHandler) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    return middleware


def create_rate_limit_middleware(
    *,
    api_prefix: str,
    max_requests: int,
    window_seconds: int,
) -> Callable[[Request, RequestHandler], Awaitable[Response]]:
    limiter = InMemoryRateLimiter(max_requests=max_requests, window_seconds=window_seconds)
    guarded_methods = {"POST", "PATCH", "DELETE"}

    async def middleware(request: Request, call_next: RequestHandler) -> Response:
        if request.method not in guarded_methods or not request.url.path.startswith(api_prefix):
            return await call_next(request)

        if not getattr(request.state, "request_id", None):
            request.state.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        client_host = request.client.host if request.client else "unknown"
        key = f"{client_host}:{request.method}"
        if not await limiter.is_allowed(key):
            return build_error_response(
                request=request,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                code="rate_limit_exceeded",
                message="Too many write requests. Please try again later.",
            )

        return await call_next(request)

    return middleware
