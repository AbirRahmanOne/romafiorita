from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import StaffRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class StaffMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: StaffRole


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name_it: str
    name_en: str
    description_it: str | None
    description_en: str | None
    base_price_cents: int
    occasion: str | None
    is_active: bool


class ProductList(BaseModel):
    items: list[ProductRead]
    total: int


class ProductCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=160)
    name_it: str = Field(min_length=1)
    name_en: str = Field(min_length=1)
    description_it: str | None = None
    description_en: str | None = None
    base_price_cents: int = Field(ge=0)
    occasion: str | None = None
    is_active: bool = True


class ProductUpdate(BaseModel):
    name_it: str | None = Field(default=None, min_length=1)
    name_en: str | None = Field(default=None, min_length=1)
    description_it: str | None = None
    description_en: str | None = None
    base_price_cents: int | None = Field(default=None, ge=0)
    occasion: str | None = None
    is_active: bool | None = None
