from httpx import AsyncClient


async def test_list_products(client: AsyncClient) -> None:
    resp = await client.get("/products")
    assert resp.status_code == 200
    body = resp.json()
    # Two active products; the inactive one is excluded.
    assert body["total"] == 2
    slugs = {p["slug"] for p in body["items"]}
    assert slugs == {"rose-di-roma", "primavera-romana"}


async def test_filter_by_occasion(client: AsyncClient) -> None:
    resp = await client.get("/products", params={"occasion": "birthday"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["slug"] == "primavera-romana"


async def test_get_product_by_slug(client: AsyncClient) -> None:
    resp = await client.get("/products/rose-di-roma")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name_en"] == "Roses of Rome"
    assert body["base_price_cents"] == 4900


async def test_inactive_product_is_404(client: AsyncClient) -> None:
    resp = await client.get("/products/nascosto")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "product_not_found"


async def test_unknown_product_is_404(client: AsyncClient) -> None:
    resp = await client.get("/products/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "product_not_found"


async def test_create_product(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, headers = owner
    payload = {
        "slug": "nuovo-bouquet",
        "name_it": "Nuovo Bouquet",
        "name_en": "New Bouquet",
        "base_price_cents": 3300,
        "occasion": "thank-you",
    }
    resp = await client.post("/products", json=payload, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["slug"] == "nuovo-bouquet"
    assert body["is_active"] is True
    # Now visible in the public list.
    listed = await client.get("/products")
    assert "nuovo-bouquet" in {p["slug"] for p in listed.json()["items"]}


async def test_create_duplicate_slug_is_409(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, headers = owner
    resp = await client.post(
        "/products",
        json={
            "slug": "rose-di-roma",
            "name_it": "x",
            "name_en": "x",
            "base_price_cents": 100,
        },
        headers=headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "slug_taken"


async def test_update_product(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, headers = owner
    resp = await client.patch(
        "/products/id/1",
        json={"base_price_cents": 5500, "is_active": False},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["base_price_cents"] == 5500
    # Deactivated -> gone from the public list.
    listed = await client.get("/products")
    assert "rose-di-roma" not in {p["slug"] for p in listed.json()["items"]}


async def test_update_missing_product_is_404(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, headers = owner
    resp = await client.patch(
        "/products/id/999", json={"name_en": "x"}, headers=headers
    )
    assert resp.status_code == 404


async def test_delete_product(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, headers = owner
    resp = await client.delete("/products/id/2", headers=headers)
    assert resp.status_code == 204
    listed = await client.get("/products")
    assert "primavera-romana" not in {p["slug"] for p in listed.json()["items"]}


# --- authz on catalog writes --------------------------------------------

_NEW = {"slug": "x", "name_it": "x", "name_en": "x", "base_price_cents": 100}


async def test_create_unauthenticated_is_401(client: AsyncClient) -> None:
    resp = await client.post("/products", json=_NEW)
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "not_authenticated"


async def test_create_without_csrf_is_403(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, _ = owner  # logged in, but omit the X-CSRF-Token header
    resp = await client.post("/products", json=_NEW)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "csrf_failed"


async def test_create_as_florist_is_403(
    florist: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, headers = florist
    resp = await client.post("/products", json=_NEW, headers=headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"
