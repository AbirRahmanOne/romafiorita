import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from .api import system
from .api.v1 import v1_router
from .config import settings
from .core.logging import configure_logging
from .db import dispose_engine

_access_log = logging.getLogger("romafiorita.access")

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
}


def _error(
    code: str, message: str, request_id: str, details: Any = None
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": request_id,
        }
    }


def _request_id(request: Request) -> str:
    rid: str = getattr(request.state, "request_id", "")
    return rid


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    logging.getLogger("romafiorita").info(
        "startup", extra={"env": settings.environment}
    )
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(title="Roma Fiorita API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization", "Content-Type", "X-CSRF-Token", "Idempotency-Key"
        ],
    )

    @app.middleware("http")
    async def context_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id

        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > settings.max_request_bytes:
            return JSONResponse(
                status_code=413,
                content=_error(
                    "request_too_large", "Request body too large.", request_id
                ),
            )

        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        for key, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        _access_log.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - start) * 1000, 1),
            },
        )
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        detail: Any = exc.detail
        rid = _request_id(request)
        if isinstance(detail, dict) and "code" in detail:
            content = _error(
                detail.get("code", "http_error"),
                detail.get("message", ""),
                rid,
                detail.get("details"),
            )
        else:
            content = _error("http_error", str(detail), rid)
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error(
                "validation_error",
                "Request validation failed.",
                _request_id(request),
                {"errors": exc.errors()},
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_error(
                "internal_error", "Internal server error.", _request_id(request)
            ),
        )

    app.include_router(system.router)
    app.include_router(v1_router)
    return app


app = create_app()
