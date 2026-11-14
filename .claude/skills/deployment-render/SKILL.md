---
name: deployment-render
description: Use when working on deploy config (Cloudflare + render.yaml), custom domains/SSL, DNS, R2 setup, Stripe live config, migrations-on-deploy, cron jobs, or production monitoring.
---

# Deployment — Cloudflare (frontends) + Render Frankfurt (backend)

Hosting is split:

| What | Where |
|---|---|
| **web** (apps/web, Next.js SSR/ISR) | **Cloudflare** via the **OpenNext** adapter (or Render as fallback). Domain `romafiorita.com`, **www → apex** redirect. |
| **admin** (apps/admin, Vite React SPA) | **Cloudflare Pages** as **static files**. Domain `admin.romafiorita.com`. |
| **api** (apps/api, FastAPI) | **Render**, Frankfurt. Domain `api.romafiorita.com`. **Pre-deploy** runs `alembic upgrade head`. |
| **Postgres 16** + **Redis** (Key Value) | **Render**, Frankfurt (managed). |
| **cron / worker** | **Render**, Frankfurt — arq worker + scheduled jobs (reminders, abandoned cart). |

`render.yaml` covers the **backend** services (api, worker/cron, Postgres, Redis). The
frontends deploy to Cloudflare (Pages/Workers config, e.g. `wrangler`), not `render.yaml`.

- API: **health check** `/health`, env vars (below), **zero-downtime** deploys.
- Admin static build: SPA fallback (serve `index.html` for client routes).
- **Never let free-tier instances sleep in production** — use paid Render instances for the API.

## Env vars (never in git)

- **Render (api / worker):** `DATABASE_URL`, `REDIS_URL`, `STRIPE_SECRET_KEY` (live),
  `STRIPE_WEBHOOK_SECRET`, `RESEND_API_KEY`, R2 creds (`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`,
  `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`), `JWT_SECRET`, `GA4_*`.
- **Cloudflare (web):** `NEXT_PUBLIC_API_URL` and other `NEXT_PUBLIC_*`.
- **Cloudflare (admin, build-time):** `VITE_API_URL` and other `VITE_*` (Vite only inlines
  `VITE_`-prefixed vars — these are public, never put secrets here).

Keep `.env.example` in sync for every app.

## DNS checklist

- **Cloudflare DNS:** `romafiorita.com` → Cloudflare (web), `www` → apex redirect,
  `admin.` → Cloudflare Pages (admin). SSL via Cloudflare.
- **Render:** `api.` → Render service + SSL issued.
- **Resend:** SPF, DKIM, DMARC for `romafiorita.com` sending domain.
- **Cloudflare R2:** bucket created, **CORS** configured for signed uploads from the web/admin
  origins.

## Stripe (live)

- Live keys in Render (api) env. Webhook endpoint: **`https://api.romafiorita.com/webhooks/stripe`**;
  copy its signing secret to `STRIPE_WEBHOOK_SECRET`.
- Statement descriptor `ROMAFIORITA`.

## Operations

- **Migrations** run pre-deploy (above); deploys are **zero-downtime**.
- **Backups:** managed Postgres automated backups enabled; verify restore periodically.
- **Monitoring:** health endpoints on all services; error logging/alerting; watch SSE/worker
  health.
