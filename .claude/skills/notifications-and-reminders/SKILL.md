---
name: notifications-and-reminders
description: Use when building transactional emails, occasion reminders, admin Web Push, or the (flagged) WhatsApp add-on.
---

# Notifications & reminders

Transactional email via **Resend** with **React Email** templates. From
`ordini@romafiorita.com` (display "Roma Fiorita"), reply-to `info@romafiorita.com`. Sending
domain `romafiorita.com` with SPF/DKIM/DMARC (see `deployment-render`). Dispatched via **arq**
after the DB transaction commits.

## Email templates (branded, IT + EN)

Each exists in both locales; send in the sender's chosen locale.

| Template | Trigger |
|---|---|
| order confirmation | → NEW (paid) |
| accepted | → ACCEPTED |
| bouquet photo | → PHOTO_SENT |
| out for delivery | → OUT_FOR_DELIVERY |
| delivered | → DELIVERED |
| declined / refunded | → DECLINED / REFUNDED |
| reminder | occasion reminder job |
| abandoned cart | cart left unpaid past a threshold |

Rules: Roma Fiorita branding, all-in prices, order number `RF-YYYY-NNNNN`, link to the
tracking page. **No hard-coded copy** — localised strings only. Honour hide-sender in
recipient-facing content.

## Occasion reminders

- Remind senders **7 days** and **2 days** before saved important dates (birthdays,
  anniversaries, and calendar occasions like Festa della Donna 8 Mar, Festa della Mamma).
- Scheduled via **arq** cron jobs; store sent state so a reminder goes out once per occurrence.
- Requires marketing consent (see `legal-and-compliance-italy`).

## Admin Web Push

New-order alerts to the admin (plus SSE + sound in-app). Store push subscriptions per staff
device; fan out via arq. Respect notification-recipient settings.

## WhatsApp (later)

WhatsApp messages are a **later add-on behind a feature flag** — do not build or enable
unless the flag is explicitly turned on.
