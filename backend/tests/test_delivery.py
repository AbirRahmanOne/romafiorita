from datetime import UTC, date, datetime

from app.domain import delivery
from app.domain.delivery import DeliveryTypeCode, Zone

# --- zones ---------------------------------------------------------------


def test_rome_cap_range() -> None:
    assert delivery.zone_for("00118") is Zone.ROME
    assert delivery.zone_for("00144") is Zone.ROME
    assert delivery.zone_for("00199") is Zone.ROME


def test_just_outside_rome_range_is_national() -> None:
    assert delivery.zone_for("00117") is Zone.NATIONAL
    assert delivery.zone_for("00200") is Zone.NATIONAL
    assert delivery.zone_for("20121") is Zone.NATIONAL  # Milan


def test_invalid_cap_rejected() -> None:
    assert delivery.zone_for("abc") is None
    assert delivery.zone_for("123") is None
    assert delivery.zone_for("001180") is None
    assert delivery.zone_for("") is None


def test_cap_is_trimmed() -> None:
    assert delivery.zone_for("  00144 ") is Zone.ROME


def test_delivery_types_by_zone() -> None:
    assert delivery.delivery_types(Zone.ROME) == [
        DeliveryTypeCode.STANDARD,
        DeliveryTypeCode.WINDOW,
        DeliveryTypeCode.EXACT,
    ]
    assert delivery.delivery_types(Zone.NATIONAL) == [DeliveryTypeCode.COURIER]


# --- slots ---------------------------------------------------------------

# 07:00–23:45 inclusive, every 15 min = 68 slots.
_EXPECTED_SLOTS = 68


def test_slot_count_and_bounds() -> None:
    # now far in the past so everything is available
    now = datetime(2026, 1, 1, tzinfo=UTC)
    slots = delivery.generate_slots(date(2026, 6, 15), now)
    assert len(slots) == _EXPECTED_SLOTS
    assert slots[0].time == "07:00"
    assert slots[-1].time == "23:45"
    assert all(s.available for s in slots)


def test_min_notice_marks_near_slots_unavailable() -> None:
    # "now" = 2026-06-15 10:00 Rome (08:00 UTC, summer +02:00); +3h notice => 13:00.
    now = datetime(2026, 6, 15, 8, 0, tzinfo=UTC)
    generated = delivery.generate_slots(date(2026, 6, 15), now)
    slots = {s.time: s.available for s in generated}
    assert slots["12:45"] is False  # before cutoff
    assert slots["13:00"] is True  # exactly at cutoff
    assert slots["13:15"] is True


def test_slots_dst_spring_forward_day() -> None:
    # 2026-03-29 Europe/Rome clocks jump 02:00->03:00; our window is unaffected.
    slots = delivery.generate_slots(date(2026, 3, 29), datetime(2026, 1, 1, tzinfo=UTC))
    assert len(slots) == _EXPECTED_SLOTS
    assert slots[0].iso.endswith("+02:00")  # already summer time at 07:00


def test_slots_dst_fall_back_day() -> None:
    # 2026-10-25 clocks fall back 03:00->02:00; 07:00 is already winter (+01:00).
    past = datetime(2026, 1, 1, tzinfo=UTC)
    slots = delivery.generate_slots(date(2026, 10, 25), past)
    assert len(slots) == _EXPECTED_SLOTS
    assert slots[0].iso.endswith("+01:00")


def test_cutoff_is_rome_two_pm() -> None:
    cutoff = delivery.same_day_cutoff(date(2026, 6, 15))
    assert cutoff.strftime("%H:%M") == "14:00"
    assert cutoff.utcoffset().total_seconds() == 2 * 3600  # summer +02:00
