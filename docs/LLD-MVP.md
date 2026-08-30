# Claim360 AI — MVP Phase 1 Low-Level Design

**Companion to:** [PLAN.md](./PLAN.md) §3, [REQUIREMENTS.md](./REQUIREMENTS.md)  
**Scope:** Phase 1 MVP only (synthetic data, HITL required, stub payment/comms)  
**Date:** 2026-08-29  
**Status:** Design for implementation  

---

## 1. Purpose

This document specifies **components, contracts, data stores, APIs, agent I/O, state machine, and exact tech stack** for the MVP vertical slice:

**Intake → sequential Policy / Fraud / Medical Necessity → proposed decision + draft letter → specialist review → recorded disposition + audit.**

It does **not** cover Phase 2 HIPAA/RBAC product, live payer APIs, parallel agents, drift/canary, or call bot.

---

## 2. Design constraints (locked)

| Constraint | Choice |
|------------|--------|
| Agent execution | Sequential: Policy → Fraud → Medical Necessity |
| Human review | Required for every claim (no auto-approve) |
| External systems | Fixture adapters behind interfaces |
| Ack SLA | HTTP 202 + `claim_id` in ≤ 30s; adjudication async |
| Isolation | One workflow instance per `claim_id`; no shared in-memory claim state |
| LLM | Structured JSON out; deterministic rule fallback if LLM fails |
| Secrets | Environment / `.env` (gitignored); never committed |

---

## 3. Tech stack (pinned for MVP)

Versions are **minimum recommended**. Pin exact versions in lockfiles at implement time.

### 3.1 Runtime and language

| Layer | Technology | Version | Role |
|-------|------------|---------|------|
| Language | Python | 3.12+ | API, workers, agents, evals |
| Package manager | uv or Poetry | uv 0.4+ / Poetry 1.8+ | Lockfile, venv |
| Node | Node.js | 20 LTS | Specialist UI |
| Package manager (UI) | npm or pnpm | pnpm 9+ preferred | Frontend lockfile |

### 3.2 Application services

| Component | Technology | Version | Role |
|-----------|------------|---------|------|
| HTTP API | FastAPI | 0.115+ | Intake, specialist APIs, health |
| ASGI server | Uvicorn | 0.32+ | Run API |
| Validation / DTOs | Pydantic | v2.10+ | Request/response and agent schemas |
| Settings | pydantic-settings | 2.x | Typed env config |
| Orchestrator graph | LangGraph | 0.2+ | Claim state machine, checkpoints |
| LLM SDK | OpenAI Python SDK **or** Anthropic SDK | latest stable | Draft letter + optional agent rationale |
| Structured LLM | `instructor` **or** LangChain `with_structured_output` | matching LangGraph | Schema-constrained agent JSON |
| Fallback | Pure Python rules | — | Eligibility/fraud/necessity if LLM down |
| HTTP client (fixtures later) | httpx | 0.28+ | Adapter interface (unused to real hosts in MVP) |
| Migrations | Alembic | 1.14+ | Schema versioning |
| ORM | SQLAlchemy | 2.0+ | Persistence |

**Why LangGraph:** maps cleanly to TR-04 stages, retry per node, and per-claim checkpointing (NFR-01 lite) without a custom FSM library.

**Why not CrewAI/AutoGen for MVP:** less explicit sequential control and weaker typed I/O. Revisit in later phases if needed.

### 3.3 Data and async

| Component | Technology | Version | Role |
|-----------|------------|---------|------|
| Primary DB | PostgreSQL | 16 | Cases, findings, drafts, audit, feedback |
| Driver | psycopg | 3.2+ | Sync/async via SQLAlchemy |
| Broker / cache | Redis | 7.2+ | Job queue + optional LangGraph checkpoint backend |
| Workers | Celery | 5.4+ | Run orchestration off the request thread |
| Celery result backend | Redis | same | Job status for UI polling (optional) |

**Local data plane:** Install PostgreSQL 16 and Redis 7 via Homebrew; API and Celery worker run on the host and connect to `localhost`. Do **not** use SQLite for MVP if two concurrent claims must be demoed (NFR-06). Hosted Redis (e.g. Redis Cloud 30 MB free) is optional, not required.

### 3.4 Frontend

| Component | Technology | Version | Role |
|-----------|------------|---------|------|
| UI | React | 18.3+ | Specialist workspace |
| Bundler | Vite | 6.x | Dev server + build |
| Language | TypeScript | 5.6+ | Typed API client |
| Routing | React Router | 6.x | Queue, claim detail, audit |
| HTTP | fetch or ky | — | REST |
| Styling | Tailwind CSS | 3.4+ | Fast layout without design system |

No Next.js for MVP (no SSR/auth product). No component library required; keep forms simple.

### 3.5 Auth (MVP-grade, not HIPAA)

| Component | Technology | Role |
|-----------|------------|------|
| Specialist login | JWT (HS256) via python-jose or PyJWT | Single `SPECIALIST` role |
| Password | bcrypt (passlib) | One seeded user from env |
| API protection | FastAPI `Depends` | `/api/v1/specialist/*` |
| Portal mock | API key header `X-Portal-Key` | Intake only |

No OAuth2/mTLS until Phase 2.

### 3.6 Observability and quality

| Component | Technology | Role |
|-----------|------------|------|
| Logs | structlog | JSON logs with `claim_id`, `agent`, `event` |
| Health | FastAPI routes | `GET /health`, `GET /ready` (DB + Redis ping) |
| Tests | pytest, pytest-asyncio, httpx | API + agent schema + golden smoke |
| HTTP mocks | respx (if needed) | Unused until real HTTP adapters |
| CI | GitHub Actions | lint, test, golden eval |
| Lint/format | Ruff + mypy (backend), ESLint + tsc (UI) | Gate PRs |
| Local run | Homebrew Postgres + Redis; API/worker/UI on the host | No Docker Compose for MVP |

No Prometheus/Grafana, OpenTelemetry collector, or ELK in MVP. Log to stdout.

### 3.7 LLM and prompts

| Item | MVP choice |
|------|------------|
| Default model | `gpt-4o-mini` or `claude-3-5-haiku` (cost) |
| Temperature | `0` for agents; `0.2` for letter draft |
| Timeouts | 45s per agent LLM call |
| Prompt store | Versioned files under `prompts/<agent>/vN.md` + `PROMPT_VERSION` env |
| Grounding | Inject fixture policy snippets into the prompt; never free-form “invent policy” |
| Kill switch | `LLM_ENABLED=false` → rules-only agents + template letter |

API key: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in env only (TR-25).

### 3.8 Explicitly not in MVP stack

Kafka, Kubernetes, Terraform, Vault, S3, SendGrid, Twilio, FHIR servers, Okta, LangSmith (optional later), vector DB, RAG over PDFs.

---

## 4. System context and components

```mermaid
flowchart TB
  Portal[Payer portal mock\nHTTP client or curl]
  UI[Specialist UI\nReact + Vite]
  API[claim360-api\nFastAPI]
  Q[Redis]
  W[claim360-worker\nCelery + LangGraph]
  DB[(PostgreSQL)]
  LLM[LLM provider]
  Fix[Fixture stores\nJSON files]

  Portal -->|POST /api/v1/portal/claims\nX-Portal-Key| API
  UI -->|JWT REST| API
  API -->|enqueue orchestrate| Q
  W --> Q
  API --> DB
  W --> DB
  W --> LLM
  W --> Fix
```

| Process | Responsibility |
|---------|----------------|
| **claim360-api** | Auth, intake ack, CRUD for specialist, enqueue work, read audit |
| **claim360-worker** | Load claim, run graph, persist findings/decision/draft, retries |
| **claim360-web** | Queue, claim workspace, audit timeline |
| **postgres** | System of record |
| **redis** | Celery broker |
| **fixtures** | Eligibility, history, guidelines, policy snippets, members/providers |

Agents are **Python modules invoked in-process inside the worker**, not separate microservices (NFR-22 deferred to Phase 2).

---

## 5. Repository layout

```text
claim360/
  backend/
    claim360/
      api/             # FastAPI routes
      worker/          # Celery + LangGraph
      agents/          # policy, fraud, mednec, letter
      adapters/        # fixture implementations
      models/          # Pydantic + SQLAlchemy
    alembic/
    tests/
    pyproject.toml
  web/                 # Vite + React
  fixtures/
    members.json
    eligibility.json
    claims_history.json
    guidelines.json
    policies.json
    providers.json
  prompts/
    policy/v1.md
    fraud/v1.md
    medical_necessity/v1.md
    letter/v1.md
  evals/
    golden/
      cases/*.json
      expected/*.json
    run_smoke.py
  .env.example
```

One Python package `claim360` imported by both API and worker. Do not split `packages/contracts` or separate `apps/api` vs `apps/worker` until Phase 2 independently deployable agents. Keep `fixtures/`, `prompts/`, and `evals/` at repo root (data, not code).

---

## 6. Claim lifecycle and orchestrator graph

### 6.1 Status enum

```text
RECEIVED → QUEUED → POLICY_RUNNING → FRAUD_RUNNING → MEDNEC_RUNNING
       → PROPOSED → AWAITING_HUMAN → ESCALATED
       → FINALIZED
       → FAILED_ESCALATED   # unrecoverable after retries
```

`PROPOSED` is internal (decision written). UI treats `AWAITING_HUMAN` as the review queue. Escalation sets `ESCALATED` (same workspace, flagged). `FINALIZED` after specialist approve (any disposition).

### 6.2 LangGraph nodes (sequential)

```mermaid
stateDiagram-v2
  [*] --> load_claim
  load_claim --> policy_agent
  policy_agent --> fraud_agent
  fraud_agent --> mednec_agent
  mednec_agent --> formulate_decision
  formulate_decision --> draft_letter
  draft_letter --> persist_proposed
  persist_proposed --> [*]
```

Each agent node: call adapter → LLM or rules → **Pydantic validate** → persist finding → append audit event. On validation failure: retry node (max 3). On exhaustion: set `FAILED_ESCALATED`, audit `agent_failed`, stop graph.

**Checkpointer:** `MemorySaver` is **not** enough across worker restarts. Use LangGraph `PostgresSaver` or Redis checkpointer keyed by `claim_id` so a killed worker can resume (NFR-01 lite).

### 6.3 Celery task

- Name: `orchestrate_claim`
- Args: `claim_id: UUID`
- Idempotency: if status already `AWAITING_HUMAN` or later, no-op
- Time limit: 10 minutes (soft 8)
- Intake path: API inserts row `RECEIVED`, commits, enqueues, returns 202 (must not wait for agents)

---

## 7. Decision aggregation (deterministic)

Specialist agents **do not** pick the final code. Orchestrator `formulate_decision` applies this order (first match wins):

| Priority | Condition | Proposed `decision` | Notes |
|----------|-----------|---------------------|--------|
| 1 | Fraud `risk_level == high` | `pend` | Always human; UI shows fraud banner |
| 2 | Policy `outcome == ineligible` | `deny` | |
| 3 | Policy `outcome == needs_clarification` | `pend` | |
| 4 | MedNec `determination == not_necessary` | `deny` | |
| 5 | MedNec `determination == insufficient_info` | `pend` | |
| 6 | Policy `outcome == partial` | `partial_approve` | |
| 7 | Else all pass | `approve` | |

`rationale_bullets` = concatenate policy findings + fraud indicators + mednec rationale (capped). Letter prompt receives this structured bundle only.

---

## 8. Data model (PostgreSQL)

Use UUID PKs, `TIMESTAMPTZ`, JSONB for structured payloads. **Audit table is insert-only** (no UPDATE/DELETE in application code).

### 8.1 Tables

**members** (fixture-backed, optional cache)  
`id`, `member_external_id`, `display_name`, `created_at`

**claims**  
| Column | Type | Notes |
|--------|------|--------|
| id | UUID PK | `claim_id` |
| portal_claim_ref | TEXT UNIQUE | Provider’s claim number |
| status | TEXT | enum above |
| payload | JSONB | Submitted claim body |
| member_external_id | TEXT | |
| proposed_decision | TEXT NULL | approve/deny/partial_approve/pend |
| proposed_rationale | JSONB NULL | |
| final_decision | TEXT NULL | After human |
| final_rationale | JSONB NULL | |
| draft_letter | TEXT NULL | |
| final_letter | TEXT NULL | Edited copy |
| agent_versions | JSONB | `{model, prompts, graph}` |
| error_message | TEXT NULL | |
| created_at / updated_at | TIMESTAMPTZ | |

**agent_findings**  
`id`, `claim_id` FK, `agent` (`policy`\|`fraud`\|`mednec`), `payload` JSONB, `schema_version` TEXT, `created_at`  
Unique `(claim_id, agent)` for MVP (overwrite only via new row + audit if you prefer immutable findings; **recommended:** insert-only, latest by `created_at`).

**audit_events**  
`id` BIGSERIAL, `claim_id`, `event_type`, `actor` (`system`\|`specialist`\|`portal`), `payload` JSONB, `created_at`  
Events: `claim_received`, `queued`, `policy_completed`, `fraud_completed`, `mednec_completed`, `decision_proposed`, `letter_drafted`, `human_edited`, `human_approved`, `human_escalated`, `disposition_stubbed`, `agent_retry`, `agent_failed`.

**specialist_feedback**  
`id`, `claim_id`, `proposed_decision`, `final_decision`, `letter_edit_distance` INT, `override_notes` TEXT, `created_at`  
Populated on finalize (EVAL-26 store only).

**users**  
`id`, `email` UNIQUE, `password_hash`, `role` (`specialist`)

**provider_responses** (stub outbound)  
`id`, `claim_id`, `status` (`pending`\|`recorded`), `body` JSONB, `created_at`  
On finalize, insert RESPONSE payload; no HTTP callback in MVP unless time allows a logged no-op.

Indexes: `claims(status)`, `claims(portal_claim_ref)`, `audit_events(claim_id, created_at)`, `agent_findings(claim_id)`.

### 8.2 Submitted claim payload (JSON)

Minimum fields for agents:

```json
{
  "portal_claim_ref": "CLM-1001",
  "member_external_id": "MEM-001",
  "provider_npi": "1234567890",
  "date_of_service": "2026-06-01",
  "diagnosis_codes": ["M54.5"],
  "procedure_codes": ["97110"],
  "place_of_service": "11",
  "billed_amount_cents": 15000,
  "units": 2,
  "service_description": "Therapeutic exercises"
}
```

Validate with Pydantic on intake; 422 if missing required fields.

---

## 9. Agent contracts (schema_version `1.0`)

Reject and retry if validation fails (NFR-17).

### 9.1 Policy Compliance

**Input:** claim payload + `EligibilityRecord` from adapter.

**Output:**

```json
{
  "outcome": "eligible | ineligible | partial | needs_clarification",
  "field_findings": [
    { "field": "procedure_codes", "status": "pass | fail | unclear", "message": "..." }
  ],
  "policy_refs": ["POL-PT-001"],
  "confidence": 0.0
}
```

### 9.2 Fraud Detection

**Input:** claim + `MemberHistory` (prior claims, amounts, providers).

**Output:**

```json
{
  "risk_level": "low | medium | high",
  "risk_score": 0,
  "indicators": [{ "code": "DUP_DOS", "detail": "..." }],
  "confidence": 0.0
}
```

`risk_score` 0–100. Thresholds in config: high ≥ 80, medium ≥ 50 (NFR-24 later; env vars in MVP).

### 9.3 Medical Necessity

**Input:** claim + `GuidelineHits` + prior treatments.

**Output:**

```json
{
  "determination": "necessary | not_necessary | insufficient_info",
  "guideline_refs": ["GL-LBP-01"],
  "rationale": "string",
  "confidence": 0.0
}
```

### 9.4 Letter draft

**Input:** proposed decision + all three outputs + policy snippet texts.

**Output:** `{ "subject": "...", "body": "..." }` — member-facing, includes policy rationale (FR-19). Template fallback if LLM off.

---

## 10. Adapters (interfaces)

All in `backend/claim360/adapters`. MVP implementations read `fixtures/*.json`.

| Adapter | Methods | Fixture |
|---------|---------|---------|
| `EligibilityAdapter` | `get_eligibility(member_id, dos)` | `eligibility.json` |
| `HistoryAdapter` | `get_claims(member_id)` | `claims_history.json` |
| `GuidelineAdapter` | `match(dx, px)` | `guidelines.json` |
| `PolicySnippetAdapter` | `snippets(refs)` | `policies.json` |
| `PaymentAdapter` | `record_disposition(claim_id, decision)` | no-op + audit `disposition_stubbed` |
| `CommsAdapter` | `queue_member_letter(...)` | persist only; no send |

Do not call the internet from adapters in MVP.

---

## 11. HTTP API

Base: `/api/v1`. JSON. CORS allow Vite origin.

### 11.1 Public / portal

| Method | Path | Auth | Behavior |
|--------|------|------|----------|
| POST | `/portal/claims` | `X-Portal-Key` | Validate, insert, enqueue, **202** `{ claim_id, status: "queued" }` |
| GET | `/portal/claims/{claim_id}` | portal key | Status + final RESPONSE if `FINALIZED` else `in_progress` |

Duplicate `portal_claim_ref`: **409**.

### 11.2 Specialist (JWT)

| Method | Path | Behavior |
|--------|------|----------|
| POST | `/auth/login` | `{ email, password }` → `{ access_token }` |
| GET | `/specialist/queue` | Claims in `AWAITING_HUMAN` or `ESCALATED` |
| GET | `/specialist/claims/{id}` | Payload, findings, proposed decision, draft letter |
| PATCH | `/specialist/claims/{id}` | Edit `final_decision` and/or `final_letter` (draft copy-on-write) |
| POST | `/specialist/claims/{id}/approve` | Require edited or confirm draft; set FINALIZED; payment stub; provider_response; feedback row |
| POST | `/specialist/claims/{id}/escalate` | Status `ESCALATED`, audit, optional `notes` |
| GET | `/specialist/claims/{id}/audit` | Ordered `audit_events` |

Approve is rejected if status not `AWAITING_HUMAN` or `ESCALATED`.

### 11.3 Ops

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/health` | 200 `{ status: "ok" }` |
| GET | `/ready` | 200 if DB + Redis OK else 503 |

---

## 12. Specialist UI screens

1. **Login** — email/password.  
2. **Queue** — table: claim_id, member, DOS, proposed decision, fraud level, status, age.  
3. **Claim workspace** (NFR-20) — four columns/sections: claim summary; Policy / Fraud / MedNec cards; proposed decision + editable letter (textarea); actions Approve / Escalate.  
4. **Audit** — timeline on same page or `/claims/:id/audit`.

No provider portal UI (mock is API). No member UI.

---

## 13. Error handling and retries

| Failure | Behavior |
|---------|----------|
| LLM timeout / 5xx | Retry 3× exponential backoff 1s, 2s, 4s |
| Invalid JSON / schema | Retry 3× with “repair” prompt once, then rules fallback **or** `FAILED_ESCALATED` if rules cannot run |
| Fixture miss (unknown member) | Policy `needs_clarification`; do not crash |
| Worker crash mid-graph | Resume from checkpointer; if corrupt, `FAILED_ESCALATED` |
| DB error on intake | 503; do not ack |

Celery `acks_late=True` so a killed worker requeues.

---

## 14. Concurrency

- One Celery task per `claim_id`; Redis lock `lock:claim:{id}` (SET NX EX 600) around graph run.  
- API uses connection pool; no global claim dict.  
- UI poll queue every 5s or manual refresh (WebSockets out of MVP).

---

## 15. Security (MVP)

| Control | Implementation |
|---------|----------------|
| Secrets | `.env` / Compose `env_file`; `.env.example` without keys |
| Portal | Shared static key, rotate via env |
| JWT | 8h expiry, `JWT_SECRET` ≥ 32 chars |
| PHI | Synthetic fixtures only; no real member data in git |
| TLS | Optional in Compose; not required locally |

---

## 16. Evaluation (thin gate)

`evals/golden/cases/` — at least four labeled claims:

| Case | Expected path |
|------|----------------|
| happy | approve |
| ineligible | deny via policy |
| high fraud | pend |
| not medically necessary | deny |

CI: `pytest evals/` loads fixtures, runs agents **rules mode** (`LLM_ENABLED=false`) so CI is deterministic, asserts schema + aggregated decision. Optional second job with LLM if secrets present (non-blocking).

---

## 17. Configuration reference

```text
DATABASE_URL=postgresql+psycopg://claim360:claim360@localhost:5432/claim360
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
JWT_SECRET=
PORTAL_API_KEY=
SPECIALIST_EMAIL=specialist@local
SPECIALIST_PASSWORD=
LLM_ENABLED=true
LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
PROMPT_VERSION=1
FRAUD_HIGH_THRESHOLD=80
FRAUD_MEDIUM_THRESHOLD=50
AGENT_MAX_RETRIES=3
```

---

## 18. Local run (Homebrew)

Install and start on the Mac (one-time):

```bash
brew install postgresql@16 redis
brew services start postgresql@16
brew services start redis
createdb claim360   # or create role + DB to match DATABASE_URL
```

Then run three host processes: `uvicorn` (API :8000), `celery` worker, `pnpm dev` (UI :5173).  
`VITE_API_BASE=http://localhost:8000`.

**Optional hosted Redis:** Redis Cloud “30 MB free” (one DB/account, ~30 connections, ~100 ops/s). Fine for a queue prototype; inactivity can reclaim the free DB. Prefer local Redis for daily MVP work (no account, no TLS hassle, no idle teardown).

No Docker Compose in Phase 1.

---

## 19. Sequence (happy path)

```mermaid
sequenceDiagram
  participant P as Portal mock
  participant A as API
  participant R as Redis
  participant W as Worker
  participant DB as Postgres
  participant H as Specialist UI

  P->>A: POST /portal/claims
  A->>DB: INSERT claim RECEIVED
  A->>R: enqueue orchestrate_claim
  A-->>P: 202 claim_id
  W->>DB: run graph, findings, proposed, draft
  W->>DB: status AWAITING_HUMAN
  H->>A: GET queue / claim
  H->>A: POST approve
  A->>DB: FINALIZED + stub payment + feedback
  P->>A: GET claim (optional)
  A-->>P: RESPONSE body
```

---

## 20. Build order (implementation)

Matches PLAN.md §7:

1. Pydantic contracts + Alembic tables + seed specialist user  
2. Adapters + fixtures  
3. Agent nodes (rules first) + aggregation + audit writes  
4. Celery + FastAPI intake 202  
5. Letter draft (template, then LLM)  
6. Specialist APIs + React workspace  
7. Golden pytest + Compose README  

---

## 21. Out of this LLD

Phase 2+: OAuth, encryption at rest as a control, independent agent services, parallel graph edges, payment rail, outbound email/SMS, eval dashboards, OpenTelemetry.

---

## 22. Document control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-29 | Initial MVP Phase 1 LLD and tech stack |
| 1.1 | 2026-08-29 | Local Homebrew Postgres/Redis; flatter `backend/` + `web/` layout |
