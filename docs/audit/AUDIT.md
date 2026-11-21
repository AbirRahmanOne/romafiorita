# Roma Fiorita Backend — Audit (Phase 0)

**Date:** 2026-11-20 · **Scope:** `backend/` only (frontend is a separate repo,
`romafiorita-frontend`, consuming this API via a generated OpenAPI client).
**Method:** read-only. No code or behaviour changed. Tooling (ruff/mypy/pytest/pip-audit)
was run to report real results.

> **Headline:** the backend is an early *scaffold*, not a near-complete API. ~7% of the
> target spec exists. One real feature area ships (Products CRUD + health). The ORM models
> sketch ~5 more areas but **there are no migrations**, so none of those tables exist in any
> database, and nothing is wired to a router. Payments, delivery engine, orders lifecycle,
> auth, cart/quote, checkout, payment-requests, admin API, jobs, uploads, SSE, insights,
> GDPR — all **Missing**.

---

## 1. Architecture map

| Concern | Where | Notes |
|---|---|---|
| Entry point / app factory | `app/main.py` | Module-level `FastAPI(...)`, not a factory; no lifespan, no `/v1` prefix. |
| Config | `app/config.py` | `pydantic-settings` `Settings`, single flat object, env-overridable. No startup validation beyond type coercion. |
| DB session | `app/db.py` | Async engine + `async_sessionmaker` built lazily via `@lru_cache`; `get_session` FastAPI dependency. No pool tuning, no statement timeout. |
| Auth | — | **None.** No login, JWT, cookies, roles, or guards. |
| Errors | `app/main.py:22-39` | One `HTTPException` handler → `{"error": {code, message, details}}`. No `request_id`, no handler for `RequestValidationError` (422 keeps FastAPI's default shape), no catch-all 500 handler. |
| Routers | `app/routers/` | `health.py`, `products.py`. Registered in `app/main.py:42-43`. |
| Repositories | `app/repositories/products.py` | SQLAlchemy queries for products only. |
| Models (ORM) | `app/models.py` | 13 tables defined (see §2). Most are unused by any router. |
| Schemas | `app/schemas.py` | Product read/list/create/update only. |
| Background jobs / arq | — | **None.** Redis is in config + docker-compose but unused by app code. |
| Integrations (Stripe/Resend/R2/GSC) | — | **None.** Keys in config, no client code. |
| Migrations | `alembic/` | `env.py` + `script.py.mako` only. `alembic/versions/` is **empty** (no revisions). |

**Layering vs target (`prompt.txt` §3):** current layout is `routers/ + repositories/ +
models.py + schemas.py`. Target wants `api/v1/{public,admin,webhooks}`, `domain/`,
`services/`, `integrations/`, `workers/`, `core/`. The `domain/`, `services/`,
`integrations/`, `workers/`, `core/` layers do not exist.

---

## 2. Inventory

### Endpoints (all of them)

| Method | Path | Auth | Request → Response |
|---|---|---|---|
| GET | `/health` | none | → `{"status":"ok"}` (`routers/health.py`) |
| GET | `/products` | **none (should be mixed)** | query `occasion,include_inactive,limit,offset` → `ProductList` |
| GET | `/products/{slug}` | none | → `ProductRead` (active only) |
| POST | `/products` | **none — admin action, unguarded** | `ProductCreate` → `ProductRead` 201 |
| PATCH | `/products/id/{id}` | **none — admin action, unguarded** | `ProductUpdate` → `ProductRead` |
| DELETE | `/products/id/{id}` | **none — admin action, unguarded** | → 204 |

No `/v1` prefix anywhere. No pagination envelope beyond `ProductList{items,total}`.

### DB tables (defined in `app/models.py`; **none migrated**)

`staff` (52,90), `customers` (101), `recipients` (115), `products` (133),
`product_variants` (154), `addons` (167), `delivery_zones` (180), `time_slot_rules` (190),
`orders` (208), `order_items` (237), `order_events` (253), `reminders` (272),
`payments` (284), `stripe_events` (299).

Relations: Customer→Recipient/Order/Reminder; Product→Variant; Order→Item/Event; Payment→Order
(FK only, no relationship). **No slot-booking/reservation table** (capacity can't be tracked).
**No payment-request / token table.** **No discount-code table.** **No audit table beyond
`order_events`.**

### Alembic migrations

**Zero.** `env.py` targets `Base.metadata`; autogenerate has never been run. The schema is
created only by `Base.metadata.create_all` in tests (`tests/conftest.py:23`) and implicitly
expected by `seed.py`. **There is no reproducible way to build the production schema.**

### Env vars (`app/config.py`, `.env.example`)

`ENVIRONMENT`, `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`, `JWT_SECRET` (default
`"dev-only-change-me"`), `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `RESEND_API_KEY`.
Missing vs spec: R2, Google Search Console, statement descriptor, cookie domain, rate-limit
config, Sentry DSN, token-expiry settings.

### Scheduled jobs / webhooks

**None implemented.** `StripeEvent` table exists as an idempotency ledger but **no webhook
endpoint consumes it**.

---

## 3. Gap analysis vs target spec (`prompt.txt` §4–8)

Legend: ✅ Exists · 🟡 Partial · ❌ Missing · ⚠️ Wrong

| Area | State | Evidence |
|---|---|---|
| **Catalog — products** | 🟡 | `products.py` CRUD exists, but model is flat (`base_price_cents`, `name_it/en`) — not the required 3-tier `STANDARD/PREMIUM/LUXURY` variant model. `models.py:133,154`. |
| Catalog — tiers / is_default / eligibility | ❌/⚠️ | `ProductVariant` has no `tier`, `is_default`, `same_day`, `exact_time`, `images`, `description`. `models.py:154-165`. Spec §4A requires exactly 3 tiers + constraints. |
| Catalog — locale fallback (`?locale=`) | ❌ | API returns both `name_it`+`name_en`; frontend expects single localised `name` via `?locale`. |
| Catalog — add-ons | 🟡 | `AddOn` model exists (`models.py:167`); no endpoint. |
| Catalog — bulk price change w/ preview | ❌ | None. |
| **Delivery engine** | ❌ | No zone-by-CAP logic, no `domain/`, no `/delivery/check` or `/delivery/slots`. `DeliveryZone`/`TimeSlotRule` models exist but unused. |
| Slot availability / capacity / race-safety | ❌ | No slot-booking table; no `SELECT … FOR UPDATE`; overbooking impossible to prevent. |
| Slot reservation expiry | ❌ | None. |
| **Pricing (server-side quote)** | ❌ | No `/cart/quote`. Risk: when added, must not trust client prices. |
| Discount codes | ❌ | No model, no logic. |
| **Orders & state machine** | ❌ | `Order`/`OrderEvent` models exist; no transitions, no guards, no endpoints. `OrderStatus` enum (`models.py:59`) **differs from spec** (has `PREPARING`; missing `AWAITING_PHOTO`, `APPROVED`, `PARTIALLY_REFUNDED`, `PAYMENT_REQUESTED`, `EXPIRED`). |
| Accept-with-change / auto-accept / alerts | ❌ | None. |
| Order capture fields (sender/recipient/address type/items snapshot) | 🟡 | Partial on models; `Recipient.address_type` is free `String` default `"residential"` not the HOME/OFFICE/HOSPITAL/… enum (`models.py:126`). |
| Public tracking `/orders/track/{token}` | ❌ | No token field on Order, no endpoint. |
| **Payments (Stripe)** | ❌ | No Stripe client, no PaymentIntent, no manual-capture flow. `Payment` model exists (`models.py:284`) but unused. |
| Stripe webhooks (verify + idempotent) | ❌ | `StripeEvent` ledger table exists (`models.py:299`) but **no `/webhooks/stripe` endpoint**. |
| Admin money actions (capture/cancel/refund) | ❌ | None. |
| Admin payments API (list/held/payouts/balance/disputes/report) | ❌ | None. |
| **Payment requests + token + PDF + verify** | ❌ | No model, no token hashing, no `/pay/{token}`, no `/verify`, no PDF. |
| **Notifications & jobs (arq, emails, SSE, push)** | ❌ | Redis unused; no arq; no Resend; no SSE; no Web Push. |
| **Uploads (R2 signed PUT, EXIF strip, thumbs)** | ❌ | None. |
| **Insights (GSC + sales analytics)** | ❌ | None. |
| **Content & settings (faqs/cities/business/settings)** | ❌ | None. |
| Reviews (real only) | ❌ | No model; frontend already returns empty by design. |
| **Auth / roles / JWT / cookies / CSRF / 2FA** | ❌ | None. `Staff`+`StaffRole` modelled (`models.py:52,90`) but no auth layer. |
| **Security — rate limits / headers / size limits** | ❌ | None. |
| **GDPR — retention / export / delete / consent** | ❌ | None. |
| Health `/healthz` + `/readyz` | 🟡 | Only `/health` (liveness-ish); no readiness check of DB/Redis. |
| **OpenAPI discipline (operation_ids, examples, /v1, diff in CI)** | 🟡 | `export_openapi.py` dumps schema; no `/v1`, no operation_ids, no CI diff. |
| **Observability (structured logs, request_id, Sentry, metrics)** | ❌ | None. |

---

## 4. Risk list (ranked)

### Critical
1. **No migrations — production schema is unbuildable / not reproducible.** `alembic/versions/`
   empty; schema only created via `create_all` in tests (`tests/conftest.py:23`). Any deploy
   has no DB. *Fix:* generate the initial Alembic revision against Postgres, make it the
   source of truth; forbid `create_all` outside tests.
2. **Admin write endpoints are completely unauthenticated.** `POST/PATCH/DELETE /products`
   have no auth (`routers/products.py:52,74,96`). Anyone can create/modify/delete the catalog.
   *Fix:* auth layer + role guard (`OWNER/MANAGER`) before any write ships publicly. (Noted in
   an existing `ponytail:` comment at `routers/products.py:9`.)
3. **`CORS allow_credentials=True` with `allow_methods=["*"]`/`allow_headers=["*"]`.**
   `main.py:14-17`. Credentialed CORS with wildcards is fragile and over-broad once cookie
   auth lands. *Fix:* explicit methods/headers; keep the origin allow-list (already present).

### High
4. **Default `JWT_SECRET="dev-only-change-me"` in code and `.env.example`.** `config.py:23`.
   If an env var is missing in prod, the app silently runs with a known secret. *Fix:*
   fail-fast at startup in non-dev if secret is default/empty.
5. **No server-side pricing / checkout yet — but the contract demands it.** When `/cart/quote`
   and `/checkout` are built, prices must be recomputed server-side from IDs (spec §4C). This
   is the #1 thing to get right the first time; flagged now so it's never built the wrong way.
6. **Stripe idempotency ledger exists but no webhook verification path.** `StripeEvent`
   (`models.py:299`) implies intent but there's no signature-verifying endpoint. Building
   webhooks without `stripe.Webhook.construct_event` + event-id dedupe would be a money bug.
7. **`OrderStatus` enum diverges from spec** (`models.py:59-71`). Shipping lifecycle logic on
   the current enum then changing it is a breaking migration. *Fix:* reconcile the enum before
   any order logic is written.

### Medium
8. **`pytest` (as documented in CLAUDE.md) fails** — `ModuleNotFoundError: No module named
   'app'`. Only `PYTHONPATH=. python -m pytest` works; no `pythonpath`/`rootdir` config in
   `pyproject.toml`. *Fix:* add `[tool.pytest.ini_options] pythonpath = ["."]`.
9. **Tests run on SQLite, prod is Postgres 16.** `tests/conftest.py:18`. Divergence hides
   Postgres-only behaviour (enums, `FOR UPDATE`, server defaults, JSONB, constraints). *Fix:*
   add Postgres-backed integration tests (testcontainers or a test DB) before relying on DB
   constraints for correctness.
10. **No pagination ceiling pattern beyond products; no filtering/sorting whitelist.** Spec §3
    requires max page size + whitelists on every list endpoint.
11. **Error envelope incomplete:** no `request_id`, 422 validation errors bypass the envelope
    (`main.py:22`). Frontend expects one consistent shape.
12. **`get_sessionmaker` is `@lru_cache`’d on a module-global `settings`** (`db.py:14`) — fine
    now, but makes per-test engine swapping rely on dependency override only; acceptable.

### Low
13. `DeliveryZone.cap_prefix` is a 3-char prefix (`models.py:184`) but spec wants an explicit
    Rome CAP range 00118–00199 (configurable). Prefix `001` over-matches.
14. No `updated_at` trigger at DB level (app-side `onupdate` only) — fine for now.
15. `seed.py` relies on `get_sessionmaker()` hitting a real Postgres; no guard if DB absent.

**Security positives:** no money-as-float anywhere (all `Integer` cents — `models.py` passim);
no secrets committed (only empty/dev placeholders); timestamps are timezone-aware UTC
(`models.py:39,utcnow`); no client-price-trust code exists yet because checkout doesn't exist.

---

## 5. Contract check vs frontend (authoritative source: MSW handlers)

The frontend currently runs **entirely on mocks** (`packages/mocks/src/handlers.ts`, MSW).
Its *generated* client (`packages/api-client/src/schema.ts`) covers only 4 paths; its
hand-written clients (`apps/storefront/src/lib/api.ts`, `apps/admin/src/lib/api.ts`) and the
MSW handlers describe the **full** expected surface. All under base `/v1`.

**Differences that will bite:**

- **Prefix:** frontend calls `/v1/...`; backend serves `/products` (no `/v1`, no `catalog/`).
- **Product shape mismatch:** frontend `Product` = `{slug, name, subtitle, occasion, category,
  tags, images, variants[]}` with localised single `name` and tiered `variants`
  (`tier: STANDARD|PREMIUM|LUXURY`, `is_default`, `same_day`, `exact_time`, `images`). Backend
  returns `{id, name_it, name_en, base_price_cents, ...}` with a flat price and a non-tiered
  variant model. **Not interchangeable.**
- **Locale:** frontend sends `?locale=it|en` expecting a localised payload; backend has no
  locale handling.
- **Quote contract (must match exactly):** `POST /v1/cart/quote` →
  `{subtotal_cents, delivery_cents:0, time_fee_cents, total_cents, currency:"EUR"}`. Time fees
  per `packages/mocks/src/quote.ts`: `window=500`, `exact=900`, `standard/courier=0`;
  `delivery_cents` always `0` (all-in). Backend must reproduce this.
- **Endpoint surface the frontend already calls (none exist in backend):**
  public — `/v1/catalog/{products,products/:slug,occasions,addons}`,
  `/v1/delivery/{check,slots}`, `/v1/cart/quote`, `/v1/checkout`,
  `/v1/orders/track/:token`, `/v1/content/{reviews,stats,cities,journal}`,
  `/v1/config/{business,settings}`, `/v1/pay/:token` (+`/intent`), `/v1/verify`.
  admin — `/v1/admin/dashboard`, `/orders` (+`/:id` + transition actions + `/photo`),
  `/products` (+`/:slug`, `/bulk-price`), `/uploads/sign`,
  `/payments` (+`/held`, `/:id/{capture,cancel-hold,refund}`, `/refunds`,
  `/reports/monthly`), `/payouts`, `/disputes`, `/insights/seo`, `/settings`,
  `/payment-requests` (+ `/:id/{cancel,resend,duplicate,pdf}`, PATCH, POST).
- **Spec §8 vs real frontend disagree** on content routes: §8 lists `/content/faqs`,
  `/content/business`; the real frontend uses `/content/{reviews,stats,cities,journal}` and
  `/config/{business,settings}`. **The running frontend is the source of truth** — build to
  the MSW handlers, record the deviation from §8 in an ADR.

**Net:** there is currently **no contract overlap** — the one implemented area (`/products`)
is at the wrong path with the wrong shape. Nothing the frontend calls works against this
backend today. (This is expected for a scaffold; it just means "fix endpoints" = "build the
contract from near-scratch", not "tweak existing ones".)

---

## 6. Tooling state (actually run, 2026-11-20)

| Tool | Result |
|---|---|
| `ruff check .` | ✅ All checks passed. |
| `mypy app` (strict) | ✅ Success, no issues in 11 files. |
| `pytest` (as documented) | ❌ Fails — `ModuleNotFoundError: No module named 'app'`. |
| `PYTHONPATH=. python -m pytest` | ✅ 11 passed in 0.34s. |
| `pip-audit` | ✅ No known vulnerabilities. |
| Coverage | Not measured (no `pytest-cov` installed). Tests cover only health + products CRUD; **critical paths untested** (there are none yet). |
| CI (GitHub Actions) | ❌ None in this repo. |
| Docker | ✅ `backend/Dockerfile` + root `docker-compose.yml` (postgres 16 + redis + api). |
| `render.yaml` | ❌ Not present. |
| Pre-commit | ❌ Not present. |
| Dependency versions | Runtime deps are lower-bound pins only (`>=`); no lockfile. Env runs Python **3.14** though `pyproject` targets 3.12. |

---

## 7. Summary

The backend is a clean, well-typed **scaffold** (good: integer-cents money, tz-aware UTC,
typed, lint/type clean, no committed secrets) with **one** working feature (Products CRUD).
Against the target spec it is ~7% complete. The two things that make it "not production" are
structural, not cosmetic: **no migrations** (no reproducible schema) and **no auth** (admin
writes are open). Everything money-, delivery-, order-, and payment-related is unbuilt — which
is good news for correctness, because the high-risk code (pricing, webhooks, slot races) can
be built right the first time rather than fixed. See `PLAN.md` for the sequenced build-out.
