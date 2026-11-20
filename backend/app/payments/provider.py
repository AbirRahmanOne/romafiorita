"""Payment provider seam (ADR 0002).

Everything money-related goes through ``PaymentProvider``. The default is
``MockPaymentProvider`` so checkout/orders work end to end with no Stripe account:
website orders use manual capture (authorise at checkout, capture on accept).

A real ``StripeProvider`` is a drop-in later: implement this Protocol and bind it
in ``get_payment_provider`` (plus the webhook route). No order/request rework.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PaymentIntent:
    id: str
    client_secret: str
    status: str  # authorized | captured | cancelled | refunded | failed


class PaymentProvider(Protocol):
    def create_intent(
        self,
        *,
        amount_cents: int,
        currency: str,
        manual_capture: bool,
        metadata: dict[str, str],
    ) -> PaymentIntent: ...

    def capture(self, intent_id: str) -> PaymentIntent: ...

    def cancel(self, intent_id: str) -> PaymentIntent: ...

    def refund(
        self, intent_id: str, *, amount_cents: int | None = None
    ) -> PaymentIntent: ...


class MockPaymentProvider:
    """In-process fake. Manual-capture intents are immediately ``authorized``
    (a real Stripe hold would flip to authorized via a webhook)."""

    def create_intent(
        self,
        *,
        amount_cents: int,
        currency: str,
        manual_capture: bool,
        metadata: dict[str, str],
    ) -> PaymentIntent:
        intent_id = f"pi_mock_{secrets.token_hex(12)}"
        status = "authorized" if manual_capture else "captured"
        return PaymentIntent(
            id=intent_id, client_secret=f"{intent_id}_secret", status=status
        )

    def capture(self, intent_id: str) -> PaymentIntent:
        return PaymentIntent(intent_id, f"{intent_id}_secret", "captured")

    def cancel(self, intent_id: str) -> PaymentIntent:
        return PaymentIntent(intent_id, f"{intent_id}_secret", "cancelled")

    def refund(
        self, intent_id: str, *, amount_cents: int | None = None
    ) -> PaymentIntent:
        return PaymentIntent(intent_id, f"{intent_id}_secret", "refunded")


_provider: PaymentProvider = MockPaymentProvider()


def get_payment_provider() -> PaymentProvider:
    """FastAPI dependency / seam. Swap to StripeProvider by rebinding here."""
    return _provider
