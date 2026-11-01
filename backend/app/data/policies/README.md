# Lumen & Oak policy corpus

Synthetic policies for a fictional UK online retailer of consumer electronics and home-office accessories. Nothing here is real or legal advice. Every file has `synthetic: true` in its front matter.

## Files

| File | doc_id | Region | Status |
|---|---|---|---|
| returns-refunds-v2.md | returns-refunds-v2 | global | current |
| returns-refunds-v1.md | returns-refunds-v1 | global | superseded |
| shipping-uk.md | shipping-uk | uk | current |
| shipping-international.md | shipping-international | international | current |
| order-cancellations-and-changes.md | order-cancellations-and-changes | global | current |
| warranty-and-faulty-goods.md | warranty-and-faulty-goods | global | current |
| payments-and-billing.md | payments-and-billing | global | current |
| promotions-and-gift-cards.md | promotions-and-gift-cards | global | current |
| account-and-privacy.md | account-and-privacy | global | current |
| contact-and-escalation.md | contact-and-escalation | global | current |

## Front matter fields

`doc_id`, `title`, `doc_type`, `region` (`uk`, `international` or `global`), `version`, `status` (`current` or `superseded`), `effective_date`, `end_date`, `supersedes`, `superseded_by`, `last_reviewed`, `source_url`, `tags`, `synthetic`.

Store all of these as Pinecone metadata, except `tags` if you want to keep it small.

## Ingestion rules

1. Skip this `README.md`. Do not ingest anything from `evals/`.
2. Ingest **superseded files too**, with `status` in the metadata. The retriever must filter them out, and the evals check that it does.
3. Split on `##` and `###` headings. Prepend the heading path to each chunk, for example `Returns and Refunds Policy > Return shipping costs > UK orders`.
4. Keep each `### Q:` FAQ entry as its own chunk.
5. Keep tables whole. Do not split a table across chunks.
6. Use deterministic chunk IDs: `{doc_id}:{section-slug}:{index}`.

## Query-time filters

- `status = "current"`
- `region` in `{customer_region, "global"}`, where `customer_region` is `uk` or `international`

## Simulated URLs

`source_url` values use the reserved `.example` domain, so they can never resolve to a real site. For local use, serve the files from FastAPI and map the path:

`https://lumenandoak.example/policies/<slug>` to `http://localhost:8000/policies/<slug>`

Keep the base URL in config (for example `POLICY_BASE_URL`) and rewrite it when building citations.

## Files that reference each other

The policies link to one another by `source_url`. That is deliberate: it gives you realistic cross-document references to test.
