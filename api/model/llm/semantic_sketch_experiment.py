from __future__ import annotations

import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from .handler import call_openai
from .keyword_hints import extract_keyword_hints
from .semantic_sketch_plan_model import SemanticSketchPlan
from .topology_artifact_model import TopologyArtifact, TopologyStructure

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

logger = logging.getLogger(__name__)

SEMANTIC_SKETCH_PLAN_SCHEMA: Dict[str, Any] = SemanticSketchPlan.model_json_schema()

_DECISION_STRUCTURE_STOPWORDS = {
    "a",
    "an",
    "additional",
    "approval",
    "approve",
    "approved",
    "are",
    "be",
    "check",
    "checks",
    "decision",
    "determine",
    "determines",
    "evaluates",
    "evaluate",
    "if",
    "is",
    "needed",
    "needs",
    "non",
    "of",
    "officer",
    "or",
    "outcome",
    "reject",
    "rejected",
    "required",
    "requires",
    "require",
    "review",
    "should",
    "the",
    "whether",
}

_EXPLICIT_ACTIVITY_VERBS = {
    "analyze",
    "analyzes",
    "analyse",
    "analyses",
    "assess",
    "assesses",
    "audit",
    "audits",
    "check",
    "checks",
    "examine",
    "examines",
    "inspect",
    "inspects",
    "review",
    "reviews",
    "screen",
    "screens",
    "validate",
    "validates",
    "verify",
    "verifies",
}

_DECISION_PROXY_VERBS = {
    "check",
    "checks",
    "decide",
    "decides",
    "determine",
    "determines",
    "evaluate",
    "evaluates",
}


class SemanticSketchPlanGenerationError(Exception):
    def __init__(self, message: str, *, debug_artifacts: Dict[str, Any]) -> None:
        super().__init__(message)
        self.debug_artifacts = debug_artifacts


def _normalize_topology_artifact(topology_artifact: Dict[str, Any] | TopologyArtifact) -> TopologyArtifact:
    if isinstance(topology_artifact, TopologyArtifact):
        return topology_artifact
    return TopologyArtifact.model_validate(topology_artifact)


def _normalize_semantic_plan(semantic_plan: Dict[str, Any] | SemanticSketchPlan) -> SemanticSketchPlan:
    if isinstance(semantic_plan, SemanticSketchPlan):
        return semantic_plan
    return SemanticSketchPlan.model_validate(
        semantic_plan,
        context={"require_explicit_branch_steps": True},
    )


def _normalize_action_text(value: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", " ", str(value or "").strip().lower())
    cleaned = re.sub(r"\b(the|a|an)\b", " ", cleaned)
    return " ".join(cleaned.split())


def _tokenize(value: str) -> List[str]:
    return re.findall(r"[a-z]+", _normalize_action_text(value))


def _split_process_fragments(process_text: str) -> List[str]:
    fragments: List[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+", process_text.strip()):
        stripped_sentence = sentence.strip()
        if not stripped_sentence:
            continue
        for fragment in re.split(r"[;,]", stripped_sentence):
            cleaned = fragment.strip().strip(".!?")
            if cleaned:
                fragments.append(cleaned)
    return fragments


def _structure_actor_keywords(structure: TopologyStructure) -> List[str]:
    tokens = _tokenize(structure.purpose or "")
    keywords = [
        token
        for token in tokens
        if len(token) > 2 and token not in _DECISION_STRUCTURE_STOPWORDS
    ]
    return keywords


def _fragment_is_explicit_activity(fragment: str, actor_keywords: List[str]) -> bool:
    if not actor_keywords:
        return False
    tokens = set(_tokenize(fragment))
    if not tokens.intersection(actor_keywords):
        return False
    return bool(tokens.intersection(_EXPLICIT_ACTIVITY_VERBS))


def _looks_like_decision_proxy(step_action: str, structure: TopologyStructure, actor_keywords: List[str]) -> bool:
    tokens = set(_tokenize(step_action))
    if not tokens:
        return False
    if not tokens.intersection(set(_tokenize(structure.purpose or "")) | set(actor_keywords)):
        return False
    return bool(tokens.intersection(_DECISION_PROXY_VERBS))


def _revalidate_semantic_plan(semantic_plan: Dict[str, Any]) -> Dict[str, Any]:
    return SemanticSketchPlan.model_validate(
        semantic_plan,
        context={"require_explicit_branch_steps": True},
    ).model_dump(mode="json")


def preserve_explicit_business_activities(
    process_text: str,
    *,
    topology_artifact: Dict[str, Any] | TopologyArtifact,
    semantic_plan: Dict[str, Any] | SemanticSketchPlan,
) -> Dict[str, Any]:
    """Deterministically restore explicit branch-local activities omitted by planning.

    This pass does not redesign topology. It only fills in branch-local business
    actions for nested decision scopes when the source text explicitly describes
    such an activity and the semantic plan omitted it or replaced it with a
    generic decision-proxy step.
    """
    artifact = _normalize_topology_artifact(topology_artifact)
    plan = _normalize_semantic_plan(semantic_plan).model_dump(mode="json")
    branch_plan_map = {
        (entry["structure_id"], entry["branch"]): entry
        for entry in plan.get("branch_plans") or []
    }
    represented_actions = {
        _normalize_action_text(root_action.get("action", ""))
        for root_action in plan.get("root_actions") or []
        if _normalize_action_text(root_action.get("action", ""))
    }
    represented_actions.update(
        _normalize_action_text(step.get("action", ""))
        for branch_plan in plan.get("branch_plans") or []
        for step in branch_plan.get("steps") or []
        if _normalize_action_text(step.get("action", ""))
    )
    fragments = _split_process_fragments(process_text)

    for structure in artifact.structures:
        if structure.parent == "ROOT" or structure.type != "decision" or not structure.parent_branch:
            continue

        parent_key = (structure.parent, structure.parent_branch)
        parent_branch_plan = branch_plan_map.get(parent_key)
        if parent_branch_plan is None:
            continue

        actor_keywords = _structure_actor_keywords(structure)
        if not actor_keywords:
            continue

        candidate_actions = [
            _normalize_action_text(fragment)
            for fragment in fragments
            if _fragment_is_explicit_activity(fragment, actor_keywords)
            and _normalize_action_text(fragment)
            and _normalize_action_text(fragment) not in represented_actions
        ]
        if not candidate_actions:
            continue

        explicit_action = candidate_actions[-1]
        existing_steps = parent_branch_plan.get("steps") or []
        if not existing_steps:
            parent_branch_plan["steps"] = [{"action": explicit_action}]
            represented_actions.add(explicit_action)
            continue

        if all(
            _looks_like_decision_proxy(step.get("action", ""), structure, actor_keywords)
            for step in existing_steps
        ):
            parent_branch_plan["steps"] = [{"action": explicit_action}]
            represented_actions.add(explicit_action)

    return _revalidate_semantic_plan(plan)


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


def _strip_optional_json_code_fence(raw_output: str) -> str:
    stripped = raw_output.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if not lines:
        return stripped
    if not lines[0].startswith("```"):
        return stripped

    body_lines = lines[1:]
    if body_lines and body_lines[-1].strip() == "```":
        body_lines = body_lines[:-1]
    return "\n".join(body_lines).strip()


def parse_semantic_sketch_plan_json(raw_output: str) -> Dict[str, Any]:
    parsed_json = json.loads(_strip_optional_json_code_fence(raw_output))
    return _revalidate_semantic_plan(parsed_json)


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
    "preserve_explicit_business_activities",
    "semantic_sketch_plan_response_format",
]
