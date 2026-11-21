# Runbook — Roma Fiorita API

## Local development

```bash
docker compose up -d postgres redis
cd backend
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
python seed.py
uvicorn app.main:app --reload       # http://localhost:8000/healthz
# worker (optional, needs Redis):
arq app.workers.arq.WorkerSettings
```

Tests / checks: `pytest`, `ruff check .`, `mypy app`.
Regenerate the client schema after API changes: `python -m scripts.export_openapi`
(commit `openapi.json`; `test_openapi_snapshot` fails on unintended drift).

## Deploy (Render, Frankfurt)

Blueprint = `render.yaml` (API web + arq worker + Postgres 16 + Redis). Migrations run in the
API `preDeployCommand` (`alembic upgrade head`). Health check: `/healthz`.

Set in the dashboard (never in git): `RESEND_API_KEY`, and when enabled `STRIPE_SECRET_KEY`,
`STRIPE_WEBHOOK_SECRET`, R2 and Google Search Console credentials. `JWT_SECRET` is generated.

**Rollback:** redeploy the previous image from the Render dashboard. If a migration must be
reversed, run `alembic downgrade -1` via a one-off shell (only with approval; back up first).

## Migrations

```bash
alembic revision --autogenerate -m "msg"   # needs Postgres up
alembic upgrade head
alembic downgrade -1
```

Pre-deployment the initial migration is squashed/regenerated (ADR 0001); **once deployed,
migrations are append-only and two-step for any drop/rename**. CI verifies
`upgrade → downgrade → upgrade` on real Postgres.

## Common tasks

- **Rotate `JWT_SECRET`**: set a new value in Render → redeploy. All sessions are invalidated
  (tokens fail to verify); staff log in again.
- **Restore DB**: restore the Render Postgres backup, then `alembic upgrade head`.
- **Replay Stripe webhooks** (once Stripe is live): resend from the Stripe dashboard; the
  `stripe_events` table makes processing idempotent.
- **Peak day (Valentine's/Women's Day) checklist**: raise slot `capacity`/`daily_capacity` in
  admin settings and `blocked_dates` as needed; scale the web + worker plans; watch
  `/readyz`, request latency, and the held-payments queue.
- **GDPR request**: `GET /v1/admin/gdpr/export?email=` (access) ·
  `POST /v1/admin/gdpr/delete` (erasure — anonymises PII, keeps financial records).

## Health

- `/healthz` — liveness (process up).
- `/readyz` — readiness (DB reachable). Returns 503 if the DB is down.
