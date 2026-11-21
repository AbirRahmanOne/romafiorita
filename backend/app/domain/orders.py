"""Order state machine — pure, table-driven (spec §4D).

Each action maps to one transition with a source state, target state, the roles
allowed to trigger it, an optional guard, and the payment side effect the service
layer must run. No FastAPI/DB here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.models import OrderStatus, StaffRole

OWNER, MANAGER, FLORIST, RIDER = (
    StaffRole.OWNER,
    StaffRole.MANAGER,
    StaffRole.FLORIST,
    StaffRole.RIDER,
)


class PaymentEffect(StrEnum):
    NONE = "none"
    CAPTURE = "capture"
    CANCEL = "cancel"
    REFUND = "refund"


@dataclass(frozen=True)
class Transition:
    source: OrderStatus
    target: OrderStatus
    roles: frozenset[StaffRole]
    effect: PaymentEffect = PaymentEffect.NONE
    requires_photo: bool = False


# action -> transition. "authorize" is system-only (payment authorised).
TRANSITIONS: dict[str, Transition] = {
    "authorize": Transition(
        OrderStatus.PENDING_PAYMENT, OrderStatus.NEW, frozenset()
    ),
    "accept": Transition(
        OrderStatus.NEW, OrderStatus.ACCEPTED, frozenset({OWNER, MANAGER}),
        effect=PaymentEffect.CAPTURE,
    ),
    "decline": Transition(
        OrderStatus.NEW, OrderStatus.DECLINED, frozenset({OWNER, MANAGER}),
        effect=PaymentEffect.CANCEL,
    ),
    "photo": Transition(
        OrderStatus.ACCEPTED, OrderStatus.AWAITING_PHOTO,
        frozenset({OWNER, MANAGER, FLORIST}),
    ),
    "send_photo": Transition(
        OrderStatus.AWAITING_PHOTO, OrderStatus.PHOTO_SENT,
        frozenset({OWNER, MANAGER, FLORIST}), requires_photo=True,
    ),
    "approve": Transition(
        OrderStatus.PHOTO_SENT, OrderStatus.APPROVED, frozenset({OWNER, MANAGER}),
    ),
    "dispatch": Transition(
        OrderStatus.APPROVED, OrderStatus.OUT_FOR_DELIVERY,
        frozenset({OWNER, MANAGER, RIDER}),
    ),
    "deliver": Transition(
        OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED,
        frozenset({OWNER, MANAGER, RIDER}),
    ),
}

# Refund is allowed from any post-capture state.
_REFUNDABLE = frozenset(
    {
        OrderStatus.ACCEPTED,
        OrderStatus.AWAITING_PHOTO,
        OrderStatus.PHOTO_SENT,
        OrderStatus.APPROVED,
        OrderStatus.OUT_FOR_DELIVERY,
        OrderStatus.DELIVERED,
    }
)


class TransitionError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Resolved:
    target: OrderStatus
    effect: PaymentEffect


def resolve(
    action: str,
    *,
    current: OrderStatus,
    role: StaffRole,
    has_photo: bool,
) -> Resolved:
    """Validate and resolve a transition, or raise TransitionError."""
    if action == "refund":
        if role not in (OWNER, MANAGER):
            raise TransitionError("forbidden", "Not allowed for this role.")
        if current not in _REFUNDABLE:
            raise TransitionError(
                "invalid_state", f"Cannot refund an order in state {current}."
            )
        return Resolved(OrderStatus.REFUNDED, PaymentEffect.REFUND)

    t = TRANSITIONS.get(action)
    if t is None:
        raise TransitionError("unknown_action", f"Unknown action: {action}")
    if not t.roles:  # system-only transition
        raise TransitionError("forbidden", "System transition.")
    if role not in t.roles:
        raise TransitionError("forbidden", "Not allowed for this role.")
    if current != t.source:
        raise TransitionError(
            "invalid_state",
            f"Cannot '{action}' an order in state {current} (needs {t.source}).",
        )
    if t.requires_photo and not has_photo:
        raise TransitionError("photo_required", "A bouquet photo is required first.")
    return Resolved(t.target, t.effect)
