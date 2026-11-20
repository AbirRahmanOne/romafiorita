from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import PaymentRequestCreate
from app.services import payment_requests as svc

ADMIN = "/v1/admin/payment-requests"

_PR = {
    "customer": "Sofia Greco",
    "email": "sofia@example.com",
    "whatsapp": "+391234567890",
    "recipient": "Aurora Greco · Monti",
    "delivery_slot": "Sat 24 · 11:00",
    "card_message": "Con amore.",
    "items": [{"title": "Custom bridal bouquet", "price_cents": 8400}],
    "expiry_hours": 48,
    "discount_cents": 400,
}


async def _create(client: AsyncClient, headers: dict[str, str]) -> dict:
    resp = await client.post(ADMIN, json=_PR, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


# --- admin create + authz ------------------------------------------------


async def test_create_returns_token_and_amount(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = owner
    body = await _create(client, h)
    assert body["order_number"].startswith("RF-")
    assert body["token"]
    assert body["amount_cents"] == 8000  # 8400 - 400 discount
    assert body["status"] == "SENT"


async def test_create_unauthenticated_401(client: AsyncClient) -> None:
    assert (await client.post(ADMIN, json=_PR)).status_code == 401


async def test_create_as_florist_403(
    florist: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = florist
    assert (await client.post(ADMIN, json=_PR, headers=h)).status_code == 403


async def test_list_hides_token(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, h = owner
    await _create(client, h)
    listing = (await client.get(ADMIN, headers=h)).json()
    assert len(listing["items"]) >= 1
    assert listing["items"][0]["token"] is None


# --- public pay / verify -------------------------------------------------


async def test_pay_summary_marks_viewed(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = owner
    token = (await _create(client, h))["token"]
    resp = await client.get(f"/v1/pay/{token}")
    assert resp.status_code == 200
    assert resp.headers["X-Robots-Tag"] == "noindex"
    body = resp.json()
    assert body["amount_cents"] == 8000
    assert body["status"] == "VIEWED"
    assert body["items"][0]["title"] == "Custom bridal bouquet"


async def test_pay_intent_then_not_payable(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = owner
    token = (await _create(client, h))["token"]
    resp = await client.post(f"/v1/pay/{token}/intent")
    assert resp.status_code == 200
    assert resp.json()["client_secret"].startswith("pi_mock_")
    # Second attempt is refused (already paid).
    again = await client.post(f"/v1/pay/{token}/intent")
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "not_payable"


async def test_pay_unknown_token_404(client: AsyncClient) -> None:
    assert (await client.get("/v1/pay/nope")).status_code == 404


async def test_verify_match_and_nomatch(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = owner
    body = await _create(client, h)
    ok = await client.post(
        "/v1/verify",
        json={"order_number": body["order_number"], "email": "sofia@example.com"},
    )
    assert ok.json()["genuine"] is True
    assert ok.json()["amount_cents"] == 8000
    # Wrong email -> no leak.
    bad = await client.post(
        "/v1/verify",
        json={"order_number": body["order_number"], "email": "nope@example.com"},
    )
    assert bad.json() == {
        "genuine": False,
        "order_number": None,
        "amount_cents": None,
        "status": None,
    }


# --- admin lifecycle -----------------------------------------------------


async def test_cancel_blocks_payment(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = owner
    created = await _create(client, h)
    token, pr_id = created["token"], created["id"]
    assert (
        await client.post(f"{ADMIN}/{pr_id}/cancel", headers=h)
    ).status_code == 200
    resp = await client.post(f"/v1/pay/{token}/intent")
    assert resp.status_code == 409


async def test_resend_rotates_token(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = owner
    created = await _create(client, h)
    old, pr_id = created["token"], created["id"]
    new = (await client.post(f"{ADMIN}/{pr_id}/resend", headers=h)).json()["token"]
    assert new and new != old
    assert (await client.get(f"/v1/pay/{old}")).status_code == 404
    assert (await client.get(f"/v1/pay/{new}")).status_code == 200


async def test_edit_updates_amount_and_rotates_token(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = owner
    created = await _create(client, h)
    old, pr_id = created["token"], created["id"]
    resp = await client.patch(
        f"{ADMIN}/{pr_id}",
        headers=h,
        json={"items": [{"title": "Bigger bouquet", "price_cents": 12000}]},
    )
    assert resp.status_code == 200
    assert resp.json()["amount_cents"] == 12000 - 400
    assert (await client.get(f"/v1/pay/{old}")).status_code == 404


async def test_duplicate_makes_new_order(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, h = owner
    created = await _create(client, h)
    dup = (await client.post(f"{ADMIN}/{created['id']}/duplicate", headers=h)).json()
    assert dup["order_number"] != created["order_number"]
    assert dup["token"] and dup["token"] != created["token"]


async def test_pdf_is_pdf(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, h = owner
    pr_id = (await _create(client, h))["id"]
    resp = await client.get(f"{ADMIN}/{pr_id}/pdf", headers=h)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"


# --- service-level expiry ------------------------------------------------


async def test_expired_request_cannot_be_paid(db_session: AsyncSession) -> None:
    pr, _token = await svc.create(db_session, PaymentRequestCreate(**_PR))
    pr.expires_at = datetime.now(UTC) - timedelta(hours=1)
    await db_session.commit()
    assert svc.effective_status(pr) == "EXPIRED"
    from app.payments import MockPaymentProvider

    try:
        await svc.pay(db_session, MockPaymentProvider(), pr)
        raise AssertionError("expected expiry error")
    except svc.PaymentRequestError as exc:
        assert exc.code == "expired"
