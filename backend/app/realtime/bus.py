"""In-process pub/sub for admin SSE.

ponytail: single-process only. For multiple API instances, back this with Redis
pub/sub (publish to a channel, each instance fans out to its subscribers) — the
EventBus interface stays the same.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    async def publish(self, event: dict[str, Any]) -> None:
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass  # slow consumer drops events rather than blocking producers

    @asynccontextmanager
    async def subscribe(self) -> AsyncIterator[asyncio.Queue[dict[str, Any]]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)
        try:
            yield queue
        finally:
            self._subscribers.discard(queue)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


_bus = EventBus()


def get_event_bus() -> EventBus:
    return _bus
