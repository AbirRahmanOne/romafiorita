# API changelog

The OpenAPI schema (`backend/openapi.json`) is the contract for the frontend client.
`test_openapi_snapshot` guards against unintended drift. Additive changes are safe; breaking
changes must bump versioning and be coordinated with the frontend.

## Unreleased (v0.1.0, pre-launch)

Initial API build-out. Notable surface (all under `/v1`):

- **Catalog** `GET /catalog/{products,products/{slug},occasions,addons}` — tiered variants,
  `?locale`, ETag/Cache-Control. Admin `POST /admin/products`.
- **Delivery** `GET /delivery/{check,slots}` — CAP zones, DST-safe slots.
- **Cart** `POST /cart/quote` — server-side totals.
- **Checkout** `POST /checkout`; **tracking** `GET /orders/track/{token}`.
- **Admin orders** list/detail + transitions (accept/decline/send-photo/approve/dispatch/
  deliver/photo/refund); SSE `GET /admin/orders/stream`.
- **Payment requests** admin CRUD + `GET /{id}/pdf`; public `GET /pay/{token}`,
  `POST /pay/{token}/intent`, `POST /verify`.
- **Admin** payments views, settings, staff, uploads/sign, dashboard, insights (sales; seo
  stub), GDPR export/delete. Public `GET /config/{business,settings}`, `GET /content/reviews`.
- **System** `GET /healthz`, `/readyz`, `/health` (deprecated).

Deprecated: `/products*` (scaffold) was removed before any client used it; `/health` → use
`/healthz`.

Payments run on a mock provider (no live Stripe yet) — see ADR 0002.
