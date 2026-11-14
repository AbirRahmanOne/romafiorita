# Roma Fiorita — romafiorita.com

Online flower & gift shop based in Rome. Customers order from anywhere; **delivery is
Italy-only**. In Rome, the shop's own riders deliver same-day (standard / 2-hour window /
exact time ±15 min). Rest of Italy: next-day boxed bouquet by courier, date only. The core
promise is **trust**: a real photo of the bouquet before delivery, all-in prices, on-time.

Languages: Italian (`it`) + English (`en`). Currency: **EUR only**.

## Repo map

```
frontend/   Next.js app (App Router): storefront (pink, SSR/SSG) + /admin routes (blue).
            Serves romafiorita.com and admin.romafiorita.com.
backend/    FastAPI + PostgreSQL 16 (api.romafiorita.com).
docker-compose.yml   Postgres 16 + Redis + api, for local dev.
.claude/skills/      Area playbooks — read the relevant one before working in its area.
```

> Structure note: the project uses a simple `frontend/` + `backend/` split (not the
> `apps/*` + `packages/*` monorepo some skills still describe). The admin lives as `/admin`
> routes inside the Next.js app, not a separate Vite SPA. **Payments (Stripe) are out of
> scope for this version.**

## Tech stack

- **Frontend (`frontend/`):** Next.js (App Router, latest stable), React 19, TypeScript
  strict, Tailwind v4, next-intl (`/it`, `/en`). Storefront pages SSR/SSG (ISR for
  product/occasion/city pages) — SEO + AI-crawler friendly. Admin is `/admin/*` routes
  (blue theme, behind login, not indexed).
- **Backend (`backend/`):** FastAPI, Pydantic v2, SQLAlchemy 2.0 async + Alembic,
  PostgreSQL 16. Background jobs via **arq + Redis** (later).
- **Services (planned, later phases):** Resend (React Email) from `ordini@romafiorita.com`;
  Cloudflare R2 for images; SSE + Web Push for admin alerts; GA4 on storefront. Stripe
  payments are **deferred** (not in this version).
- **Hosting:** web on Cloudflare (OpenNext adapter) or Render; admin as static files on
  Cloudflare; API + Postgres + Redis on Render, Frankfurt. Local dev: docker-compose
  (Postgres + Redis).

## Domains

- Storefront `romafiorita.com` (www → apex) · Admin `admin.romafiorita.com` · API
  `api.romafiorita.com`
- Email from `ordini@romafiorita.com` (display "Roma Fiorita"), reply-to `info@romafiorita.com`.

## Run / test / lint

```bash
# Infra (from repo root)
docker compose up -d postgres redis     # Postgres 16 + Redis for local dev
# or run the API in Docker too: docker compose up --build

# Frontend (frontend/)
npm install
npm run dev          # http://localhost:3000  (/it, /en, /it/admin ...)
npm run build && npm run lint

# Backend (backend/)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload           # http://localhost:8000/health
pytest && ruff check . && mypy app
alembic revision --autogenerate -m "msg" && alembic upgrade head
python seed.py                          # sample products + Rome zone
```

> Tooling note: this env has no pnpm/uv, so the frontend uses **npm** and the backend uses
> **venv + pip**. First Alembic migration must be generated once Postgres is up (DB required
> for autogenerate).

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
