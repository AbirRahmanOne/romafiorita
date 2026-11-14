---
name: checkout-and-delivery-rules
description: Use when implementing or changing delivery zones, delivery types, time slots, cut-offs, blocked dates, fees, recipient options, or card messages in checkout.
---

# Checkout & delivery rules

Delivery is **Italy-only**. Zone and available delivery types are decided by the recipient's
**CAP** (postcode). `Europe/Rome` is the source of truth for all cut-off/slot logic; also
display the sender's local time.

## Zones by CAP

- **Rome (own riders):** CAP `001xx` (i.e. `00100`–`00199`). Same-day delivery.
- **Rest of Italy (courier):** every other valid Italian CAP. Next-day boxed bouquet, **date
  only**.
- Non-Italian CAP → not deliverable. Block at checkout with a clear message.

> CAP ranges, slot capacity, cut-off, fees and blocked dates are **admin-configurable
> settings**, seeded from the defaults below. Business logic reads them from the DB, not
> hard-coded constants.

## Delivery types

| Type | Zone | Timing | Fee |
|---|---|---|---|
| `ROME_SAME_DAY` | Rome | any time that day (standard) | none |
| `ROME_WINDOW` | Rome | a 2-hour window | `€[X]` |
| `ROME_EXACT` | Rome | exact time, ±15 min | `€[Y]` |
| `NATIONAL_COURIER` | rest of IT | a date | courier fee |

## Slots, capacity, cut-offs

- Time slots step in **15-minute** increments (Europe/Rome).
- **Capacity per rider per slot** — once a slot's booked riders are full, the slot is
  unavailable. Capacity is a setting.
- **Same-day cut-off `[14:00]`** (placeholder): orders for same-day Rome must be placed before
  cut-off; after that, earliest is next day.
- **Exact-time minimum notice `≥ [3]h` ahead** (placeholder): an exact time must be at least
  this far in the future.
- **Blocked dates** (holidays, closures) and **peak-day caps** (e.g. Valentine's, Festa della
  Donna, Festa della Mamma) reduce or close capacity. Honour both.

## Other checkout fields

- **Recipient address types:** residential, business/office, hospital, hotel, other — may
  affect delivery instructions.
- **"Recipient not home" options:** leave with neighbour / concierge / retry / call sender.
- **Card message:** free text with a max length (define in settings); strip/escape before
  print & email.
- **Hide-sender option:** anonymous delivery — sender name omitted from recipient-facing
  output.

## Decision table

| Recipient CAP | Now vs cut-off | Requested type | Result |
|---|---|---|---|
| `00187` | before 14:00 | `ROME_SAME_DAY` | ✅ today, standard |
| `00187` | before 14:00 | `ROME_EXACT` 17:30 | ✅ if ≥3h ahead & slot has capacity |
| `00187` | 14:30 | `ROME_SAME_DAY` | ❌ past cut-off → earliest tomorrow |
| `00187` | any | `ROME_EXACT` 2h ahead | ❌ under 3h notice |
| `00187` | any | any, slot full | ❌ slot at capacity → offer another |
| `00187` | blocked date | any | ❌ blocked → pick another date |
| `20121` (Milan) | any | `NATIONAL_COURIER` | ✅ next-day, date only |
| `20121` | any | `ROME_SAME_DAY` | ❌ wrong zone |
| `75001` (non-IT) | any | any | ❌ not deliverable |

## Test cases (must exist — see `testing-and-quality`)

Unit-test the zone resolver and slot/cut-off logic with fixed `Europe/Rome` clocks:
- Rome CAP before/after cut-off; exact-time at exactly 3h and just under; slot at capacity;
  blocked date; peak-day cap; non-Rome Italian CAP → courier; non-Italian CAP rejected; DST
  boundary day.
