"""Rate limiting.

``InMemoryRateLimiter`` (sliding window) is the default for a single process /
dev. ``RedisRateLimiter`` (fixed window via INCR+EXPIRE) is for multi-instance
production. The active limiter lives on ``app.state.rate_limiter`` (set in the
lifespan); if it's absent — e.g. tests that don't run the lifespan — limiting is
skipped.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Protocol


class RateLimiter(Protocol):
    async def allow(self, key: str, limit: int, window_seconds: int) -> bool: ...


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        hits = [t for t in self._hits[key] if t > cutoff]
        hits.append(now)
        self._hits[key] = hits
        return len(hits) <= limit

    def reset(self) -> None:
        self._hits.clear()


class RedisRateLimiter:
    """Fixed-window counter in Redis. Used in production (multi-instance)."""

    def __init__(self, redis: object) -> None:
        self._redis = redis

    async def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        bucket = f"rl:{key}:{int(time.time()) // window_seconds}"
        count = await self._redis.incr(bucket)  # type: ignore[attr-defined]
        if count == 1:
            await self._redis.expire(bucket, window_seconds)  # type: ignore[attr-defined]
        return bool(count <= limit)
