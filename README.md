# Ecommerce Support Agent

The Ecommerce Support Agent is a customer-support assistant for **Lumen & Oak**, a fictional UK retailer. It answers questions about policies, orders, and accounts in natural language, using the store's own documentation and live order data. Where it cannot help safely, it hands the conversation to a human.

The project is a working prototype structured so it can grow into an MVP and a production system. Policies and seed data are synthetic, so the system can be developed, tested, and demonstrated without real customer information.

Logging rules are in [docs/logging.md](docs/logging.md).

## Objective

Build a realistic retrieval-plus-tools support agent end to end, with ordinary engineering practice around it.

Quality is measured with an evaluation set of answerable, tool-requiring, and out-of-scope questions, so a change to chunking, models, or prompts is judged on evidence. Providers stay swappable through configuration wherever that is cheap. The database path is SQLite for local prototype work, with PostgreSQL in CI from the first migration and as the database for the MVP and production.

```text
ecommerce-support-agent/
├── .env               # committed, no real values
├── docker-compose.yml            # local Postgres (+ optional services)
├── Makefile
├── README.md
├── docs/
│   └── architecture.md
├── scripts/
│   ├── ingest_docs.py            # load policies/FAQs → chunk → embed → Pinecone
│   └── seed_db.py                # fake customers/orders for dev
├── evals/                        # golden Q&A set, retrieval + answer quality checks
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/                  # migrations (SQLite → Postgres path)
│   ├── tests/                    # unit / integration
│   └── app/
│       ├── main.py
│       ├── api/
│       │   ├── deps.py
│       │   └── v1/               # chat.py, conversations.py, orders.py, health.py, admin.py
│       ├── core/                 # config.py (pydantic-settings), logging, security
│       ├── db/                   # session.py, base.py, models/ (SQLAlchemy ORM)
│       ├── schemas/              # Pydantic request/response models
│       ├── repositories/         # customer, order, conversation, ticket (SQL only)
│       ├── services/             # chat_service, order_service, ticket_service, escalation
│       ├── rag/
│       │   ├── ingestion/        # loaders, chunking, metadata
│       │   ├── vectorstore.py    # Pinecone client/wrapper
│       │   └── retriever.py      # query → top-k chunks (+ rerank, filters)
│       ├── agent/
│       │   ├── orchestrator.py   # the loop / graph
│       │   ├── tools/            # lookup_order, search_policies, create_ticket, handoff_to_human
│       │   ├── prompts/          # system prompts as versioned files
│       │   └── guardrails.py     # PII redaction, refusal rules, scope checks
│       ├── llm/                  # thin provider interface (OpenAI / Anthropic)
│       └── data/                 # sample docs, seed data
│
└── frontend/                     # same shape as yours
    └── app/ (assets, callbacks, components, pages, api_client.py, config.py, layout.py, main.py)
```


### Secrets Baseline
source .venv/bin/activate
pip install 'detect-secrets==1.5.0'
detect-secrets scan --exclude-files '\.env$|\.venv/' > .secrets.baseline

git add .secrets.baseline
git commit -m "Add detect-secrets baseline"