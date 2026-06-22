from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from .handler import call_openai
from .keyword_hints import extract_keyword_hints
from .semantic_sketch_plan_model import SemanticSketchPlan
from .topology_artifact_model import TopologyArtifact

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

logger = logging.getLogger(__name__)

SEMANTIC_SKETCH_PLAN_SCHEMA: Dict[str, Any] = SemanticSketchPlan.model_json_schema()


class SemanticSketchPlanGenerationError(Exception):
    def __init__(self, message: str, *, debug_artifacts: Dict[str, Any]) -> None:
        super().__init__(message)
        self.debug_artifacts = debug_artifacts


def _normalize_topology_artifact(topology_artifact: Dict[str, Any] | TopologyArtifact) -> TopologyArtifact:
    if isinstance(topology_artifact, TopologyArtifact):
        return topology_artifact
    return TopologyArtifact.model_validate(topology_artifact)


def _build_root_slots(artifact: TopologyArtifact) -> List[Dict[str, str]]:
    root_structures = [structure for structure in artifact.structures if structure.parent == "ROOT"]
    slots: List[Dict[str, str]] = [
        {
            "slot_id": "ROOT_START",
            "description": (
                f"Action before the first root structure {root_structures[0].id}"
                if root_structures
                else "Primary root-scope action for a linear process"
            ),
        }
    ]
    for structure in root_structures:
        slots.append(
            {
                "slot_id": f"AFTER_{structure.id}",
                "description": f"Action after root structure {structure.id} completes",
            }
        )
    return slots


def _build_branch_slots(artifact: TopologyArtifact) -> List[Dict[str, Any]]:
    slots: List[Dict[str, Any]] = []
    for structure in artifact.structures:
        for branch in structure.branches:
            slots.append(
                {
                    "structure_id": structure.id,
                    "branch": branch,
                    "type": structure.type,
                    "purpose": structure.purpose,
                }
            )
    return slots


def build_semantic_sketch_experiment_prompt(
    process_text: str,
    *,
    topology_artifact: Dict[str, Any] | TopologyArtifact,
    keyword_hints: Optional[Dict[str, Any]] = None,
) -> str:
    artifact = _normalize_topology_artifact(topology_artifact)
    template = _env.get_template("activity_semantic_sketch_experiment_prompt.jinja")
    return template.render(
        process_text=process_text,
        topology_artifact=artifact.model_dump(mode="json"),
        keyword_hints=keyword_hints,
        root_slots=_build_root_slots(artifact),
        branch_slots=_build_branch_slots(artifact),
    ).rstrip() + "\n"


def semantic_sketch_plan_response_format() -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "semantic_sketch_plan",
            "schema": SEMANTIC_SKETCH_PLAN_SCHEMA,
            "strict": True,
        },
    }


def parse_semantic_sketch_plan_json(raw_output: str) -> Dict[str, Any]:
    parsed_json = json.loads(raw_output)
    validated = SemanticSketchPlan.model_validate(parsed_json)
    return validated.model_dump(mode="json")


def generate_semantic_sketch_plan(
    process_text: str,
    *,
    topology_artifact: Dict[str, Any] | TopologyArtifact,
    model: str = "gpt-4o",
) -> Dict[str, Any]:
    normalized_topology_artifact = _normalize_topology_artifact(topology_artifact).model_dump(mode="json")
    keyword_hints = extract_keyword_hints(process_text)
    prompt = build_semantic_sketch_experiment_prompt(
        process_text,
        topology_artifact=normalized_topology_artifact,
        keyword_hints=keyword_hints,
    )
    response_mode = "structured_output"
    fallback_reason = None
    try:
        raw_output = call_openai(
            model=model,
            prompt=prompt,
            response_format=semantic_sketch_plan_response_format(),
            require_structured_output=True,
        )
    except Exception as exc:
        response_mode = "fallback_json_mode"
        fallback_reason = str(exc)
        logger.warning(
            "Semantic sketch experiment structured output failed; falling back to unconstrained JSON mode.",
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
    try:
        artifact = parse_semantic_sketch_plan_json(raw_output)
    except Exception as exc:
        raise SemanticSketchPlanGenerationError(
            f"SemanticSketchPlan validation failed: {exc}",
            debug_artifacts={
                "process_text": process_text,
                "topology_artifact": normalized_topology_artifact,
                "keyword_hints": keyword_hints,
                "semantic_prompt": prompt,
                "semantic_raw_output": raw_output,
                "semantic_response_mode": response_mode,
                "semantic_fallback_reason": fallback_reason,
                "semantic_validation_error": str(exc),
            },
        ) from exc
    return {
        "keyword_hints": keyword_hints,
        "prompt": prompt,
        "raw_output": raw_output,
        "artifact": artifact,
        "response_mode": response_mode,
        "fallback_reason": fallback_reason,
    }


__all__ = [
    "SEMANTIC_SKETCH_PLAN_SCHEMA",
    "SemanticSketchPlanGenerationError",
    "build_semantic_sketch_experiment_prompt",
    "generate_semantic_sketch_plan",
    "parse_semantic_sketch_plan_json",
    "semantic_sketch_plan_response_format",
]
