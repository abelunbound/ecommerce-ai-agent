# ADR 0002 — Non-goals

- Status: Accepted
- Date: 2026-11-01
- Related: [ADR 0001](0001-scope.md), [ADR 0003](0003-no-financial-actions.md), [ADR 0004](0004-single-agent.md)

## Context

The prototype is a single-store support assistant with synthetic data. Several capabilities are real product requirements and are still the wrong work for this stage. Writing them down keeps the evaluation set, the schema, and the UI from growing to fit them early.

## Decision

The prototype leaves these out:

1. **Financial actions on the agent's own authority.** Refunds and cancellations require a person. The boundary is [ADR 0003](0003-no-financial-actions.md). The prototype may propose and pause. It does not execute.
2. **Voice and other channels.** Chat over HTTP is the only surface. Email, phone, and in-app messaging wait.
3. **Real customer data.** Customers, orders, payments, and policies are synthetic. UK addresses, GBP, and dates re-based so return windows can be tested.
4. **Multi-tenant stores.** One retailer, Lumen & Oak. No store isolation, no per-tenant indexes, no per-tenant policy packs.
5. **A multi-agent runtime.** One orchestrator until the MVP. See [ADR 0004](0004-single-agent.md).
6. **Production platform pieces.** Reranking, Redis, Sentry, cloud hosting, and a secret manager belong to the MVP and production stack.

An optional large corpus for chunking stress tests is also deferred. The retail policy pack is the corpus that matters now.

## Consequences

- A feature that needs a second store, a second channel, or live customer data is out of scope until this ADR is superseded.
- Schema and seed data still include returns, refunds, and tickets, because handoff and the approval queue need rows to read and write. Those tables do not imply that the agent may settle money.
- Eval cases for out-of-scope asks expect a refusal or a handoff, not a partial implementation of the excluded feature.
