"""Delivery engine — pure business logic (no FastAPI, no DB).

Zones by Italian postcode (CAP), delivery types, same-day cut-off, exact-time
minimum notice, fees, and DST-safe 15-minute slot generation in Europe/Rome.

Values marked ``# placeholder`` are the spec's defaults (§11) until the client
confirms real ones; they will move to an admin-editable settings table later.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

ROME_TZ = ZoneInfo("Europe/Rome")

# Rome own-rider CAP range 00118–00199 (placeholder, configurable later).
ROME_CAP_MIN = 118  # placeholder
ROME_CAP_MAX = 199  # placeholder
SAME_DAY_CUTOFF = time(14, 0)  # placeholder [14:00]
EXACT_MIN_NOTICE = timedelta(hours=3)  # placeholder [3h]
WINDOW_FEE_CENTS = 500  # placeholder €[X]
EXACT_FEE_CENTS = 900  # placeholder €[Y]
SLOT_STEP = timedelta(minutes=15)
SLOT_OPEN = time(7, 0)
SLOT_CLOSE = time(23, 45)

_CAP_RE = re.compile(r"^\d{5}$")


class Zone(StrEnum):
    ROME = "ROME"
    NATIONAL = "NATIONAL"


class DeliveryTypeCode(StrEnum):
    STANDARD = "standard"
    WINDOW = "window"
    EXACT = "exact"
    COURIER = "courier"


# Time fee by delivery type (single source of truth, shared with pricing).
TIME_FEE_CENTS: dict[str, int] = {
    DeliveryTypeCode.STANDARD: 0,
    DeliveryTypeCode.COURIER: 0,
    DeliveryTypeCode.WINDOW: WINDOW_FEE_CENTS,
    DeliveryTypeCode.EXACT: EXACT_FEE_CENTS,
}


def zone_for(postcode: str) -> Zone | None:
    """Rome (00118–00199) → ROME; any other valid 5-digit CAP → NATIONAL;
    anything that isn't a 5-digit CAP → None (rejected)."""
    cap = postcode.strip()
    if not _CAP_RE.match(cap):
        return None
    return Zone.ROME if ROME_CAP_MIN <= int(cap) <= ROME_CAP_MAX else Zone.NATIONAL


def delivery_types(zone: Zone) -> list[DeliveryTypeCode]:
    if zone is Zone.ROME:
        return [
            DeliveryTypeCode.STANDARD,
            DeliveryTypeCode.WINDOW,
            DeliveryTypeCode.EXACT,
        ]
    return [DeliveryTypeCode.COURIER]


def same_day_cutoff(day: date) -> datetime:
    """The Europe/Rome instant by which a same-day order must be placed."""
    return datetime.combine(day, SAME_DAY_CUTOFF, ROME_TZ)


@dataclass(frozen=True)
class Slot:
    time: str  # "HH:MM" wall-clock, Europe/Rome
    iso: str  # full ISO-8601 with Rome offset (so the client can localise)
    available: bool


def generate_slots(
    day: date, now: datetime, *, min_notice: timedelta = EXACT_MIN_NOTICE
) -> list[Slot]:
    """15-minute slots 07:00–23:45 Europe/Rome for ``day``.

    A slot is available only if it is at least ``min_notice`` ahead of ``now``.
    DST-safe: the open/close window (07:00–23:45) never overlaps the 02:00–03:00
    transition, and offsets are recomputed by zoneinfo as wall-clock advances.
    """
    now_rome = now.astimezone(ROME_TZ)
    cutoff = now_rome + min_notice
    cur = datetime.combine(day, SLOT_OPEN, ROME_TZ)
    end = datetime.combine(day, SLOT_CLOSE, ROME_TZ)
    slots: list[Slot] = []
    while cur <= end:
        slots.append(Slot(cur.strftime("%H:%M"), cur.isoformat(), cur >= cutoff))
        cur += SLOT_STEP
    return slots
