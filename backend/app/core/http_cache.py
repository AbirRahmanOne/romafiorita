"""ETag + Cache-Control for public GETs.

Call ``cache_or_304`` with the built response model: it sets validators and, on a
matching If-None-Match, returns a 304 for the handler to return instead.
"""

from __future__ import annotations

import hashlib

from fastapi import Request, Response
from pydantic import BaseModel


def _etag(body: bytes) -> str:
    return '"' + hashlib.sha256(body).hexdigest()[:32] + '"'


def cache_or_304(
    request: Request, response: Response, model: BaseModel, *, max_age: int = 300
) -> Response | None:
    etag = _etag(model.model_dump_json().encode())
    cache_control = f"public, max-age={max_age}"
    if request.headers.get("if-none-match") == etag:
        return Response(
            status_code=304,
            headers={"ETag": etag, "Cache-Control": cache_control},
        )
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = cache_control
    return None
