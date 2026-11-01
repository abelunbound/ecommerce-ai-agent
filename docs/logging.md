# Logging

Logs answer whether the backend broke. Langfuse, added later, answers why the agent replied as it did. This page covers logs only.

## Levels

| Level | Use |
| --- | --- |
| `DEBUG` | Health checks and local detail. |
| `INFO` | A request finished, or a normal state change. |
| `WARNING` | Something unexpected that the request survived. |
| `ERROR` | A request failed. Include the traceback once. |
| `CRITICAL` | The process cannot continue. |

`LOG_LEVEL` defaults to `DEBUG` when `APP_ENV=local`, otherwise `INFO`. `LOG_FORMAT` defaults to `text` locally and `json` elsewhere. Invalid values stop startup.

## What to log

Log the event and a stable identifier such as `customer_id`, an order number, or a ticket reference. Add structured fields with `extra={"customer_id": customer_id}`.

Never log secrets, card numbers, passwords, email addresses, postcodes, request bodies, headers, or raw prompts. Identify a customer by `customer_id` only. The formatter masks those patterns in the message, in arguments, in `extra`, and in tracebacks. Call `redact()` yourself before storing a chat message.

## Request id

Every API request gets an id. A safe `X-Request-ID` header is kept. Anything else is replaced. The id is returned on the response and attached to every log line as `request_id`. Outside a request the value is `-`.

One line is written when the request finishes: method, path without the query string, status, and `duration_ms`. `/health` is logged at `DEBUG`.

## Adding a pattern

Add a precompiled expression in `backend/app/core/redaction.py` and a test that the raw value is gone and a second `redact()` call does not change the text. Prefer masking too much.
