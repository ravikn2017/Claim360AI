# Claim360 AI — graded implementation

Learner checklist for MVP Phase 1. Product scope lives in [docs/PLAN.md](docs/PLAN.md) §3. Implementation contracts live in [docs/LLD-MVP.md](docs/LLD-MVP.md). If they conflict, **LLD-MVP.md** wins.

Do **one slice per session**. Agents are typed functions first; LangGraph, Celery, and the LLM come later.

| Slice | Status | Concept | Done when |
| ----- | ------ | ------- | --------- |
| L0 | **done** | API process, env, DB, health | `GET /health` returns `{ "status": "ok" }`; Homebrew Postgres/Redis are local (not started by this slice) |
| L1 | **done** | Pydantic contracts + Postgres tables | pytest creates a claim row and an audit event |
| L2 | **done** | Fixture adapters | unit tests load `MEM-001` without FastAPI |
| L3 | pending | Rules-only agents | each agent returns schema-valid JSON in pytest |
| L4 | pending | Deterministic aggregation | `adjudicate_sync(claim_id)` writes `PROPOSED` fields |
| L5 | pending | Sequential LangGraph | graph ends `AWAITING_HUMAN` |
| L6 | pending | FastAPI 202 + Celery | intake returns in milliseconds; GET shows `AWAITING_HUMAN` |
| L7 | pending | HITL APIs + specialist UI | approve one claim in the browser; audit is complete |
| L8 | pending | Optional LLM + golden CI | CI green with `LLM_ENABLED=false` |

## L0 — how to run

```bash
# one-time data plane (Homebrew) — confirm with: psql -d claim360 -c 'select 1' and redis-cli ping
brew install postgresql@16 redis
brew services start postgresql@16
brew services start redis
# as a Postgres superuser (password must match DATABASE_URL)
# CREATE USER claim360 WITH PASSWORD 'claim360';
# CREATE DATABASE claim360 OWNER claim360;

# API (uv if installed; otherwise the committed venv workflow)
cd backend
uv sync   # or: python3.12 -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp ../.env.example ../.env   # fill secrets later; not required for /health
uv run uvicorn claim360.api.main:app --reload --port 8000
# GET http://localhost:8000/health → {"status":"ok"}
```

## L1 — contracts and persistence

Needs a Postgres database matching `DATABASE_URL` (default `claim360:claim360@localhost:5432/claim360`). On the existing local server (as a superuser):

```sql
CREATE USER claim360 WITH PASSWORD 'claim360';
CREATE DATABASE claim360 OWNER claim360;
```

Or set `DATABASE_URL` in `.env` to a user/database you already have.

```bash
cd backend
.venv/bin/pip install -e ".[dev]"
.venv/bin/alembic upgrade head
.venv/bin/pytest -q
# GET http://localhost:8000/ready → {"status":"ok","database":"ok"} after migrate
```

Seed the specialist user once `SPECIALIST_PASSWORD` is set in `.env`:

```bash
cd backend
.venv/bin/python -m claim360.seed
```

## L2 — fixture adapters

Agents call adapters, not files or the network. JSON lives under repo-root `fixtures/`.

```bash
cd backend
.venv/bin/pytest tests/test_adapters.py -q
```
