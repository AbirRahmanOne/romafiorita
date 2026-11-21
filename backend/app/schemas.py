import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import ProductTier, StaffRole

Locale = str  # "it" | "en"


# --- Auth ----------------------------------------------------------------


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class StaffMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: StaffRole


# --- Catalog (public, localised) -----------------------------------------


class VariantRead(BaseModel):
    id: str  # public sku
    tier: ProductTier
    price_cents: int
    description_it: str | None = None
    description_en: str | None = None
    images: list[str] = []
    active: bool
    is_default: bool
    same_day: bool
    exact_time: bool


class ProductRead(BaseModel):
    slug: str
    name: str
    subtitle: str | None = None
    occasion: str | None = None
    category: str | None = None
    tags: list[str] = []
    images: list[str] = []
    variants: list[VariantRead]


class ProductListResponse(BaseModel):
    items: list[ProductRead]


class OccasionRead(BaseModel):
    slug: str
    name_it: str
    name_en: str


class OccasionListResponse(BaseModel):
    items: list[OccasionRead]


class AddonRead(BaseModel):
    id: str  # public code
    name_it: str
    name_en: str
    price_cents: int


class AddonListResponse(BaseModel):
    items: list[AddonRead]


# --- Catalog writes (admin) ----------------------------------------------


class VariantCreate(BaseModel):
    tier: ProductTier
    price_cents: int = Field(ge=0)
    description_it: str | None = None
    description_en: str | None = None
    images: list[str] = []
    is_default: bool = False
    same_day: bool = True
    exact_time: bool = True
    stock: int | None = Field(default=None, ge=0)


class ProductCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=160)
    name_it: str = Field(min_length=1)
    name_en: str = Field(min_length=1)
    subtitle_it: str | None = None
    subtitle_en: str | None = None
    occasion: str | None = None
    category: str | None = None
    tags: list[str] = []
    images: list[str] = []
    is_active: bool = True
    variants: list[VariantCreate] = Field(min_length=1)


# --- Delivery ------------------------------------------------------------


class DeliveryFees(BaseModel):
    standard_cents: int
    window_cents: int
    exact_cents: int


class DeliveryCheckResponse(BaseModel):
    zone: str  # ROME | NATIONAL
    types: list[str]
    fees: DeliveryFees
    cutoff: str | None


class SlotRead(BaseModel):
    time: str
    iso: str
    available: bool


class SlotListResponse(BaseModel):
    slots: list[SlotRead]


# --- Cart / quote --------------------------------------------------------


class CartItem(BaseModel):
    variant_id: str
    quantity: int = Field(ge=1, le=99)
    addons: list[str] = []


class CartQuoteRequest(BaseModel):
    items: list[CartItem] = Field(min_length=1)
    postcode: str | None = None
    date: datetime.date | None = None
    delivery_type: str = "standard"


class CartQuoteResponse(BaseModel):
    subtotal_cents: int
    delivery_cents: int
    time_fee_cents: int
    total_cents: int
    currency: str = "EUR"


# --- Checkout ------------------------------------------------------------


class SenderIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    locale: str = Field(default="it", pattern="^(it|en)$")


class RecipientIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    address_line: str = Field(min_length=1, max_length=512)
    cap: str = Field(pattern=r"^\d{5}$")
    city: str = Field(min_length=1, max_length=128)
    address_type: str = Field(default="HOME", max_length=32)


class CheckoutRequest(BaseModel):
    items: list[CartItem] = Field(min_length=1)
    delivery_type: str = "standard"
    delivery_slot: str | None = None  # ISO datetime for Rome window/exact
    sender: SenderIn
    recipient: RecipientIn
    card_message: str | None = Field(default=None, max_length=300)
    hide_sender: bool = False


class CheckoutResponse(BaseModel):
    order_number: str
    token: str
    client_secret: str
    subtotal_cents: int
    delivery_cents: int
    time_fee_cents: int
    total_cents: int
    currency: str = "EUR"


# --- Tracking (public-safe) ----------------------------------------------


class TimelineStep(BaseModel):
    status: str
    done: bool


class TrackItem(BaseModel):
    name: str
    tier: str


class TrackResponse(BaseModel):
    order_number: str
    status: str
    timeline: list[TimelineStep]
    bouquet_photo: str | None
    delivery_slot: str | None
    total_cents: int
    items: list[TrackItem]


# --- Admin orders --------------------------------------------------------


class AdminOrderItem(BaseModel):
    name: str
    tier: str | None
    quantity: int
    unit_price_cents: int


class OrderEventRead(BaseModel):
    actor: str
    from_status: str | None
    to_status: str | None
    note: str | None


class AdminOrderRead(BaseModel):
    id: int
    number: str
    status: str
    sender_name: str | None
    sender_email: str | None
    sender_country: str | None
    recipient_name: str | None
    recipient_address: str | None
    recipient_cap: str | None
    delivery_type: str
    delivery_date: datetime.date | None
    slot_start: datetime.datetime | None
    total_cents: int
    currency: str
    card_message: str | None
    hide_sender: bool
    bouquet_photo: str | None
    items: list[AdminOrderItem]
    events: list[OrderEventRead] = []


class AdminOrderListResponse(BaseModel):
    items: list[AdminOrderRead]
    counts: dict[str, int]


class PhotoBody(BaseModel):
    url: str = Field(min_length=1, max_length=512)


class RefundBody(BaseModel):
    amount_cents: int | None = Field(default=None, ge=1)
    reason: str | None = Field(default=None, max_length=255)


# --- Payment requests (custom orders) ------------------------------------


class CustomItem(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    price_cents: int = Field(ge=0)


class PaymentRequestCreate(BaseModel):
    customer: str = Field(min_length=1, max_length=255)
    email: EmailStr
    whatsapp: str | None = Field(default=None, max_length=32)
    recipient: str | None = Field(default=None, max_length=512)
    delivery_slot: str | None = Field(default=None, max_length=128)
    card_message: str | None = Field(default=None, max_length=300)
    items: list[CustomItem] = Field(min_length=1)
    expiry_hours: int = Field(default=48, ge=1, le=720)
    discount_cents: int = Field(default=0, ge=0)
    hide_sender: bool = False
    locale: str = Field(default="it", pattern="^(it|en)$")


class PaymentRequestUpdate(BaseModel):
    customer: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    whatsapp: str | None = Field(default=None, max_length=32)
    recipient: str | None = Field(default=None, max_length=512)
    delivery_slot: str | None = Field(default=None, max_length=128)
    card_message: str | None = Field(default=None, max_length=300)
    items: list[CustomItem] | None = Field(default=None, min_length=1)
    discount_cents: int | None = Field(default=None, ge=0)
    hide_sender: bool | None = None


class PaymentRequestRead(BaseModel):
    id: int
    order_number: str
    customer: str
    email: str
    whatsapp: str | None
    amount_cents: int
    currency: str
    status: str
    # Raw token: present only on create/resend/duplicate/edit; None in lists.
    token: str | None = None
    expires_at: datetime.datetime
    last_viewed_at: datetime.datetime | None
    items: list[CustomItem]
    recipient: str | None
    delivery_slot: str | None
    card_message: str | None
    discount_cents: int
    hide_sender: bool


class PaymentRequestListResponse(BaseModel):
    items: list[PaymentRequestRead]


# --- Public pay / verify -------------------------------------------------


class LocalEstimate(BaseModel):
    currency: str
    amount_cents: int


class PaySummary(BaseModel):
    order_number: str
    items: list[CustomItem]
    recipient: str | None
    delivery_slot: str | None
    card_message: str | None
    amount_cents: int
    currency: str
    local_estimate: LocalEstimate | None = None
    status: str
    expires_at: datetime.datetime


class PayIntentResponse(BaseModel):
    client_secret: str
    order_number: str


class VerifyRequest(BaseModel):
    order_number: str = Field(min_length=1, max_length=20)
    email: EmailStr


class VerifyResponse(BaseModel):
    genuine: bool
    order_number: str | None = None
    amount_cents: int | None = None
    status: str | None = None


# --- Settings ------------------------------------------------------------


class BusinessIdentity(BaseModel):
    # Nullable until the client supplies real values (spec §J).
    company_name: str | None = None
    address: str | None = None
    vat_number: str | None = None
    pec: str | None = None
    phone: str | None = None
    whatsapp: str | None = None


class ZoneSetting(BaseModel):
    name: str
    type: str
    fee_cents: int


class SlotPricing(BaseModel):
    window_cents: int
    exact_cents: int


class Cutoffs(BaseModel):
    rome_hour: int
    suburbs_hour: int


class SettingsRead(BaseModel):
    zones: list[ZoneSetting]
    slot_pricing: SlotPricing
    cutoffs: Cutoffs
    blocked_dates: list[str]
    daily_capacity: int
    notification_recipients: list[str]
    business: BusinessIdentity


class PublicSettings(BaseModel):
    zones: list[ZoneSetting]
    slot_pricing: SlotPricing
    cutoffs: Cutoffs
    blocked_dates: list[str]


class SettingsUpdate(BaseModel):
    zones: list[ZoneSetting] | None = None
    slot_pricing: SlotPricing | None = None
    cutoffs: Cutoffs | None = None
    blocked_dates: list[str] | None = None
    daily_capacity: int | None = Field(default=None, ge=0)
    notification_recipients: list[str] | None = None
    business: BusinessIdentity | None = None


# --- Staff ---------------------------------------------------------------


class StaffRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: StaffRole
    is_active: bool


class StaffListResponse(BaseModel):
    items: list[StaffRead]


class StaffCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    role: StaffRole
    password: str = Field(min_length=8, max_length=128)


class StaffUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    role: StaffRole | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


# --- Admin payments ------------------------------------------------------


class PaymentRow(BaseModel):
    id: int
    order_number: str
    source: str  # WEBSITE | PAYMENT_REQUEST
    status: str  # held | captured | failed | refunded | cancelled
    amount_cents: int
    currency: str
    fee_cents: int | None  # from Stripe balance tx (null without Stripe)
    net_cents: int | None
    created_at: datetime.datetime


class PaymentKpis(BaseModel):
    gross_cents: int
    fees_cents: int
    refunds_cents: int
    net_cents: int


class PaymentsListResponse(BaseModel):
    kpis: PaymentKpis
    items: list[PaymentRow]


class HeldPayment(BaseModel):
    id: int
    order_number: str
    amount_cents: int
    currency: str
    created_at: datetime.datetime
    hold_expires_at: datetime.datetime


class HeldListResponse(BaseModel):
    items: list[HeldPayment]


class MonthlyReport(BaseModel):
    month: str
    filename: str
    csv: str


class Balance(BaseModel):
    available_cents: int
    pending_cents: int


class PayoutsResponse(BaseModel):
    items: list[dict[str, object]]
    balance: Balance


class DisputesResponse(BaseModel):
    items: list[dict[str, object]]


class ReviewsResponse(BaseModel):
    items: list[dict[str, object]]


# --- Uploads -------------------------------------------------------------


class UploadSignRequest(BaseModel):
    content_type: str = "image/jpeg"


class UploadSignResponse(BaseModel):
    upload_url: str
    public_url: str
