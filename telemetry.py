"""
Per-request telemetry — the capstone's instrumentation layer.

`audit.py` records *decisions* (nine fields, append-only, unit 7/8). This module
records *requests*: one JSON line in `logs/requests.jsonl` for every call to
`/submit`, whatever happened to it — a decision, a refusal, a 429, a crash.

Why a second file: the audit log's shape is fixed so unit 8's entries stay
comparable with new ones, and it only knows about requests that reached a
handler branch that logs. A request that dies before that point (a rate-limit
rejection, an unexpected exception) would be an absence. This one is written by
Flask hooks, so it sits outside the handler and cannot be skipped by it.

Fields:

    timestamp        UTC, ISO-8601, seconds
    request_id       12 hex chars, also returned to the caller in X-Request-Id
    route            "/submit"
    creator_id       who it counted against (or null)
    text_type        python type name of the `text` field ("str", "NoneType"...)
    text_chars       length of text, if a string
    text_hash        first 12 hex of sha256(text) — same input, same hash
    status_code      HTTP status sent back
    outcome          decided | rejected | rate_limited | error
    reason           the `error` code in the response body, if any
    content_id       decision id, if one was made
    guess, label_short, confidence, model_score, style_score
    duration_ms      wall-clock, before_request to after_request
    cpu_ms           CPU time of this process over the same span
    detector_cold    True if the model had to be loaded during this request
"""

import hashlib
import json
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

import config

_lock = threading.Lock()


def start(detector_cold: bool) -> dict:
    """Open a timing context at the top of a request."""
    return {
        "request_id": uuid.uuid4().hex[:12],
        "t0": time.perf_counter(),
        "c0": time.process_time(),
        "detector_cold": detector_cold,
    }


def _outcome(status: int) -> str:
    if status == 200:
        return "decided"
    if status == 429:
        return "rate_limited"
    if status >= 500:
        return "error"
    return "rejected"


def finish(ctx: dict, req, resp) -> dict | None:
    """
    Close the context and write the record. Never raises: a broken log must not
    turn a good response into a bad one.
    """
    try:
        body = req.get_json(silent=True)
        body = body if isinstance(body, dict) else {}
        text = body.get("text")
        creator = body.get("creator_id")
        out = resp.get_json(silent=True) if resp.is_json else None
        out = out if isinstance(out, dict) else {}

        t0 = ctx.get("t0")
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "request_id": ctx["request_id"],
            "route": req.path,
            "creator_id": creator if isinstance(creator, str) else None,
            "text_type": type(text).__name__,
            "text_chars": len(text) if isinstance(text, str) else None,
            "text_hash": (hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:12]
                          if isinstance(text, str) else None),
            "status_code": resp.status_code,
            "outcome": _outcome(resp.status_code),
            "reason": out.get("error"),
            "content_id": out.get("content_id"),
            "guess": out.get("guess"),
            "confidence": out.get("confidence"),
            "model_score": out.get("model_score"),
            "style_score": out.get("style_score"),
            "duration_ms": round((time.perf_counter() - t0) * 1000, 1) if t0 else None,
            "cpu_ms": round((time.process_time() - ctx["c0"]) * 1000, 1) if t0 else None,
            "detector_cold": ctx.get("detector_cold"),
        }
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False)
        with _lock:
            with config.REQUEST_LOG.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        return record
    except Exception as exc:  # noqa: BLE001
        print(f"[telemetry] could not write record: {exc!r}", file=sys.stderr)
        return None


def read_records(limit: int | None = None) -> list[dict]:
    """The request log, oldest first. Bad lines are skipped, as in audit.py."""
    if not config.REQUEST_LOG.exists():
        return []
    rows = []
    for line in config.REQUEST_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-limit:] if limit else rows
