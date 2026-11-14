# Roma Fiorita — romafiorita.com

Online flower & gift shop based in Rome. Customers order from anywhere; **delivery is
Italy-only**. In Rome, the shop's own riders deliver same-day (standard / 2-hour window /
exact time ±15 min). Rest of Italy: next-day boxed bouquet by courier, date only. The core
promise is **trust**: a real photo of the bouquet before delivery, all-in prices, on-time.

Languages: Italian (`it`) + English (`en`). Currency: **EUR only**.

## Monorepo map

```
apps/web        Customer storefront (romafiorita.com) — Next.js (SSR/SSG), pink theme
apps/admin      Admin dashboard (admin.romafiorita.com) — Vite + React SPA, blue/white theme
apps/api        Backend (api.romafiorita.com) — FastAPI, Python 3.12
packages/ui-tokens    Shared design tokens (both themes)
packages/api-client   TS client generated from the API OpenAPI schema (never hand-written)
.claude/skills/       Area playbooks — read the relevant one before working in its area
```

## Tech stack

- **Web (storefront):** Next.js (App Router, latest stable), TypeScript strict, Tailwind,
  shadcn/ui, next-intl (`/it`, `/en`). Public pages SSR/SSG (ISR for product/occasion/city
  pages; cart/checkout dynamic) — SEO + AI-crawler friendly.
- **Admin:** **Vite + React SPA** (TanStack Router or React Router, TanStack Query + TanStack
  Table, Recharts), TypeScript strict, Tailwind, shadcn/ui. Behind login, no SEO → no SSR;
  lightweight static build.
- **API:** FastAPI, Pydantic v2, SQLAlchemy 2.0 async + Alembic, PostgreSQL 16. Background
  jobs via **arq + Redis**.
- **Services:** Stripe (Payment Element, descriptor `ROMAFIORITA`) + webhooks; Resend (React
  Email) from `ordini@romafiorita.com`; Cloudflare R2 for images; SSE + Web Push for admin
  alerts; GA4 on storefront.
- **Hosting:** web on Cloudflare (OpenNext adapter) or Render; admin as static files on
  Cloudflare; API + Postgres + Redis on Render, Frankfurt. Local dev: docker-compose
  (Postgres + Redis).

## Domains

- Storefront `romafiorita.com` (www → apex) · Admin `admin.romafiorita.com` · API
  `api.romafiorita.com`
- Email from `ordini@romafiorita.com` (display "Roma Fiorita"), reply-to `info@romafiorita.com`.

## Run / test / lint

```bash
# everything (from repo root)
pnpm dev            # all apps
pnpm build
pnpm lint
pnpm typecheck
pnpm test

docker compose up   # Postgres 16 + Redis for local dev

# API (apps/api)
uv run uvicorn app.main:app --reload
uv run pytest
uv run ruff check . && uv run mypy .
uv run alembic upgrade head        # migrations
```

Copy each app's `.env.example` to `.env` before running.

## Coding conventions

- **No hard-coded user-facing text** — everything through i18n (`it` + `en`).
- **Money = integer cents, EUR.** Never trust client amounts; recompute server-side.
- **Time:** store UTC, business logic in `Europe/Rome`, also show sender's local time.
- **No secrets in git.** Use `.env`; keep `.env.example` current.
- TS strict, no `any`. Python: Ruff + mypy strict on app code.
- Keep placeholders (legal name, Rome address, Partita IVA, PEC, phone, cut-off `[14:00]`,
  exact-time notice `[3h]`, fees `€[X]`/`€[Y]`) until real values are supplied.

## Git conventions

- **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`, `test:`…).
- Small, focused commits and **small PRs**. One concern per PR.

## Definition of done

Passes lint + typecheck + tests, ships with the tests its area requires, meets WCAG AA
(44px tap targets, visible focus, colour never the only signal), strings localised, and the
relevant skill updated if a convention changed.

## The rule

**Read the relevant skill in `.claude/skills/` before working in its area.** Start any new
feature or phase with the `new-feature` skill.
