from httpx import AsyncClient

SIGN = "/v1/admin/uploads/sign"


async def test_sign_default(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, h = owner
    resp = await client.post(SIGN, headers=h, json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["upload_url"].startswith("https://")
    assert body["public_url"].endswith(".jpg")


async def test_florist_can_sign(
    florist: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = florist
    assert (await client.post(SIGN, headers=h, json={})).status_code == 200


async def test_sign_unauthenticated_401(client: AsyncClient) -> None:
    assert (await client.post(SIGN, json={})).status_code == 401


async def test_sign_requires_csrf(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, _ = owner
    assert (await client.post(SIGN, json={})).status_code == 403


async def test_sign_rejects_bad_type(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = owner
    resp = await client.post(SIGN, headers=h, json={"content_type": "application/pdf"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "unsupported_type"
