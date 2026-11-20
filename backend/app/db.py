from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import settings


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Build the async engine lazily (keeps import free of the asyncpg driver)."""
    return create_async_engine(settings.database_url, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: one AsyncSession per request."""
    async with get_sessionmaker()() as session:
        yield session


async def dispose_engine() -> None:
    """Dispose the pool on shutdown (no-op if the engine was never built)."""
    if get_engine.cache_info().currsize:
        await get_engine().dispose()
