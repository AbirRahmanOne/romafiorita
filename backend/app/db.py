from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import settings


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Build the engine + sessionmaker lazily.

    Deferring creation keeps importing this module free of the DB driver
    (asyncpg) — important for tests that override the session dependency.
    """
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: one AsyncSession per request."""
    async with get_sessionmaker()() as session:
        yield session
