from collections.abc import Callable

from httpx import AsyncClient

PAYMENTS = "/v1/admin/payments"
ORDERS = "/v1/admin/orders"


async def _checkout_and_order_id(
    client: AsyncClient, body: dict
) -> tuple[str, int]:
    co = (await client.post("/v1/checkout", json=body)).json()
    listing = (await client.get(ORDERS)).json()
    oid = next(o["id"] for o in listing["items"] if o["number"] == co["order_number"])
    return co["order_number"], oid


async def test_payments_list_held_then_captured(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, h = owner
    number, oid = await _checkout_and_order_id(client, checkout_body())

    listing = (await client.get(PAYMENTS)).json()
    row = next(p for p in listing["items"] if p["order_number"] == number)
    assert row["status"] == "held"
    assert row["source"] == "WEBSITE"
    assert row["fee_cents"] is None  # no Stripe balance tx yet

    # held view shows it with an expiry.
    held = (await client.get(f"{PAYMENTS}/held")).json()
    assert any(p["order_number"] == number for p in held["items"])

    # Accept -> captured; KPIs reflect gross.
    await client.post(f"{ORDERS}/{oid}/accept", headers=h)
    listing2 = (await client.get(PAYMENTS)).json()
    row2 = next(p for p in listing2["items"] if p["order_number"] == number)
    assert row2["status"] == "captured"
    assert listing2["kpis"]["gross_cents"] >= 4900


async def test_payments_owner_only(
    florist: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, _ = florist
    assert (await client.get(PAYMENTS)).status_code == 403


async def test_monthly_report_csv(
    owner: tuple[AsyncClient, dict[str, str]], checkout_body: Callable[..., dict]
) -> None:
    client, h = owner
    _, oid = await _checkout_and_order_id(client, checkout_body())
    await client.post(f"{ORDERS}/{oid}/accept", headers=h)  # capture
    report = (await client.get(f"{PAYMENTS}/reports/monthly")).json()
    assert report["filename"].endswith(".csv")
    assert "order_number,date,amount_eur,status" in report["csv"]


async def test_payouts_and_disputes_stubs(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, _ = owner
    payouts = (await client.get("/v1/admin/payouts")).json()
    assert payouts["items"] == []
    assert payouts["balance"] == {"available_cents": 0, "pending_cents": 0}
    assert (await client.get("/v1/admin/disputes")).json() == {"items": []}
