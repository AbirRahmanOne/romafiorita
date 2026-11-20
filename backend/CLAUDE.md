# backend — FastAPI

API at **api.romafiorita.com**. FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2.0 async +
Alembic, PostgreSQL 16. Managed locally with **venv + pip** (no uv in this env).

Read before working here: **`backend-api-conventions`**. Domain rules:
`checkout-and-delivery-rules`, `order-lifecycle`, `notifications-and-reminders`.
(The skill describes a `routers/services/repositories/schemas/models` package layout; we add
`services/` and `repositories/` when features need them — not scaffolded empty.)

## Layout

```
app/main.py        create_app() factory + lifespan, middleware, error handlers
app/config.py      pydantic-settings (.env)
app/db.py          lazy async engine + get_session + dispose_engine (lifespan)
app/models.py      SQLAlchemy models (15 tables)
app/schemas.py     Pydantic read models
app/core/          security (auth), logging, ids (order number + tokens)
app/domain/        pure logic: delivery engine, pricing, order state machine — no FastAPI/DB
app/payments/      PaymentProvider interface + MockPaymentProvider (ADR 0002)
app/services/      use cases: checkout (validate→price→book slot→order→authorise)
app/api/system.py  unversioned infra: /healthz, /readyz, /health (deprecated)
app/api/v1/        router tree: admin/ (auth, catalog, orders), public/ (catalog,
                   delivery, cart, checkout, orders)
app/deps.py        auth deps: current_staff, require_roles, csrf_protect
app/repositories/  DB access (catalog, orders, slots)
alembic/           async migrations (initial schema committed under versions/)
scripts/export_openapi.py   dump openapi.json (TS client source)
openapi.json       committed contract snapshot (test_openapi_snapshot guards drift)
seed.py            sample products + Rome zone + slot rule
tests/             pytest; SQLite by default, Postgres if TEST_DATABASE_URL is set
.github/workflows/ci.yml   lint, typecheck, PG-backed tests, migration round-trip, pip-audit
```

## API

- `GET /healthz` (liveness) · `GET /readyz` (DB check) · `GET /health` (deprecated alias)
- Catalog (public, `?locale=it|en`): `GET /v1/catalog/products` (filter `occasion`,
  `category`) · `/products/{slug}` · `/occasions` · `/addons`. Tiered variants
  (STANDARD/PREMIUM/LUXURY); variant `id` is the opaque `sku`.
- Delivery: `GET /v1/delivery/check?postcode=&date=` · `/v1/delivery/slots` — zones by CAP
  (Rome 00118–00199), 15-min slots 07:00–23:45 Europe/Rome, fees window 500 / exact 900.
- Cart: `POST /v1/cart/quote` — server-side totals from IDs only; never trust client prices.
- Checkout: `POST /v1/checkout` — books a slot (race-safe), creates the order, authorises
  payment (mock), returns `client_secret` + tracking `token`. Manual capture.
- Tracking: `GET /v1/orders/track/{token}` — public-safe (no sender email / payment).
- Admin orders: `GET /v1/admin/orders` (filter `status`, `q`) · `/{id}` ·
  transitions `POST /{id}/{accept|decline|send-photo|approve|dispatch|deliver}` ·
  `/{id}/photo` · `/{id}/refund`. State machine in `app/domain/orders.py` enforces
  source state + per-action roles + guards; each move writes an OrderEvent.
- Admin catalog: `POST /v1/admin/products` (create tiered product) — OWNER/MANAGER + CSRF.
- `POST /v1/admin/auth/login` · `/refresh` · `/logout` · `GET /v1/admin/auth/me` —
  argon2 passwords, JWT in httpOnly cookies, rotating refresh (reuse-detected), login
  lockout. See `app/api/v1/admin/auth.py`, `app/deps.py`, `app/core/security.py`.
- Errors use `{"error": {code, message, details, request_id}}` (handlers in `main.py`;
  covers HTTPException, 422 validation, and a generic 500). `X-Request-ID` on every
  response; security headers + request-size limit via middleware.
- Export schema: `python -m scripts.export_openapi` → `openapi.json` (commit the diff;
  `test_openapi_snapshot` fails on unintended drift).

## Auth deps (use these on admin routes)

- `Depends(get_current_staff)` — require a logged-in staff member.
- `Depends(require_roles(StaffRole.OWNER, ...))` — role guard (403 otherwise).
- `Depends(csrf_protect)` — double-submit CSRF check on cookie-authenticated mutations.

## Rules

- **Money = integer cents**, currency EUR. **No live Stripe yet** — all payments go through
  the `PaymentProvider` interface with `MockPaymentProvider` (ADR 0002). A real
  `StripeProvider` + `/v1/webhooks/stripe` is a drop-in later.
- Store timestamps **UTC** (timezone-aware); convert to `Europe/Rome` in the service layer.
- Settings via `app/config.py`; keep `.env.example` current. **No secrets in git.**
- CORS allowlist is in settings (storefront + admin + localhost).
- Run: `uvicorn app.main:app --reload`. Test/lint: `pytest`, `ruff check .`, `mypy app`.
- Migrations: `alembic revision --autogenerate -m "msg"` then `alembic upgrade head`
  (needs Postgres running — `docker compose up -d postgres`). Then `python seed.py`.
- Regenerate the TS API client for the frontend after schema changes (later phase).
