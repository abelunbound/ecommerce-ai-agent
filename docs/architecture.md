# Ecommerce Support Agent

The Ecommerce Support Agent is a customer-support assistant for **Lumen & Oak**, a fictional UK retailer. It answers questions about policies, orders, and accounts in natural language, using the store's own documentation and live order data. Where it cannot help safely, it hands the conversation to a human.

The project is a working prototype structured so it can grow into an MVP and a production system. Policies and seed data are synthetic, so the system can be developed, tested, and demonstrated without real customer information.

## Objective

Build a realistic retrieval-plus-tools support agent end to end, with ordinary engineering practice around it.

Quality is measured with an evaluation set of answerable, tool-requiring, and out-of-scope questions, so a change to chunking, models, or prompts is judged on evidence. Providers stay swappable through configuration wherever that is cheap. The database path is SQLite for local prototype work, with PostgreSQL in CI from the first migration and as the database for the MVP and production.

Decisions that bound this design are recorded in:

- [ADR 0001 — Scope](adr/0001-scope.md)
- [ADR 0002 — Non-goals](adr/0002-non-goals.md)
- [ADR 0003 — No financial actions](adr/0003-no-financial-actions.md)
- [ADR 0004 — Single agent for the prototype](adr/0004-single-agent.md)

The corpus and seed-data inventory is in [Artefacts](artefacts.md).

## What a customer can do

- Ask about returns, shipping, warranty, payments, and promo codes. The answer is written from retrieved policy passages and cites its source.
- Ask about an order. Status, delivery estimates, and items come from backend tools. Order rows are never embedded in the vector index.
- Get a support ticket and a human handoff when the question is out of scope, a policy is ambiguous, or the customer is frustrated.
- Hear a direct admission when the policies do not support an answer.
- Ask a follow-up. Conversation history is stored and sent with the next turn.

## How a request moves

```
Dash chat
  → httpx POST /chat
    → API (validate, load conversation)
      → guardrails (redact personal data, keep the turn on support topics)
        → orchestrator
            → retriever (embed the question, filter chunks by metadata)
            → tools (order lookup, policy search, ticket, pending action)
              → services
                → repositories
                  → SQLite or Postgres
        → persist the turn
      → response with source links
    → Dash renders the answer
```

Langfuse records the prompt, the retrieved chunks, and any tool calls for that turn.

Financial actions leave this path at the tool boundary. A refund or cancellation is written as a pending action and the turn pauses for a person. Nothing in the agent loop charges, refunds, or cancels. See [ADR 0003](adr/0003-no-financial-actions.md).

### Offline ingestion

Policy markdown is split into chunks, embedded, and upserted to Pinecone with metadata: document type, region, version, effective date, and source URL. Ingestion is a script, not part of the chat request. Re-running it for a new policy version replaces the chunks that version supersedes.

### Retrieval

At question time the customer's question is embedded and matched against stored chunks. Metadata filters restrict the search to the relevant region and the current policy version before any model sees the passages.

### Agent loop

The prototype has one orchestrator. It receives the question, the retrieved passages, the conversation so far, and the tool list. It answers from policy, calls a tool, creates a ticket, or escalates. The tool set and the later multi-agent split are described in [ADR 0004](adr/0004-single-agent.md).

## Packages and layers

Two installable packages. The web layer does not import the vector store or the model client directly; services do.

```
backend/
  app/
    api/            FastAPI routes: /health, /chat, /orders
    schemas/        Pydantic request and response models
    services/       Use cases. The only layer the API calls for work
    repositories/   SQLAlchemy queries. No HTTP, no model calls
    agent/          Orchestrator, versioned prompts, guardrails, tool adapters
    rag/            Chunking, ingestion, retriever
    core/           pydantic-settings, env selection
  alembic/          Migrations that apply on SQLite and Postgres
frontend/
  app/
    main.py         Dash entrypoint
    layout.py       Chat page, later an admin approvals page
    api_client.py   httpx calls to FastAPI
    config.py       Frontend settings
```

Dependency direction:

```
api → services → repositories
              → agent → rag
                     → services
```

`repositories` and `rag` do not import `api`. Tools are thin adapters over services, so order lookup, ticket creation, and the customer-verification gate have unit tests that never call a model.

## Environments

| Environment | Role | Database | Vector index | Secrets |
| --- | --- | --- | --- | --- |
| local | Day-to-day prototype | SQLite file | Pinecone dev index | `.env.local` |
| dev | Shared integration | Postgres | Pinecone dev index | `.env.dev` |
| staging | Pre-production | Postgres | Separate index | Secret manager, later |
| production | Live | Postgres | Separate index | Secret manager, later |

`APP_ENV` selects `.env.{APP_ENV}`. A missing required value fails process startup. CI runs the same migrations and tests against SQLite and Postgres from the first schema change.

## Prototype stack

| Layer | Tool | Role |
| --- | --- | --- |
| Language | Python 3.11+, venv | Runtime |
| Backend | FastAPI, Uvicorn | `/health`, `/chat`, `/orders` |
| Frontend | Plotly Dash | Chat, later admin and eval views |
| HTTP | httpx | Dash to FastAPI |
| Schemas and config | Pydantic, pydantic-settings | Requests, responses, typed env |
| Database | SQLite locally, PostgreSQL in CI and later stages | Customers, orders, conversations, tickets, pending actions |
| ORM and migrations | SQLAlchemy 2.0, Alembic | Access and schema versioning across both databases |
| Vectors | Pinecone | Policy-chunk search. Needs an API key |
| Model | OpenAI chat model | Answers and tool decisions. Needs an API key |
| Embeddings | OpenAI `text-embedding-3-small` | Chunks and queries. Same key |
| Orchestration | OpenAI tool calling; LangGraph optional | Agent loop. LangGraph is the intended place for approval interrupts |
| Tests | pytest, pytest-asyncio | Unit and integration |
| Tracing | Langfuse | Prompts, retrievals, tool calls. Separate key |
| Evals | Golden set, retrieval and routing checks, DeepEval | PR gate, plus a larger nightly run |
| CI | GitHub Actions | Lint, types, tests, and evals on push and pull request |
| Handoff | Pending-action record and a human approval | Required before any refund or cancellation |

## Later stack

These arrive with the MVP and production, and are not part of the prototype:

| Tool | Role |
| --- | --- |
| Pinecone reranker or Cohere Rerank | Reorder retrieved chunks |
| Redis | Cache, rate limit, session state |
| Sentry | Error monitoring |
| Cloud hosting (GCP) | Staging and production |
| Secret manager | Staging and production secrets |
| LangChain, LangGraph, LangSmith throughout | Multi-agent orchestration: a documents agent, a database agent, and a supervisor |

## Five-minute version

Lumen & Oak's assistant answers policy questions from retrieved store documents, looks up orders through tools, and keeps the thread. It creates a ticket or escalates when it should not continue alone. It can propose a refund and then wait. It cannot issue one. The prototype is one agent, synthetic UK data, a Dash chat, and an eval set that fails a change when answers, routing, or that boundary regress.
