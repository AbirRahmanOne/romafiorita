"""Compose + send order notifications. Call sites just pass an order + a kind."""

from __future__ import annotations

from app.models import Order
from app.notifications.provider import EmailMessage, get_email_provider
from app.notifications.templates import NotificationKind, render


def _euro(cents: int) -> str:
    return f"{cents / 100:.2f}"


def notify_order(order: Order, kind: NotificationKind, *, link: str = "") -> None:
    """Send the email for an order event. No-op if we have no sender email."""
    customer = order.customer
    if customer is None or not customer.email:
        return
    recipient_name = order.recipient.name if order.recipient else ""
    subject, body, template_id = render(
        kind,
        customer.locale,
        number=order.number,
        recipient=recipient_name,
        total=_euro(order.total_cents),
        link=link,
    )
    get_email_provider().send(
        EmailMessage(
            to=customer.email,
            subject=subject,
            body=body,
            template=template_id,
            locale=customer.locale,
        )
    )


_REMINDER = {
    "it": ("Promemoria: {occasion} in arrivo",
           "Si avvicina {occasion}. Ordina in tempo i fiori con Roma Fiorita."),
    "en": ("Reminder: {occasion} is coming up",
           "{occasion} is approaching. Order flowers in time with Roma Fiorita."),
}


def notify_occasion_reminder(email: str, locale: str, occasion: str) -> None:
    subject, body = _REMINDER.get(locale, _REMINDER["en"])
    get_email_provider().send(
        EmailMessage(
            to=email,
            subject=subject.format(occasion=occasion),
            body=body.format(occasion=occasion),
            template="occasion_reminder.v1",
            locale=locale,
        )
    )
