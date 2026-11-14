# Roma Fiorita — romafiorita.com

Online flower & gift shop based in Rome. Customers order from anywhere in the world;
**delivery is Italy-only** (same-day by the shop's own riders in Rome, next-day by courier
across Italy). Bilingual **IT / EN**, **EUR** only. The promise is trust: a real photo of the
bouquet before delivery, all-in prices, on-time delivery.

> **This version does not include payments (Stripe).** It is the project scaffold: a working
> storefront, an admin dashboard shell, and a FastAPI + PostgreSQL backend.

## Structure

```
frontend/   Next.js app — storefront (pink) + /admin routes (blue). IT/EN.
backend/    FastAPI + PostgreSQL 16 + Alembic.
docker-compose.yml   Postgres 16 + Redis + api (local dev).
.claude/skills/      Area playbooks for Claude Code.
CLAUDE.md            Project guide.
```

## Prerequisites

Node 20+, Python 3.12+, Docker (for Postgres/Redis). This environment has no `pnpm`/`uv`, so
the frontend uses **npm** and the backend uses **venv + pip**.

## Run it locally

**1. Infra**
```bash
docker compose up -d postgres redis
```

**2. Backend** (http://localhost:8000)
```bash
cd backend
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic revision --autogenerate -m "initial schema"   # first time only
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
# check: curl http://localhost:8000/health  ->  {"status":"ok"}
```

**3. Frontend** (http://localhost:3000)
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
# storefront: /it or /en   ·   admin: /it/admin   ·   login: /it/admin/login
```

Alternatively, run the API fully in Docker: `docker compose up --build`.

## Quality

```bash
# frontend
cd frontend && npm run build && npm run lint
# backend
cd backend && source .venv/bin/activate && pytest && ruff check . && mypy app
```

## Notes

- Placeholders kept until real values are supplied: legal company name, Rome address,
  Partita IVA, PEC, phone; same-day cut-off `[14:00]`, exact-time notice `[3h]`, delivery
  fees `€[X]`/`€[Y]`.
- See `CLAUDE.md` and `.claude/skills/` for conventions and area guides.
