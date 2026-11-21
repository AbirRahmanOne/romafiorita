"""Settings: one JSON document (row id=1) merged over code defaults.

Business identity fields stay null until the client supplies them (spec §J).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppSettings

DEFAULTS: dict[str, Any] = {
    "zones": [{"name": "Roma", "type": "ROME", "fee_cents": 0}],
    "slot_pricing": {"window_cents": 500, "exact_cents": 900},
    "cutoffs": {"rome_hour": 14, "suburbs_hour": 14},
    "blocked_dates": [],
    "daily_capacity": 50,
    "notification_recipients": [],
    "business": {
        "company_name": None,
        "address": None,
        "vat_number": None,
        "pec": None,
        "phone": None,
        "whatsapp": None,
    },
}


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = {**out[key], **value}
        else:
            out[key] = value
    return out


async def _row(session: AsyncSession) -> AppSettings:
    row = await session.get(AppSettings, 1)
    if row is None:
        row = AppSettings(id=1, data={})
        session.add(row)
        await session.flush()
    return row


async def get_settings(session: AsyncSession) -> dict[str, Any]:
    row = await _row(session)
    return _merge(DEFAULTS, row.data)


async def update_settings(
    session: AsyncSession, patch: dict[str, Any]
) -> dict[str, Any]:
    row = await _row(session)
    row.data = _merge(row.data, patch)  # reassign so SQLAlchemy tracks the change
    await session.commit()
    return _merge(DEFAULTS, row.data)
