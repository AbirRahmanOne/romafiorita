import json
from typing import Any

import httpx

from app.notifications import EmailMessage, ResendProvider

_MSG = EmailMessage(
    to="buyer@example.com",
    subject="Order RF-2026-00001 received",
    body="Thank you!",
    template="order_received.v1",
    locale="en",
)


async def test_resend_posts_expected_payload() -> None:
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers.get("authorization")
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "email_123"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    await ResendProvider("re_test", client=client).send(_MSG)
    await client.aclose()

    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["auth"] == "Bearer re_test"
    body = captured["body"]
    assert body["to"] == ["buyer@example.com"]
    assert body["from"].startswith("Roma Fiorita <")
    assert body["subject"] == _MSG.subject
    assert body["text"] == "Thank you!"
    assert body["reply_to"] == "info@romafiorita.com"


async def test_resend_retries_then_dead_letters() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = ResendProvider(
        "re_test", client=client, max_attempts=3, backoff_base=0
    )
    # Must not raise into the caller — dead-letters after exhausting retries.
    await provider.send(_MSG)
    await client.aclose()
    assert calls["n"] == 3


async def test_resend_recovers_on_retry() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500 if calls["n"] == 1 else 200, json={"id": "ok"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    await ResendProvider("re_test", client=client, backoff_base=0).send(_MSG)
    await client.aclose()
    assert calls["n"] == 2
