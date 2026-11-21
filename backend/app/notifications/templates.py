"""Versioned transactional email templates (IT + EN). All text is here, not in
call sites. Bump the version suffix when wording changes."""

from __future__ import annotations

from enum import StrEnum

VERSION = "v1"


class NotificationKind(StrEnum):
    ORDER_RECEIVED = "order_received"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    PHOTO_SENT = "photo_sent"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    REFUNDED = "refunded"
    PAYMENT_REQUEST = "payment_request"
    PAYMENT_RECEIVED = "payment_received"


# kind -> locale -> (subject, body). Bodies use {number} {recipient} {total} {link}.
_T: dict[NotificationKind, dict[str, tuple[str, str]]] = {
    NotificationKind.ORDER_RECEIVED: {
        "it": ("Ordine {number} ricevuto",
               "Grazie! Abbiamo ricevuto l'ordine {number} per {recipient}. "
               "Totale EUR {total}."),
        "en": ("Order {number} received",
               "Thank you! We received order {number} for {recipient}. "
               "Total EUR {total}."),
    },
    NotificationKind.ACCEPTED: {
        "it": ("Ordine {number} accettato", "Prepariamo i fiori per {recipient}."),
        "en": ("Order {number} accepted",
               "We're preparing the flowers for {recipient}."),
    },
    NotificationKind.DECLINED: {
        "it": ("Ordine {number} annullato",
               "Spiacenti, non possiamo evadere l'ordine {number}. Nessun addebito."),
        "en": ("Order {number} declined",
               "Sorry, we can't fulfil order {number}. You were not charged."),
    },
    NotificationKind.PHOTO_SENT: {
        "it": ("La foto del tuo bouquet {number}",
               "Ecco la foto reale del bouquet per {recipient} prima della consegna."),
        "en": ("Your bouquet photo for {number}",
               "Here is the real photo of the bouquet for {recipient} "
               "before delivery."),
    },
    NotificationKind.OUT_FOR_DELIVERY: {
        "it": ("Ordine {number} in consegna",
               "Il bouquet per {recipient} è in consegna."),
        "en": ("Order {number} out for delivery",
               "The bouquet for {recipient} is on its way."),
    },
    NotificationKind.DELIVERED: {
        "it": ("Ordine {number} consegnato", "Consegnato a {recipient}. Grazie!"),
        "en": ("Order {number} delivered", "Delivered to {recipient}. Thank you!"),
    },
    NotificationKind.REFUNDED: {
        "it": ("Rimborso ordine {number}", "Abbiamo rimborsato l'ordine {number}."),
        "en": ("Refund for order {number}", "We've refunded order {number}."),
    },
    NotificationKind.PAYMENT_REQUEST: {
        "it": ("Richiesta di pagamento {number}",
               "Completa il pagamento per {recipient}: {link}"),
        "en": ("Payment request {number}",
               "Complete your payment for {recipient}: {link}"),
    },
    NotificationKind.PAYMENT_RECEIVED: {
        "it": ("Pagamento ricevuto {number}",
               "Grazie! Pagamento per {number} ricevuto."),
        "en": ("Payment received {number}",
               "Thank you! Payment for {number} received."),
    },
}


def render(
    kind: NotificationKind, locale: str, **ctx: str
) -> tuple[str, str, str]:
    by_locale = _T[kind]
    subject, body = by_locale.get(locale, by_locale["en"])
    template_id = f"{kind.value}.{VERSION}"
    return subject.format(**ctx), body.format(**ctx), template_id
