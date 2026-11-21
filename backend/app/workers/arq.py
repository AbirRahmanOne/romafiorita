"""arq worker: schedules the background task functions on cron.

Run on Render as a separate worker service:  arq app.workers.arq.WorkerSettings
Requires Redis (settings.redis_url). Not imported by the API process.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from arq import cron
from arq.connections import RedisSettings

from app.config import settings
from app.db import get_sessionmaker
from app.notifications.provider import EmailMessage, get_email_provider
from app.workers import tasks


async def send_email(
    ctx: dict[str, Any],
    *,
    to: str,
    subject: str,
    body: str,
    template: str,
    locale: str,
) -> None:
    await get_email_provider().send(
        EmailMessage(
            to=to, subject=subject, body=body, template=template, locale=locale
        )
    )


async def expire_holds(ctx: dict[str, Any]) -> int:
    async with get_sessionmaker()() as session:
        return await tasks.expire_stale_holds(session)


async def occasion_reminders(ctx: dict[str, Any]) -> int:
    async with get_sessionmaker()() as session:
        return await tasks.send_due_occasion_reminders(session)


async def gdpr_retention(ctx: dict[str, Any]) -> int:
    cutoff = datetime.now(UTC) - timedelta(days=30 * settings.retention_months)
    async with get_sessionmaker()() as session:
        return await tasks.anonymise_old_recipients(session, cutoff)


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [send_email]
    cron_jobs = [
        # Release lapsed slot holds every 5 minutes.
        cron(expire_holds, minute=set(range(0, 60, 5))),
        # Occasion reminders once a day (08:00 UTC).
        cron(occasion_reminders, hour={8}, minute={0}),
        # GDPR retention sweep nightly (03:00 UTC).
        cron(gdpr_retention, hour={3}, minute={0}),
    ]
