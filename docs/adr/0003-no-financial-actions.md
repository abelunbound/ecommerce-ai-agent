# ADR 0003 — No financial actions without approval

- Status: Accepted
- Date: 2026-11-01
- Related: [ADR 0001](0001-scope.md), [ADR 0002](0002-non-goals.md)

## Context

Customers will ask for refunds and cancellations. Those requests change money. An autonomous tool that calls a payment API, or that marks an order refunded in the database, can do harm even when the policy text would allow the refund. The prototype has to show the safe path: understand the request, check policy and order state, and stop for a person.

## Decision

The agent may:

- Explain refund, cancellation, and return rules from retrieved policy, with citations.
- Look up the order, once the customer is verified.
- Propose a refund or cancellation by writing a **pending action**.
- Pause the conversation until a person approves or rejects that action.
- Create a ticket and hand the case to a human.

The agent may not:

- Execute a refund, cancellation, or any other movement of money.
- Call a payment provider.
- Update payment or refund rows to a completed state.
- Resume a paused financial action unless an approval record exists for that pending action.

There is no tool whose success path settles money. The only write on this path is the pending action (and, when appropriate, a ticket). A later executor, if one is added, refuses to run when the approval record is missing. The prototype ships with that refusal tested.

Customer verification is a separate gate on order lookup. Passing it does not authorize a refund.

## Consequences

- Tooling exposes `pending_actions`, not `refund_order` or `cancel_order`.
- The admin UI is an approval queue. Approving records a decision. It is the only way a paused refund continues.
- Routing evals expect a refund request to propose and pause.
- A test must fail if any code path completes a refund without an approval record.
- Traces and logs store the proposal and the decision. They do not need card numbers or full payment payloads, and personal data is redacted.
