# Roma Fiorita — API (api.romafiorita.com)

Backend for the Roma Fiorita flower & gift shop. Online orders from anywhere,
**delivery is Italy-only** (same-day by the shop's own riders in Rome, next-day by courier
across Italy). Bilingual **IT / EN**, **EUR** only.

The storefront + admin frontend lives in a separate repo (`romafiorita-frontend`).

> **This version does not include payments (Stripe).**

## Structure

```
backend/             FastAPI + PostgreSQL 16 + Alembic.
docker-compose.yml   Postgres 16 + Redis + api (local dev).
.claude/skills/      Area playbooks for Claude Code.
CLAUDE.md            Project guide.
```

## Prerequisites

Python 3.12+, Docker (for Postgres/Redis). This environment has no `uv`, so the backend uses
**venv + pip**.

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

Alternatively, run the API fully in Docker: `docker compose up --build`.

## Quality

```bash
cd backend && source .venv/bin/activate && pytest && ruff check . && mypy app
```

## Notes

- Placeholders kept until real values are supplied: legal company name, Rome address,
  Partita IVA, PEC, phone; same-day cut-off `[14:00]`, exact-time notice `[3h]`, delivery
  fees `€[X]`/`€[Y]`.
- See `CLAUDE.md` and `.claude/skills/` for conventions and area guides.
