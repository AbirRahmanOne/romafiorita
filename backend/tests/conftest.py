import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, StaticPool

from app.core.security import hash_password
from app.db import get_session
from app.main import app
from app.models import Base, Product, Staff, StaffRole

OWNER_EMAIL = "owner@romafiorita.com"
FLORIST_EMAIL = "florist@romafiorita.com"
PASSWORD = "correct-horse-battery-staple"
LOGIN_URL = "/v1/admin/auth/login"

# Default to in-memory SQLite so local runs need no DB. CI sets
# TEST_DATABASE_URL to a real Postgres 16 to catch Postgres-only behaviour
# (native enums, FOR UPDATE, server defaults, constraints).
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


def _make_engine() -> AsyncEngine:
    if TEST_DATABASE_URL:
        # Fresh connection per test keeps function-scoped teardown clean.
        return create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    # Shared in-memory SQLite: StaticPool keeps a single connection so setup
    # and request handlers see the same database.
    return create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    engine = _make_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSession = async_sessionmaker(engine, expire_on_commit=False)
    async with TestSession() as session:
        session.add_all(
            [
                Product(
                    slug="rose-di-roma",
                    name_it="Rose di Roma",
                    name_en="Roses of Rome",
                    base_price_cents=4900,
                    occasion="love",
                ),
                Product(
                    slug="primavera-romana",
                    name_it="Primavera Romana",
                    name_en="Roman Spring",
                    base_price_cents=3900,
                    occasion="birthday",
                ),
                Product(
                    slug="nascosto",
                    name_it="Nascosto",
                    name_en="Hidden",
                    base_price_cents=1000,
                    occasion="love",
                    is_active=False,
                ),
                Staff(
                    email=OWNER_EMAIL,
                    hashed_password=hash_password(PASSWORD),
                    name="Owner",
                    role=StaffRole.OWNER,
                ),
                Staff(
                    email=FLORIST_EMAIL,
                    hashed_password=hash_password(PASSWORD),
                    name="Florist",
                    role=StaffRole.FLORIST,
                ),
            ]
        )
        await session.commit()

    async def override_get_session() -> AsyncGenerator:
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    if TEST_DATABASE_URL:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def _login(client: AsyncClient, email: str) -> dict[str, str]:
    """Log in; return the CSRF header to use on subsequent mutations."""
    resp = await client.post(LOGIN_URL, json={"email": email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"X-CSRF-Token": client.cookies["rf_csrf"]}


@pytest_asyncio.fixture
async def owner(client: AsyncClient) -> tuple[AsyncClient, dict[str, str]]:
    return client, await _login(client, OWNER_EMAIL)


@pytest_asyncio.fixture
async def florist(client: AsyncClient) -> tuple[AsyncClient, dict[str, str]]:
    return client, await _login(client, FLORIST_EMAIL)
