"""Order numbers and opaque tokens."""

from __future__ import annotations

import hashlib
import secrets


def order_number(order_id: int, year: int) -> str:
    """Human-facing order number RF-YYYY-NNNNN.

    ponytail: derived from the global order id, not a per-year sequence — unique,
    monotonic and gap-tolerant. Add a per-year counter table if the reset matters.
    """
    return f"RF-{year}-{order_id:05d}"


def new_token() -> str:
    """32-byte URL-safe token (tracking / payment links). Store only its hash."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
