import pytest

from app.domain.orders import PaymentEffect, TransitionError, resolve
from app.models import OrderStatus, StaffRole


def test_accept_captures() -> None:
    r = resolve(
        "accept", current=OrderStatus.NEW, role=StaffRole.OWNER, has_photo=False
    )
    assert r.target is OrderStatus.ACCEPTED
    assert r.effect is PaymentEffect.CAPTURE


def test_decline_cancels() -> None:
    r = resolve(
        "decline", current=OrderStatus.NEW, role=StaffRole.MANAGER, has_photo=False
    )
    assert r.target is OrderStatus.DECLINED
    assert r.effect is PaymentEffect.CANCEL


def test_florist_cannot_accept() -> None:
    with pytest.raises(TransitionError) as exc:
        resolve(
            "accept", current=OrderStatus.NEW, role=StaffRole.FLORIST, has_photo=False
        )
    assert exc.value.code == "forbidden"


def test_wrong_source_state() -> None:
    with pytest.raises(TransitionError) as exc:
        resolve(
            "deliver", current=OrderStatus.NEW, role=StaffRole.RIDER, has_photo=False
        )
    assert exc.value.code == "invalid_state"


def test_send_photo_requires_photo() -> None:
    with pytest.raises(TransitionError) as exc:
        resolve(
            "send_photo",
            current=OrderStatus.AWAITING_PHOTO,
            role=StaffRole.FLORIST,
            has_photo=False,
        )
    assert exc.value.code == "photo_required"


def test_send_photo_with_photo_ok() -> None:
    r = resolve(
        "send_photo",
        current=OrderStatus.AWAITING_PHOTO,
        role=StaffRole.FLORIST,
        has_photo=True,
    )
    assert r.target is OrderStatus.PHOTO_SENT


def test_refund_from_delivered() -> None:
    r = resolve(
        "refund", current=OrderStatus.DELIVERED, role=StaffRole.OWNER, has_photo=False
    )
    assert r.target is OrderStatus.REFUNDED
    assert r.effect is PaymentEffect.REFUND


def test_refund_not_allowed_before_capture() -> None:
    with pytest.raises(TransitionError) as exc:
        resolve(
            "refund", current=OrderStatus.NEW, role=StaffRole.OWNER, has_photo=False
        )
    assert exc.value.code == "invalid_state"


def test_system_transition_not_user_triggerable() -> None:
    with pytest.raises(TransitionError) as exc:
        resolve(
            "authorize",
            current=OrderStatus.PENDING_PAYMENT,
            role=StaffRole.OWNER,
            has_photo=False,
        )
    assert exc.value.code == "forbidden"
