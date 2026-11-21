"""v1 API router tree: public/ (storefront) + admin/ + webhooks/ (later).

Each sub-router owns its full path prefix, so this aggregator adds none.
"""

from fastapi import APIRouter

from app.api.v1.admin import auth
from app.api.v1.admin import catalog as admin_catalog
from app.api.v1.admin import gdpr as admin_gdpr
from app.api.v1.admin import insights as admin_insights
from app.api.v1.admin import orders as admin_orders
from app.api.v1.admin import payment_requests as admin_payment_requests
from app.api.v1.admin import payments as admin_payments
from app.api.v1.admin import settings as admin_settings
from app.api.v1.admin import staff as admin_staff
from app.api.v1.admin import stream as admin_stream
from app.api.v1.admin import uploads as admin_uploads
from app.api.v1.public import (
    cart,
    catalog,
    checkout,
    config,
    content,
    delivery,
    orders,
    pay,
)

v1_router = APIRouter()
# admin
v1_router.include_router(auth.router)
v1_router.include_router(admin_catalog.router)
# /orders/stream must register before /orders/{order_id} to win the match.
v1_router.include_router(admin_stream.router)
v1_router.include_router(admin_orders.router)
v1_router.include_router(admin_payment_requests.router)
v1_router.include_router(admin_payments.router)
v1_router.include_router(admin_payments.extras_router)
v1_router.include_router(admin_settings.router)
v1_router.include_router(admin_staff.router)
v1_router.include_router(admin_uploads.router)
v1_router.include_router(admin_insights.router)
v1_router.include_router(admin_gdpr.router)
# public (storefront)
v1_router.include_router(catalog.router)
v1_router.include_router(delivery.router)
v1_router.include_router(cart.router)
v1_router.include_router(checkout.router)
v1_router.include_router(orders.router)
v1_router.include_router(pay.router)
v1_router.include_router(config.router)
v1_router.include_router(content.router)
