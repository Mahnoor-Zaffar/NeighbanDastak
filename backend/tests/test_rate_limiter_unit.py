from __future__ import annotations

import asyncio

from app.core.middleware import InMemoryRateLimiter


def test_in_memory_rate_limiter_blocks_after_limit() -> None:
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)

    async def _run() -> None:
        assert await limiter.is_allowed("127.0.0.1:POST")
        assert await limiter.is_allowed("127.0.0.1:POST")
        assert not await limiter.is_allowed("127.0.0.1:POST")

    asyncio.run(_run())


def test_in_memory_rate_limiter_is_key_scoped() -> None:
    limiter = InMemoryRateLimiter(max_requests=1, window_seconds=60)

    async def _run() -> None:
        assert await limiter.is_allowed("127.0.0.1:POST")
        assert await limiter.is_allowed("127.0.0.1:PATCH")
        assert not await limiter.is_allowed("127.0.0.1:POST")

    asyncio.run(_run())
