"""BL-1.0: one configuration contract for generation and the generated runtime.

This module deliberately has no Django, provider, or generator imports.
"""
from __future__ import annotations

from copy import deepcopy

CONFIG_VERSION = "1.2"
MODEL_PROFILES = {
    "cheap": {"provider": "groq", "model": "openai/gpt-oss-20b", "timeout_s": 20},
    "strong": {"provider": "openai", "model": "gpt-5.1", "timeout_s": 60},
}
READING_CHAIN = [
    "reading_plan_analyze_taste_v1",
    "reading_plan_recommend_v1",
    "reading_plan_sequence_v1",
]
MAX_PROMPT_CHARS = 60000


class ConfigurationError(ValueError):
    code = "configuration_error"


def validate_ai_config(config, owner_model, owner_attribute):
    """Return a defensive copy; never repair an invalid or legacy configuration."""
    prefix = f"{owner_model}.{owner_attribute}"

    def fail(path, message):
        raise ConfigurationError(f"{prefix}: {path}: {message}")

    def obj(value, path, keys, required=None):
        if not isinstance(value, dict):
            fail(path, "must be an object")
        unknown = set(value) - set(keys)
        if unknown:
            fail(path, f"unsupported keys: {', '.join(sorted(unknown))}")
        missing = set(required if required is not None else keys) - set(value)
        if missing:
            fail(path, f"missing keys: {', '.join(sorted(missing))}")
        return value

    def same(value, expected, path):
        if type(value) is not type(expected) or value != expected:
            fail(path, f"must equal {expected!r}")

    def integer(value, low, high, path):
        if type(value) is not int or not low <= value <= high:
            fail(path, f"must be an integer in {low}..{high}")

    def string(value, maximum, path):
        if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > maximum:
            fail(path, f"must be a trimmed non-empty string of at most {maximum} characters")

    if (owner_model, owner_attribute) not in {("BookLoan", "late_risk"), ("Customer", "reading_plan")}:
        fail("owner", "unsupported Library AI attribute")
    risk = owner_model == "BookLoan"
    cfg = obj(config, "ai_config", {"ai_config_version", "trigger", "context", "template", "model_profile", "output"})
    same(cfg["ai_config_version"], CONFIG_VERSION, "ai_config_version")
    trigger = obj(cfg["trigger"], "trigger", {"type", "class", "on"} if risk else {"type", "class"})
    same(trigger["class"], owner_model, "trigger.class")
    same(trigger["type"], "post_save" if risk else "user_action", "trigger.type")
    if risk:
        same(trigger["on"], "create", "trigger.on")
    context = obj(cfg["context"], "context", {"history", "fields", "relations"}, {"history"})
    for key in ("fields", "relations"):
        if key in context and (not isinstance(context[key], list) or not all(isinstance(x, str) for x in context[key])):
            fail(f"context.{key}", "must be an array of descriptive strings")
    history = obj(context["history"], "context.history", {"scope", "unit", "completed_only", "as_of", "order_by", "limit", "max_scan_records"})
    same(history["scope"], "Loan.Customer", "context.history.scope")
    same(history["unit"], "book_loan", "context.history.unit")
    same(history["completed_only"], True, "context.history.completed_only")
    same(history["as_of"], "loan_date" if risk else "today", "context.history.as_of")
    if history["order_by"] not in ("-return_date", "-loan_date"):
        fail("context.history.order_by", "unsupported order")
    integer(history["limit"], 1, 50, "context.history.limit")
    integer(history["max_scan_records"], history["limit"], 1000, "context.history.max_scan_records")
    if not isinstance(cfg["model_profile"], str) or cfg["model_profile"] not in MODEL_PROFILES:
        fail("model_profile", "unknown model profile")
    template = obj(cfg["template"], "template", {"name"} if risk else {"chain"})
    same(template.get("name") if risk else template.get("chain"), "library_late_risk_v3" if risk else READING_CHAIN, "template")
    output = obj(cfg["output"], "output", {"format", "write_back", "on_skip", "allowed_values", "reason"} if risk else {"format", "write_back", "on_skip"})
    same(output["format"], "risk_label" if risk else "reading_plan", "output.format")
    same(output["write_back"], owner_attribute, "output.write_back")
    string(output["on_skip"], 255, "output.on_skip")
    if risk:
        labels = output["allowed_values"]
        if not isinstance(labels, list) or not 2 <= len(labels) <= 5:
            fail("output.allowed_values", "requires 2..5 labels ordered from lower to higher risk")
        for label in labels:
            string(label, 32, "output.allowed_values")
        if len(set(labels)) != len(labels) or output["on_skip"] in labels:
            fail("output.allowed_values", "labels must be unique and exclude on_skip")
        reason = obj(output["reason"], "output.reason", {"required", "max_length"})
        same(reason["required"], True, "output.reason.required")
        integer(reason["max_length"], 1, 120, "output.reason.max_length")
    return deepcopy(cfg)
