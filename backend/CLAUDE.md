# backend — FastAPI

API at **api.romafiorita.com**. FastAPI, Python 3.12, Pydantic v2, SQLAlchemy 2.0 async +
Alembic, PostgreSQL 16. Managed locally with **venv + pip** (no uv in this env).

Read before working here: **`backend-api-conventions`**. Domain rules:
`checkout-and-delivery-rules`, `order-lifecycle`, `notifications-and-reminders`.
(The skill describes a `routers/services/repositories/schemas/models` package layout; we add
`services/` and `repositories/` when features need them — not scaffolded empty.)

## Layout

```
app/main.py        FastAPI app + CORS + error handler + routers
app/config.py      pydantic-settings (.env)
app/db.py          lazy async engine + get_session dependency
app/models.py      SQLAlchemy models (14 tables)
app/schemas.py     Pydantic read models
app/routers/       endpoints: health, products
app/repositories/  DB access (products)
alembic/           async migrations
scripts/export_openapi.py   dump openapi.json (TS client source)
seed.py            sample products + Rome zone + slot rule
tests/             pytest against in-memory SQLite (httpx ASGITransport)
```

## API

- `GET /health` → `{"status":"ok"}`
- `GET /products?occasion=&limit=&offset=` → `{items, total}` (active only)
- `GET /products/{slug}` → product or 404
- Errors use `{"error": {code, message, details}}` (see the handler in `main.py`).
- Export schema: `python -m scripts.export_openapi` → `openapi.json`.

## Rules

- **Money = integer cents**, currency EUR. **No Stripe / payments in this version** (the
  `Payment`/`StripeEvent` models + empty Stripe settings are inert scaffolding for later).
- Store timestamps **UTC** (timezone-aware); convert to `Europe/Rome` in the service layer.
- Settings via `app/config.py`; keep `.env.example` current. **No secrets in git.**
- CORS allowlist is in settings (storefront + admin + localhost).
- Run: `uvicorn app.main:app --reload`. Test/lint: `pytest`, `ruff check .`, `mypy app`.
- Migrations: `alembic revision --autogenerate -m "msg"` then `alembic upgrade head`
  (needs Postgres running — `docker compose up -d postgres`). Then `python seed.py`.
- Regenerate the TS API client for the frontend after schema changes (later phase).
