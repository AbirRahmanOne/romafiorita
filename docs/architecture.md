# Roma Fiorita API — Architecture

Backend for romafiorita.com (api.romafiorita.com). FastAPI + PostgreSQL 16 +
(Redis for the worker). The storefront + admin frontend is a **separate repo**
and consumes this API via the generated OpenAPI client (`backend/openapi.json`).

## Layers

```
HTTP  →  app/api/v1/{public,admin}/*   routers (thin: validate, call, serialize)
         app/deps.py                   auth (current_staff, require_roles, csrf), rate_limit
         app/services/*                use cases (checkout, payment_requests, settings,
                                       analytics, gdpr, pdf) — orchestrate domain+repos+integrations
         app/domain/*                  pure logic (delivery engine, pricing, order state machine)
         app/repositories/*            SQLAlchemy queries (catalog, orders, slots, analytics)
         app/models.py                 ORM (17 tables)   app/schemas.py  Pydantic I/O
Seams:   app/payments (Stripe), app/notifications (Resend), app/integrations/r2,
         app/realtime (SSE bus)        — interfaces + Mock* defaults, real adapters drop in
Jobs:    app/workers/tasks.py (pure) scheduled by app/workers/arq.py (cron + Redis)
Core:    app/core/{config,security,logging,ids,ratelimit,http_cache}
```

## Request flow

1. `context_middleware` assigns a `request_id` (echoed as `X-Request-ID`), enforces a
   body-size limit, adds security headers, logs the request as JSON.
2. Routers depend on `get_session` (one `AsyncSession` per request), auth deps, and
   `rate_limit(...)` where applicable.
3. Errors are normalised to `{"error": {code, message, details, request_id}}` (handlers for
   `HTTPException`, 422 validation, and a catch-all 500).

## Key decisions

- **Money** is integer cents, EUR; totals always recomputed server-side (clients send IDs).
- **Time** stored UTC; business rules in `Europe/Rome`; slots are DST-safe.
- **Slots** are race-safe: an atomic `UPDATE … WHERE held_count < capacity` (no overbooking).
- **Orders** move through a table-driven state machine (roles + guards + payment effects);
  every change writes an `OrderEvent`.
- **Payments** are behind a `PaymentProvider` interface — `MockPaymentProvider` today,
  `StripeProvider` + `/v1/webhooks/stripe` later (ADR 0002). Website orders use manual
  capture (authorise at checkout, capture on accept); payment-requests auto-capture.
- **Tokens** (order tracking, payment-request links) are stored only as SHA-256 hashes.
- **Auth**: argon2 passwords, JWT access + rotating refresh (reuse-detected) in httpOnly
  cookies, CSRF double-submit, per-account login lockout.

## Processes

- **web** — `uvicorn app.main:app` (the API).
- **worker** — `arq app.workers.arq.WorkerSettings`: cron for slot-expiry sweep, occasion
  reminders, GDPR retention. Needs Redis.

## Data model (tables)

staff · customers · recipients · products · product_variants · addons · delivery_zones ·
time_slot_rules · slot_capacity · orders · order_items · order_events · reminders ·
payments · payment_requests · app_settings · stripe_events.

## Deferred / stubbed (tracked in memory + ADRs)

Real Stripe adapter + webhooks; Resend async dispatch (emails currently sent synchronously
via the mock); SSE Redis pub/sub for multi-instance (bus is in-process); Google Search
Console (`/insights/seo` is an empty stub); WhatsApp adapter; EXIF-strip/thumbnails on
uploads; TOTP 2FA; accept-with-change / auto-accept; rider order-scoping.
