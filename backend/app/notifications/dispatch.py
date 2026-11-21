"""Email dispatch seam.

If an arq pool is configured (set in the API lifespan), emails are enqueued to the
worker — off the request path, durable. Otherwise they're sent inline via the
provider (dev / tests / Redis down). The pool is duck-typed so this module needs
no arq import (keeps `app.main` importable without arq).
"""

from __future__ import annotations

from typing import Any

from app.notifications.provider import EmailMessage, get_email_provider

_pool: Any = None


def set_arq_pool(pool: Any) -> None:
    global _pool
    _pool = pool


def get_arq_pool() -> Any:
    return _pool


async def enqueue_email(message: EmailMessage) -> None:
    if _pool is not None:
        await _pool.enqueue_job(
            "send_email",
            to=message.to,
            subject=message.subject,
            body=message.body,
            template=message.template,
            locale=message.locale,
        )
    else:
        await get_email_provider().send(message)  # inline fallback (no broker)
