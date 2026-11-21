import logging

from httpx import AsyncClient

from app.core.logging import JsonFormatter


async def test_healthz(client: AsyncClient) -> None:
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_readyz_ok(client: AsyncClient) -> None:
    resp = await client.get("/readyz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"]["db"] == "ok"


async def test_health_alias_still_works(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_json_formatter_includes_custom_fields() -> None:
    import json

    record = logging.LogRecord(
        name="romafiorita.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request",
        args=(),
        exc_info=None,
    )
    record.request_id = "abc123"
    record.status = 200
    out = json.loads(JsonFormatter().format(record))
    assert out["message"] == "request"
    assert out["request_id"] == "abc123"
    assert out["status"] == 200
    assert out["level"] == "INFO"
