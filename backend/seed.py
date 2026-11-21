"""Seed sample Roma Fiorita data. Run: python seed.py (after migrations)."""

import asyncio
from datetime import time

from sqlalchemy import select

from app.db import get_sessionmaker
from app.models import (
    AddOn,
    DeliveryType,
    DeliveryZone,
    Product,
    ProductTier,
    ProductVariant,
    TimeSlotRule,
)


def _tiers(slug: str, premium_cents: int) -> list[ProductVariant]:
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
            is_default=is_default,
        )
        for tier, cents, is_default in spec
    ]


async def seed() -> None:
    session_maker = get_sessionmaker()
    async with session_maker() as session:
        existing = await session.scalar(select(Product).limit(1))
        if existing:
            print("Already seeded; skipping.")
            return

        session.add_all(
            [
                Product(
                    slug="rose-di-roma",
                    name_it="Rose di Roma",
                    name_en="Roses of Rome",
                    subtitle_it="Un classico mazzo di rose fresche.",
                    subtitle_en="A classic bouquet of fresh roses.",
                    occasion="love",
                    category="Roses",
                    variants=_tiers("rose-di-roma", 4900),
                ),
                Product(
                    slug="primavera-romana",
                    name_it="Primavera Romana",
                    name_en="Roman Spring",
                    subtitle_it="Composizione colorata di stagione.",
                    subtitle_en="A colourful seasonal arrangement.",
                    occasion="birthday",
                    category="Seasonal",
                    variants=_tiers("primavera-romana", 3900),
                ),
            ]
        )
        session.add_all(
            [
                AddOn(code="card", name_it="Biglietto scritto a mano",
                      name_en="Handwritten card", price_cents=0),
                AddOn(code="chocolates", name_it="Scatola di cioccolatini",
                      name_en="Box of chocolates", price_cents=1200),
                AddOn(code="vase", name_it="Vaso di vetro",
                      name_en="Glass vase", price_cents=1800),
            ]
        )

        # Rome own-rider zone (CAP 001xx) + default slot rule.
        session.add(
            DeliveryZone(
                name="Roma",
                cap_prefix="001",
                delivery_type=DeliveryType.ROME_SAME_DAY,
            )
        )
        session.add(
            TimeSlotRule(
                delivery_type=DeliveryType.ROME_EXACT,
                step_minutes=15,
                capacity_per_rider=1,
                cutoff_time=time(14, 0),  # placeholder [14:00]
                exact_min_notice_minutes=180,  # placeholder [3h]
                window_fee_cents=500,  # placeholder €[X]
                exact_fee_cents=900,  # placeholder €[Y]
            )
        )

        await session.commit()
        print("Seeded sample products, add-ons, Rome zone and slot rule.")


if __name__ == "__main__":
    asyncio.run(seed())
