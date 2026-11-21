from collections.abc import Callable

from httpx import AsyncClient

CHECKOUT = "/v1/checkout"
SLOT = "2027-06-15T10:00:00+02:00"


async def test_standard_checkout(
    client: AsyncClient, checkout_body: Callable[..., dict]
) -> None:
    resp = await client.post(CHECKOUT, json=checkout_body())
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["order_number"].startswith("RF-")
    assert body["client_secret"].startswith("pi_mock_")
    assert body["total_cents"] == 4900
    assert body["token"]


async def test_exact_checkout_has_time_fee(
    client: AsyncClient, checkout_body: Callable[..., dict]
) -> None:
    resp = await client.post(
        CHECKOUT, json=checkout_body(delivery_type="exact", slot=SLOT)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["time_fee_cents"] == 900
    assert body["total_cents"] == 5800


async def test_exact_requires_slot(
    client: AsyncClient, checkout_body: Callable[..., dict]
) -> None:
    resp = await client.post(CHECKOUT, json=checkout_body(delivery_type="exact"))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "slot_required"


async def test_delivery_type_zone_mismatch(
    client: AsyncClient, checkout_body: Callable[..., dict]
) -> None:
    # Rome CAP but courier type.
    resp = await client.post(CHECKOUT, json=checkout_body(delivery_type="courier"))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_delivery_type"


async def test_slot_cannot_be_overbooked(
    client: AsyncClient, checkout_body: Callable[..., dict]
) -> None:
    # SLOT_CAPACITY = 3: three exact orders for the same slot fit, the fourth doesn't.
    body = checkout_body(delivery_type="exact", slot=SLOT)
    for _ in range(3):
        assert (await client.post(CHECKOUT, json=body)).status_code == 200
    resp = await client.post(CHECKOUT, json=body)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "slot_unavailable"
