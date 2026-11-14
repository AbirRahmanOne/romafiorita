---
name: backend-api-conventions
description: Use when working in apps/api — project layout, async SQLAlchemy, Alembic migrations, Pydantic schemas, errors, pagination, auth, CORS, or OpenAPI/client generation.
---

# Backend API conventions (FastAPI)

Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 async + Alembic, PostgreSQL 16, arq + Redis.
Managed with **uv**.

## Layout

```
app/
  main.py            app factory, middleware, router mounting
  config.py          Settings (pydantic-settings)
  db.py              async engine + session
  routers/           HTTP endpoints (thin: parse, authorise, call service)
  services/          business logic (transactions, domain rules)
  repositories/      DB access (queries) — no business logic
  schemas/           Pydantic request/response models
  models/            SQLAlchemy ORM models
  workers/           arq jobs
```

Routers stay thin; logic lives in services; DB access in repositories. Don't query the DB
from routers.

## Async SQLAlchemy

- One `AsyncSession` per request (FastAPI dependency). Open a transaction per unit of work;
  commit in the service, not the repository.
- Use `select()` 2.0 style; load relationships explicitly (`selectinload`) to avoid lazy-load
  in async context.

## Alembic

- One migration per schema change; autogenerate then **review** (names, types, indexes,
  nullability). Never edit a migration that has shipped — add a new one.
- Migrations run pre-deploy on Render (see `deployment-render`).

## Pydantic v2 schemas

- Separate `Create` / `Update` / `Read` schemas. Use `model_config = ConfigDict(from_attributes=True)`
  for ORM reads.
- **Money is integer cents** (`int`), field named like `amount_cents`. Currency fixed EUR.

## Error format

Consistent JSON error body, e.g.:
```json
{ "error": { "code": "slot_full", "message": "That delivery slot is full.", "details": {} } }
```
Map domain errors to HTTP status in one place (exception handlers). Messages shown to users
are localised client-side by code where needed.

## Pagination

Cursor or limit/offset with a consistent envelope: `{ "items": [...], "total": n, "next": ... }`.

## Time & money

- Store timestamps **UTC** (`timezone=True`). Convert to `Europe/Rome` in the service layer
  for business logic and display.
- All money integer cents; never floats.

## Settings & logging

- `pydantic-settings` reads `.env`. Keep `.env.example` current. **No secrets in git.**
- Structured logging (JSON) with request id. Rate-limit public endpoints.

## CORS & auth

- CORS allowlist: `https://romafiorita.com`, `https://admin.romafiorita.com` (+ `localhost`
  in dev). No wildcard.
- Admin auth: **JWT in httpOnly cookies**, roles OWNER/MANAGER/FLORIST/RIDER; enforce role on
  every protected route. Customer accounts optional — **guest checkout** supported.

## OpenAPI → TS client

Generate `packages/api-client` from the API's OpenAPI schema; **never hand-write** client
types. Regenerate after any schema change and commit the result.
