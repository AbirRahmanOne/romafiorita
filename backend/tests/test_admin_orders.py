from collections.abc import Callable

from httpx import AsyncClient

ORDERS = "/v1/admin/orders"
CHECKOUT = "/v1/checkout"
SLOT = "2027-06-15T10:00:00+02:00"


async def _checkout_id(client: AsyncClient, body: dict) -> int:
    co = (await client.post(CHECKOUT, json=body)).json()
    listing = (await client.get(ORDERS)).json()
    return next(o["id"] for o in listing["items"] if o["number"] == co["order_number"])


async def test_list_and_detail(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, _ = owner
    oid = await _checkout_id(client, checkout_body())
    listing = (await client.get(ORDERS)).json()
    assert listing["counts"].get("NEW", 0) >= 1
    detail = (await client.get(f"{ORDERS}/{oid}")).json()
    assert detail["status"] == "NEW"
    assert detail["items"][0]["tier"] == "PREMIUM"
    assert any(e["to_status"] == "NEW" for e in detail["events"])


async def test_happy_path(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, h = owner
    oid = await _checkout_id(client, checkout_body())

    async def act(action: str, **kw: object) -> dict:
        resp = await client.post(f"{ORDERS}/{oid}/{action}", headers=h, **kw)  # type: ignore[arg-type]
        assert resp.status_code == 200, resp.text
        return resp.json()

    assert (await act("accept"))["status"] == "ACCEPTED"
    assert (await act("photo", json={"url": "https://img/x.jpg"}))["status"] == (
        "AWAITING_PHOTO"
    )
    assert (await act("send-photo"))["status"] == "PHOTO_SENT"
    assert (await act("approve"))["status"] == "APPROVED"
    assert (await act("dispatch"))["status"] == "OUT_FOR_DELIVERY"
    assert (await act("deliver"))["status"] == "DELIVERED"


async def test_florist_cannot_accept(
    florist: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, h = florist
    oid = await _checkout_id(client, checkout_body())
    resp = await client.post(f"{ORDERS}/{oid}/accept", headers=h)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


async def test_accept_requires_csrf(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, _ = owner
    oid = await _checkout_id(client, checkout_body())
    resp = await client.post(f"{ORDERS}/{oid}/accept")  # no CSRF header
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "csrf_failed"


async def test_invalid_transition(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, h = owner
    oid = await _checkout_id(client, checkout_body())
    resp = await client.post(f"{ORDERS}/{oid}/deliver", headers=h)  # NEW -> deliver
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "invalid_state"


async def test_unknown_action(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, h = owner
    oid = await _checkout_id(client, checkout_body())
    resp = await client.post(f"{ORDERS}/{oid}/frobnicate", headers=h)
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "unknown_action"


async def test_refund_after_accept(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, h = owner
    oid = await _checkout_id(client, checkout_body())
    await client.post(f"{ORDERS}/{oid}/accept", headers=h)
    resp = await client.post(f"{ORDERS}/{oid}/refund", headers=h, json={"reason": "x"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "REFUNDED"


async def test_decline_releases_slot(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, h = owner
    body = checkout_body(delivery_type="exact", slot=SLOT)
    ids = [await _checkout_id(client, body) for _ in range(3)]  # fill capacity 3
    assert (await client.post(CHECKOUT, json=body)).status_code == 409  # full
    # Decline one -> its seat is released.
    assert (
        await client.post(f"{ORDERS}/{ids[0]}/decline", headers=h)
    ).status_code == 200
    assert (await client.post(CHECKOUT, json=body)).status_code == 200
