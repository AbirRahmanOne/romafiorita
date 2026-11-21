from collections.abc import Callable

from httpx import AsyncClient


async def test_track_returns_public_view(
    client: AsyncClient, checkout_body: Callable[..., dict]
) -> None:
    checkout = (await client.post("/v1/checkout", json=checkout_body())).json()
    resp = await client.get(f"/v1/orders/track/{checkout['token']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["order_number"] == checkout["order_number"]
    assert body["status"] == "NEW"
    assert body["total_cents"] == 4900
    assert body["items"][0]["tier"] == "PREMIUM"
    # public-safe: no sender email / payment fields
    assert "sender_email" not in body
    first = next(s for s in body["timeline"] if s["status"] == "NEW")
    assert first["done"] is True


async def test_track_unknown_token_404(client: AsyncClient) -> None:
    resp = await client.get("/v1/orders/track/nope")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "order_not_found"
