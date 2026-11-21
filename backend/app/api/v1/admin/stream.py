import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.deps import get_current_staff
from app.models import Staff
from app.realtime.bus import get_event_bus

router = APIRouter(prefix="/v1/admin/orders", tags=["admin-stream"])

_HEARTBEAT_SECONDS = 15


@router.get("/stream")
async def stream(staff: Staff = Depends(get_current_staff)) -> StreamingResponse:
    """Authenticated Server-Sent Events of order changes (heartbeat keeps it open)."""

    async def events() -> AsyncIterator[str]:
        async with get_event_bus().subscribe() as queue:
            yield ": connected\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(
                        queue.get(), timeout=_HEARTBEAT_SECONDS
                    )
                    yield f"data: {json.dumps(event)}\n\n"
                except TimeoutError:
                    yield ": heartbeat\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
