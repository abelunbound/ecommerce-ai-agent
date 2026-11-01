"""Validate the eval case files.

Run standalone:  python evals/validate_cases.py
Run with pytest: pytest evals/validate_cases.py

No LLM calls and no network. Needs only pyyaml.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

BEHAVIOURS = {
    "answer", "tool_answer", "ask_verification", "refuse", "redirect",
    "escalate", "safety_escalate", "admit", "deescalate", "wellbeing", "clarify",
}
TOOLS = {"lookup_order", "search_policies", "create_ticket", "handoff_to_human", "issue_refund"}
SEVERITIES = {"blocker", "major", "minor"}
REGIONS = {"uk", "international"}
EXPECT_KEYS = {
    "behaviour", "sources", "forbidden_sources", "tools", "tools_any", "optional_tools",
    "forbidden_tools", "must_include", "must_not_include", "must_not_leak",
    "log_must_not_contain",
}
CASE_KEYS = {
    "id", "ci", "trap", "customer_region", "customer", "verified", "question",
    "expect", "rubric", "category", "severity", "decision",
}
TRAP_ID = re.compile(r"^[TN]\d{2}$")
PLACEHOLDER = re.compile(r"\{(FX\d+)\}")


def _load(name: str):
    return yaml.safe_load((HERE / name).read_text(encoding="utf-8"))


def _policy_doc_ids() -> set[str] | None:
    folder = ROOT / "data" / "policies"
    if not folder.exists():
        return None
    ids = set()
    for f in folder.glob("*.md"):
        if f.name == "README.md":
            continue
        m = re.match(r"^---\n(.*?)\n---\n", f.read_text(encoding="utf-8"), re.S)
        if m:
            ids.add(yaml.safe_load(m.group(1))["doc_id"])
    return ids


def _register_trap_ids() -> set[str] | None:
    path = HERE / "policy-trap-register.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"^\| ([TN]\d{2}) \|", text, re.M))


def _check_text_rules(case_id: str, key: str, value, problems: list[str]) -> None:
    if not isinstance(value, list):
        problems.append(f"{case_id}: {key} must be a list")
        return
    for item in value:
        ok = isinstance(item, str) or (
            isinstance(item, list) and item and all(isinstance(x, str) for x in item)
        )
        if not ok:
            problems.append(f"{case_id}: {key} entries must be a string or a list of strings")


def validate() -> list[str]:
    problems: list[str] = []
    questions = _load("questions.yaml")
    guardrails = _load("guardrails.yaml")
    fixtures = _load("fixtures.yaml")

    customers = {c["id"] for c in fixtures["customers"]}
    orders = {o["id"]: o for o in fixtures["orders"]}
    for o in orders.values():
        if o["customer"] not in customers:
            problems.append(f"fixture {o['id']}: unknown customer {o['customer']}")
        if ("placed_offset" in o) == ("placed_hours_ago" in o):
            problems.append(f"fixture {o['id']}: give exactly one of placed_offset or placed_hours_ago")

    doc_ids = _policy_doc_ids()
    register = _register_trap_ids()
    if doc_ids is None:
        print("note: data/policies not found, skipping doc_id checks", file=sys.stderr)
    if register is None:
        print("note: policy-trap-register.md not found, skipping trap checks", file=sys.stderr)

    all_cases = [("questions", c) for c in questions["cases"]] + [
        ("guardrails", c) for c in guardrails["cases"]
    ]
    seen: set[str] = set()
    covered: set[str] = set()
    ci_count = 0

    for source, c in all_cases:
        cid = c.get("id", "<missing id>")
        if cid in seen:
            problems.append(f"{cid}: duplicate id")
        seen.add(cid)

        unknown = set(c) - CASE_KEYS
        if unknown:
            problems.append(f"{cid}: unknown keys {sorted(unknown)}")
        for required in ("id", "question", "expect", "rubric"):
            if not c.get(required):
                problems.append(f"{cid}: missing {required}")

        if source == "guardrails":
            if c.get("severity") not in SEVERITIES:
                problems.append(f"{cid}: bad or missing severity")
            if not c.get("category"):
                problems.append(f"{cid}: missing category")

        if c.get("ci"):
            ci_count += 1

        region = c.get("customer_region", "uk")
        if region not in REGIONS:
            problems.append(f"{cid}: bad customer_region {region}")

        customer = c.get("customer")
        if customer is not None and customer not in customers:
            problems.append(f"{cid}: unknown customer {customer}")

        for ref in PLACEHOLDER.findall(c.get("question", "")):
            if ref not in orders:
                problems.append(f"{cid}: question refers to unknown fixture {ref}")
            if customer is None:
                problems.append(f"{cid}: question uses {{{ref}}} but no customer is set")

        trap = c.get("trap")
        if trap:
            if not TRAP_ID.match(trap):
                problems.append(f"{cid}: bad trap id {trap}")
            elif register is not None and trap not in register:
                problems.append(f"{cid}: trap {trap} is not in the register")
            covered.add(trap)

        expect = c.get("expect") or {}
        extra = set(expect) - EXPECT_KEYS
        if extra:
            problems.append(f"{cid}: unknown expect keys {sorted(extra)}")
        if expect.get("behaviour") not in BEHAVIOURS:
            problems.append(f"{cid}: bad behaviour {expect.get('behaviour')}")

        for key in ("tools", "tools_any", "optional_tools", "forbidden_tools"):
            for t in expect.get(key, []):
                if t not in TOOLS:
                    problems.append(f"{cid}: unknown tool {t} in {key}")
        for key in ("sources", "forbidden_sources"):
            for d in expect.get(key, []):
                if doc_ids is not None and d not in doc_ids:
                    problems.append(f"{cid}: unknown doc_id {d} in {key}")
        overlap = set(expect.get("tools", [])) & set(expect.get("forbidden_tools", []))
        if overlap:
            problems.append(f"{cid}: tools both required and forbidden: {sorted(overlap)}")
        overlap = set(expect.get("sources", [])) & set(expect.get("forbidden_sources", []))
        if overlap:
            problems.append(f"{cid}: sources both required and forbidden: {sorted(overlap)}")
        for key in ("must_include", "must_not_include"):
            if key in expect:
                _check_text_rules(cid, key, expect[key], problems)
        for ref in expect.get("must_not_leak", []):
            if ref not in orders:
                problems.append(f"{cid}: must_not_leak refers to unknown fixture {ref}")

    if ci_count == 0:
        problems.append("no cases are marked ci: true")

    if register is not None:
        missing = sorted(register - covered)
        if missing:
            problems.append(f"traps in the register with no case: {missing}")

    return problems


def test_eval_cases_are_valid() -> None:
    problems = validate()
    assert not problems, "\n".join(problems)


if __name__ == "__main__":
    found = validate()
    questions = _load("questions.yaml")["cases"]
    guardrails = _load("guardrails.yaml")["cases"]
    print(f"questions: {len(questions)}, guardrails: {len(guardrails)}")
    print(f"ci cases: {sum(1 for c in questions + guardrails if c.get('ci'))}")
    print(f"problems: {len(found)}")
    for p in found:
        print("  -", p)
    sys.exit(1 if found else 0)
