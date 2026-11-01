# Artefacts

Inventory of the synthetic corpus and seed data for Lumen & Oak, compared with the langsmith-agent-lifecycle workshop. Numbers match that list; item 3 is unused.

Policies need a UK region, versions, exceptions, and overlaps. Five policy files are too few, and workshop content is not verified for this store. Order dates are re-based so return windows can be tested. Bitext-style placeholders such as `{{Customer Support Phone Number}}` are cleaned before any phrasing is reused.

| # | Artefact | Purpose | Action |
| --- | --- | --- | --- |
| 1 | Policy documents (8–10 markdown files) | RAG corpus for Pinecone | Create |
| 2 | Policy metadata (front matter: `doc_type`, `region`, `version`, `effective_date`, `source_url`) | Filtering, citations, re-ingestion | Create |
| 4 | Product catalogue and specs | Product questions and return-eligibility rules | Adapt. Add the flags policies reference: final-sale, hygiene, battery items |
| 5 | Customers | Order and account lookup | Adapt to UK addresses, GBP, and this schema |
| 6 | Orders, order items, payments | `lookup_order` | Adapt. Re-base dates to today so return windows can be tested |
| 7 | Order status coverage: delivered, in transit, delayed, cancelled, returned, partially refunded | Tool-routing evals | Create or patch edge-case orders |
| 8 | Shipment and tracking events | "Where's my order?" answers | Create |
| 9 | Returns, refunds, tickets, conversations | Agent writes, handoff, history | Create the schema and a few seed rows |
| 10 | Customer question phrasing | Realistic wording for evals | Reuse phrasing only. Strip placeholders |
| 11 | Golden eval set (question, expected source, expected behaviour) | Measure retrieval and routing | Create, mapped to these policies |
| 12 | Guardrail cases: prompt injection, personal-data requests, off-topic, abusive | Safety evals | Create |
| 13 | `seed_db.py`, `ingest_docs.py` | Reproducible setup | Adapt |
| 14 | Scale corpus | Chunking and retrieval stress test | Optional, later. The workshop corpus is not retail |

Seed data has to support the verification gate: two customers, and at least one order that customer A must not be able to read as customer B.
