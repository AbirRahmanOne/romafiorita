# Roma Fiorita Backend — Remediation Plan (Phase 0 output)

Derived from `AUDIT.md` and `prompt.txt` §10. Small, PR-sized steps. Each step: **what it
changes · risk · how it's tested · how it rolls back.** Suite stays green after every step.
Phases end with a **STOP** for review (per working rules).

Because the backend is a scaffold (not a legacy system to protect), "characterization tests"
only matter for the one real area (Products). Elsewhere we build forward with tests-first.

---

## Phase 1 — Safety net (no behaviour change)  → STOP

| Step | Changes | Risk | Test | Rollback |
|---|---|---|---|---|
| 1.1 | Fix `pytest` invocation: add `[tool.pytest.ini_options] pythonpath=["."]`. | Low | `pytest` now works without `PYTHONPATH`. | revert pyproject. |
| 1.2 | **Generate the initial Alembic migration** from current models against Postgres 16; verify `upgrade head` + `downgrade base` on an empty DB. | Med (first real migration) | migration round-trip in CI. | delete revision. |
| 1.3 | Add Postgres integration test harness (testcontainers or a test DB) alongside the SQLite unit tests. | Low | existing tests pass on PG too. | keep SQLite path. |
| 1.4 | Characterization tests for the only live behaviour: `/products` list/get/create/patch/delete + error envelope. | Low | snapshot current responses. | n/a. |
| 1.5 | OpenAPI snapshot: commit `openapi.json` + a test that fails on unintended diff (oasdiff later). | Low | snapshot test. | delete snapshot. |
| 1.6 | GitHub Actions: ruff + mypy + pytest + pip-audit + migration round-trip. | Low | CI green. | delete workflow. |

---

## Phase 2 — Critical fixes (security & money foundations)  → STOP

Addresses AUDIT risks #2, #3, #4, #7, #11.

| Step | Changes | Risk | Test | Rollback |
|---|---|---|---|---|
| 2.1 | **Config fail-fast:** reject default/empty `JWT_SECRET` (+ required secrets) outside dev at startup. | Low | startup test with/without env. | revert validator. |
| 2.2 | **CORS tighten:** explicit methods/headers; keep origin allow-list; add security headers + request-size limit middleware. | Low | CORS/headers tests. | revert middleware. |
| 2.3 | **Error envelope complete:** `request_id` on every error; handler for `RequestValidationError` (422) and a catch-all 500, all in `{error:{code,message,details,request_id}}`. | Low | error-shape tests. | revert handlers. |
| 2.4 | **Reconcile `OrderStatus` enum** to spec (add `AWAITING_PHOTO/APPROVED/PARTIALLY_REFUNDED/PAYMENT_REQUESTED/EXPIRED`, drop/rename `PREPARING`) — now, before any order logic exists, so it's a cheap migration. | Low (no data yet) | migration + enum test. | down-migration. |
| 2.5 | **Auth layer:** argon2 password hashing, short-lived JWT + rotating refresh in httpOnly/Secure/SameSite=Lax cookies scoped to `.romafiorita.com`, CSRF for cookie mutations, login rate-limit/lockout. `deps.py` with `current_user` + role guards. | **High** | per-role allow/deny tests; cookie/CSRF tests. | feature-flag / revert router. |
| 2.6 | **Guard the existing admin product writes** behind `OWNER/MANAGER` (removes the open-write risk + the `ponytail:` TODO in `routers/products.py:9`). | Med | 401/403 tests. | revert guard. |

> **Blocked on your confirmation before 2.x ships:** cookie domain in non-prod, lockout
> thresholds. Sensible defaults will be used and recorded in an ADR unless you say otherwise.

---

## Phase 3 — Structure  → STOP

| Step | Changes | Risk | Test |
|---|---|---|---|
| 3.1 | Introduce `/v1` router tree (`api/v1/{public,admin,webhooks}`); **keep `/products` working** as a deprecated alias with a sunset note. | Med | both paths tested. |
| 3.2 | App factory + lifespan (startup config validation, engine/redis init, graceful shutdown). | Low | boot test. |
| 3.3 | `core/` (config, logging=structured JSON w/ request_id, security, errors, ids=`RF-YYYY-NNNNN` + token helpers, time=Europe/Rome + DST-safe, money). | Low | unit tests per helper (DST switches!). |
| 3.4 | `/healthz` (liveness) + `/readyz` (DB+Redis+config). | Low | endpoint tests. |
| 3.5 | Seed `domain/`, `services/`, `repositories/`, `integrations/` skeletons (interfaces only, no speculative impls). | Low | import tests. |

---

## Phase 4 — Features to spec (the bulk; satisfies the frontend contract)  → STOP

Build to the **MSW-handler contract** (§5 of AUDIT), each sub-area its own PR.

| Step | Changes | Key correctness bar |
|---|---|---|
| 4.1 | **Catalog w/ tiers:** migrate Product/Variant to 3-tier `STANDARD/PREMIUM/LUXURY` (unique `(product_id,tier)`, exactly-one `is_default`, ≥1 active, DB checks); `?locale` localisation + fallback; `/v1/catalog/{products,products/:slug,occasions,addons}`. | shape matches `schema.ts`/`handlers.ts`. |
| 4.2 | **Delivery engine (pure `domain/`, ~100% tested):** CAP→zone (Rome 00118–00199 configurable, else NATIONAL, else reject), delivery types, cut-offs, exact-notice, fees, DST-safe 15-min slots 07:00–23:45, blocked dates; `/v1/delivery/{check,slots}` w/ Europe/Rome + ISO times. | DST March/Oct tests; cut-off/blocked-date tests. |
| 4.3 | **Pricing + `/v1/cart/quote`:** server-side only, IDs in → cents out, **never trust client prices**; match `quote.ts` fees (window 500 / exact 900 / else 0, delivery 0). Discount codes model. | recompute test; client-price-ignored test. |
| 4.4 | **Slot booking (race-safe):** reservation table + `SELECT … FOR UPDATE`/atomic counter; reservations expire after N min. | **concurrency test: 2 checkouts can't overbook.** |
| 4.5 | **Orders + state machine (`domain/`, table-driven):** full status set, per-transition roles/guards/side-effects, `OrderEvent` audit, order-number `RF-YYYY-NNNNN`, tracking token; `/v1/orders/track/:token` public-safe; admin order list/detail + transition actions + `/photo`. | guard tests (e.g. photo required before PHOTO_SENT); IDOR tests. |
| 4.6 | **Stripe (behind `PaymentProvider` interface):** manual-capture PaymentIntent (website) / auto (requests), metadata, idempotency keys; `/v1/webhooks/stripe` with **signature verify + event-id dedupe** (uses existing `stripe_events`), async-fast-2xx; admin money actions (capture/cancel/refund, audited, idempotent). | webhook fixture replay (idempotent); capture/cancel/refund flows. |
| 4.7 | **Payment requests:** request model + 32B token stored **hashed**, expiry; `/v1/pay/:token` (+`/intent`, auto-capture), `/v1/verify` (rate-limited, no leaks); branded PDF (WeasyPrint, **not** labelled “fattura”), wa.me + email text; admin CRUD + resend/duplicate/cancel/pdf. | token expiry/single-use; verify no-leak test. |
| 4.8 | **Admin payments API + content/settings:** payments list/held/refunds/payouts/balance/disputes/monthly CSV; `/v1/content/{reviews,stats,cities,journal}`, `/v1/config/{business,settings}`, `/v1/admin/settings` (zones/fees/slots/blocked/capacity/recipients/business identity — nullable). | contract shape tests. |

---

## Phase 5 — Jobs & integrations  → STOP

arq + Redis workers; Resend emails (IT/EN, versioned, retry/backoff/dead-letter); occasion
reminders (7d/2d) + abandoned-checkout + request-reminder crons; SSE `/v1/admin/orders/stream`
via Redis pub/sub (multi-instance, heartbeat, authed) + Web Push; R2 signed-PUT uploads +
EXIF-strip + thumbnails; Google Search Console daily cache; GDPR retention jobs. WhatsApp
adapter behind an off-by-default flag.

## Phase 6 — Hardening  → FINAL REPORT

Indexes for frequent filters (`orders(status,delivery_date)`, `orders(order_number)`,
`payments(created_at)`, slots(date)); fix N+1 with `selectinload`; pool tuning + statement
timeouts; Redis caching for catalog/settings + ETag/Cache-Control; Sentry (PII-scrubbed) +
metrics; k6/Locust load test on checkout + slots (Valentine burst) with a report; GDPR
export/delete endpoints; `render.yaml` (Frankfurt, pre-deploy migrations, health checks, cron,
no sleeping); docs (`architecture.md`, `runbook.md`, `api-changelog.md`, ADRs) + the 14 skills;
final `openapi.json` publish + `oasdiff` breaking-change gate for the frontend.

---

## Decisions needed from you (placeholders until confirmed — `prompt.txt` §11)

Rome CAP list/range · same-day cut-offs per zone · window/exact fees · slot capacity
per-slot/per-rider · reservation + payment-request expiry hours · GDPR retention period ·
business identity (legal name, address, P.IVA, PEC, phone, WhatsApp). Where unconfirmed, code
uses documented defaults and an ADR records the assumption.

## Cross-cutting rules (every PR)

Conventional Commits · suite green · two-step migrations for any drop/rename (expand→migrate→
contract) + your approval · no destructive commands on non-local DBs · docs/skills/openapi.json
updated in the same commit · when spec and code disagree, ADR or ask.
