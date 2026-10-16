from __future__ import annotations

import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from jinja2 import Environment, FileSystemLoader

from .control_completeness_guard import extract_control_requirements
from .control_evidence import extract_control_evidence
from .handler import call_openai
from .keyword_hints import extract_keyword_hints, extract_parallel_evidence
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
_MAX_CORRECTION_ATTEMPTS = 2

_TOPOLOGY_TYPE_CANONICALIZATION = {
    "retry": "loop",
}

_DECISION_EVIDENCE_PHRASES = (
    " if ",
    " whether ",
    " either ",
    " otherwise ",
    " else ",
    " approve or reject",
    " approved or rejected",
    " reject or approve",
    " decide whether",
    " determine whether",
    " determines whether",
    " decide if",
    " determine if",
    " determines if",
    " choose whether",
    " route ",
    " routing ",
    " based on ",
    " depending on ",
)
_EXPLICIT_OR_DECISION_STEMS = (
    "approv",
    "reject",
    "confirm",
    "accept",
    "declin",
    "deny",
    "simpl",
    "complex",
    "valid",
    "invalid",
    "pass",
    "fail",
)
_LOOP_EVIDENCE_PHRASES = (
    " retry ",
    " retries ",
    " repeat ",
    " repeats ",
    " repeated ",
    " until ",
    " rework ",
    " revise ",
    " revises ",
    " resubmit ",
    " resubmits ",
    " resubmission ",
    " again ",
)
_GENERIC_BRANCH_TOKENS = {
    "approved",
    "rejected",
    "ready",
    "blocked",
    "archive",
    "archived",
    "retain",
    "cancelled",
    "approved",
    "success",
    "retry",
}
_PURPOSE_STOPWORDS = {
    "a",
    "an",
    "the",
    "for",
    "of",
    "to",
    "and",
    "or",
    "path",
    "branch",
}
_SHARED_POST_BRANCH_SCOPE_PHRASES = (
    " based on the outcome ",
    " based on the result ",
    " based on whether ",
    " depending on the outcome ",
    " depending on the result ",
    " according to the outcome ",
    " according to the result ",
)
_SHARED_CONTINUATION_PHRASES = (
    " once ",
    " after ",
    " when ",
    " upon ",
)
_SHARED_OUTCOME_PHRASE_TOKENS = tuple(
    tuple(phrase.strip().split())
    for phrase in _SHARED_POST_BRANCH_SCOPE_PHRASES
)
_SHARED_CONTINUATION_TOKENS = {"once", "after", "when", "upon"}
_SHARED_ALTERNATIVE_STOP_TOKENS = {
    "claim",
    "claims",
    "relevant",
    "form",
    "forms",
    "once",
    "after",
    "when",
    "upon",
    "then",
    "and",
    "they",
    "it",
}


class TopologyArtifactGenerationError(Exception):
    def __init__(self, message: str, *, debug_artifacts: Dict[str, Any]) -> None:
        super().__init__(message)
        self.debug_artifacts = debug_artifacts


def _unsupported_structure_ids(validation_error: str) -> List[str]:
    return re.findall(r"'id': '([^']+)'", str(validation_error or ""))


def _shared_scope_preservation_guidance(
    *,
    process_text: str,
    parsed_topology_output: Dict[str, Any] | None,
    validation_error: str,
) -> str:
    if parsed_topology_output is None or "shared post-branch" not in validation_error:
        return ""
    try:
        artifact = TopologyArtifact.model_validate(parsed_topology_output)
    except Exception:
        return ""

    normalized_text = _normalize_text(process_text)
    alternative_pairs = _extract_shared_scope_alternative_pairs(normalized_text)
    if not alternative_pairs:
        return ""

    earlier_decision = None
    for structure in artifact.structures:
        if structure.type != "decision" or structure.parent == "ROOT":
            continue
        if any(_shared_scope_alternative_pair_matches_structure(pair, structure) for pair in alternative_pairs):
            earlier_decision = structure
            break

    if earlier_decision is None:
        return ""

    unsupported_ids = set(_unsupported_structure_ids(validation_error))
    later_structure = None
    for structure in artifact.structures:
        if structure.id == earlier_decision.id:
            continue
        if unsupported_ids and structure.id not in unsupported_ids:
            continue
        if structure.parent == earlier_decision.id and structure.parent_branch in earlier_decision.branches:
            later_structure = structure
            break
        if structure.parent == "ROOT":
            later_structure = structure
            break
    if later_structure is None:
        for structure in artifact.structures:
            if structure.id == earlier_decision.id:
                continue
            if structure.parent == earlier_decision.id and structure.parent_branch in earlier_decision.branches:
                later_structure = structure
                break
            if structure.parent == "ROOT":
                later_structure = structure
                break
    if later_structure is None:
        return ""

    return (
        "Preservation guidance for this correction:\n"
        f'- Preserve the existing earlier sibling decision exactly as a separate structure: `id="{earlier_decision.id}"`, '
        f'`parent="{earlier_decision.parent}"`, `parent_branch="{earlier_decision.parent_branch}"`, '
        f'`branches={json.dumps(earlier_decision.branches, ensure_ascii=False)}`.\n'
        "- Do not delete it, replace it, or collapse its sibling branches.\n"
        f'- Move only the later shared continuation structure: `id="{later_structure.id}"`.\n'
        "- Reuse the preserved earlier decision's parent and parent_branch for the relocated later structure.\n"
        f'- The relocated later structure must use `parent="{earlier_decision.parent}"` and '
        f'`parent_branch="{earlier_decision.parent_branch}"`.\n'
        "- Keep the later shared structure ordered after the preserved earlier decision.\n"
    )


def _build_topology_correction_prompt(
    *,
    base_prompt: str,
    process_text: str,
    invalid_topology_output: str,
    parsed_topology_output: Dict[str, Any] | None,
    validation_error: str,
    correction_attempt: int,
) -> str:
    unsupported_ids = _unsupported_structure_ids(validation_error)
    parsed_pretty = (
        json.dumps(parsed_topology_output, ensure_ascii=False, indent=2)
        if parsed_topology_output is not None
        else "null"
    )
    unsupported_id_text = ", ".join(unsupported_ids) if unsupported_ids else "none"
    shared_scope_guidance = ""
    if "shared post-branch" in validation_error:
        shared_scope_guidance = (
            "\nShared post-branch correction guidance:\n"
            "- Keep the earlier sibling decision that introduces the branch alternatives.\n"
            "- Place the later shared control as a later sibling with the same parent and parent_branch as that earlier decision.\n"
            "- Reuse the parent and parent_branch of the earlier sibling decision itself, not one of that decision's branch handles.\n"
            "- Do not duplicate the shared control under the sibling branches.\n"
            "- Do not attach it to only one sibling branch.\n"
            "- Do not promote it to ROOT or outside the required outer branch scope.\n"
        )
        preservation_guidance = _shared_scope_preservation_guidance(
            process_text=process_text,
            parsed_topology_output=parsed_topology_output,
            validation_error=validation_error,
        )
        if preservation_guidance:
            shared_scope_guidance += preservation_guidance
    if "missing shared post-branch decision after the sibling decision" in validation_error:
        shared_scope_guidance += (
            "- If the later shared continuation itself contains an if/otherwise-style split, model that shared continuation as a decision first.\n"
            "- If that shared decision contains retry, recheck, update, or repeat behavior, place any retry or recheck loop inside the retry/incomplete branch of that shared decision.\n"
            "- Do not collapse a shared decision-plus-retry region into a single sibling loop when the text first checks a condition and only then retries.\n"
        )
    return (
        f"{base_prompt}\n"
        "\nCorrection attempt:\n"
        f"This is correction attempt {correction_attempt}.\n"
        "Your previous topology artifact failed deterministic validation.\n"
        "Return a complete corrected TopologyArtifact JSON object only.\n"
        "Do not repeat unsupported control structures.\n"
        "Do not add explanations outside the JSON object.\n"
        "\nOriginal process text:\n"
        f"{process_text}\n"
        "\nInvalid topology raw output:\n"
        f"{invalid_topology_output}\n"
        "\nInvalid topology parsed JSON:\n"
        f"{parsed_pretty}\n"
        "\nDeterministic validation error:\n"
        f"{validation_error}\n"
        "\nUnsupported structure ids:\n"
        f"{unsupported_id_text}\n"
        f"{shared_scope_guidance}"
    )


def _call_topology_planner(
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
    return {
        "raw_output": raw_output,
        "response_mode": response_mode,
        "fallback_reason": fallback_reason,
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


def _normalize_text(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9\s_-]", " ", str(value or "").strip().lower())
    return f" {' '.join(normalized.split())} "


def _tokenize_handle(value: str) -> List[str]:
    normalized = re.sub(r"[_-]+", " ", str(value or "").strip().lower())
    return [
        token
        for token in re.findall(r"[a-z0-9]+", normalized)
        if token and token not in _GENERIC_BRANCH_TOKENS
    ]


def _contains_any_phrase(normalized_text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in normalized_text for phrase in phrases)


def _contains_any_stem(normalized_text: str, stems: tuple[str, ...]) -> bool:
    words = re.findall(r"[a-z0-9]+", normalized_text)
    for word in words:
        for stem in stems:
            if word.startswith(stem):
                return True
            if stem == "confirm" and word.startswith("confirme"):
                return True
    return False


def _count_evidenced_branch_handles(normalized_text: str, branches: List[str]) -> int:
    evidenced = 0
    for branch in branches:
        tokens = _tokenize_handle(branch)
        if not tokens:
            continue
        if all(_contains_any_stem(normalized_text, (token,)) for token in tokens):
            evidenced += 1
    return evidenced


def _has_explicit_sentence_level_disjunction(normalized_text: str) -> bool:
    return " or " in normalized_text and _contains_any_stem(
        normalized_text,
        _EXPLICIT_OR_DECISION_STEMS,
    )


def _has_shared_post_branch_scope_signal(normalized_text: str) -> bool:
    return _contains_any_phrase(normalized_text, _SHARED_POST_BRANCH_SCOPE_PHRASES) and _contains_any_phrase(
        normalized_text,
        _SHARED_CONTINUATION_PHRASES,
    )


def _has_post_branch_control_evidence(normalized_text: str) -> bool:
    continuation_positions = [
        normalized_text.find(phrase)
        for phrase in _SHARED_CONTINUATION_PHRASES
        if normalized_text.find(phrase) >= 0
    ]
    if not continuation_positions:
        return False
    continuation_tail = normalized_text[min(continuation_positions):]
    return (
        _contains_any_phrase(continuation_tail, _DECISION_EVIDENCE_PHRASES)
        or _contains_any_phrase(continuation_tail, _LOOP_EVIDENCE_PHRASES)
        or _has_explicit_sentence_level_disjunction(continuation_tail)
    )


def _has_post_branch_decision_evidence(normalized_text: str) -> bool:
    continuation_positions = [
        normalized_text.find(phrase)
        for phrase in _SHARED_CONTINUATION_PHRASES
        if normalized_text.find(phrase) >= 0
    ]
    if not continuation_positions:
        return False
    continuation_tail = normalized_text[min(continuation_positions):]
    return _contains_any_phrase(continuation_tail, _DECISION_EVIDENCE_PHRASES) or _has_explicit_sentence_level_disjunction(
        continuation_tail
    )


def _stem_equivalent(left: str, right: str) -> bool:
    normalized_left = str(left or "").strip().lower()
    normalized_right = str(right or "").strip().lower()
    if not normalized_left or not normalized_right:
        return False
    return normalized_left.startswith(normalized_right) or normalized_right.startswith(normalized_left)


def _extract_shared_scope_alternative_pairs(normalized_text: str) -> List[Tuple[List[str], List[str]]]:
    tokens = normalized_text.split()
    pairs: List[Tuple[List[str], List[str]]] = []
    seen: set[Tuple[Tuple[str, ...], Tuple[str, ...]]] = set()

    for phrase_tokens in _SHARED_OUTCOME_PHRASE_TOKENS:
        phrase_length = len(phrase_tokens)
        for start_index in range(len(tokens) - phrase_length):
            if tuple(tokens[start_index : start_index + phrase_length]) != phrase_tokens:
                continue
            lookahead = tokens[start_index + phrase_length : start_index + phrase_length + 8]
            if "or" not in lookahead:
                continue
            or_index = lookahead.index("or")
            left_tokens = [
                token
                for token in lookahead[:or_index]
                if token not in _SHARED_ALTERNATIVE_STOP_TOKENS
            ]
            right_tokens: List[str] = []
            for token in lookahead[or_index + 1 :]:
                if token in _SHARED_ALTERNATIVE_STOP_TOKENS:
                    break
                right_tokens.append(token)
                if len(right_tokens) >= 2:
                    break
            if not left_tokens or not right_tokens:
                continue
            pair_key = (tuple(left_tokens[-2:]), tuple(right_tokens[:2]))
            if pair_key in seen:
                continue
            seen.add(pair_key)
            pairs.append((list(pair_key[0]), list(pair_key[1])))
    return pairs


def _branch_phrase_matches_handle(branch_phrase_tokens: List[str], handle_tokens: List[str]) -> bool:
    if not branch_phrase_tokens or not handle_tokens:
        return False
    return all(
        any(_stem_equivalent(branch_token, handle_token) for handle_token in handle_tokens)
        for branch_token in branch_phrase_tokens
    )


def _shared_scope_alternative_pair_matches_structure(
    branch_pair: Tuple[List[str], List[str]],
    structure: Any,
) -> bool:
    handle_token_sets = [_tokenize_handle(branch) for branch in structure.branches]
    matched_indices: set[int] = set()
    for branch_phrase_tokens in branch_pair:
        matched_index = None
        for index, handle_tokens in enumerate(handle_token_sets):
            if index in matched_indices:
                continue
            if _branch_phrase_matches_handle(branch_phrase_tokens, handle_tokens):
                matched_index = index
                break
        if matched_index is None:
            return False
        matched_indices.add(matched_index)
    return True


def _shared_post_branch_scope_issues(
    artifact: TopologyArtifact,
    normalized_text: str,
) -> List[Dict[str, Any]]:
    if not _has_shared_post_branch_scope_signal(normalized_text):
        return []
    if not _has_post_branch_control_evidence(normalized_text):
        return []

    alternative_pairs = _extract_shared_scope_alternative_pairs(normalized_text)
    if not alternative_pairs:
        return []

    issues: List[Dict[str, Any]] = []
    ordered_structures = list(artifact.structures)

    for branch_pair in alternative_pairs:
        matching_decisions = [
            structure
            for structure in ordered_structures
            if structure.type == "decision"
            and structure.parent != "ROOT"
            and _shared_scope_alternative_pair_matches_structure(branch_pair, structure)
        ]
        if not matching_decisions:
            issues.append(
                {
                    "id": "MISSING_SHARED_SCOPE_BRANCH_DECISION",
                    "type": "decision",
                    "reason": "missing nested sibling decision before shared post-branch continuation",
                    "branches": [" ".join(tokens) for tokens in branch_pair],
                    "structure": None,
                }
            )
            continue

        for decision in matching_decisions:
            decision_index = ordered_structures.index(decision)
            later_structures = ordered_structures[decision_index + 1 :]
            sibling_later_structures = [
                structure
                for structure in later_structures
                if structure.parent == decision.parent and structure.parent_branch == decision.parent_branch
            ]
            if sibling_later_structures:
                if _has_post_branch_decision_evidence(normalized_text) and not any(
                    structure.type == "decision" for structure in sibling_later_structures
                ):
                    issues.append(
                        {
                            "id": decision.id,
                            "type": decision.type,
                            "reason": "missing shared post-branch decision after the sibling decision",
                            "branches": decision.branches,
                            "parent": decision.parent,
                            "parent_branch": decision.parent_branch,
                            "structure": decision.model_dump(mode="json"),
                        }
                    )
                continue

            branch_local_later_structures = [
                structure
                for structure in later_structures
                if structure.parent == decision.id and structure.parent_branch in decision.branches
            ]
            promoted_later_structures = [
                structure
                for structure in later_structures
                if structure.parent == "ROOT"
            ]

            if branch_local_later_structures:
                distinct_branches = {structure.parent_branch for structure in branch_local_later_structures}
                reason = (
                    "shared post-branch continuation is attached to only one sibling branch"
                    if len(distinct_branches) == 1
                    else "duplicate branch-local structures suggest a shared post-branch control region"
                )
                for structure in branch_local_later_structures:
                    issues.append(
                        {
                            "id": structure.id,
                            "type": structure.type,
                            "reason": reason,
                            "branches": structure.branches,
                            "parent": structure.parent,
                            "parent_branch": structure.parent_branch,
                            "structure": structure.model_dump(mode="json"),
                        }
                    )
                continue

            if promoted_later_structures:
                for structure in promoted_later_structures:
                    issues.append(
                        {
                            "id": structure.id,
                            "type": structure.type,
                            "reason": "shared post-branch continuation was promoted outside the required outer branch scope",
                            "branches": structure.branches,
                            "parent": structure.parent,
                            "parent_branch": structure.parent_branch,
                            "structure": structure.model_dump(mode="json"),
                        }
                    )
                continue

            issues.append(
                {
                    "id": decision.id,
                    "type": decision.type,
                    "reason": "missing shared post-branch continuation after the sibling decision",
                    "branches": decision.branches,
                    "parent": decision.parent,
                    "parent_branch": decision.parent_branch,
                    "structure": decision.model_dump(mode="json"),
                }
            )

    return issues


def _purpose_scope_signature(purpose: str | None, parent_branches: List[str]) -> str:
    tokens = re.findall(r"[a-z0-9]+", str(purpose or "").lower())
    ignored_tokens = set(_PURPOSE_STOPWORDS)
    for branch in parent_branches:
        ignored_tokens.update(_tokenize_handle(branch))
    return " ".join(token for token in tokens if token not in ignored_tokens)


def _duplicate_branch_local_structures(
    artifact: TopologyArtifact,
    normalized_text: str,
) -> List[Dict[str, Any]]:
    if not _has_shared_post_branch_scope_signal(normalized_text):
        return []

    duplicates: List[Dict[str, Any]] = []

    for parent in artifact.structures:
        if parent.type != "decision":
            continue
        children = [
            structure
            for structure in artifact.structures
            if structure.parent == parent.id and structure.parent_branch in parent.branches
        ]
        grouped: Dict[tuple[str, tuple[str, ...], str], List[Any]] = {}
        for child in children:
            signature = (
                child.type,
                tuple(child.branches),
                _purpose_scope_signature(child.purpose, parent.branches),
            )
            grouped.setdefault(signature, []).append(child)

        for sibling_group in grouped.values():
            distinct_parent_branches = {child.parent_branch for child in sibling_group}
            if len(sibling_group) < 2 or len(distinct_parent_branches) < 2:
                continue
            for child in sibling_group:
                duplicates.append(
                    {
                        "id": child.id,
                        "type": child.type,
                        "reason": "duplicate branch-local structures suggest a shared post-branch control region",
                        "parent": child.parent,
                        "parent_branch": child.parent_branch,
                        "branches": child.branches,
                        "structure": child.model_dump(mode="json"),
                    }
                )
    return duplicates


def _validate_topology_artifact_against_process_text(
    *,
    process_text: str,
    topology_artifact: Dict[str, Any] | TopologyArtifact,
) -> Dict[str, Any]:
    artifact = TopologyArtifact.model_validate(topology_artifact)
    normalized_text = _normalize_text(process_text)
    parallel_evidence = extract_parallel_evidence(process_text)
    control_requirements = extract_control_requirements(process_text)
    unsupported_structures: List[Dict[str, Any]] = []

    present_types = {structure.type for structure in artifact.structures}
    missing_issue_ids = {item["id"] for item in unsupported_structures}
    for topology_kind in ("parallel", "decision", "loop"):
        requirements = [
            requirement
            for requirement in control_requirements
            if requirement["required_topology_kind"] == topology_kind
        ]
        issue_id = f"MISSING_{topology_kind.upper()}"
        if requirements and topology_kind not in present_types and issue_id not in missing_issue_ids:
            unsupported_structures.append(
                {
                    "id": issue_id,
                    "type": topology_kind,
                    "reason": "missing topology type for explicit high-certainty control requirement",
                    "branches": [],
                    "structure": None,
                    "requirements": requirements,
                }
            )

    for structure in artifact.structures:
        structure_payload = structure.model_dump(mode="json")
        evidenced_branch_count = _count_evidenced_branch_handles(normalized_text, structure.branches)
        if structure.type == "decision":
            has_decision_cue = _contains_any_phrase(
                normalized_text,
                _DECISION_EVIDENCE_PHRASES,
            ) or _has_explicit_sentence_level_disjunction(normalized_text)
            if not has_decision_cue and evidenced_branch_count < 2:
                unsupported_structures.append(
                    {
                        "id": structure.id,
                        "type": structure.type,
                        "reason": "missing explicit branching evidence in process text",
                        "branches": structure.branches,
                    }
                )
        elif structure.type == "loop":
            if not _contains_any_phrase(normalized_text, _LOOP_EVIDENCE_PHRASES):
                unsupported_structures.append(
                    {
                        "id": structure.id,
                        "type": structure.type,
                        "reason": "missing explicit repetition evidence in process text",
                        "branches": structure.branches,
                    }
                )
        elif structure.type == "parallel":
            if not parallel_evidence:
                unsupported_structures.append(
                    {
                        "id": structure.id,
                        "type": structure.type,
                        "reason": "missing explicit concurrency or join evidence in process text",
                        "branches": structure.branches,
                    }
                )

        if unsupported_structures and unsupported_structures[-1].get("id") == structure.id:
            unsupported_structures[-1]["structure"] = structure_payload

    unsupported_structures.extend(
        _duplicate_branch_local_structures(
            artifact,
            normalized_text,
        )
    )
    unsupported_structures.extend(
        _shared_post_branch_scope_issues(
            artifact,
            normalized_text,
        )
    )

    if unsupported_structures:
        raise ValueError(
            "TopologyArtifact contains unsupported control structures for the current process text. "
            f"unsupported_structures={unsupported_structures}"
        )
    return artifact.model_dump(mode="json")


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
    control_evidence = extract_control_evidence(process_text)
    prompt = build_topology_experiment_prompt(
        process_text,
        keyword_hints=keyword_hints,
    )
    planner_attempts: List[Dict[str, Any]] = []
    current_prompt = prompt
    last_exc: Exception | None = None
    parsed_artifact: Dict[str, Any] | None = None
    artifact: Dict[str, Any] | None = None
    raw_output = ""
    response_mode = "structured_output"
    fallback_reason = None
    for correction_attempt in range(_MAX_CORRECTION_ATTEMPTS + 1):
        planner_call = _call_topology_planner(
            model=model,
            prompt=current_prompt,
        )
        raw_output = planner_call["raw_output"]
        response_mode = planner_call["response_mode"]
        fallback_reason = planner_call["fallback_reason"]
        parsed_artifact = None
        try:
            parsed_artifact = parse_topology_artifact_json(raw_output)
            artifact = _validate_topology_artifact_against_process_text(
                process_text=process_text,
                topology_artifact=parsed_artifact,
            )
            planner_attempts.append(
                {
                    "attempt_index": correction_attempt,
                    "prompt": current_prompt,
                    "raw_output": raw_output,
                    "parsed_output": parsed_artifact,
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
                    "parsed_output": parsed_artifact,
                    "response_mode": response_mode,
                    "fallback_reason": fallback_reason,
                    "validation_error": str(exc),
                }
            )
            if correction_attempt >= _MAX_CORRECTION_ATTEMPTS:
                break
            current_prompt = _build_topology_correction_prompt(
                base_prompt=prompt,
                process_text=process_text,
                invalid_topology_output=raw_output,
                parsed_topology_output=parsed_artifact,
                validation_error=str(exc),
                correction_attempt=correction_attempt + 1,
            )

    if artifact is None:
        exc = last_exc or ValueError("TopologyArtifact validation failed")
        raise TopologyArtifactGenerationError(
            f"TopologyArtifact validation failed: {exc}",
            debug_artifacts={
                "process_text": process_text,
                "control_evidence": control_evidence,
                "keyword_hints": keyword_hints,
                "topology_prompt": prompt,
                "topology_raw_output": raw_output,
                "topology_parsed_output": parsed_artifact,
                "topology_response_mode": response_mode,
                "topology_fallback_reason": fallback_reason,
                "topology_validation_error": str(exc),
                "topology_attempts": planner_attempts,
            },
        ) from exc
    return {
        "control_evidence": control_evidence,
        "keyword_hints": keyword_hints,
        "prompt": current_prompt,
        "raw_output": raw_output,
        "artifact": artifact,
        "response_mode": response_mode,
        "fallback_reason": fallback_reason,
        "planner_attempts": planner_attempts,
    }


__all__ = [
    "TOPOLOGY_ARTIFACT_SCHEMA",
    "_canonicalize_topology_artifact_payload",
    "TopologyArtifactGenerationError",
    "build_topology_experiment_prompt",
    "generate_topology_artifact",
    "parse_topology_artifact_json",
    "topology_artifact_response_format",
]
