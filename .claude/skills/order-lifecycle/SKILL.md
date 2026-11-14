---
name: order-lifecycle
description: Use when implementing order states, transitions, who can trigger them, side effects (emails/push/audit), accept-with-change, or auto-accept/timeout logic.
---

# Order lifecycle

## Order numbers

Format **`RF-YYYY-NNNNN`** (year + zero-padded sequence per year, e.g. `RF-2026-00042`).
Human-facing; distinct from the DB id.

## State machine

```
PENDING_PAYMENT ──paid──▶ NEW ──accept──▶ ACCEPTED ──▶ PREPARING ──▶ PHOTO_SENT
      │                                                                    │
      │                                                            out_for_delivery
      ▼                                                                    ▼
  (expire/fail)                                                    OUT_FOR_DELIVERY ──▶ DELIVERED
```

**Side states** (from NEW/ACCEPTED/PREPARING as applicable):
- `DECLINED` — shop declines → **automatic full refund** → effectively REFUNDED.
- `CANCELLED` — cancelled before fulfilment.
- `REFUNDED` — full/partial refund issued (see `stripe-payments`).
- `PROBLEM` — needs attention (dispute, delivery failure); recoverable to a normal state.

## Allowed transitions & roles

Roles: OWNER / MANAGER / FLORIST / RIDER (and `system` for automated).

| From → To | Who | Notes |
|---|---|---|
| PENDING_PAYMENT → NEW | system | on `payment_intent.succeeded` |
| PENDING_PAYMENT → CANCELLED | system | payment expired/failed |
| NEW → ACCEPTED | OWNER/MANAGER (or system if auto-accept) | start of fulfilment |
| NEW → DECLINED | OWNER/MANAGER | triggers full refund |
| ACCEPTED → PREPARING | OWNER/MANAGER/FLORIST | |
| PREPARING → PHOTO_SENT | OWNER/MANAGER/FLORIST | bouquet photo uploaded & sent |
| PHOTO_SENT → OUT_FOR_DELIVERY | OWNER/MANAGER/RIDER | rider assigned |
| OUT_FOR_DELIVERY → DELIVERED | RIDER/OWNER/MANAGER | |
| any active → PROBLEM | OWNER/MANAGER/system | |
| any active → CANCELLED/REFUNDED | OWNER/MANAGER | refund per policy |

Reject any transition not in this table. Enforce in the service layer, not the UI.

## Side effects per transition

Every transition writes an **`OrderEvent`** (audit log: actor, from, to, timestamp UTC,
note). Plus:

| Transition | Email (IT/EN, from ordini@) | Admin push |
|---|---|---|
| → NEW | order confirmation to sender | **new-order alert** |
| → ACCEPTED | "order accepted" | — |
| → PHOTO_SENT | bouquet photo email | — |
| → OUT_FOR_DELIVERY | "out for delivery" | — |
| → DELIVERED | "delivered" | — |
| → DECLINED | "declined + refund" | — |
| → REFUNDED | refund confirmation | — |

Emails/push are dispatched via arq (see `notifications-and-reminders`), after the DB
transaction commits.

## Accept-with-change flow

When the shop must substitute/adjust (stock, size), it proposes a change; the **sender must
approve** before fulfilment continues. If declined by sender → refund path. Record both the
proposal and the response as `OrderEvent`s.

## Auto-accept & timeout

- **Auto-accept** setting (per shop): NEW → ACCEPTED automatically, still logged as a `system`
  event.
- **Acceptance timeout:** if a NEW order isn't accepted within the configured window, raise an
  escalating **alert** (push + sound) so it isn't missed. Timeout window is a setting.
