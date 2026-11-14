---
name: testing-and-quality
description: Use when writing tests, setting up CI, or deciding what must be tested before calling work done. Defines the test pyramid, required tests, and definition of done.
---

# Testing & quality

## Test pyramid

Many fast **unit** tests (domain logic) → fewer **integration** tests (API + DB, webhooks) →
a small number of **E2E** tests (Playwright happy paths). Don't invert it.

## Required tests per area

- **Delivery rules** (`checkout-and-delivery-rules`): unit tests for the zone resolver and
  slot/cut-off logic with fixed `Europe/Rome` clocks — Rome before/after cut-off, exact-time at
  exactly `[3]h` and just under, slot at capacity, blocked date, peak-day cap, non-Rome Italian
  CAP → courier, non-Italian CAP rejected, DST boundary.
- **Stripe webhooks** (`stripe-payments`): tests with event fixtures — signature verify,
  idempotency (duplicate event id skipped), succeeded/failed/refunded/dispute/payout handling.
- **Order state machine** (`order-lifecycle`): every allowed transition passes, disallowed
  transitions rejected, each writes an `OrderEvent`, decline → full refund, auto-accept &
  timeout.
- **Money/i18n:** amounts are integer cents; no hard-coded user-facing strings (lint/check).

## E2E happy path (Playwright)

`home → product → exact-time checkout in Rome → confirmation → admin accept → delivered.`
Run against test-mode Stripe.

## Tooling

- Web (Next.js) & Admin (Vite React SPA): **Vitest** (unit/component) + **Playwright** (E2E).
  Admin E2E runs against the built SPA (or its Vite dev server) with the API mocked or in
  test mode.
- API: **pytest** + **httpx** (async client), test DB per run.
- Lint/type: **ESLint + Prettier** (TS, no `any`); **Ruff + mypy** strict on API app code.
- **Pre-commit hooks** run lint + format.

## CI (GitHub Actions, every PR)

`lint → typecheck → test` for all apps. PR cannot merge red. Keep PRs small.

## Definition of done

- Lint + typecheck + tests green locally and in CI.
- Area-required tests above are present.
- WCAG AA, 44px targets, visible focus, colour never the only signal.
- Strings localised (it + en). Money in cents. Times UTC / Europe/Rome.
- Relevant skill updated if a convention changed.
