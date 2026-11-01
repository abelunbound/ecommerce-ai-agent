# ADR 0004 — Single agent for the prototype

- Status: Accepted
- Date: 2026-11-01
- Related: [ADR 0001](0001-scope.md), [ADR 0003](0003-no-financial-actions.md)

## Context

A production support system can justify several agents: one for policy documents, one for order data, and a supervisor that routes between them. That split costs a routing layer, extra prompts, and evals for handoffs between agents. The prototype's open question is simpler: given one customer message, does the system answer from policy, call the right tool, or stop for a human?

The tools themselves will still exist as separate services. The choice here is how many model-driven agents sit in front of them.

## Decision

The prototype runs **one orchestrator**.

It is given the conversation, the retrieved policy passages, and these tools:

- `lookup_order` — order status, items, and delivery estimates, behind the customer-verification gate
- `search_policies` — metadata-filtered retrieval over the policy pack
- `create_ticket` — handoff record when the agent should stop
- `pending_actions` — propose a refund or cancellation and pause

Tool calling uses the OpenAI tools API. LangGraph is optional in the prototype and is the intended mechanism for the approval interrupt (propose, pause, approve, resume). Prompts are versioned. Guardrails redact personal data and keep turns on support topics.

The MVP and production design replaces this with three agents coordinated by LangChain, LangGraph, and LangSmith:

- a **documents agent** for policy retrieval and cited answers
- a **database agent** for order and account tools
- a **supervisor** that routes between them and owns handoff

That split waits until the single-agent routing evals are stable. The service and repository boundaries stay as they are, so the later split changes the orchestrator and not the order or ticket code.

## Consequences

- Routing evals have one decision point: the right tool, a grounded answer, a clarifying question, or a handoff.
- Adding a second agent in the prototype is a change to this ADR, not a local refactor.
- Approval pauses are modeled as state on the conversation and the pending action, so they survive a process restart and can move under a supervisor later.
- LangSmith-wide tracing is an MVP concern. The prototype traces with Langfuse.
