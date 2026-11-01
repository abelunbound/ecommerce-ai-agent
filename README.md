ecommerce-support-agent/
├── .env.example                  # committed, no real values
├── .env.local / .env.dev / .env.staging   # gitignored
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


source .venv/bin/activate
pip install 'detect-secrets==1.5.0'
detect-secrets scan --exclude-files '\.env$|\.venv/' > .secrets.baseline

git add .secrets.baseline
git commit -m "Add detect-secrets baseline"