"""SQLAlchemy 2.0 models for Roma Fiorita.

Conventions (see .claude/skills/backend-api-conventions):
- money is integer cents, currency EUR;
- timestamps stored in UTC (timezone-aware);
- business-logic timezone conversion (Europe/Rome) happens in the service layer.
"""

from __future__ import annotations

import enum
from datetime import UTC, date, datetime, time

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        server_default=func.now(),
    )


# --- Enums ---------------------------------------------------------------


class StaffRole(enum.StrEnum):
    OWNER = "OWNER"
    MANAGER = "MANAGER"
    FLORIST = "FLORIST"
    RIDER = "RIDER"


class OrderStatus(enum.StrEnum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    NEW = "NEW"
    ACCEPTED = "ACCEPTED"
    PREPARING = "PREPARING"
    PHOTO_SENT = "PHOTO_SENT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    DECLINED = "DECLINED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    PROBLEM = "PROBLEM"


class DeliveryType(enum.StrEnum):
    ROME_SAME_DAY = "ROME_SAME_DAY"
    ROME_WINDOW = "ROME_WINDOW"
    ROME_EXACT = "ROME_EXACT"
    NATIONAL_COURIER = "NATIONAL_COURIER"


class PaymentStatus(enum.StrEnum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


# --- Staff & customers ---------------------------------------------------


class Staff(Base, TimestampMixin):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[StaffRole] = mapped_column(Enum(StaffRole, native_enum=False))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable email supports guest checkout.
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    locale: Mapped[str] = mapped_column(String(2), default="it")

    recipients: Mapped[list[Recipient]] = relationship(back_populates="customer")
    orders: Mapped[list[Order]] = relationship(back_populates="customer")
    reminders: Mapped[list[Reminder]] = relationship(back_populates="customer")


class Recipient(Base, TimestampMixin):
    __tablename__ = "recipients"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32))
    address_line: Mapped[str] = mapped_column(String(512))
    cap: Mapped[str] = mapped_column(String(5), index=True)  # Italian postcode
    city: Mapped[str] = mapped_column(String(128))
    address_type: Mapped[str] = mapped_column(String(32), default="residential")

    customer: Mapped[Customer | None] = relationship(back_populates="recipients")


# --- Catalogue -----------------------------------------------------------


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    name_it: Mapped[str] = mapped_column(String(255))
    name_en: Mapped[str] = mapped_column(String(255))
    description_it: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column(Text)
    base_price_cents: Mapped[int] = mapped_column(Integer)
    occasion: Mapped[str | None] = mapped_column(String(64), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # SEO
    seo_title_it: Mapped[str | None] = mapped_column(String(255))
    seo_title_en: Mapped[str | None] = mapped_column(String(255))

    variants: Mapped[list[ProductVariant]] = relationship(back_populates="product")


class ProductVariant(Base, TimestampMixin):
    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    name_it: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    price_cents: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    product: Mapped[Product] = relationship(back_populates="variants")


class AddOn(Base, TimestampMixin):
    __tablename__ = "addons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_it: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    price_cents: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# --- Delivery config -----------------------------------------------------


class DeliveryZone(Base, TimestampMixin):
    __tablename__ = "delivery_zones"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    cap_prefix: Mapped[str] = mapped_column(String(5), index=True)  # e.g. "001"
    delivery_type: Mapped[DeliveryType] = mapped_column(
        Enum(DeliveryType, native_enum=False)
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TimeSlotRule(Base, TimestampMixin):
    __tablename__ = "time_slot_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    delivery_type: Mapped[DeliveryType] = mapped_column(
        Enum(DeliveryType, native_enum=False)
    )
    step_minutes: Mapped[int] = mapped_column(Integer, default=15)
    capacity_per_rider: Mapped[int] = mapped_column(Integer, default=1)
    # Same-day cutoff (Europe/Rome). Placeholder default 14:00.
    cutoff_time: Mapped[time | None] = mapped_column(Time)
    # Minimum notice for ROME_EXACT. Placeholder default 180 min (3h).
    exact_min_notice_minutes: Mapped[int] = mapped_column(Integer, default=180)
    window_fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    exact_fee_cents: Mapped[int] = mapped_column(Integer, default=0)


# --- Orders --------------------------------------------------------------


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False),
        default=OrderStatus.PENDING_PAYMENT,
        index=True,
    )
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    recipient_id: Mapped[int | None] = mapped_column(ForeignKey("recipients.id"))

    delivery_type: Mapped[DeliveryType] = mapped_column(
        Enum(DeliveryType, native_enum=False)
    )
    delivery_date: Mapped[date | None] = mapped_column(Date)
    slot_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    slot_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    subtotal_cents: Mapped[int] = mapped_column(Integer, default=0)
    delivery_fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    card_message: Mapped[str | None] = mapped_column(Text)
    hide_sender: Mapped[bool] = mapped_column(Boolean, default=False)

    customer: Mapped[Customer | None] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(back_populates="order")
    events: Mapped[list[OrderEvent]] = relationship(back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    variant_id: Mapped[int | None] = mapped_column(ForeignKey("product_variants.id"))
    name_snapshot: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price_cents: Mapped[int] = mapped_column(Integer)

    order: Mapped[Order] = relationship(back_populates="items")


class OrderEvent(Base):
    __tablename__ = "order_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    actor: Mapped[str] = mapped_column(String(64))  # staff email or "system"
    from_status: Mapped[OrderStatus | None] = mapped_column(
        Enum(OrderStatus, native_enum=False)
    )
    to_status: Mapped[OrderStatus | None] = mapped_column(
        Enum(OrderStatus, native_enum=False)
    )
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    order: Mapped[Order] = relationship(back_populates="events")


# --- Reminders & payments ------------------------------------------------


class Reminder(Base, TimestampMixin):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    occasion: Mapped[str] = mapped_column(String(64))
    remind_on: Mapped[date] = mapped_column(Date, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer: Mapped[Customer] = relationship(back_populates="reminders")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), index=True
    )
    amount_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False), default=PaymentStatus.PENDING
    )


class StripeEvent(Base):
    """Idempotency ledger for Stripe webhooks."""

    __tablename__ = "stripe_events"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # evt_...
    type: Mapped[str] = mapped_column(String(128))
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
