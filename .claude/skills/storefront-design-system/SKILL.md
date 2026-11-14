---
name: storefront-design-system
description: Use when building or changing any storefront (apps/web) UI — colours, typography, components, photography, or the trust elements on product/cart/checkout.
---

# Storefront design system — Pink theme

For **`apps/web`** (Next.js App Router) — the `next/font` / `next/image` references below are
Next.js APIs and apply to the storefront only (the admin is a Vite SPA, see
`admin-design-system`).

Romantic, elegant, warm, premium-but-friendly; a feeling of Roman spring. WCAG AA, 44px tap
targets, visible focus rings, **colour never the only signal**. Respect
`prefers-reduced-motion`.

## Tokens

Defined in `packages/ui-tokens` and exposed as both a Tailwind theme and CSS variables.

| Token | Hex | Use |
|---|---|---|
| primary | `#C2185B` | buttons, links (white text passes AA) |
| primary-hover | `#A3134C` | hover/active |
| primary-soft | `#F8BBD0` | badges, highlights |
| blush | `#FCE4EC` | section backgrounds |
| background | `#FFF7FA` | page background |
| surface | `#FFFFFF` | cards |
| ink | `#3A1F2B` | headings, body (never pure black) |
| ink-muted | `#6B4E5A` | secondary text |
| border | `#F3D1DE` | borders/dividers |
| success | `#2E7D5B` | "fresh", confirmations |
| warning | `#B26A00` | warnings |
| danger | `#C62828` | errors |

```css
:root {
  --rf-primary: #C2185B; --rf-primary-hover: #A3134C; --rf-primary-soft: #F8BBD0;
  --rf-blush: #FCE4EC; --rf-bg: #FFF7FA; --rf-surface: #FFFFFF;
  --rf-ink: #3A1F2B; --rf-ink-muted: #6B4E5A; --rf-border: #F3D1DE;
  --rf-success: #2E7D5B; --rf-warning: #B26A00; --rf-danger: #C62828;
}
```

## Typography & wordmark

- Headings + wordmark: **Cormorant Garamond** 600/700. Body/UI: **DM Sans** 400/500/700.
  Load via `next/font`.
- Wordmark "Roma Fiorita" is the temporary logo (until a real logo is supplied): Cormorant
  Garamond, in `ink` or `primary` on light backgrounds, white on `primary`. Never stretch or
  recolour arbitrarily.
- Scale (suggested): display 48/56, h1 40/48, h2 32/40, h3 24/32, body 16/26, small 14/22.

## Style

- Radius: cards 12–20px; buttons full-pill. Soft shadows. Generous whitespace.
- Large real product photography; subtle Roman touches (delivery photos around Rome).
- Subtle motion only.

## Components (rules)

- **Button** — pill, `primary` fill + white text, `primary-hover` on hover; min height 44px;
  visible focus ring; variants: primary / outline / ghost.
- **Card** — `surface`, 12–20px radius, soft shadow, `border`.
- **Badge** — `primary-soft` bg + `ink` text, or status colour + label.
- **Input** — 44px min, `border`, focus ring in `primary`; always a visible label.
- **DatePicker** — prefer native `<input type="date">` where it serves; locale-aware; disable
  blocked/past dates (see `checkout-and-delivery-rules`).
- **TimeChip** — selectable chip for a slot/window; selected = `primary` fill; shows fee if
  any; disabled when capacity full.
- **Stepper** — checkout progress (cart → details → delivery → payment); current step labelled,
  not colour-only.
- **ProductCard** — image (`next/image`), name, all-in price, occasion/size, add-to-cart.
- **TrustStrip** — row of trust promises (photo before delivery, all-in price, on-time).
- **CountdownTimer** — same-day cut-off countdown; accessible live text, not colour-only.

## Trust elements (required)

These must appear on **product, cart and checkout** pages:

- "We send a photo of your real bouquet before delivery."
- All-in price, **no hidden fees** (fees shown inline when a delivery option adds one).
- On-time delivery promise + same-day cut-off countdown for Rome.
- Secure payment (Stripe) + accepted methods.

## Accessibility checklist

- [ ] AA contrast for all text/controls.
- [ ] Every interactive element ≥44px, visible focus ring.
- [ ] Status/feedback has a text label, not colour alone.
- [ ] Images have meaningful `alt`; decorative images `alt=""`.
- [ ] All copy via next-intl (`it` + `en`); layout flexes for ~25% longer Italian.
