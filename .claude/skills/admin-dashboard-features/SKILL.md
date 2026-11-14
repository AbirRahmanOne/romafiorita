---
name: admin-dashboard-features
description: Use when building admin screens — what each screen shows, the data it needs, and role-based visibility. Pair with admin-design-system for the look.
---

# Admin dashboard features

Roles: OWNER / MANAGER / FLORIST / RIDER. **Riders and florists never see payment data.**
Look & layout: see `admin-design-system`. Order actions: see `order-lifecycle`.

## Screens & data

### Dashboard (KPIs)
Today/this-week: orders count, revenue (EUR), orders by status, upcoming deliveries,
acceptance-timeout alerts, late-risk count. Tabular numbers, delta vs previous period.

### Orders inbox (real-time)
- Live new orders via **SSE** + **Web Push** + **sound**. Unread count in top bar.
- Per order: Accept / **Accept-with-change** / Decline (decline = auto full refund).
- Filter by status/zone/date; search by order number / recipient.

### Order detail
- Timeline from `OrderEvent` (audit log).
- **Upload bouquet photo** (→ R2) and send it (→ PHOTO_SENT email).
- **Assign rider** (Rome). **Refund** full/partial (OWNER/MANAGER only).
- **Print** branded Roma Fiorita card (sender's message) and delivery note.
- Recipient details, delivery type/slot, card message, hide-sender flag.

### Delivery schedule
- Day/week view by booked time; rider capacity per slot; **late-risk alerts**.
- Rome same-day/window/exact and national-courier dates. Europe/Rome times.

### Products CRUD
- **IT/EN fields side by side** (name, description). Sizes/variants, add-ons, availability.
- SEO fields (slug per locale, meta). **Image upload to R2** (signed).

### Customers & reminders · Discount codes
- Customer list + order history; saved recipients; important dates.
- Occasion **reminders** (7 & 2 days before). Discount code CRUD (type, value, limits, expiry).

### Payments (OWNER/MANAGER only)
- Stripe history, refunds, payouts, disputes. **CSV export** + monthly accountant report.

### Analytics
- Own sales data (from our DB) + **embedded Looker Studio** (GA4/Search Console/Ads).

### Settings
- Delivery **zones**, **fees**, **slots**/capacity, **blocked dates**, peak-day caps.
- Notification recipients, auto-accept + timeout window.
- **Staff & roles** (OWNER/MANAGER/FLORIST/RIDER).

## Role visibility matrix

| Screen | OWNER | MANAGER | FLORIST | RIDER |
|---|---|---|---|---|
| Dashboard | ✅ | ✅ | limited | limited |
| Orders inbox / detail | ✅ | ✅ | ✅ (no payment) | ✅ (assigned, no payment) |
| Delivery schedule | ✅ | ✅ | ✅ | ✅ (own) |
| Products | ✅ | ✅ | ✅ | ❌ |
| Customers / reminders / discounts | ✅ | ✅ | ❌ | ❌ |
| **Payments** | ✅ | ✅ | ❌ | ❌ |
| Analytics | ✅ | ✅ | ❌ | ❌ |
| Settings (incl. staff/roles) | ✅ | partial | ❌ | ❌ |

Enforce visibility **server-side** too (API role gate), not just by hiding UI.
