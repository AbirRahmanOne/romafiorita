from httpx import ASGITransport, AsyncClient

from app.main import app

# Kept in sync with tests/conftest.py (seeded staff).
OWNER_EMAIL = "owner@romafiorita.com"
FLORIST_EMAIL = "florist@romafiorita.com"
PASSWORD = "correct-horse-battery-staple"
LOGIN_URL = "/v1/admin/auth/login"
ME = "/v1/admin/auth/me"
LOGOUT = "/v1/admin/auth/logout"
REFRESH = "/v1/admin/auth/refresh"


async def test_login_sets_cookies_and_returns_me(client: AsyncClient) -> None:
    resp = await client.post(
        LOGIN_URL, json={"email": OWNER_EMAIL, "password": PASSWORD}
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "OWNER"
    assert "rf_access" in client.cookies
    assert "rf_refresh" in client.cookies
    assert "rf_csrf" in client.cookies


async def test_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.get(ME)
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "not_authenticated"


async def test_me_after_login(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, _ = owner
    resp = await client.get(ME)
    assert resp.status_code == 200
    assert resp.json()["email"] == OWNER_EMAIL


async def test_wrong_password_is_401(client: AsyncClient) -> None:
    resp = await client.post(LOGIN_URL, json={"email": OWNER_EMAIL, "password": "nope"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_credentials"


async def test_unknown_email_is_401_no_leak(client: AsyncClient) -> None:
    resp = await client.post(
        LOGIN_URL, json={"email": "ghost@romafiorita.com", "password": PASSWORD}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_credentials"


async def test_logout_revokes_session(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, headers = owner
    resp = await client.post(LOGOUT, headers=headers)
    assert resp.status_code == 204
    assert (await client.get(ME)).status_code == 401


async def test_refresh_rotates_token(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, headers = owner
    before = client.cookies["rf_refresh"]
    resp = await client.post(REFRESH, headers=headers)
    assert resp.status_code == 200
    assert client.cookies["rf_refresh"] != before
    # New session still works.
    assert (await client.get(ME)).status_code == 200


async def test_refresh_reuse_is_rejected(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, headers = owner
    stale = client.cookies["rf_refresh"]
    assert (await client.post(REFRESH, headers=headers)).status_code == 200  # rotates
    # Replay the pre-rotation token from a fresh client (same app → same DB).
    # Reuse detection must reject it because the stored jti has rotated.
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        cookies={"rf_refresh": stale, "rf_csrf": "x"},
    ) as replay:
        resp = await replay.post(REFRESH, headers={"X-CSRF-Token": "x"})
    assert resp.status_code == 401


async def test_lockout_after_max_attempts(client: AsyncClient) -> None:
    for _ in range(5):  # login_max_attempts
        r = await client.post(
            LOGIN_URL, json={"email": FLORIST_EMAIL, "password": "wrong"}
        )
        assert r.status_code == 401
    # Even the correct password is now locked out.
    r = await client.post(
        LOGIN_URL, json={"email": FLORIST_EMAIL, "password": PASSWORD}
    )
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "account_locked"
