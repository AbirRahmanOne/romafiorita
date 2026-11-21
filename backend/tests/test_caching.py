from httpx import AsyncClient


async def test_products_etag_and_304(client: AsyncClient) -> None:
    r1 = await client.get("/v1/catalog/products")
    assert r1.status_code == 200
    etag = r1.headers["etag"]
    assert etag
    assert "max-age" in r1.headers["cache-control"]
    # Same ETag -> 304 Not Modified.
    r2 = await client.get(
        "/v1/catalog/products", headers={"If-None-Match": etag}
    )
    assert r2.status_code == 304


async def test_product_detail_etag(client: AsyncClient) -> None:
    r1 = await client.get("/v1/catalog/products/rose-di-roma")
    etag = r1.headers["etag"]
    r2 = await client.get(
        "/v1/catalog/products/rose-di-roma", headers={"If-None-Match": etag}
    )
    assert r2.status_code == 304
