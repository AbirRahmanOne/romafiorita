from collections.abc import Callable
from typing import Any

from httpx import AsyncClient

ORDERS = "/v1/admin/orders"


async def _order_id(client: AsyncClient, body: dict) -> tuple[str, int]:
    co = (await client.post("/v1/checkout", json=body)).json()
    listing = (await client.get(ORDERS)).json()
    oid = next(o["id"] for o in listing["items"] if o["number"] == co["order_number"])
    return co["order_number"], oid


async def test_checkout_sends_order_received(
    client: AsyncClient, checkout_body: Callable[..., dict], emails: Any
) -> None:
    await client.post("/v1/checkout", json=checkout_body())
    assert len(emails.sent) == 1
    msg = emails.sent[0]
    assert msg.template == "order_received.v1"
    assert msg.to == "sam@example.com"
    assert msg.locale == "en"


async def test_transitions_send_matching_emails(
    owner: tuple[AsyncClient, dict[str, str]],
    checkout_body: Callable[..., dict],
    emails: Any,
) -> None:
    client, h = owner
    _, oid = await _order_id(client, checkout_body())
    emails.sent.clear()  # ignore the order_received from checkout
    await client.post(f"{ORDERS}/{oid}/accept", headers=h)
    await client.post(f"{ORDERS}/{oid}/photo", headers=h, json={"url": "x"})
    await client.post(f"{ORDERS}/{oid}/send-photo", headers=h)
    templates = [m.template for m in emails.sent]
    # accept -> accepted; photo -> none; send-photo -> photo_sent
    assert templates == ["accepted.v1", "photo_sent.v1"]


async def test_italian_locale(
    client: AsyncClient, checkout_body: Callable[..., dict], emails: Any
) -> None:
    body = checkout_body()
    body["sender"]["locale"] = "it"
    await client.post("/v1/checkout", json=body)
    assert "ricevuto" in emails.sent[0].subject
