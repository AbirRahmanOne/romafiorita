from collections.abc import Callable

from httpx import AsyncClient

EXPORT = "/v1/admin/gdpr/export"
DELETE = "/v1/admin/gdpr/delete"
SENDER = "sam@example.com"


async def test_export_customer(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, _ = owner
    await client.post("/v1/checkout", json=checkout_body())
    resp = await client.get(EXPORT, params={"email": SENDER})
    assert resp.status_code == 200
    body = resp.json()
    assert body["customer"]["email"] == SENDER
    assert len(body["orders"]) == 1
    assert body["orders"][0]["items"][0]["tier"] == "PREMIUM"


async def test_export_unknown_404(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, _ = owner
    resp = await client.get(EXPORT, params={"email": "ghost@x.com"})
    assert resp.status_code == 404


async def test_export_owner_only(
    florist: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, _ = florist
    assert (await client.get(EXPORT, params={"email": SENDER})).status_code == 403


async def test_delete_anonymises(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, h = owner
    await client.post("/v1/checkout", json=checkout_body())
    resp = await client.post(DELETE, headers=h, json={"email": SENDER})
    assert resp.status_code == 200
    assert resp.json() == {"anonymised": True}
    # The customer can no longer be found by email (erased).
    assert (await client.get(EXPORT, params={"email": SENDER})).status_code == 404


async def test_delete_requires_csrf(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, _ = owner
    await client.post("/v1/checkout", json=checkout_body())
    assert (await client.post(DELETE, json={"email": SENDER})).status_code == 403
