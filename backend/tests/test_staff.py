from httpx import AsyncClient

STAFF = "/v1/admin/staff"
LOGIN = "/v1/admin/auth/login"

_NEW = {
    "email": "rider@romafiorita.com",
    "name": "Rico Rider",
    "role": "RIDER",
    "password": "password123",
}


async def test_list_staff(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, _ = owner
    body = (await client.get(STAFF)).json()
    emails = {s["email"] for s in body["items"]}
    assert "owner@romafiorita.com" in emails
    assert "florist@romafiorita.com" in emails


async def test_staff_is_owner_only(
    florist: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, _ = florist
    assert (await client.get(STAFF)).status_code == 403


async def test_create_staff_and_login(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = owner
    resp = await client.post(STAFF, json=_NEW, headers=h)
    assert resp.status_code == 201
    assert resp.json()["role"] == "RIDER"
    # The new member can authenticate.
    login = await client.post(
        LOGIN, json={"email": _NEW["email"], "password": _NEW["password"]}
    )
    assert login.status_code == 200


async def test_create_duplicate_email_409(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = owner
    dup = {**_NEW, "email": "owner@romafiorita.com"}
    resp = await client.post(STAFF, json=dup, headers=h)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "email_taken"


async def test_create_requires_csrf(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, _ = owner
    assert (await client.post(STAFF, json=_NEW)).status_code == 403


async def test_patch_staff(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, h = owner
    created = (await client.post(STAFF, json=_NEW, headers=h)).json()
    resp = await client.patch(
        f"{STAFF}/{created['id']}", headers=h, json={"is_active": False}
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False
