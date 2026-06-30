import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from django.conf import settings
from pydantic import create_model

from .context import build_context
from .parsers import JsonOutputParser
from .routing import call_model
from .templates import render_prompt

LOG_PATH = Path(settings.BASE_DIR) / "ai_invocations.jsonl"


def _build_output_schema(write_back, allowed_values):
    # M05 declarative output spec drives the M03 validation schema.
    if not write_back:
        raise ValueError("ai_config.output.write_back is required")
    if not allowed_values:
        raise ValueError("ai_config.output.allowed_values is required for risk_label output")
    annotation = Literal[tuple(allowed_values)]
    return create_model("AiOutput", **{write_back: (annotation, ...)})


def invoke(ai_config, instance):
    """Step 7 - full runtime for one AI-managed attribute. Orchestrates
    M02 context -> M01 render -> M06 route -> M03 parse, logs a full trace, and returns the
    parsed write-back value (or None). The generated hook performs the ORM write-back."""
    model_profile = ai_config.get("model_profile")
    template_name = ai_config["template"]["name"]
    output_cfg = ai_config.get("output", {})
    write_back = output_cfg.get("write_back")
    allowed_values = output_cfg.get("allowed_values")

    context = build_context(ai_config, instance)          # M02
    prompt = render_prompt(template_name, context)        # M01
    routed = call_model(model_profile, prompt)            # M06
    raw = routed.get("content", "")

    schema = _build_output_schema(write_back, allowed_values)   # M05 -> M03
    parsed = JsonOutputParser(schema).parse(raw)               # M03
    value = getattr(parsed.data, write_back) if parsed.success else None

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "invoke",
        "trigger": ai_config.get("trigger", {}).get("type"),
        "model": instance.__class__.__name__,
        "pk": instance.pk,
        "model_profile": model_profile,
        "mode": routed.get("mode"),
        "provider": routed.get("provider"),
        "routed_model": routed.get("model"),
        "template": template_name,
        "context": context,
        "raw_output": raw,
        "parsed_output": value if parsed.success else None,
        "write_back": {"field": write_back, "value": value},
        "status": "success" if parsed.success else "parse_error",
        "error": None if parsed.success else {"code": parsed.error.code, "message": parsed.error.message},
        "ai_config_version": ai_config.get("ai_config_version"),
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return value