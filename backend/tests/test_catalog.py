from httpx import AsyncClient

PRODUCTS = "/v1/catalog/products"
ADMIN_PRODUCTS = "/v1/admin/products"

_NEW = {
    "slug": "nuovo-bouquet",
    "name_it": "Nuovo",
    "name_en": "New",
    "occasion": "love",
    "variants": [
        {"tier": "STANDARD", "price_cents": 3000, "is_default": False},
        {"tier": "PREMIUM", "price_cents": 4000, "is_default": True},
        {"tier": "LUXURY", "price_cents": 6000, "is_default": False},
    ],
}


# --- public reads --------------------------------------------------------


async def test_list_products_active_only_with_variants(client: AsyncClient) -> None:
    body = (await client.get(PRODUCTS)).json()
    slugs = {p["slug"] for p in body["items"]}
    assert slugs == {"rose-di-roma", "primavera-romana"}  # nascosto is inactive
    rose = next(p for p in body["items"] if p["slug"] == "rose-di-roma")
    assert len(rose["variants"]) == 3
    default = [v for v in rose["variants"] if v["is_default"]]
    assert len(default) == 1 and default[0]["tier"] == "PREMIUM"
    v = rose["variants"][0]
    assert {"id", "tier", "price_cents", "active", "same_day", "exact_time"} <= set(v)
    assert v["id"].startswith("rose-di-roma-")


async def test_filter_by_occasion(client: AsyncClient) -> None:
    body = (await client.get(PRODUCTS, params={"occasion": "love"})).json()
    assert {p["slug"] for p in body["items"]} == {"rose-di-roma"}


async def test_locale_switches_name(client: AsyncClient) -> None:
    en = (await client.get(f"{PRODUCTS}/rose-di-roma", params={"locale": "en"})).json()
    it = (await client.get(f"{PRODUCTS}/rose-di-roma", params={"locale": "it"})).json()
    assert en["name"] == "Roses of Rome"
    assert it["name"] == "Rose di Roma"


async def test_inactive_and_unknown_are_404(client: AsyncClient) -> None:
    assert (await client.get(f"{PRODUCTS}/nascosto")).status_code == 404
    assert (await client.get(f"{PRODUCTS}/ghost")).status_code == 404


async def test_occasions(client: AsyncClient) -> None:
    body = (await client.get("/v1/catalog/occasions")).json()
    assert len(body["items"]) == 6
    assert {"slug", "name_it", "name_en"} == set(body["items"][0])


async def test_addons(client: AsyncClient) -> None:
    body = (await client.get("/v1/catalog/addons")).json()
    by_id = {a["id"]: a for a in body["items"]}
    assert by_id["vase"]["price_cents"] == 1800
    assert by_id["card"]["price_cents"] == 0


# --- admin create + authz ------------------------------------------------


async def test_create_product(owner: tuple[AsyncClient, dict[str, str]]) -> None:
    client, headers = owner
    resp = await client.post(ADMIN_PRODUCTS, json=_NEW, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["slug"] == "nuovo-bouquet"
    assert len(body["variants"]) == 3
    assert (await client.get(f"{PRODUCTS}/nuovo-bouquet")).status_code == 200


async def test_create_unauthenticated_is_401(client: AsyncClient) -> None:
    resp = await client.post(ADMIN_PRODUCTS, json=_NEW)
    assert resp.status_code == 401


async def test_create_without_csrf_is_403(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, _ = owner
    resp = await client.post(ADMIN_PRODUCTS, json=_NEW)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "csrf_failed"


async def test_create_as_florist_is_403(
    florist: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, headers = florist
    resp = await client.post(ADMIN_PRODUCTS, json=_NEW, headers=headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "forbidden"


async def test_create_duplicate_slug_is_409(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, headers = owner
    dup = {**_NEW, "slug": "rose-di-roma"}
    resp = await client.post(ADMIN_PRODUCTS, json=dup, headers=headers)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "slug_taken"


async def test_create_duplicate_tier_is_422(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, headers = owner
    bad = {
        **_NEW,
        "variants": [
            {"tier": "PREMIUM", "price_cents": 1, "is_default": True},
            {"tier": "PREMIUM", "price_cents": 2, "is_default": False},
        ],
    }
    resp = await client.post(ADMIN_PRODUCTS, json=bad, headers=headers)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "duplicate_tier"


async def test_create_requires_exactly_one_default(
    owner: tuple[AsyncClient, dict[str, str]],
) -> None:
    client, headers = owner
    bad = {
        **_NEW,
        "variants": [
            {"tier": "STANDARD", "price_cents": 1, "is_default": True},
            {"tier": "PREMIUM", "price_cents": 2, "is_default": True},
        ],
    }
    resp = await client.post(ADMIN_PRODUCTS, json=bad, headers=headers)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "one_default_required"
