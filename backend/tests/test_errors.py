from httpx import AsyncClient


async def test_404_envelope_has_request_id(client: AsyncClient) -> None:
    resp = await client.get("/products/does-not-exist")
    assert resp.status_code == 404
    err = resp.json()["error"]
    assert err["code"] == "product_not_found"
    assert set(err) == {"code", "message", "details", "request_id"}
    assert err["request_id"]
    assert resp.headers["X-Request-ID"] == err["request_id"]


async def test_validation_error_uses_envelope(client: AsyncClient) -> None:
    # Invalid email trips Pydantic validation (login needs no auth).
    resp = await client.post(
        "/v1/admin/auth/login", json={"email": "not-an-email", "password": "x"}
    )
    assert resp.status_code == 422
    err = resp.json()["error"]
    assert err["code"] == "validation_error"
    assert err["request_id"]


async def test_security_headers_present(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "X-Request-ID" in resp.headers
