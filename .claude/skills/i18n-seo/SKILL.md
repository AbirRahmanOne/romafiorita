---
name: i18n-seo
description: Use when working on translations, locale routing, metadata, structured data, sitemaps/robots, landing pages, or Core Web Vitals in apps/web.
---

# i18n & SEO

This skill is for the **storefront (`apps/web`, Next.js App Router)** — the only app that is
indexed. The admin (`apps/admin`) is a Vite React SPA behind login with **no SEO**; it still
needs i18n (see note at the end) but none of the SEO rules below.

Languages **it** + **en**. URLs `romafiorita.com/it/...` and `/en/...`. **No auto-redirect by
location** — offer an IT|EN switcher instead. Canonical host: `https://romafiorita.com`.

## next-intl

- Messages in `apps/web/messages/it.json` and `messages/en.json`, same key structure in both.
- **No hard-coded user-facing strings** — ever. Use the `t()` API; interpolate values, don't
  concatenate (plural/gender rules differ).
- Italian runs **~25% longer** than English — layouts must flex (no fixed-width buttons/labels,
  no truncation of meaningful text).
- Format dates, times and money via locale-aware formatters. Money: integer cents → EUR.

## Localised slugs

Translate slugs, don't just prefix a locale. Keep a slug map per locale.

```
/en/flower-delivery-rome   ↔  /it/consegna-fiori-roma
/en/same-day-flowers-rome  ↔  /it/fiori-domicilio-roma-oggi
```

## Metadata (Next Metadata API)

- Per-page `title`, `description`, canonical on `https://romafiorita.com`, OpenGraph/Twitter.
- Default titles:
  - EN: `Roma Fiorita — Flower Delivery in Rome & Italy`
  - IT: `Roma Fiorita — Consegna Fiori a Roma e in tutta Italia`
- **hreflang** on every page: `it`, `en`, and `x-default`. Each page links to its counterpart
  locale via the slug map.

## Rendering strategy (App Router)

- **Product, occasion and city/neighbourhood pages:** static generation with revalidation
  (**ISR**) — `generateStaticParams` + `revalidate`. Fast, crawlable, cheap.
- **Cart / checkout:** dynamic (no caching, per-request).
- Metadata via **`generateMetadata`**; sitemap via **`sitemap.ts`**; robots via **`robots.ts`**
  (don't hand-maintain static `sitemap.xml`/`robots.txt`).

## robots & sitemaps

- `sitemap.ts` emits per-locale entries (both URLs for each page), regenerated on revalidate.
- `robots.ts` must **allow**: `OAI-SearchBot`, `ChatGPT-User`, `Claude-SearchBot`,
  `Claude-User`, `PerplexityBot`, `Googlebot`, `Bingbot`. Point to the sitemap.

## JSON-LD (structured data)

Emit on relevant pages:
- **Organization** — name "Roma Fiorita", url, logo, `sameAs` (socials).
- **Florist / LocalBusiness** — Rome address (placeholder until supplied), geo, hours.
- **Product + Offer** — price EUR, availability, `shippingDetails` (Italy-only).
- **BreadcrumbList** — category → product trail.

## Landing pages

- Rome neighbourhood pages (Trastevere, Prati, Parioli, EUR, Centro Storico…) and other
  Italian cities.
- **Real data only** — real delivery info, real copy. **No thin or duplicate pages.** If a
  neighbourhood has nothing distinct to say, don't ship a page for it.

## Core Web Vitals targets

- LCP < 2.5s · INP < 200ms · CLS < 0.1.
- SSR/ISR public pages; `next/image` with explicit sizes (no CLS); preload fonts via
  `next/font`; minimal client JS on content pages.

## Admin i18n (no SEO)

The admin SPA still shows IT/EN — use a client i18n lib (e.g. `react-i18next`) with the same
message-key discipline (no hard-coded strings, `it` + `en`). None of the SSR/metadata/sitemap
rules apply there.
