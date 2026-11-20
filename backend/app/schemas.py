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
