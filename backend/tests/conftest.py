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

from app.db import get_session
from app.main import app
from app.models import Base, Product

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
