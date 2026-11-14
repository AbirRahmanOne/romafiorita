# apps/api — Backend

API at **api.romafiorita.com**. FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2.0 async +
Alembic, PostgreSQL 16, arq + Redis for jobs. Managed with **uv**.

Read before working here: **`backend-api-conventions`** (layout, patterns, error format).
Also the relevant domain skill: `checkout-and-delivery-rules`, `stripe-payments`,
`order-lifecycle`, `notifications-and-reminders`.

- Layout: `routers / services / repositories / schemas / models`. Business logic lives in
  services, DB access in repositories.
- **Money = integer cents.** Recompute all amounts server-side; never trust the client.
- Store timestamps **UTC**; convert to `Europe/Rome` in the service layer for business logic
  and display.
- Settings via **pydantic-settings** (`.env`). Structured logging. Rate limiting on public
  endpoints.
- **CORS** limited to `romafiorita.com`, `admin.romafiorita.com` (+ localhost in dev).
- Auth: admin JWT in httpOnly cookies, roles OWNER/MANAGER/FLORIST/RIDER. Customer accounts
  optional (guest checkout allowed).
- Stripe webhooks at `/webhooks/stripe`: verify signature, process idempotently (store event
  ids in `StripeEvent`).
- Alembic: one migration per schema change, reviewed; never edit a shipped migration.
- Run: `uv run uvicorn app.main:app --reload`. Regenerate the TS client from OpenAPI after
  any schema change (`packages/api-client`).
