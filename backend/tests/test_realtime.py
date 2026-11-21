from httpx import AsyncClient

from app.realtime.bus import EventBus


async def test_bus_publish_to_subscriber() -> None:
    bus = EventBus()
    async with bus.subscribe() as queue:
        assert bus.subscriber_count == 1
        await bus.publish({"order_id": 1, "status": "ACCEPTED"})
        assert queue.get_nowait() == {"order_id": 1, "status": "ACCEPTED"}
    assert bus.subscriber_count == 0


async def test_publish_without_subscribers_is_noop() -> None:
    bus = EventBus()
    await bus.publish({"x": 1})  # does not raise


async def test_stream_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/v1/admin/orders/stream")
    assert resp.status_code == 401
