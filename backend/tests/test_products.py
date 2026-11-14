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
