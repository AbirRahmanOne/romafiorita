"""Password hashing (argon2) and JWT access/refresh tokens.

Keep this framework-free: no FastAPI, no DB. Request-level wiring lives in
`app/deps.py`.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings

_hasher = PasswordHasher()
_ALGO = "HS256"


def hash_password(plain: str) -> str:
    return _hasher.hash(plain)


def verify_password(hashed: str, plain: str) -> bool:
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def _encode(claims: dict[str, Any], ttl: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {**claims, "iat": now, "exp": now + ttl}
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGO)


def create_access_token(staff_id: int, role: str) -> str:
    return _encode(
        {"sub": str(staff_id), "role": role, "type": "access"},
        timedelta(minutes=settings.access_token_ttl_minutes),
    )


def create_refresh_token(staff_id: int, jti: str) -> str:
    return _encode(
        {"sub": str(staff_id), "jti": jti, "type": "refresh"},
        timedelta(days=settings.refresh_token_ttl_days),
    )


class TokenError(Exception):
    """Raised when a token is missing/invalid/expired or the wrong type."""


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload: dict[str, Any] = jwt.decode(
            token, settings.jwt_secret, algorithms=[_ALGO]
        )
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
    if payload.get("type") != expected_type:
        raise TokenError("wrong token type")
    return payload


def new_jti() -> str:
    return secrets.token_urlsafe(16)


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)
