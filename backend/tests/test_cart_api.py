from httpx import AsyncClient

QUOTE = "/v1/cart/quote"
PREMIUM = "rose-di-roma-premium"  # seeded, 4900 cents


async def test_quote_single_variant(client: AsyncClient) -> None:
    body = (
        await client.post(
            QUOTE, json={"items": [{"variant_id": PREMIUM, "quantity": 1}]}
        )
    ).json()
    assert body["subtotal_cents"] == 4900
    assert body["delivery_cents"] == 0
    assert body["time_fee_cents"] == 0
    assert body["total_cents"] == 4900
    assert body["currency"] == "EUR"


async def test_quote_with_addon_and_quantity(client: AsyncClient) -> None:
    body = (
        await client.post(
            QUOTE,
            json={
                "items": [
                    {"variant_id": PREMIUM, "quantity": 2, "addons": ["vase"]}
                ]
            },
        )
    ).json()
    # (4900 + 1800) * 2
    assert body["subtotal_cents"] == 13400
    assert body["total_cents"] == 13400


async def test_quote_exact_time_fee(client: AsyncClient) -> None:
    body = (
        await client.post(
            QUOTE,
            json={
                "items": [{"variant_id": PREMIUM, "quantity": 1}],
                "delivery_type": "exact",
            },
        )
    ).json()
    assert body["time_fee_cents"] == 900
    assert body["total_cents"] == 5800


async def test_quote_unknown_variant_422(client: AsyncClient) -> None:
    resp = await client.post(
        QUOTE, json={"items": [{"variant_id": "nope", "quantity": 1}]}
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "unknown_variant"


async def test_quote_unknown_addon_422(client: AsyncClient) -> None:
    resp = await client.post(
        QUOTE,
        json={"items": [{"variant_id": PREMIUM, "quantity": 1, "addons": ["gold"]}]},
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "unknown_addon"


async def test_quote_empty_items_422(client: AsyncClient) -> None:
    resp = await client.post(QUOTE, json={"items": []})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


async def test_inactive_product_variant_not_quotable(client: AsyncClient) -> None:
    # 'nascosto' product is inactive -> its variants must not price.
    resp = await client.post(
        QUOTE, json={"items": [{"variant_id": "nascosto-premium", "quantity": 1}]}
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "unknown_variant"
