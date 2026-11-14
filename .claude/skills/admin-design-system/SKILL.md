---
name: admin-design-system
description: Use when building or changing any admin dashboard (apps/admin) UI — layout, tables, KPI cards, charts, status badges, forms, or empty/loading/error states.
---

# Admin design system — Blue & white theme

For **`apps/admin`** — a **Vite + React SPA** (TanStack Router or React Router, TanStack Query
+ TanStack Table, Recharts, shadcn/ui). No SSR. All data is fetched client-side through
`packages/api-client` wrapped in **TanStack Query** (cache, loading/error state, refetch).

Clean, calm, data-first, **highly usable on a phone**. WCAG AA, 44px tap targets, visible
focus, **colour never the only signal**.

## Tokens

From `packages/ui-tokens` (admin theme).

| Token | Hex | Use |
|---|---|---|
| primary | `#2563EB` | actions, active nav |
| primary-hover | `#1D4ED8` | hover/active |
| primary-soft | `#DBEAFE` | highlights, selected rows |
| background | `#F5F8FF` | page background |
| surface | `#FFFFFF` | cards, tables |
| sidebar | `#0F2A5F` | navy sidebar, white text |
| ink | `#0F172A` | primary text |
| ink-muted | `#475569` | secondary text |
| border | `#E2E8F0` | borders/dividers |

**Typography:** Inter everywhere. **Tabular numbers** in tables and KPIs.

## Status colours (always with a text label)

| Status | Colour |
|---|---|
| new | blue |
| accepted | indigo |
| preparing | amber |
| out-for-delivery | violet |
| delivered | green |
| cancelled / refunded | slate / red |

Render as a badge = dot/background colour **plus** the status word. Never colour alone.

## Layout

- **Navy sidebar** `#0F2A5F`, white text, wordmark "Roma Fiorita · Admin". Nav: Dashboard,
  Orders, Delivery Schedule, Products, Customers, Payments, Analytics, Settings. Active item
  uses `primary`.
- **Top bar:** page title, search, notification bell (new-order count), user menu.
- Content on `background`, cards on `surface` with `border`.
- Hide nav items the role can't access (see `admin-dashboard-features` for role matrix).

## Components

- **Tables** (TanStack Table): sticky header, sortable, tabular numbers, row actions, pagination
  or virtualised for long lists. On mobile, collapse to stacked cards.
- **KPI card:** big tabular number, label, delta vs. previous period (↑/↓ + text, not
  colour-only).
- **Charts** (Recharts): accessible labels, legend, EUR formatted; avoid colour-only series
  distinction (use labels/patterns).
- **Status badge:** see table above.
- **Forms:** labelled inputs, inline validation, 44px controls, destructive actions confirmed.

## Mobile — order inbox

- Must be fully usable one-handed on a phone.
- New orders stream in (SSE); show a prominent card per order with Accept / Accept-with-change
  / Decline as large tap targets.
- Audible + push alert on new order; a visible unread count that clears on view.

## Empty / loading / error states (required on every screen)

- **Empty:** friendly line + what to do next (e.g. "No orders yet today").
- **Loading:** skeletons matching final layout (avoid layout shift).
- **Error:** plain message + retry; never a blank screen. Log details for staff, show a
  human message.
