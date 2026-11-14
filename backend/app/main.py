from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .routers import health, products

app = FastAPI(title="Roma Fiorita API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """Normalise errors to {"error": {code, message, details}}."""
    detail: Any = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        error = {
            "code": detail.get("code"),
            "message": detail.get("message", ""),
            "details": detail.get("details", {}),
        }
    else:
        error = {"code": "http_error", "message": str(detail), "details": {}}
    return JSONResponse(status_code=exc.status_code, content={"error": error})


app.include_router(health.router)
app.include_router(products.router)
