import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, StaticPool

from app.core.security import hash_password
from app.db import get_session
from app.main import app
from app.models import (
    AddOn,
    Base,
    Product,
    ProductTier,
    ProductVariant,
    Staff,
    StaffRole,
)

OWNER_EMAIL = "owner@romafiorita.com"
FLORIST_EMAIL = "florist@romafiorita.com"
PASSWORD = "correct-horse-battery-staple"
LOGIN_URL = "/v1/admin/auth/login"


def _tiers(slug: str, premium_cents: int) -> list[ProductVariant]:
    """Three ascending tiers; PREMIUM is the default."""
    spec = [
        (ProductTier.STANDARD, round(premium_cents * 0.8), False),
        (ProductTier.PREMIUM, premium_cents, True),
        (ProductTier.LUXURY, round(premium_cents * 1.4), False),
    ]
    return [
        ProductVariant(
            sku=f"{slug}-{tier.value.lower()}",
            tier=tier,
            price_cents=cents,
            description_en=f"{tier.value} bouquet",
            description_it=f"Mazzo {tier.value}",
            is_default=is_default,
        )
        for tier, cents, is_default in spec
    ]

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
                    occasion="love",
                    category="Roses",
                    variants=_tiers("rose-di-roma", 4900),
                ),
                Product(
                    slug="primavera-romana",
                    name_it="Primavera Romana",
                    name_en="Roman Spring",
                    occasion="birthday",
                    category="Seasonal",
                    variants=_tiers("primavera-romana", 3900),
                ),
                Product(
                    slug="nascosto",
                    name_it="Nascosto",
                    name_en="Hidden",
                    occasion="love",
                    is_active=False,
                    variants=_tiers("nascosto", 1000),
                ),
                AddOn(code="card", name_it="Biglietto", name_en="Card", price_cents=0),
                AddOn(
                    code="vase", name_it="Vaso", name_en="Vase", price_cents=1800
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


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Raw session (fresh schema, no seed) for repository/domain tests."""
    engine = _make_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    await engine.dispose()


def _checkout_body(
    *,
    variant_id: str = "rose-di-roma-premium",
    delivery_type: str = "standard",
    slot: str | None = None,
    cap: str = "00144",
    quantity: int = 1,
) -> dict:
    body: dict = {
        "items": [{"variant_id": variant_id, "quantity": quantity}],
        "delivery_type": delivery_type,
        "sender": {"name": "Sam Sender", "email": "sam@example.com", "locale": "en"},
        "recipient": {
            "name": "Rita Recipient",
            "address_line": "Via Appia 1",
            "cap": cap,
            "city": "Roma",
        },
    }
    if slot:
        body["delivery_slot"] = slot
    return body


@pytest.fixture
def checkout_body():  # type: ignore[no-untyped-def]
    return _checkout_body


@pytest.fixture
def emails():  # type: ignore[no-untyped-def]
    """The MockEmailProvider singleton, cleared for the test."""
    from app.notifications import get_email_provider

    provider = get_email_provider()
    provider.sent.clear()  # type: ignore[attr-defined]
    return provider
