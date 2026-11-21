"""Email provider seam.

``MockEmailProvider`` records messages in memory (default when no RESEND_API_KEY —
tests, local dev). ``ResendProvider`` sends via the Resend HTTP API with retries +
dead-letter logging. Sending is async and awaited at the call site.

ponytail: awaited inline (off the event loop, but on the request path). To move it
fully off-request, enqueue to the arq worker — the EmailProvider interface is unchanged.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from app.config import settings

FROM_ADDRESS = "ordini@romafiorita.com"  # display "Roma Fiorita"
REPLY_TO = "info@romafiorita.com"
_RESEND_URL = "https://api.resend.com/emails"
_log = logging.getLogger("romafiorita.email")


@dataclass
class EmailMessage:
    to: str
    subject: str
    body: str
    template: str  # e.g. "order_received.v1"
    locale: str


class EmailProvider(Protocol):
    async def send(self, message: EmailMessage) -> None: ...


@dataclass
class MockEmailProvider:
    sent: list[EmailMessage] = field(default_factory=list)

    async def send(self, message: EmailMessage) -> None:
        self.sent.append(message)


class ResendProvider:
    def __init__(
        self,
        api_key: str,
        *,
        from_addr: str = FROM_ADDRESS,
        reply_to: str = REPLY_TO,
        client: httpx.AsyncClient | None = None,
        max_attempts: int = 3,
        backoff_base: float = 0.5,
    ) -> None:
        self._api_key = api_key
        self._from = from_addr
        self._reply_to = reply_to
        self._client = client
        self._max_attempts = max_attempts
        self._backoff_base = backoff_base

    async def send(self, message: EmailMessage) -> None:
        payload = {
            "from": f"Roma Fiorita <{self._from}>",
            "to": [message.to],
            "subject": message.subject,
            "text": message.body,
            "reply_to": self._reply_to,
            "headers": {"X-Entity-Ref-ID": message.template},
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}
        client = self._client or httpx.AsyncClient(timeout=10.0)
        try:
            for attempt in range(self._max_attempts):
                try:
                    resp = await client.post(_RESEND_URL, json=payload, headers=headers)
                    resp.raise_for_status()
                    return
                except Exception as exc:  # noqa: BLE001 - retry any send failure
                    if attempt + 1 >= self._max_attempts:
                        # Dead-letter: never raise into the request; log for replay.
                        _log.error(
                            "email_dead_letter",
                            extra={
                                "to": message.to,
                                "template": message.template,
                                "error": str(exc),
                            },
                        )
                        return
                    await asyncio.sleep(self._backoff_base * (attempt + 1))
        finally:
            if self._client is None:
                await client.aclose()


def _build() -> EmailProvider:
    if settings.resend_api_key:
        return ResendProvider(settings.resend_api_key)
    return MockEmailProvider()


_provider: EmailProvider = _build()


def get_email_provider() -> EmailProvider:
    return _provider
