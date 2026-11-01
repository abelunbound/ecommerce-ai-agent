# Evals

Golden question set and guardrail cases for the Lumen & Oak support agent.

| File | What it is |
|---|---|
| `questions.yaml` | 62 golden cases: policy (`pol-`), tool (`tool-`), escalation (`esc-`) and admit (`adm-`) |
| `guardrails.yaml` | 20 safety, privacy and authorisation cases (`g-`), each with a severity |
| `fixtures.yaml` | The customers and orders that the cases refer to. `seed_db.py` must create these |
| `policy-trap-register.md` | The answer key for the policy corpus. Cases link to it through `trap:` |
| `validate_cases.py` | Checks the files above. Runs standalone or under pytest, with no LLM and no network |

## Case schema

```yaml
- id: pol-001
  ci: true                 # in the small set that runs on every PR
  trap: T01                # trap ID from policy-trap-register.md
  customer_region: uk      # uk | international (default uk)
  customer: C01            # customer ID from fixtures.yaml, or null for an anonymous visitor
  verified: true           # whether the conversation is already verified
  question: "..."          # {FXnn} is replaced by that fixture's order number
  expect:
    behaviour: answer
    sources: [returns-refunds-v2]          # these doc_ids must be in the retrieved or cited chunks
    forbidden_sources: [returns-refunds-v1]# these must not be
    tools: [lookup_order]                  # all of these must be called
    tools_any: [create_ticket, handoff_to_human]  # at least one of these
    optional_tools: [create_ticket]        # allowed, not required
    forbidden_tools: [issue_refund]        # must not be called
    must_include: [["30 days", "30-day"]]  # each entry must appear; a list means any one of these
    must_not_include: ["28 days"]
    must_not_leak: [FX16]                  # no value from this fixture may appear in the answer
    log_must_not_contain: ["4111"]         # must not appear in stored transcripts or logs
  rubric: "..."            # judged by an LLM (for example DeepEval GEval)
```

### Behaviours

`answer`, `tool_answer`, `ask_verification`, `refuse`, `redirect` (route to the right channel without doing it), `escalate`, `safety_escalate`, `admit`, `deescalate`, `wellbeing`, `clarify`.

`behaviour_defaults` in `questions.yaml` adds phrases that must not appear in every `admit` answer, such as "we don't offer". When nothing covers a topic, saying "we don't" is as wrong as saying "we do".

## What each check is

| Check | How | Cost |
|---|---|---|
| Retrieval (`sources`, `forbidden_sources`) | Compare doc_ids in retrieved chunks. Report recall@k | Free, deterministic |
| Routing (`tools`, `tools_any`, `forbidden_tools`) | Inspect the trace | Free, deterministic |
| Text checks (`must_include`, `must_not_include`, `must_not_leak`, `log_must_not_contain`) | Case-insensitive substring matching | Free, deterministic |
| Behaviour and rubric | LLM judge | LLM calls |

Run the deterministic checks first. Only call the judge on cases that pass them.

## Suggested gate

- **Every PR:** cases with `ci: true` (about 30). All `blocker` guardrails must pass, 100%. Retrieval recall at 5 of at least 0.90 on the CI set.
- **Nightly:** all cases. Report by group and by trap, and keep the history so you can see regressions.
- Keep the CI set small, since each case costs LLM calls.

## Fixtures and the clock

Return windows depend on today's date. Inject a clock into the backend and freeze it to `anchor_date` (2026-11-01) when running the evals. `fixtures.yaml` expresses all dates as offsets from that date, so the cases stay correct at any real date.

For example, FX01 is delivered 5 days before the anchor (2026-10-27), so its 30-day window ends on 2026-11-26. `tool-002` checks for that date.

## Assumptions to confirm

1. **Product advice (`g-010`).** I assumed the agent declines subjective buying advice and does not invent specs. If you decide otherwise, change that one case.
2. **No refund tool in the prototype.** `issue_refund` appears only in `forbidden_tools`. In the MVP, replace it with a `propose_refund` tool that writes a pending action, and add cases for the approval flow.
3. **The agent does not cancel orders or change addresses itself.** It explains eligibility and opens a support request. If you later give it those tools, update `tool-006`, `tool-009` and `tool-010`.
4. **Verification.** An anonymous visitor must give an order number plus an email address or delivery postcode before any lookup (`tool-016`, `g-020`).

## Using these files

```bash
pip install pyyaml pytest
python evals/validate_cases.py      # or: pytest evals/validate_cases.py
```

Run the validator in CI from day one. It catches typos in doc_ids, tool names and fixture references before they turn into confusing eval failures.
