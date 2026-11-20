"""v1 API router tree: public/ (storefront) + admin/ + webhooks/ (later).

Each sub-router owns its full path prefix, so this aggregator adds none.
"""

from fastapi import APIRouter

from app.api.v1.admin import auth
from app.api.v1.admin import catalog as admin_catalog
from app.api.v1.admin import orders as admin_orders
from app.api.v1.public import cart, catalog, checkout, delivery, orders

v1_router = APIRouter()
# admin
v1_router.include_router(auth.router)
v1_router.include_router(admin_catalog.router)
v1_router.include_router(admin_orders.router)
# public (storefront)
v1_router.include_router(catalog.router)
v1_router.include_router(delivery.router)
v1_router.include_router(cart.router)
v1_router.include_router(checkout.router)
v1_router.include_router(orders.router)
