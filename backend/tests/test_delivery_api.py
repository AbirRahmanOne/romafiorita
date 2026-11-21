from httpx import AsyncClient

CHECK = "/v1/delivery/check"
SLOTS = "/v1/delivery/slots"


async def test_check_rome(client: AsyncClient) -> None:
    body = (await client.get(CHECK, params={"postcode": "00144"})).json()
    assert body["zone"] == "ROME"
    assert body["types"] == ["standard", "window", "exact"]
    assert body["fees"] == {
        "standard_cents": 0,
        "window_cents": 500,
        "exact_cents": 900,
    }
    assert body["cutoff"] is not None


async def test_check_national(client: AsyncClient) -> None:
    body = (await client.get(CHECK, params={"postcode": "20121"})).json()
    assert body["zone"] == "NATIONAL"
    assert body["types"] == ["courier"]
    assert body["cutoff"] is None


async def test_check_invalid_postcode(client: AsyncClient) -> None:
    resp = await client.get(CHECK, params={"postcode": "nope"})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_postcode"


async def test_slots_rome(client: AsyncClient) -> None:
    body = (await client.get(SLOTS, params={"postcode": "00144"})).json()
    assert len(body["slots"]) == 68
    first = body["slots"][0]
    assert {"time", "iso", "available"} == set(first)


async def test_slots_national_empty(client: AsyncClient) -> None:
    body = (await client.get(SLOTS, params={"postcode": "20121"})).json()
    assert body["slots"] == []
