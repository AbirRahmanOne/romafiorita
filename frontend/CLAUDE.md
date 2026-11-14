# frontend — Next.js app

One Next.js App Router app (React 19, TypeScript strict, Tailwind v4, next-intl) serving
**both**: the public **storefront** (pink theme, SSR/SSG, SEO) and the **/admin** dashboard
(blue theme, behind login, not indexed).

Read before working here: **`storefront-design-system`**, **`admin-design-system`**,
**`admin-dashboard-features`**, **`i18n-seo`**. (Those skills predate this layout — the
admin is `/admin/*` routes here, not a separate Vite SPA, and tokens live in
`src/app/globals.css`, not a `packages/ui-tokens`.)

## Layout

```
src/app/[locale]/(site)/      storefront pages (Header/Footer/CookieBanner, pink)
src/app/[locale]/admin/(app)/ admin pages (Sidebar/Topbar, blue)
src/app/[locale]/admin/login/ admin login (bare)
src/app/robots.ts, sitemap.ts
src/i18n/                      routing, navigation, request config (next-intl)
src/components/{ui,storefront,admin}
src/lib/api.ts                typed API client (fetch) + helpers
src/lib/api-types.ts          generated from OpenAPI — DO NOT edit (npm run gen:api)
src/lib/                      utils (cn, formatPrice), fonts, occasions
messages/{it,en}.json         all UI copy — no hard-coded strings
```

## Rules

- Locale routes only: `/it/...`, `/en/...`. No auto-redirect (see `src/i18n/routing.ts`).
- **No hard-coded user-facing strings** — add keys to `messages/it.json` + `messages/en.json`.
- Prices are integer cents → `formatPrice(cents, locale)` (EUR). Never compute amounts client-side.
- Two themes via CSS vars in `globals.css`: `rf-*` (pink storefront), `ad-*` (blue admin).
- Fonts via `next/font` (Cormorant + DM Sans storefront; Inter admin).
- Pages read `params` with `use(params)` + `setRequestLocale(locale)` so they stay static.
- Dev: `npm run dev`. Verify: `npm run build && npm run lint && npm test`. API base: `NEXT_PUBLIC_API_URL`.
- Data: storefront catalog + admin Products read/write the backend via `src/lib/api.ts`.
  Regenerate types after a backend schema change: `npm run gen:api` (backend must be running).
- Admin screens other than Dashboard/Products are placeholders until their backend lands.
- Cart is a client-side store (`src/lib/cart.tsx`, localStorage via `useSyncExternalStore`);
  checkout is a no-payment summary/confirmation.
- Product/hero images are static SVGs in `public/` mapped by `src/lib/images.ts` (swap for
  real R2 photography later; `next.config.ts` sets `dangerouslyAllowSVG`).
- **No Stripe / payments in this version.**
