from collections.abc import Callable

from httpx import AsyncClient

ORDERS = "/v1/admin/orders"
DASH = "/v1/admin/dashboard"
SALES = "/v1/admin/insights/sales"
SEO = "/v1/admin/insights/seo"


async def _checkout_accept(client: AsyncClient, h: dict[str, str], body: dict) -> None:
    co = (await client.post("/v1/checkout", json=body)).json()
    listing = (await client.get(ORDERS)).json()
    oid = next(o["id"] for o in listing["items"] if o["number"] == co["order_number"])
    await client.post(f"{ORDERS}/{oid}/accept", headers=h)  # -> captured (PAID)


async def test_dashboard(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, h = owner
    await _checkout_accept(client, h, checkout_body())
    body = (await client.get(DASH)).json()
    assert body["kpis"]["orders_today"] >= 1
    assert body["kpis"]["revenue_today_cents"] >= 4900
    assert body["kpis"]["photos_to_send"] >= 1  # ACCEPTED awaits a photo
    assert len(body["revenue_series"]) == 7
    assert body["google"]["clicks"] == 0  # GSC not wired


async def test_sales_insights(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, h = owner
    await _checkout_accept(client, h, checkout_body())
    body = (await client.get(SALES, params={"range": 30})).json()
    assert body["range_days"] == 30
    assert len(body["revenue_series"]) == 30
    assert any(b["key"] == "PREMIUM" for b in body["by_tier"])
    assert any(b["key"] == "ROME_SAME_DAY" for b in body["by_delivery_type"])
    assert body["new_customers"] >= 1


async def test_seo_is_empty_stub(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, _ = owner
    body = (await client.get(SEO)).json()
    assert body == {
        "kpis": [],
        "clicks": [],
        "impressions": [],
        "queries": [],
        "landing": [],
        "keywords": [],
        "connected": False,
    }


async def test_insights_owner_or_manager_only(
    florist: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, _ = florist
    assert (await client.get(DASH)).status_code == 403
    assert (await client.get(SALES)).status_code == 403
