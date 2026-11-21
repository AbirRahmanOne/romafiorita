from httpx import AsyncClient

ADMIN = "/v1/admin/settings"


async def test_defaults(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, _ = owner
    body = (await client.get(ADMIN)).json()
    assert body["slot_pricing"] == {"window_cents": 500, "exact_cents": 900}
    assert body["business"]["company_name"] is None  # null until supplied
    assert body["daily_capacity"] == 50


async def test_patch_persists(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, h = owner
    resp = await client.patch(
        ADMIN,
        headers=h,
        json={"daily_capacity": 80, "business": {"company_name": "Roma Fiorita Srl"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["daily_capacity"] == 80
    assert body["business"]["company_name"] == "Roma Fiorita Srl"
    # persisted
    assert (await client.get(ADMIN)).json()["daily_capacity"] == 80


async def test_patch_requires_owner_or_manager(
    florist: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = florist
    resp = await client.patch(ADMIN, headers=h, json={"daily_capacity": 1})
    assert resp.status_code == 403


async def test_patch_requires_csrf(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, _ = owner
    resp = await client.patch(ADMIN, json={"daily_capacity": 1})
    assert resp.status_code == 403


async def test_public_config(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, h = owner
    await client.patch(
        ADMIN, headers=h, json={"business": {"company_name": "RF Srl", "phone": "+39"}}
    )
    business = (await client.get("/v1/config/business")).json()
    assert business["company_name"] == "RF Srl"
    public = (await client.get("/v1/config/settings")).json()
    assert "slot_pricing" in public
    assert "notification_recipients" not in public  # not exposed publicly
