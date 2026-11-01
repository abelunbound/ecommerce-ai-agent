# LOG-001: Logging foundation, request tracing, PII redaction and docstring standard

**Type:** Foundation  **Priority:** High  **Do before:** DB-001 (the seed and ingest scripts should use this from the start)
**Suggested location in repo:** `docs/tickets/LOG-001-logging-foundation.md`

## 1. Summary

Add application logging that is safe by default, and set the project's documentation standard:

1. One logging setup for the backend and scripts, using the standard library only.
2. A request ID on every API request, carried through every log line.
3. A redaction layer so card numbers, passwords, emails, postcodes and API keys never reach logs. The same function is reused later to redact chat messages before they are stored.
4. A PEP 257 docstring standard that is robust but not verbose, enforced by Ruff in CI and written into the Cursor project rules.

**Done when:** every log line carries a request ID (or `-` outside a request), sensitive values are masked in messages, arguments, extra fields and tracebacks, `print` is banned in application code, and CI fails on missing or badly formed public docstrings.

## 2. Context

- The agent will handle customer messages. The guardrail eval cases `g-007` (card number pasted into chat) and `g-008` (password pasted into chat) in `evals/guardrails.yaml` require that logs and stored transcripts never contain those values.
- Logs and LLM traces are different things. Logs answer "did the backend break?". Langfuse (a later ticket) answers "why did the agent answer that way?". This ticket covers logs only.
- Assumes `backend/app/core/config.py` (pydantic-settings, `APP_ENV`) and a FastAPI app in `backend/app/main.py` exist. If either is missing, add the minimal version.

## 3. Scope

**In scope:** everything in section 1, plus `docs/logging.md`.

**Out of scope:** Langfuse or other tracing, log shipping or aggregation, Sentry, logging for the Dash frontend (a follow-up), changing business behaviour.

## 4. Decisions already made

- **Standard library `logging` only.** No new runtime dependencies. Write a small JSON formatter.
- **Redaction happens in the formatter**, on the final text, so it covers messages, interpolated arguments, extra fields and exception tracebacks, including logs from third-party libraries.
- **Over-masking is acceptable; under-masking is not.** False positives are fine. False negatives are bugs.
- **Identify customers by internal `customer_id` only** in logs. Never by email, name or postcode.

## 5. Requirements

### 5.1 Settings (`app/core/config.py`)

| Setting | Values | Default |
|---|---|---|
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | `DEBUG` in `local`, otherwise `INFO` |
| `LOG_FORMAT` | `text`, `json` | `text` in `local`, otherwise `json` |
| `LOG_SQL` | bool | `false` (only honoured when `APP_ENV=local`) |

Invalid values fail at startup with a clear error. Add a `Settings.safe_dump()` that returns the settings with every secret masked (use `SecretStr` for keys and passwords), for the startup log line.

### 5.2 `app/core/logging.py`

- `configure_logging(settings)`: **idempotent** (calling it twice never duplicates handlers, so tests can call it freely). One stream handler to stdout on the root logger.
- **Text format:** `2026-11-01T22:00:00Z INFO app.services.chat [req=abc123] message`.
- **JSON format:** one object per line with `timestamp` (UTC, ISO 8601), `level`, `logger`, `message`, `request_id`, and any `extra` fields. Exceptions go in an `exception` field.
- **Request ID** is injected into every record from a context variable (`-` when there is none).
- **Control characters** (`\n`, `\r`) in the message part of a text-format line are escaped, so user input cannot forge extra log lines. Traceback lines keep their newlines.
- **Library noise:** set `httpx`, `httpcore`, `urllib3`, `openai` and `pinecone` loggers to `WARNING`. Take over the `uvicorn` loggers and disable `uvicorn.access`, because the request middleware writes its own access line.
- Every module uses `logger = logging.getLogger(__name__)`. Log calls use lazy formatting (`logger.info("Created ticket %s", ref)`), never f-strings.
- Replace any existing `print` in application code and scripts with logging. Scripts call `configure_logging` at startup.
- On startup, log one line with `APP_ENV`, log level and `safe_dump()`. It must contain no secrets.

### 5.3 Request context and middleware

- `app/core/request_context.py`: a `request_id_var` context variable with `get_request_id()` helper.
- `app/api/middleware.py`: `RequestContextMiddleware`.
  - Accept an inbound `X-Request-ID` only if it matches `^[A-Za-z0-9._-]{8,64}$`. Otherwise generate a new `uuid4().hex`. (This stops header values being used to inject log content.)
  - Set the context variable for the duration of the request, and reset it afterwards.
  - Return the ID in the `X-Request-ID` response header.
  - Write **one** log line per request after it finishes: method, path **without the query string**, status code, `duration_ms`. Never log request bodies or headers. Log `/health` at `DEBUG` to avoid noise.
  - An unhandled exception is logged once, with traceback, and then re-raised. Make sure it is not logged twice.

### 5.4 Redaction (`app/core/redaction.py`)

- `redact(text: str) -> str`: pure, idempotent and fast (precompiled regular expressions). Export it for reuse; the chat service will call it before storing messages.
- Mask these, replacing each with a placeholder:

| Pattern | Placeholder |
|---|---|
| Runs of 13 to 19 digits, optionally separated by single spaces or hyphens (card numbers). No Luhn check, by design | `[card]` |
| Email addresses | `[email]` |
| UK postcodes (for example `SW1A 1AA`, `TE1 1ST`) | `[postcode]` |
| Values after `password`, `passwd`, `pwd`, `secret`, `token`, `api_key` and `apikey`, as `key=value`, `key: value` and JSON `"key": "value"` | `[secret]` |
| `Bearer <token>` and common API key prefixes (`sk-`, `pcsk_`) | `[secret]` |

- Apply redaction to the formatted message, to every string in `extra` fields (recursively), and to the traceback text.
- Do **not** mask things the app needs to log: order numbers (`LO-900001`), RMA and ticket references, tracking numbers, prices (`£12.95`), dates and `customer_id`.

### 5.5 Documentation standard (PEP 257): robust, not verbose

This applies to **all Python code in the repo from now on** (backend, frontend, scripts).

1. Every module has a one-line docstring. Add more only if the module needs orientation.
2. Every public class, function and method has a docstring. The first line is one sentence, in the imperative ("Return the order.", not "Returns the order."), ends with a period, and fits on one line.
3. Add a body (after a blank line) **only** when the behaviour is not obvious from the name and signature: side effects, exceptions callers must handle, units, timezones or currency (pence, UTC), security-relevant behaviour, non-obvious defaults, idempotency. One to three sentences.
4. Do not restate type hints. No `Args:` or `Returns:` sections that repeat the signature. Allowed optional sections: a short `Raises:` for exceptions callers must handle, and a short `Example:` only where it prevents misuse.
5. Private helpers (leading underscore) need a docstring only when non-trivial. Otherwise a `#` comment explaining *why* is enough.
6. No narration of the implementation, no authorship, change history or TODOs in docstrings. Comments explain why, not what.
7. Use triple double quotes. For multi-line docstrings the closing quotes go on their own line.
8. Tests need no docstrings (test names describe the behaviour). Alembic revision files are exempt.

Example of the expected level of detail:

```python
def find_for_verification(self, order_number: str, email: str | None = None,
                          postcode: str | None = None) -> Order | None:
    """Return the order if the email or delivery postcode matches, else None.

    Unknown order, wrong email and wrong postcode all return None, so callers
    cannot tell which one failed.
    """
```

```python
def redact(text: str) -> str:
    """Mask card numbers, emails, postcodes and secrets in text."""
```

**Enforcement**

- Add Ruff rules to `backend/pyproject.toml` (and the frontend's): select `D` with `convention = "pep257"`, plus `G` (logging format) and `T20` (no `print`).
- Per-file ignores: `tests/**` (all `D` rules), `alembic/versions/**` (all `D` rules), `**/__init__.py` (`D104`), and `D107` globally (the class docstring covers `__init__`). If another rule is clearly wrong for this codebase, ignore it and record why in a comment next to the setting.
- **Backfill:** add the missing docstrings to all existing code in the same pull request that turns the rules on, so CI is green.
- Add a "Python conventions" section to the Cursor project rules (`.cursorrules` or `.cursor/rules/`) that restates rules 1 to 8, the logging rules (module logger, lazy formatting, no `print`, no secrets or personal data in logs, `customer_id` only), and the layering rule (repositories are SQL only; business rules live in services).

### 5.6 Documentation

`docs/logging.md`, kept short:
- Log levels and when to use each.
- What to log and what never to log (secrets, card numbers, passwords, emails, postcodes, request bodies, raw prompts).
- How the request ID works and how to add structured fields with `extra={...}`.
- How `redact()` is used, and how to add a pattern.
- The difference between logs and LLM traces.

Update `.env.example` with `LOG_LEVEL=INFO`, `LOG_FORMAT=text`, `LOG_SQL=false`, and link `docs/logging.md` from the README.

## 6. Tests (`backend/tests/`)

No network and no API keys.

**Formatting**
- Text and JSON output have the expected fields. JSON lines parse. Timestamps are UTC.
- A message containing `a\nINFO forged` does not produce a second log line in text format.
- `configure_logging` called twice produces one handler. Invalid settings values raise.

**Request ID**
- Generated when absent. A valid inbound ID is kept. An invalid one (spaces, newline, too long, too short) is replaced.
- Echoed in the response header. A record logged inside a request carries the ID. The context variable is reset afterwards, so a later log outside a request shows `-`.
- The request line has method, path without the query string, status and `duration_ms`. Request bodies and headers never appear. An unhandled exception is logged exactly once.

**Redaction**
- Cards: `4111 1111 1111 1111`, `4111111111111111` and `4111-1111-1111-1111` become `[card]`.
- Emails, UK postcodes (`SW1A 1AA`, `te1 1st`), `password=Hunter2!`, `{"password": "Hunter2!"}`, `Bearer abc.def`, `sk-...` and `pcsk_...` are masked.
- Masking works in messages, in interpolated arguments, in `extra` fields (nested), and in exception tracebacks.
- Not masked: `LO-900001`, `RMA-...`, `TKT-...`, `£12.95`, `2026-10-27`, tracking numbers, `customer_id=12`.
- `redact(redact(x)) == redact(x)`.
- `Settings.safe_dump()` contains no secret values.

**Lint**
- CI passes with the `D`, `G` and `T20` rules on. A deliberately undocumented public function fails the lint step (check this once, then remove it).

## 7. CI

Extend the existing backend job: `ruff check` and `ruff format --check` with the new rules, then `pytest`. No secrets needed.

## 8. Changes to other tickets

Add to **DB-001** section 15 (notes for the implementer): "Use the `logging` module in `seed_db.py` and `ingest_docs.py`, call `configure_logging` at start-up, never use `print`, and never log API keys or personal data. Follow the docstring standard in LOG-001 section 5.5."

## 9. Suggested pull requests

| PR | Contents |
|---|---|
| 1 | Docstring standard: Ruff rules, backfill of existing docstrings, Cursor project rules |
| 2 | Settings additions, `core/logging.py`, `core/redaction.py`, tests |
| 3 | Request context, middleware, request log line, tests, replace `print` in existing code |
| 4 | `docs/logging.md`, `.env.example`, README link |

## 10. Definition of done

- [ ] All four PRs merged and CI green.
- [ ] Every log line has a request ID (or `-`), in text and JSON formats.
- [ ] Redaction verified for messages, arguments, extra fields and tracebacks, with no false negatives in the tests above.
- [ ] No `print` in application code or scripts. CI fails if one is added.
- [ ] Public modules, classes and functions all have PEP 257 docstrings, and CI fails when one is missing.
- [ ] The Cursor project rules contain the Python conventions.
- [ ] `g-007` and `g-008` can later assert `log_must_not_contain` against captured logs (the redaction tests prove the mechanism).