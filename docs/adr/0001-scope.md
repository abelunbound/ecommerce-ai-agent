# ADR 0001 — Scope of the prototype

- Status: Accepted
- Date: 2026-11-01

## Context

Lumen & Oak needs a support assistant that uses the store's policies and order system. The first build has to be demonstrable and measurable, and small enough to finish as a prototype that can grow into an MVP. A fictional UK retailer and synthetic data remove any need for real customer information while the evaluation set and the tool boundary are still being proven.

## Decision

The prototype includes:

1. Policy Q&A with citations, grounded in retrieved passages.
2. Order lookup through backend tools (status, items, delivery estimates), after the customer is verified.
3. Ticket creation.
4. Human handoff when a question is out of scope, a policy is ambiguous, or the customer is frustrated.
5. Conversation history, so follow-up turns keep context.
6. A Dash chat UI, and later an admin page for approvals.
7. An evaluation harness: a golden set, retrieval checks, routing checks, and a CI gate.

The assistant admits when the policies do not support an answer. Personal data is redacted from prompts and logs, and the agent stays on support topics.

## Consequences

- Every in-scope behaviour needs at least one eval case with an expected answer or an expected tool.
- Order data lives in the relational database. It is not embedded.
- UI, API, services, repositories, retrieval, and the agent stay in separate modules so each can be tested and replaced.
- Work outside this list waits for [ADR 0002](0002-non-goals.md), unless a later ADR explicitly pulls one item forward.
