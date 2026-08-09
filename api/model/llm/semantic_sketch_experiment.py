from __future__ import annotations

import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from .handler import call_openai
from .keyword_hints import extract_keyword_hints
from .semantic_sketch_plan_model import (
    SemanticSketchPlan,
    apply_semantic_branch_plan_schema_constraints,
    find_invalid_semantic_branch_plans,
)
from .topology_artifact_model import TopologyArtifact, TopologyStructure
from .topology_to_sketch_compiler import validate_semantic_plan_against_topology

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

logger = logging.getLogger(__name__)
_MAX_CORRECTION_ATTEMPTS = 2

SEMANTIC_SKETCH_PLAN_SCHEMA: Dict[str, Any] = apply_semantic_branch_plan_schema_constraints(
    SemanticSketchPlan.model_json_schema()
)

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

_UNIVERSAL_CONTINUATION_PATTERNS = (
    re.compile(r"\bin\s+(?:any|either|all)\s+(?:case|cases)\b", re.IGNORECASE),
    re.compile(r"\bregardless\s+of\s+(?:the\s+)?(?:outcome|result|decision)\b", re.IGNORECASE),
    re.compile(r"\bafter\s+both\b", re.IGNORECASE),
    re.compile(r"\bonce\s+(?:both|all)\b", re.IGNORECASE),
)

_BUSINESS_ACTION_VERB_STEMS = {
    "approve",
    "archive",
    "assign",
    "authorize",
    "cancel",
    "close",
    "complete",
    "create",
    "deliver",
    "finalize",
    "fulfill",
    "generate",
    "inform",
    "issue",
    "notify",
    "produce",
    "record",
    "register",
    "reject",
    "report",
    "schedule",
    "send",
    "store",
    "transmit",
    "update",
}

_OWNERSHIP_TOKEN_STOPWORDS = {
    "after",
    "all",
    "also",
    "an",
    "and",
    "any",
    "applies",
    "are",
    "both",
    "case",
    "cases",
    "decision",
    "either",
    "every",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "later",
    "may",
    "of",
    "once",
    "or",
    "outcome",
    "outcomes",
    "regardless",
    "result",
    "should",
    "that",
    "the",
    "then",
    "this",
    "to",
    "was",
    "were",
    "whether",
    "will",
    "with",
}

_RETRY_EVIDENCE_STEMS = {"again", "repeat", "retry", "resubmit", "rework", "update", "until"}
_GENERIC_PURPOSE_STEMS = {"check", "decide", "decision", "determine", "evaluate", "loop", "process", "result", "retry"}


class SemanticSketchPlanGenerationError(Exception):
    def __init__(self, message: str, *, debug_artifacts: Dict[str, Any]) -> None:
        super().__init__(message)
        self.debug_artifacts = debug_artifacts


class SemanticOwnershipEvidenceValidationError(ValueError):
    pass


def _required_root_slot_ids(topology_artifact: Dict[str, Any] | TopologyArtifact) -> List[str]:
    return [slot["slot_id"] for slot in _build_root_slots(_normalize_topology_artifact(topology_artifact))]


def _build_semantic_correction_prompt(
    *,
    base_prompt: str,
    process_text: str,
    topology_artifact: Dict[str, Any],
    invalid_semantic_output: str,
    parsed_semantic_output: Dict[str, Any] | None,
    validation_error: str,
    correction_attempt: int,
) -> str:
    parsed_pretty = (
        json.dumps(parsed_semantic_output, ensure_ascii=False, indent=2)
        if parsed_semantic_output is not None
        else "null"
    )
    topology_pretty = json.dumps(topology_artifact, ensure_ascii=False, indent=2)
    required_root_slots = json.dumps(
        _required_root_slot_ids(topology_artifact),
        ensure_ascii=False,
    )
    ownership_feedback = ""
    if "shared-continuation evidence" in validation_error:
        ownership_feedback = (
            "\nShared-continuation correction:\n"
            "The proposed semantic plan prevents a branch that should reach shared post-branch behavior "
            "from doing so. Preserve branch-local actions, place behavior that applies after convergence "
            "in the shared post-structure slot, and do not terminate a branch before that shared behavior.\n"
        )
    return (
        f"{base_prompt}\n"
        "\nCorrection attempt:\n"
        f"This is correction attempt {correction_attempt}.\n"
        "Your previous SemanticSketchPlan failed deterministic validation.\n"
        "Return a complete corrected SemanticSketchPlan JSON object only.\n"
        "Every required root slot must appear exactly once.\n"
        "Do not omit, duplicate, shift, or invent fallback root actions.\n"
        "Do not add explanations outside the JSON object.\n"
        "\nOriginal process text:\n"
        f"{process_text}\n"
        "\nAuthoritative topology artifact:\n"
        f"{topology_pretty}\n"
        "\nRequired root-slot sequence:\n"
        f"{required_root_slots}\n"
        "\nInvalid semantic raw output:\n"
        f"{invalid_semantic_output}\n"
        "\nInvalid semantic parsed JSON:\n"
        f"{parsed_pretty}\n"
        "\nDeterministic validation diagnostics:\n"
        f"{validation_error}\n"
        f"{ownership_feedback}"
    )


def _call_semantic_planner(
    *,
    model: str,
    prompt: str,
) -> Dict[str, Any]:
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
    return {
        "raw_output": raw_output,
        "response_mode": response_mode,
        "fallback_reason": fallback_reason,
    }


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


def _stem_ownership_token(token: str) -> str:
    irregular = {
        "archived": "archive",
        "authorized": "authorize",
        "authorised": "authorize",
        "completed": "complete",
        "confirmed": "confirm",
        "fulfilled": "fulfill",
        "rejected": "reject",
        "registered": "register",
        "sent": "send",
    }
    if token in irregular:
        return irregular[token]
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("ing") and len(token) > 5:
        return token[:-3]
    if token.endswith("ed") and len(token) > 4:
        return token[:-2]
    if token.endswith("es") and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        return token[:-1]
    return token


def _ownership_tokens(value: str) -> set[str]:
    return {
        stemmed
        for token in _tokenize(value)
        if (stemmed := _stem_ownership_token(token)) not in _OWNERSHIP_TOKEN_STOPWORDS
        and len(stemmed) > 2
    }


def _has_strong_universal_continuation(sentence: str) -> bool:
    if not any(pattern.search(sentence) for pattern in _UNIVERSAL_CONTINUATION_PATTERNS):
        return False
    tokens = _ownership_tokens(sentence)
    return bool(tokens.intersection(_BUSINESS_ACTION_VERB_STEMS)) and len(tokens) >= 2


def _root_action_texts(plan: Dict[str, Any], slot_id: str) -> List[str]:
    for entry in plan.get("root_actions") or []:
        if str(entry.get("slot_id") or "").strip() != slot_id:
            continue
        return [
            str(step.get("action") or "").strip()
            for step in entry.get("actions") or []
            if str(step.get("action") or "").strip()
        ]
    return []


def _branch_plan_lookup(plan: Dict[str, Any]) -> Dict[tuple[str, str], Dict[str, Any]]:
    return {
        (str(entry.get("structure_id") or "").strip(), str(entry.get("branch") or "").strip()): entry
        for entry in plan.get("branch_plans") or []
    }


def _action_matches_evidence(action: str, evidence_tokens: set[str]) -> bool:
    action_tokens = _ownership_tokens(action)
    overlap = action_tokens.intersection(evidence_tokens)
    return bool(overlap.intersection(_BUSINESS_ACTION_VERB_STEMS)) or len(overlap) >= 2


def _decision_ancestor_scopes(
    structure: TopologyStructure,
    by_id: Dict[str, TopologyStructure],
) -> List[tuple[TopologyStructure, str]]:
    scopes: List[tuple[TopologyStructure, str]] = []
    current = structure
    visited: set[str] = set()
    while current.parent != "ROOT":
        if current.id in visited or current.parent not in by_id:
            break
        visited.add(current.id)
        parent = by_id[current.parent]
        if parent.type == "decision" and current.parent_branch:
            scopes.append((parent, current.parent_branch))
        current = parent
    return scopes


def _purposes_share_retry_subject(decision_purpose: str, loop_purpose: str) -> bool:
    decision_tokens = _ownership_tokens(decision_purpose) - _GENERIC_PURPOSE_STEMS
    loop_tokens = _ownership_tokens(loop_purpose) - _GENERIC_PURPOSE_STEMS
    return bool(decision_tokens.intersection(loop_tokens))


def _root_ancestor_id(structure: TopologyStructure, by_id: Dict[str, TopologyStructure]) -> str | None:
    current = structure
    visited: set[str] = set()
    while current.parent != "ROOT":
        if current.id in visited or current.parent not in by_id:
            return None
        visited.add(current.id)
        current = by_id[current.parent]
    return current.id


def _raise_shared_ownership_contradiction(reason: str) -> None:
    raise SemanticOwnershipEvidenceValidationError(
        "SemanticSketchPlan contradicts strong shared-continuation evidence: "
        f"{reason}. Preserve branch-local actions, place shared behavior once in the post-structure slot, "
        "and keep every path that must reach it continuing until that slot."
    )


def validate_semantic_ownership_against_evidence(
    process_text: str,
    *,
    topology_artifact: Dict[str, Any] | TopologyArtifact,
    semantic_plan: Dict[str, Any] | SemanticSketchPlan,
) -> Dict[str, Any]:
    """Reject only strong source/topology contradictions without rewriting semantics."""
    artifact = _normalize_topology_artifact(topology_artifact)
    plan = _normalize_semantic_plan(semantic_plan).model_dump(mode="json")
    root_structures = [structure for structure in artifact.structures if structure.parent == "ROOT"]
    if len(root_structures) != 1:
        return plan

    root_structure = root_structures[0]
    post_slot_id = f"AFTER_{root_structure.id}"
    branch_plans = _branch_plan_lookup(plan)
    shared_actions = _root_action_texts(plan, post_slot_id)
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", process_text.strip())
        if sentence.strip()
    ]

    for sentence in sentences:
        if not _has_strong_universal_continuation(sentence):
            continue
        evidence_tokens = _ownership_tokens(sentence)
        if not any(_action_matches_evidence(action, evidence_tokens) for action in shared_actions):
            _raise_shared_ownership_contradiction(
                f"shared action is missing from post-structure slot {post_slot_id}"
            )
        for branch in root_structure.branches:
            branch_plan = branch_plans.get((root_structure.id, branch))
            if branch_plan is not None and branch_plan.get("intent") != "continue":
                _raise_shared_ownership_contradiction(
                    f"branch {root_structure.id}/{branch} uses intent={branch_plan.get('intent')} "
                    f"before explicit shared behavior in {post_slot_id}"
                )

    source_tokens = _ownership_tokens(process_text)
    if not source_tokens.intersection(_RETRY_EVIDENCE_STEMS):
        return plan

    structures_by_id = {structure.id: structure for structure in artifact.structures}
    for loop in artifact.structures:
        if loop.type != "loop" or loop.parent == "ROOT" or not loop.parent_branch:
            continue
        loop_branch_plans = [
            (branch, branch_plans.get((loop.id, branch)))
            for branch in loop.branches
        ]
        retry_plans = [
            (branch, branch_plan)
            for branch, branch_plan in loop_branch_plans
            if branch_plan is not None and branch_plan.get("intent") == "loop_back"
        ]
        continuing_plans = [
            (branch, branch_plan)
            for branch, branch_plan in loop_branch_plans
            if branch_plan is not None and branch_plan.get("intent") == "continue"
        ]
        if len(retry_plans) != 1 or len(continuing_plans) != 1:
            continue
        loop_success_branch, _loop_success_plan = continuing_plans[0]

        for decision, retry_side_branch in _decision_ancestor_scopes(loop, structures_by_id):
            if len(decision.branches) != 2:
                continue
            if not _purposes_share_retry_subject(decision.purpose, loop.purpose):
                continue
            if _root_ancestor_id(decision, structures_by_id) != root_structure.id:
                continue
            direct_branches = [branch for branch in decision.branches if branch != retry_side_branch]
            if len(direct_branches) != 1:
                continue
            direct_branch = direct_branches[0]
            direct_plan = branch_plans.get((decision.id, direct_branch))
            if direct_plan is None or direct_plan.get("intent") != "continue":
                continue
            direct_actions = [
                str(step.get("action") or "").strip()
                for step in direct_plan.get("steps") or []
                if str(step.get("action") or "").strip()
            ]
            evidenced_direct_actions = [
                action for action in direct_actions if _action_matches_evidence(action, source_tokens)
            ]
            if not evidenced_direct_actions:
                continue
            matching_shared_actions = [
                action
                for action in shared_actions
                if any(
                    len(_ownership_tokens(action).intersection(_ownership_tokens(direct_action))) >= 1
                    for direct_action in evidenced_direct_actions
                )
            ]
            if not matching_shared_actions:
                _raise_shared_ownership_contradiction(
                    f"retry success {loop.id}/{loop_success_branch} cannot reach shared action "
                    f"owned only by {decision.id}/{direct_branch}; move it to {post_slot_id}"
                )
            _raise_shared_ownership_contradiction(
                f"shared action remains duplicated inside {decision.id}/{direct_branch}; "
                f"keep it only in {post_slot_id}"
            )

    return plan


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


def _revalidate_semantic_plan_against_topology(
    *,
    topology_artifact: Dict[str, Any] | TopologyArtifact,
    semantic_plan: Dict[str, Any],
) -> Dict[str, Any]:
    return validate_semantic_plan_against_topology(
        topology_artifact,
        semantic_plan,
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
        _normalize_action_text(step.get("action", ""))
        for root_action in plan.get("root_actions") or []
        for step in (
            root_action.get("actions")
            or ([{"action": root_action.get("action", "")}] if root_action.get("action") else [])
        )
        if _normalize_action_text(step.get("action", ""))
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


def _parse_semantic_sketch_plan_payload(raw_output: str) -> Dict[str, Any]:
    parsed_json = json.loads(_strip_optional_json_code_fence(raw_output))
    if not isinstance(parsed_json, dict):
        raise ValueError("SemanticSketchPlan payload must be a JSON object")
    return parsed_json


def _log_invalid_semantic_branch_plans(*, raw_output: str, parsed_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    invalid_branch_plans = find_invalid_semantic_branch_plans(parsed_payload)
    for invalid_branch_plan in invalid_branch_plans:
        logger.error(
            "Semantic planner produced invalid branch plan: structure_id=%s branch=%s intent=%s "
            "parsed_branch_plan=%s raw_planner_output=%s",
            invalid_branch_plan["structure_id"],
            invalid_branch_plan["branch"],
            invalid_branch_plan["intent"],
            invalid_branch_plan["parsed_branch_plan"],
            raw_output,
        )
    return invalid_branch_plans


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
    parsed_json = _parse_semantic_sketch_plan_payload(raw_output)
    _log_invalid_semantic_branch_plans(raw_output=raw_output, parsed_payload=parsed_json)
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
    planner_attempts: List[Dict[str, Any]] = []
    current_prompt = prompt
    parsed_payload: Dict[str, Any] | None = None
    invalid_branch_plans: List[Dict[str, Any]] = []
    artifact: Dict[str, Any] | None = None
    raw_output = ""
    response_mode = "structured_output"
    fallback_reason = None
    last_exc: Exception | None = None
    for correction_attempt in range(_MAX_CORRECTION_ATTEMPTS + 1):
        planner_call = _call_semantic_planner(
            model=model,
            prompt=current_prompt,
        )
        raw_output = planner_call["raw_output"]
        response_mode = planner_call["response_mode"]
        fallback_reason = planner_call["fallback_reason"]
        parsed_payload = None
        invalid_branch_plans = []
        try:
            parsed_payload = _parse_semantic_sketch_plan_payload(raw_output)
            invalid_branch_plans = _log_invalid_semantic_branch_plans(
                raw_output=raw_output,
                parsed_payload=parsed_payload,
            )
            artifact = _revalidate_semantic_plan_against_topology(
                topology_artifact=normalized_topology_artifact,
                semantic_plan=parsed_payload,
            )
            artifact = validate_semantic_ownership_against_evidence(
                process_text,
                topology_artifact=normalized_topology_artifact,
                semantic_plan=artifact,
            )
            planner_attempts.append(
                {
                    "attempt_index": correction_attempt,
                    "prompt": current_prompt,
                    "raw_output": raw_output,
                    "parsed_output": parsed_payload,
                    "response_mode": response_mode,
                    "fallback_reason": fallback_reason,
                    "validation_error": None,
                }
            )
            break
        except Exception as exc:
            last_exc = exc
            planner_attempts.append(
                {
                    "attempt_index": correction_attempt,
                    "prompt": current_prompt,
                    "raw_output": raw_output,
                    "parsed_output": parsed_payload,
                    "response_mode": response_mode,
                    "fallback_reason": fallback_reason,
                    "validation_error": str(exc),
                }
            )
            if correction_attempt >= _MAX_CORRECTION_ATTEMPTS:
                break
            current_prompt = _build_semantic_correction_prompt(
                base_prompt=prompt,
                process_text=process_text,
                topology_artifact=normalized_topology_artifact,
                invalid_semantic_output=raw_output,
                parsed_semantic_output=parsed_payload,
                validation_error=str(exc),
                correction_attempt=correction_attempt + 1,
            )

    if artifact is None:
        exc = last_exc or ValueError("SemanticSketchPlan validation failed")
        raise SemanticSketchPlanGenerationError(
            f"SemanticSketchPlan validation failed: {exc}",
            debug_artifacts={
                "process_text": process_text,
                "topology_artifact": normalized_topology_artifact,
                "keyword_hints": keyword_hints,
                "semantic_prompt": prompt,
                "semantic_raw_output": raw_output,
                "semantic_parsed_output": parsed_payload,
                "semantic_invalid_branch_plans": invalid_branch_plans,
                "semantic_response_mode": response_mode,
                "semantic_fallback_reason": fallback_reason,
                "semantic_validation_error": str(exc),
                "semantic_attempts": planner_attempts,
            },
        ) from exc
    return {
        "keyword_hints": keyword_hints,
        "prompt": current_prompt,
        "raw_output": raw_output,
        "artifact": artifact,
        "response_mode": response_mode,
        "fallback_reason": fallback_reason,
        "planner_attempts": planner_attempts,
    }


__all__ = [
    "SEMANTIC_SKETCH_PLAN_SCHEMA",
    "SemanticOwnershipEvidenceValidationError",
    "SemanticSketchPlanGenerationError",
    "build_semantic_sketch_experiment_prompt",
    "generate_semantic_sketch_plan",
    "parse_semantic_sketch_plan_json",
    "preserve_explicit_business_activities",
    "semantic_sketch_plan_response_format",
    "validate_semantic_ownership_against_evidence",
]
