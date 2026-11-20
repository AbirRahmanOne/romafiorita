"""SQLAlchemy 2.0 models for Roma Fiorita.

Conventions (see .claude/skills/backend-api-conventions):
- money is integer cents, currency EUR;
- timestamps stored in UTC (timezone-aware);
- business-logic timezone conversion (Europe/Rome) happens in the service layer.
"""

from __future__ import annotations

import enum
from datetime import UTC, date, datetime, time
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
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


class ProductTier(enum.StrEnum):
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"
    LUXURY = "LUXURY"


class OrderStatus(enum.StrEnum):
    # Happy path (spec §4D).
    PENDING_PAYMENT = "PENDING_PAYMENT"
    NEW = "NEW"
    ACCEPTED = "ACCEPTED"
    AWAITING_PHOTO = "AWAITING_PHOTO"
    PHOTO_SENT = "PHOTO_SENT"
    APPROVED = "APPROVED"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    # Side states.
    DECLINED = "DECLINED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    PROBLEM = "PROBLEM"
    PAYMENT_REQUESTED = "PAYMENT_REQUESTED"
    EXPIRED = "EXPIRED"


class DeliveryType(enum.StrEnum):
    ROME_SAME_DAY = "ROME_SAME_DAY"
    ROME_WINDOW = "ROME_WINDOW"
    ROME_EXACT = "ROME_EXACT"
    NATIONAL_COURIER = "NATIONAL_COURIER"


class PaymentRequestStatus(enum.StrEnum):
    SENT = "SENT"
    VIEWED = "VIEWED"
    PAID = "PAID"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class PaymentStatus(enum.StrEnum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"  # hold placed (manual capture)
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"  # hold released
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


# --- Staff & customers ---------------------------------------------------


class Staff(Base, TimestampMixin):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[StaffRole] = mapped_column(Enum(StaffRole))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Auth: rotating-refresh reuse detection + login lockout.
    refresh_jti: Mapped[str | None] = mapped_column(String(64))
    failed_login_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable email supports guest checkout.
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(32))  # E.164
    country: Mapped[str | None] = mapped_column(String(2))  # ISO-3166 alpha-2
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
    subtitle_it: Mapped[str | None] = mapped_column(String(255))
    subtitle_en: Mapped[str | None] = mapped_column(String(255))
    occasion: Mapped[str | None] = mapped_column(String(64), index=True)
    category: Mapped[str | None] = mapped_column(String(64), index=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    images: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    # SEO
    seo_title_it: Mapped[str | None] = mapped_column(String(255))
    seo_title_en: Mapped[str | None] = mapped_column(String(255))

    variants: Mapped[list[ProductVariant]] = relationship(
        back_populates="product", order_by="ProductVariant.price_cents"
    )


class ProductVariant(Base, TimestampMixin):
    __tablename__ = "product_variants"
    # Exactly one variant per tier per product (spec §4A).
    __table_args__ = (UniqueConstraint("product_id", "tier", name="uq_variant_tier"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    # Stable public identifier the cart/checkout sends back (opaque to clients).
    sku: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    tier: Mapped[ProductTier] = mapped_column(Enum(ProductTier))
    price_cents: Mapped[int] = mapped_column(Integer)
    description_it: Mapped[str | None] = mapped_column(Text)
    description_en: Mapped[str | None] = mapped_column(Text)
    images: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    same_day: Mapped[bool] = mapped_column(Boolean, default=True)
    exact_time: Mapped[bool] = mapped_column(Boolean, default=True)
    stock: Mapped[int | None] = mapped_column(Integer)

    product: Mapped[Product] = relationship(back_populates="variants")


class AddOn(Base, TimestampMixin):
    __tablename__ = "addons"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Public code the cart sends (e.g. "vase").
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
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
    delivery_type: Mapped[DeliveryType] = mapped_column(Enum(DeliveryType))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TimeSlotRule(Base, TimestampMixin):
    __tablename__ = "time_slot_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    delivery_type: Mapped[DeliveryType] = mapped_column(Enum(DeliveryType))
    step_minutes: Mapped[int] = mapped_column(Integer, default=15)
    capacity_per_rider: Mapped[int] = mapped_column(Integer, default=1)
    # Same-day cutoff (Europe/Rome). Placeholder default 14:00.
    cutoff_time: Mapped[time | None] = mapped_column(Time)
    # Minimum notice for ROME_EXACT. Placeholder default 180 min (3h).
    exact_min_notice_minutes: Mapped[int] = mapped_column(Integer, default=180)
    window_fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    exact_fee_cents: Mapped[int] = mapped_column(Integer, default=0)


class SlotCapacity(Base, TimestampMixin):
    """One counter row per (date, slot). ``held_count`` is bumped atomically at
    booking via UPDATE … WHERE held_count < capacity, so concurrent checkouts
    can never overbook (see repositories/slots.py)."""

    __tablename__ = "slot_capacity"
    __table_args__ = (
        UniqueConstraint("slot_date", "slot_start", name="uq_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slot_date: Mapped[date] = mapped_column(Date, index=True)
    slot_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    capacity: Mapped[int] = mapped_column(Integer)
    held_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


# --- Orders --------------------------------------------------------------


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable only transiently: assigned from the id right after flush, before
    # commit (RF-YYYY-NNNNN needs the id). Never persisted null.
    number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus), default=OrderStatus.PENDING_PAYMENT, index=True
    )
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    recipient_id: Mapped[int | None] = mapped_column(ForeignKey("recipients.id"))

    delivery_type: Mapped[DeliveryType] = mapped_column(Enum(DeliveryType))
    delivery_date: Mapped[date | None] = mapped_column(Date)
    slot_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    slot_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    subtotal_cents: Mapped[int] = mapped_column(Integer, default=0)
    delivery_fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    time_fee_cents: Mapped[int] = mapped_column(Integer, default=0)
    total_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    card_message: Mapped[str | None] = mapped_column(Text)
    hide_sender: Mapped[bool] = mapped_column(Boolean, default=False)
    bouquet_photo: Mapped[str | None] = mapped_column(String(512))
    assigned_rider_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"))

    # Public tracking: store only the hash; the raw token goes to the buyer.
    track_token_hash: Mapped[str | None] = mapped_column(
        String(64), unique=True, index=True
    )

    customer: Mapped[Customer | None] = relationship(back_populates="orders")
    recipient: Mapped[Recipient | None] = relationship()
    items: Mapped[list[OrderItem]] = relationship(back_populates="order")
    events: Mapped[list[OrderEvent]] = relationship(
        back_populates="order", order_by="OrderEvent.id"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_variants.id")
    )
    name_snapshot: Mapped[str] = mapped_column(String(255))
    tier_snapshot: Mapped[str | None] = mapped_column(String(16))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price_cents: Mapped[int] = mapped_column(Integer)

    order: Mapped[Order] = relationship(back_populates="items")


class OrderEvent(Base):
    __tablename__ = "order_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    actor: Mapped[str] = mapped_column(String(64))  # staff email or "system"
    from_status: Mapped[OrderStatus | None] = mapped_column(Enum(OrderStatus))
    to_status: Mapped[OrderStatus | None] = mapped_column(Enum(OrderStatus))
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
        Enum(PaymentStatus), default=PaymentStatus.PENDING
    )


class PaymentRequest(Base, TimestampMixin):
    """Custom-order payment request (spec §F). Captured immediately on payment.

    Only the token hash is stored; the raw token is shown to the admin at
    create/resend/edit time and goes to the buyer via WhatsApp/email."""

    __tablename__ = "payment_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[PaymentRequestStatus] = mapped_column(
        Enum(PaymentRequestStatus), default=PaymentRequestStatus.SENT, index=True
    )
    customer: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True)
    whatsapp: Mapped[str | None] = mapped_column(String(32))
    recipient: Mapped[str | None] = mapped_column(String(512))
    delivery_slot: Mapped[str | None] = mapped_column(String(128))
    card_message: Mapped[str | None] = mapped_column(Text)
    # [{title, price_cents}]
    items: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    amount_cents: Mapped[int] = mapped_column(Integer)
    discount_cents: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    hide_sender: Mapped[bool] = mapped_column(Boolean, default=False)
    locale: Mapped[str] = mapped_column(String(2), default="it")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    order: Mapped[Order] = relationship()


class StripeEvent(Base):
    """Idempotency ledger for Stripe webhooks."""

    __tablename__ = "stripe_events"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # evt_...
    type: Mapped[str] = mapped_column(String(128))
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
