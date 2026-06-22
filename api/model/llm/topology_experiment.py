from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader

from .handler import call_openai
from .keyword_hints import extract_keyword_hints
from .topology_artifact_model import TopologyArtifact

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

logger = logging.getLogger(__name__)

TOPOLOGY_ARTIFACT_SCHEMA: Dict[str, Any] = TopologyArtifact.model_json_schema()

_TOPOLOGY_TYPE_CANONICALIZATION = {
    "retry": "loop",
}


def build_topology_experiment_prompt(
    process_text: str,
    *,
    keyword_hints: Optional[Dict[str, Any]] = None,
) -> str:
    template = _env.get_template("activity_topology_experiment_prompt.jinja")
    return template.render(
        process_text=process_text,
        keyword_hints=keyword_hints,
    ).rstrip() + "\n"


def topology_artifact_response_format() -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "topology_artifact",
            "schema": TOPOLOGY_ARTIFACT_SCHEMA,
            "strict": True,
        },
    }


def _canonicalize_topology_artifact_payload(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    structures = payload.get("structures")
    if not isinstance(structures, list):
        return payload

    normalized_structures = []
    for structure in structures:
        if not isinstance(structure, dict):
            normalized_structures.append(structure)
            continue
        normalized = dict(structure)
        raw_type = normalized.get("type")
        if raw_type is not None:
            canonical_type = _TOPOLOGY_TYPE_CANONICALIZATION.get(str(raw_type).strip().lower())
            if canonical_type is not None:
                normalized["type"] = canonical_type
        normalized_structures.append(normalized)

    normalized_payload = dict(payload)
    normalized_payload["structures"] = normalized_structures
    return normalized_payload


def parse_topology_artifact_json(raw_output: str) -> Dict[str, Any]:
    parsed_json = json.loads(raw_output)
    canonicalized_payload = _canonicalize_topology_artifact_payload(parsed_json)
    validated = TopologyArtifact.model_validate(canonicalized_payload)
    return validated.model_dump(mode="json")


def generate_topology_artifact(
    process_text: str,
    *,
    model: str = "gpt-4o",
) -> Dict[str, Any]:
    keyword_hints = extract_keyword_hints(process_text)
    prompt = build_topology_experiment_prompt(
        process_text,
        keyword_hints=keyword_hints,
    )
    response_mode = "structured_output"
    fallback_reason = None
    try:
        raw_output = call_openai(
            model=model,
            prompt=prompt,
            response_format=topology_artifact_response_format(),
            require_structured_output=True,
        )
    except Exception as exc:
        response_mode = "fallback_json_mode"
        fallback_reason = str(exc)
        logger.warning(
            "Topology experiment structured output failed; falling back to unconstrained JSON mode.",
            exc_info=True,
        )
        fallback_prompt = (
            prompt
            + "\nFallback instruction:\n"
            + "If structured output is unavailable, still return the same JSON object only."
        )
        raw_output = call_openai(
            model=model,
            prompt=fallback_prompt,
        )
    artifact = parse_topology_artifact_json(raw_output)
    return {
        "keyword_hints": keyword_hints,
        "prompt": prompt,
        "raw_output": raw_output,
        "artifact": artifact,
        "response_mode": response_mode,
        "fallback_reason": fallback_reason,
    }


__all__ = [
    "TOPOLOGY_ARTIFACT_SCHEMA",
    "_canonicalize_topology_artifact_payload",
    "build_topology_experiment_prompt",
    "generate_topology_artifact",
    "parse_topology_artifact_json",
    "topology_artifact_response_format",
]
