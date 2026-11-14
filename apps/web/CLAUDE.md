# apps/web — Storefront

Customer storefront at **romafiorita.com**. Next.js App Router, TypeScript strict, Tailwind,
shadcn/ui, next-intl.

Read before working here: **`storefront-design-system`** (pink theme, components, trust
elements) and **`i18n-seo`** (routing, metadata, SEO). Touching checkout → also
**`checkout-and-delivery-rules`** and **`stripe-payments`**.

- Locale routes only: `/it/...` and `/en/...`. **No auto-redirect by location.**
- Public pages are server-rendered (SEO + AI-crawler friendly). **Product, occasion and city
  pages use static generation with revalidation (ISR)**; **cart/checkout are dynamic**. No
  client-only content on pages that must be indexed.
- SEO plumbing via App Router: `generateMetadata` (titles/descriptions, hreflang, canonical),
  `sitemap.ts` (per-locale) and `robots.ts`, plus JSON-LD (Product/Organization/Florist). See
  `i18n-seo`.
- Pink theme tokens come from `packages/ui-tokens`. Fonts (Cormorant Garamond headings, DM
  Sans body) via `next/font`.
- Every string via next-intl messages (`messages/it.json`, `messages/en.json`). No literals.
- Prices shown all-in, EUR, from the API (integer cents → formatted). Never compute on client.
- Respect `prefers-reduced-motion`. Images via `next/image`.
- API types come from `packages/api-client` — never hand-write request/response types.
