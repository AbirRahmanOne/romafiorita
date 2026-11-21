from httpx import AsyncClient


async def test_reviews_empty_by_design(client: AsyncClient) -> None:
    # Real reviews only — none yet, so the block stays hidden.
    resp = await client.get("/v1/content/reviews")
    assert resp.status_code == 200
    assert resp.json() == {"items": []}
