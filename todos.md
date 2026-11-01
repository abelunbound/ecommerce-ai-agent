# Prototype plan

Work top to bottom. Each item is done only when its acceptance line is true.

## 0. Decisions

Write `docs/architecture.md` and a few one-page decision records:

- [x] `docs/architecture.md` — layers, packages, and how a request moves through them
- [x] ADR: scope — what the prototype is for
- [x] ADR: non-goals — what is explicitly out
- [x] ADR: no-financial-actions boundary — the agent may propose a refund; it may not execute one
- [x] ADR: single agent for the prototype — one orchestrator, no multi-agent split yet

**Done when:** you can state in 5 minutes what the prototype will and will not do.

## 1. Repo foundation

- [x] `git init`
- [x] `.gitignore` covering env files, `.venv`, and `*.db`
- [x] `pyproject.toml` per package (`backend`, `frontend`)
- [x] Ruff, mypy, and pytest config
- [x] Pre-commit, including a secrets scanner
- [x] `.env.example`
- [x] Cursor rules file describing the layering
- [ ] Makefile targets: `make test`, `make lint`, `make run`

**Done when:** `make lint` and `make test` pass on an empty project.

## 2. CI

- [ ] GitHub Actions: lint, type-check, and tests on every push and pull request
- [ ] Branch protection on `main`

**Done when:** a trivial PR shows a green check.

## 3. Config

- [x] `core/config.py` with pydantic-settings
- [x] Settings load `.env`
- [x] Process fails fast when a required value is missing

**Done when:** a test proves a missing `OPENAI_API_KEY` raises a clear error.

## 4. Walking skeleton

- [x] FastAPI `GET /health`
- [x] A Dash page that calls it via httpx
- [x] One test on the API side, one test on the Dash side

**Done when:** `make run` shows the Dash page reporting backend health.

## 5. Database

- [ ] SQLAlchemy models
- [ ] First Alembic migration
- [ ] Repositories
- [ ] `seed_db.py`
- [ ] CI runs against Postgres and SQLite

**Done when:** migrations apply cleanly on both, and the seed script is repeatable.

## 6. Data fixtures

- [ ] Policy pack with metadata
- [ ] Seed data (customers, orders) consistent with the verification gate
- [ ] First 20–30 eval cases, with expected answers written and reviewed before commit

Cover the gaps the later steps depend on:

- [ ] Order lookup only after the customer is verified
- [ ] Customer A cannot see customer B’s order
- [ ] Policy questions that must be answered from the policy pack
- [ ] Ticket creation when the agent should hand off
- [ ] Refund requests that may be proposed and must not be executed
- [ ] Out-of-scope asks (changing payment methods, issuing money, account takeover) that must be refused
- [ ] Missing or unknown orders
- [ ] Ambiguous questions where the expected route is a clarifying question, not a tool call

**Done when:** the files are reviewed and committed, and every case has an expected answer.

## 7. RAG slice

- [ ] Ingestion and chunking of the policy pack
- [ ] Pinecone dev index
- [ ] Retriever with metadata filters
- [ ] Retrieval eval with no LLM in the loop

**Done when:** recall@k is reported for the eval set, with no LLM involved.

## 8. Tools and services

- [ ] `lookup_order` with the customer-verification gate
- [ ] `search_policies`
- [ ] `create_ticket`
- [ ] `pending_actions` (propose only; nothing financial executes here)

**Done when:** unit tests pass without any model call, including “customer A can’t see customer B’s order.”

## 9. Agent v0

- [ ] Orchestrator
- [ ] Versioned prompts
- [ ] Guardrails enforcing the no-financial-actions boundary
- [ ] Conversation persistence
- [ ] `POST /chat`
- [ ] Langfuse tracing

**Done when:** routing evals pass — the right tool for the right question.

## 10. UI

- [ ] Dash chat page
- [ ] Admin page for approvals

**Done when:** you can complete a conversation end to end.

## 11. Handoff and approvals

- [ ] Propose → pause → approve → resume for refunds
- [ ] Refund execution is unreachable without an approval record

**Done when:** a refund cannot execute without approval, and a test proves it.

## 12. Eval gate

- [ ] DeepEval checks with thresholds on every PR
- [ ] A larger nightly run

**Done when:** a deliberately broken prompt fails the PR.
