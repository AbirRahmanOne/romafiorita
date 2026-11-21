from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import AsyncClient

from app.core.ratelimit import InMemoryRateLimiter
from app.main import app


@pytest_asyncio.fixture
async def rate_limited() -> AsyncIterator[None]:
    app.state.rate_limiter = InMemoryRateLimiter()
    yield
    app.state.rate_limiter = None


async def test_verify_is_rate_limited(
    client: AsyncClient, rate_limited: None
) -> None:
    body = {"order_number": "RF-2026-00001", "email": "x@example.com"}
    for _ in range(5):  # limit=5
        assert (await client.post("/v1/verify", json=body)).status_code == 200
    resp = await client.post("/v1/verify", json=body)
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "rate_limited"


async def test_no_limiter_means_no_limit(client: AsyncClient) -> None:
    # No lifespan in tests -> app.state.rate_limiter unset -> limiting skipped.
    body = {"order_number": "RF-2026-00001", "email": "x@example.com"}
    for _ in range(8):
        assert (await client.post("/v1/verify", json=body)).status_code == 200


async def test_limiter_unit() -> None:
    limiter = InMemoryRateLimiter()
    assert await limiter.allow("k", 2, 60) is True
    assert await limiter.allow("k", 2, 60) is True
    assert await limiter.allow("k", 2, 60) is False
    assert await limiter.allow("other", 2, 60) is True
