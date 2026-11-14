"""Seed sample Roma Fiorita data. Run: python seed.py (after migrations)."""

import asyncio
from datetime import time

from sqlalchemy import select

from app.db import get_sessionmaker
from app.models import DeliveryType, DeliveryZone, Product, TimeSlotRule


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
                    description_it="Un classico mazzo di rose fresche.",
                    description_en="A classic bouquet of fresh roses.",
                    base_price_cents=4900,
                    occasion="love",
                ),
                Product(
                    slug="primavera-romana",
                    name_it="Primavera Romana",
                    name_en="Roman Spring",
                    description_it="Composizione colorata di stagione.",
                    description_en="A colourful seasonal arrangement.",
                    base_price_cents=3900,
                    occasion="birthday",
                ),
                Product(
                    slug="mimosa-8-marzo",
                    name_it="Mimosa 8 Marzo",
                    name_en="Mimosa for 8 March",
                    description_it="Mimosa per la Festa della Donna.",
                    description_en="Mimosa for Women's Day.",
                    base_price_cents=2900,
                    occasion="festa-della-donna",
                ),
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
                window_fee_cents=0,  # placeholder €[X]
                exact_fee_cents=0,  # placeholder €[Y]
            )
        )

        await session.commit()
        print("Seeded sample products, Rome zone and slot rule.")


if __name__ == "__main__":
    asyncio.run(seed())
