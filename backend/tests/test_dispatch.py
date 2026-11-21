from typing import Any

from app.notifications import EmailMessage, dispatch

_MSG = EmailMessage(
    to="buyer@example.com",
    subject="Order received",
    body="Thanks",
    template="order_received.v1",
    locale="en",
)


class _FakePool:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, dict[str, Any]]] = []

    async def enqueue_job(self, name: str, **kwargs: Any) -> None:
        self.jobs.append((name, kwargs))


async def test_enqueues_when_pool_present() -> None:
    pool = _FakePool()
    dispatch.set_arq_pool(pool)
    try:
        await dispatch.enqueue_email(_MSG)
    finally:
        dispatch.set_arq_pool(None)
    assert pool.jobs[0][0] == "send_email"
    assert pool.jobs[0][1]["to"] == "buyer@example.com"
    assert pool.jobs[0][1]["template"] == "order_received.v1"


async def test_inline_fallback_without_pool(emails: Any) -> None:
    dispatch.set_arq_pool(None)
    await dispatch.enqueue_email(_MSG)
    assert emails.sent[-1].to == "buyer@example.com"
