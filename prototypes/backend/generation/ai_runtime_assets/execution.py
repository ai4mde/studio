"""Shared trace/call boundary. ORM write-back is deliberately outside this module."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from time import monotonic

from .configuration import MAX_PROMPT_CHARS


class PromptBudgetExceeded(ValueError):
    code = "prompt_budget_exceeded"


def digest(value):
    raw = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def safe_error(exc):
    message = str(exc)
    for key in ("OPENAI_API_KEY", "GROQ_API_KEY"):
        secret = os.environ.get(key)
        if secret:
            message = message.replace(secret, "[REDACTED]")
    message = re.sub(r"\b(?:sk-|gsk_)[A-Za-z0-9_-]+", "[REDACTED]", message)
    return {"code": getattr(exc, "code", type(exc).__name__), "message": message}


def prompt_record(name, prompt):
    from .templates import TEMPLATE_DIR, get_template_entry
    if len(prompt) > MAX_PROMPT_CHARS:
        raise PromptBudgetExceeded("Rendered prompt exceeds the deployment character budget")
    entry = get_template_entry(name)
    return {"template": name, "template_sha256": digest((TEMPLATE_DIR / entry.filename).read_text()),
            "prompt": prompt, "prompt_sha256": digest(prompt)}


def perform_call(outcome, config, prompt, purpose):
    from .routing import call_model
    record = {"purpose": purpose, "logical_model_calls": 1, "provider_attempts": 0,
              "external_http_calls": 0}
    outcome.calls.append(record)
    started = monotonic()
    try:
        routed = call_model(config["model_profile"], prompt, purpose=purpose,
                            allowed_values=config["output"].get("allowed_values"), call_record=record)
        outcome.mode = routed["mode"]
        return routed["content"]
    finally:
        record["elapsed_s"] = round(monotonic() - started, 6)
        if "mode" in record:
            outcome.mode = record["mode"]


def write_trace(config, instance, outcome, *, event, created=None):
    from django.conf import settings
    cfg = config if isinstance(config, dict) else {}
    output = cfg.get("output") if isinstance(cfg.get("output"), dict) else {}
    trigger = cfg.get("trigger") if isinstance(cfg.get("trigger"), dict) else {}
    record = {
        "invocation_id": outcome.invocation_id, "timestamp": outcome.evaluated_at,
        "evaluated_at": outcome.evaluated_at, "event": event,
        "model": instance.__class__.__name__, "pk": instance.pk,
        "created": created, "trigger": trigger.get("type"),
        "ai_config_version": cfg.get("ai_config_version"), "config_sha256": digest(cfg),
        "model_profile": cfg.get("model_profile"), "mode": outcome.mode,
        "status": outcome.status, "skip_reason": outcome.skip_reason, "error": outcome.error,
        "as_of": outcome.diagnostics.get("as_of"),
        "assessment_mode": outcome.diagnostics.get("assessment_mode"),
        "diagnostics": outcome.diagnostics, "context": outcome.context,
        "raw_output": outcome.raw_output, "parsed_output": outcome.parsed_output,
        "reason": outcome.reason, "failed_step": outcome.failed_step,
        "step_details": outcome.step_details, "prompts": outcome.prompts, "calls": outcome.calls,
        "call_counts": {key: sum(call.get(key, 0) for call in outcome.calls)
                        for key in ("logical_model_calls", "provider_attempts", "external_http_calls")},
        "write_back": {"field": output.get("write_back"), "intended_value": outcome.value,
                       "requested": outcome.should_write},
    }
    try:
        with (Path(settings.BASE_DIR) / "ai_invocations.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass  # Observability must not break an otherwise valid business request.
