"""Email provider seam.

Transactional email goes through ``EmailProvider``. The default
``MockEmailProvider`` records messages in memory so order flows are testable with
no Resend account. A real ResendProvider is a drop-in later.

ponytail: sending is synchronous here. Phase 5b wraps it in an arq task for
retries/backoff/dead-letter — the call sites don't change.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

FROM_ADDRESS = "ordini@romafiorita.com"  # display "Roma Fiorita"
REPLY_TO = "info@romafiorita.com"


@dataclass
class EmailMessage:
    to: str
    subject: str
    body: str
    template: str  # e.g. "order_received.v1"
    locale: str


class EmailProvider(Protocol):
    def send(self, message: EmailMessage) -> None: ...


@dataclass
class MockEmailProvider:
    sent: list[EmailMessage] = field(default_factory=list)

    def send(self, message: EmailMessage) -> None:
        self.sent.append(message)


_provider: EmailProvider = MockEmailProvider()


def get_email_provider() -> EmailProvider:
    return _provider
