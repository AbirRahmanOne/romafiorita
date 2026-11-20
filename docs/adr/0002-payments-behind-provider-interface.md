# ADR 0002 — Defer Stripe behind a PaymentProvider interface

**Status:** Accepted · **Date:** 2026-11-20 · **Phase:** 4

## Context

`prompt.txt` §E specifies full Stripe (manual-capture checkout, signature-verified
webhooks, refunds). The project `CLAUDE.md` says "Payments (Stripe) are out of scope for
this version." These conflict. The frontend's `/v1/checkout` expects a `client_secret`,
so checkout can't just omit payments entirely.

## Decision

Build everything *around* payments, with payments behind a thin `PaymentProvider`
interface and a **mock adapter** as the default:

- `PaymentProvider` interface: `create_intent(amount, capture_method, metadata, …)`,
  `capture`, `cancel`, `refund`, `construct_webhook_event`.
- Default `MockPaymentProvider`: returns deterministic fake intents/`client_secret`
  (e.g. `pi_mock_…`), records calls in memory/DB so order flows and the frontend work
  end to end without a Stripe account.
- Checkout (manual capture), order state machine, payment-requests, and admin order
  operations are all built against the interface — no live money moves.
- The `StripeProvider` adapter (and `/v1/webhooks/stripe` with signature verification +
  idempotency via the existing `stripe_events` table) is a **drop-in later change**:
  swap the provider binding, add the webhook route. No rework of orders/requests.

Selected by the product owner on 2026-11-20 over "build full Stripe now" and "orders
only, no payment-shaped code".

## Consequences

- The storefront checkout flow is testable and demo-able now; money paths are structured
  but inert.
- `CLAUDE.md`'s "no payments" note stays true (no live payments); update it to name the
  `PaymentProvider` interface when the orders/checkout slice lands.
- Going live with Stripe is a bounded, well-scoped follow-up, not a refactor.
