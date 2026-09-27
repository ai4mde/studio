#!/usr/bin/env python3
"""Draft v1.6 continuous-score contract; no evaluation or API execution."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from evaluation.friedrich_v2.run_ai_v2_calibration import extract_output_text


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "ai_evaluator_v2_output_schema_revision_1_1_continuous_draft.md"
SCHEMA_VERSION = "ai-evaluator-v2/1.1"


def load_schema_wrapper() -> dict[str, Any]:
    text = SCHEMA_PATH.read_text(encoding="utf-8")
    if f"Schema version: `{SCHEMA_VERSION}`" not in text:
        raise ValueError("Draft schema version declaration differs")
    match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
    if not match:
        raise ValueError("Strict schema JSON block not found")
    wrapper = json.loads(match.group(1))
    if wrapper.get("type") != "json_schema" or wrapper.get("strict") is not True:
        raise ValueError("Schema wrapper is not strict json_schema")
    schema = wrapper.get("schema")
    if not isinstance(schema, dict) or schema.get("additionalProperties") is not False:
        raise ValueError("Schema root must be a closed object")
    if set(schema.get("required", [])) != set(schema.get("properties", {})):
        raise ValueError("Every root property must be required")
    if schema["properties"]["schema_version"].get("enum") != [SCHEMA_VERSION]:
        raise ValueError("Schema version enum differs")
    score = schema["properties"]["overall_score"]
    if score.get("type") != "number" or score.get("minimum") != 0.0 or score.get("maximum") != 1.0 or "enum" in score:
        raise ValueError("Score field is not the continuous 0–1 numeric range")
    return wrapper


def validate_result(result: dict[str, Any], case_id: str, candidate_id: str, schema: dict[str, Any]) -> None:
    """The v1.5 runner invariants with only score-dependent checks revised."""
    required = set(schema["required"])
    if set(result) != required:
        raise ValueError(f"Result fields differ from schema: {set(result) ^ required}")
    if result["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Wrong schema_version")
    if result["case_id"] != case_id or result["candidate_id"] != candidate_id:
        raise ValueError("Result identity does not match request")
    score = result["overall_score"]
    if type(score) not in (int, float) or not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise ValueError("overall_score must be a finite number from 0 through 1")
    no_defect = score == 1.0
    if (result["main_error_type"] == "none") != no_defect:
        raise ValueError("Score/main_error_type mismatch")
    if (result["severity"] == "none") != no_defect:
        raise ValueError("Score/severity no-defect invariant failed")
    if bool(result["ambiguity_explanation"]) != bool(result["ambiguity_flag"]):
        raise ValueError("Ambiguity explanation invariant failed")
    if bool(result["review_reason"]) != bool(result["requires_human_review"]):
        raise ValueError("Review reason invariant failed")
    for field in ("action_assessment", "flow_assessment", "control_flow_assessment"):
        value = result[field]
        if not isinstance(value, dict) or set(value) != {"status", "summary"}:
            raise ValueError(f"Invalid {field}")


__all__ = ["SCHEMA_PATH", "SCHEMA_VERSION", "extract_output_text", "load_schema_wrapper", "validate_result"]
