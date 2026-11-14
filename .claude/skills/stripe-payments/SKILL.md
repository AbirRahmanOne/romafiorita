---
name: stripe-payments
description: Use when working on payments, PaymentIntents, Stripe webhooks, refunds, disputes, or the admin payments/payouts views.
---

# Stripe payments

EUR only. Statement descriptor **`ROMAFIORITA`**. Payment Element on the storefront (card,
Apple Pay, Google Pay, PayPal via Stripe), 3D Secure, Radar enabled.

## Creating payments

- Create a **PaymentIntent** server-side with `currency=eur` and the amount **recomputed
  server-side** from the cart + delivery fees. **Never trust client amounts.**
- Pass an **idempotency key** on PaymentIntent creation (e.g. keyed to the cart/order draft)
  so retries don't double-charge.
- Return only the client secret to the browser; the client confirms via Payment Element.
- Let Stripe/Radar + 3DS handle risk; don't build custom risk logic.

## Webhooks (`/webhooks/stripe`)

1. **Verify the signature** with the endpoint secret. Reject if it fails.
2. **Idempotent processing:** store every event id in `StripeEvent`; if seen before, ack and
   skip. Process inside a DB transaction.
3. Return 2xx fast; offload slow work (emails, push) to arq.

Handle at minimum:
- `payment_intent.succeeded` → mark order paid, move PENDING_PAYMENT → NEW (see
  `order-lifecycle`), send confirmation.
- `payment_intent.payment_failed` → keep order unpaid, surface to customer.
- `charge.refunded` → record refund (full/partial), update order to REFUNDED if full.
- `charge.dispute.created` → flag order PROBLEM, alert admin.
- `payout.paid` → record payout for the admin payments view.

## Refunds (from admin)

- Full or partial, keyed by charge/PaymentIntent, with an idempotency key. A **decline**
  triggers an automatic **full** refund (see `order-lifecycle`).
- Record who/when/why; reflect status from the resulting `charge.refunded` webhook, not just
  the API call.

## Admin payments view

Via the Stripe API: payment history, balance, payouts, disputes. Plus CSV export and a
monthly accountant report. **Riders and florists never see payment data** (role gate).

## Local testing

- Test-mode keys; test cards (`4242 4242 4242 4242`; 3DS `4000 0027 6000 3184`).
- Stripe CLI to forward webhooks: `stripe listen --forward-to localhost:8000/webhooks/stripe`.
- Store keys/secrets in `.env` only (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`). Live keys
  only on Render (see `deployment-render`).
