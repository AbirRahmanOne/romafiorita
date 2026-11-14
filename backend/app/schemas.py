from pydantic import BaseModel, ConfigDict


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


class ProductList(BaseModel):
    items: list[ProductRead]
    total: int
