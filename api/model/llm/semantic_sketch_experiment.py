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
    re.compile(
        r"\bin\s+(?:any|either|all)\s+(?:of\s+the\s+)?(?:case|cases)\b",
        re.IGNORECASE,
    ),
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
_LOOP_OUTCOME_STEMS = {
    "accept": "positive",
    "accepted": "positive",
    "approv": "positive",
    "approve": "positive",
    "approved": "positive",
    "complete": "complete",
    "completed": "complete",
    "ok": "positive",
    "pass": "positive",
    "resolved": "resolved",
    "success": "positive",
    "successful": "positive",
    "valid": "valid",
}
_EXPLICIT_RETRY_RETURN_PATTERN = re.compile(
    r"\b(?:again|back|repeat|restart|re-submit|resubmit|return|returned|returns|sent back)\b",
    re.IGNORECASE,
)

_COVERAGE_OPERATION_STEMS = {
    "approve": ("approv", "approve", "authoriz", "authorize"),
    "attach": ("attach",),
    "calculate": ("calculat", "calculate", "comput", "compute"),
    "call": ("call", "phone"),
    "close": ("clos", "close"),
    "combine": ("combin", "combine"),
    "confirm": ("confirm",),
    "correct": ("correct", "edit", "revis", "revise", "updat", "update", "resolv", "resolve"),
    "create": ("compil", "compile", "creat", "create", "generat", "generate", "prepar", "prepare", "produc", "produce", "writ", "write"),
    "identify": ("identif", "identify"),
    "link": ("link",),
    "notify": ("inform", "notif"),
    "pay": ("pay", "reimburs", "refund"),
    "process": ("conduct", "fulfill", "perform", "process"),
    "record": ("enter", "import", "mark", "note", "record", "register", "stor"),
    "reject": ("declin", "deni", "reject"),
    "retrieve": ("fetch", "retriev", "retrieve"),
    "review": ("analyz", "analyze", "assess", "audit", "check", "evaluat", "evaluate", "examin", "examine", "inspect", "review", "screen", "test", "validat", "validate", "verif", "verify"),
    "schedule": ("schedul", "schedule"),
    "select": ("choos", "choose", "select"),
    "send": ("deliver", "dispatch", "distribut", "distribute", "forward", "hand", "send", "ship", "submit", "transmit"),
}

_COVERAGE_OBJECT_STOPWORDS = _OWNERSHIP_TOKEN_STOPWORDS | {
    "activity",
    "accountant",
    "actor",
    "analyst",
    "begin",
    "business",
    "by",
    "clerk",
    "condition",
    "department",
    "employee",
    "finish",
    "flow",
    "manager",
    "must",
    "office",
    "officer",
    "operation",
    "organization",
    "otherwise",
    "person",
    "process",
    "staff",
    "start",
    "supervisor",
    "system",
    "team",
    "user",
}

_TOPOLOGY_REQUIRED_CUES = re.compile(
    r"\b(?:after each|another .* activity|arbitrary order|at the same time|concurrent(?:ly)?|"
    r"former case|in the meantime|latter case|meantime|parallel|repeat(?:ed|s)?|until)\b",
    re.IGNORECASE,
)


class SemanticSketchPlanGenerationError(Exception):
    def __init__(self, message: str, *, debug_artifacts: Dict[str, Any]) -> None:
        super().__init__(message)
        self.debug_artifacts = debug_artifacts


class SemanticOwnershipEvidenceValidationError(ValueError):
    pass


class SemanticCoverageEvidenceValidationError(ValueError):
    def __init__(self, issues: List[Dict[str, Any]]) -> None:
        self.issues = issues
        super().__init__(
            "SemanticSketchPlan omits high-confidence source activities: "
            + json.dumps(issues, ensure_ascii=False, sort_keys=True)
        )


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
    if "unrepresentable under the current root-slot model" in validation_error:
        ownership_feedback = (
            "\nLocal loop-continuation safety:\n"
            "The cited retry-success continuation is branch-local and has no safe shared root slot in the "
            "current representation. Preserve the action in its local branch. Do not move it into root_actions, "
            "do not invent a root_scope_* placeholder, and do not redirect the retry-success branch through an "
            "unrelated root slot. Keep retry_target (re-entry for repeated work or re-evaluation) distinct from "
            "retry_success_continuation (business work performed after success).\n"
        )
    elif "loop-success-continuation evidence" in validation_error:
        constrained_feedback = ""
        if "validator-approved constrained ownership relocation" in validation_error:
            constrained_feedback = (
                " This validator-approved relocation overrides the generic branch-local preference for the exact "
                "cited Action only. Use the previous parsed plan as the preservation baseline and apply exactly "
                "the REMOVE and ADD operations in the diagnostic. The Action must occur exactly once afterwards. "
                "Change only this diagnosed ownership relationship unless a later validator reports a separate "
                "problem. Preserve every unrelated Action, intent, target_slot_id, topology handle, and branch "
                "structure; do not move any other branch-specific Action to root/shared scope."
            )
        ownership_feedback = (
            "\nLoop-success-continuation correction:\n"
            "Correct only the cited loop ownership problem. Preserve the authoritative topology, unrelated root "
            "actions, and branch-local actions. Keep exactly one retry/rework branch on intent=\"loop_back\" and "
            "one successful exit branch on intent=\"continue\". Treat retry_target and retry_success_continuation "
            "as distinct concepts. When the diagnostic names allowed_shared_slot, place only the cited, safely "
            "shared retry-success continuation there once and remove only its duplicate from the ordinary-success "
            "branch. When the diagnostic names allowed_target_slot_id, set the successful exit branch's "
            "target_slot_id to exactly that slot for re-entry; do not choose a nearby slot and do not relocate "
            "unrelated actions. Never move branch-specific work to root scope."
            f"{constrained_feedback}\n"
        )
    coverage_feedback = ""
    if "omits high-confidence source activities" in validation_error:
        coverage_feedback = (
            "\nSource-coverage correction:\n"
            "The deterministic diagnostics identify explicit source-supported business activity that is not "
            "represented by an equivalent Action or by existing decision semantics. Re-check the cited source "
            "fragment and correct only the cited omission in its topology-compatible root or branch slot. Do not "
            "expand unrelated source details. Preserve a defensible compound Action when coordinated operations "
            "share an actor, business object, and ownership. Preserve the authoritative topology and ownership "
            "constraints; do not invent control structures, duplicate decision semantics, or turn timing/waiting "
            "language into an Action.\n"
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
        f"{coverage_feedback}"
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


def _coverage_operation(token: str, *, index: int, tokens: List[str]) -> str | None:
    stemmed = _stem_ownership_token(token)
    lowered = token.lower()
    previous = tokens[index - 1].lower() if index > 0 else ""
    following = tokens[index + 1].lower() if index + 1 < len(tokens) else ""
    if stemmed == "request":
        if (
            following in {"is", "are", "was", "were", "has", "have"}
            or previous in {"a", "an", "the"}
            or (lowered == "request" and index > 0)
        ):
            return None
        return "send"
    if stemmed == "process" and lowered == "process":
        if index > 0 or following in {"is", "continues", "ends", "starts"}:
            return None
    if stemmed == "call":
        if previous in {"cold", "center"} or (lowered == "call" and index > 0):
            return None
    for operation, stems in _COVERAGE_OPERATION_STEMS.items():
        if stemmed in stems:
            return operation
    return None


def _coverage_evidence(value: str) -> Dict[str, Any] | None:
    tokens = _tokenize(value)
    operation_occurrences = [
        (index, operation)
        for index, token in enumerate(tokens)
        if (operation := _coverage_operation(token, index=index, tokens=tokens)) is not None
    ]
    if not operation_occurrences:
        return None

    operation_tokens = {
        _stem_ownership_token(token)
        for index, token in enumerate(tokens)
        if _coverage_operation(token, index=index, tokens=tokens) is not None
    }
    objects = {
        stemmed
        for token in tokens
        if (stemmed := _stem_ownership_token(token)) not in _COVERAGE_OBJECT_STOPWORDS
        and stemmed not in operation_tokens
        and len(stemmed) > 2
    }
    if not objects:
        return None
    operation_objects: Dict[str, set[str]] = {}
    for occurrence_index, (token_index, operation) in enumerate(operation_occurrences):
        next_index = (
            operation_occurrences[occurrence_index + 1][0]
            if occurrence_index + 1 < len(operation_occurrences)
            else len(tokens)
        )
        local_objects = {
            stemmed
            for token in tokens[token_index + 1 : next_index]
            if (stemmed := _stem_ownership_token(token)) in objects
        }
        if not local_objects:
            previous_index = operation_occurrences[occurrence_index - 1][0] + 1 if occurrence_index else 0
            local_objects = {
                stemmed
                for token in tokens[previous_index:token_index]
                if (stemmed := _stem_ownership_token(token)) in objects
            }
        operation_objects.setdefault(operation, set()).update(local_objects or objects)
    return {
        "operations": sorted({operation for _, operation in operation_occurrences}),
        "objects": sorted(objects),
        "operation_objects": {
            operation: sorted(operation_objects[operation])
            for operation in sorted(operation_objects)
        },
    }


def _coverage_fragment_is_context_only(fragment: str) -> bool:
    normalized = _normalize_action_text(fragment)
    if re.search(r"\b(?:continue|proceed)(?:s|ed|ing)?\s+(?:the\s+)?process(?:ing)?\b", normalized):
        return True
    if re.fullmatch(r"process of .+ ends here", normalized):
        return True
    if re.search(
        r"\bwait(?:s|ed|ing)?\b.*\b(?:confirmation|day|days|week|weeks|month|months|until)\b",
        normalized,
    ):
        return True
    evidence = _coverage_evidence(fragment)
    if evidence and re.search(
        r"\bdoes\s+not\s+approve\b.*\breject(?:s|ed)?\b.*\brequest(?:s|ed)?\s+correction\b",
        normalized,
    ):
        return True
    if evidence and set(evidence["operations"]).issubset({"approve", "confirm", "reject", "review"}):
        if re.search(r"\b(?:approve|approved|reject|rejected|confirm|confirmed)\b.*\b(?:or|but)\b", normalized):
            return True
    if re.match(r"^(?:if|unless|whether|when|once|after|as soon as)\b", normalized) and "," not in fragment:
        return True
    return bool(
        re.fullmatch(
            r"(?:the\s+)?[\w\s-]+\s+(?:is|are|was|were|be|been)\s+"
            r"(?:approved|rejected|confirmed|completed|finished|ready|registered|valid|invalid)",
            normalized,
        )
    )


def _coverage_fragments(process_text: str) -> List[Dict[str, Any]]:
    fragments: List[Dict[str, Any]] = []
    for sentence in re.split(r"(?<=[.!?])\s+", process_text.strip()):
        stripped_sentence = sentence.strip()
        if not stripped_sentence:
            continue
        pieces = re.split(
            r"\s*;\s*|\b(?:afterwards|subsequently|then|finally)\b[,\s]*",
            stripped_sentence,
            flags=re.IGNORECASE,
        )
        for piece in pieces:
            fragment = piece.strip().strip(".!?")
            if not fragment:
                continue
            if re.match(r"^(?:if|unless|whether|when|once|after|as soon as)\b", fragment, re.IGNORECASE):
                _, separator, activity_clause = fragment.partition(",")
                if separator:
                    fragment = activity_clause.strip()
                    if not fragment:
                        continue
            if re.match(r"^in\b", fragment, re.IGNORECASE) and "," in fragment:
                comma_clauses = [clause.strip() for clause in fragment.split(",") if clause.strip()]
                executable_clauses = [clause for clause in comma_clauses if _coverage_evidence(clause)]
                if len(executable_clauses) == 1:
                    fragment = executable_clauses[0]
            if _coverage_fragment_is_context_only(fragment):
                continue
            evidence = _coverage_evidence(fragment)
            if evidence is None:
                continue
            fragments.append(
                {
                    "fragment": fragment,
                    "sentence": stripped_sentence,
                    **evidence,
                }
            )
    return fragments


def _semantic_coverage_entries(
    artifact: TopologyArtifact,
    plan: Dict[str, Any],
) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    for root in plan.get("root_actions") or []:
        slot_id = str(root.get("slot_id") or "").strip()
        for step in root.get("actions") or []:
            action = str(step.get("action") or "").strip()
            if action:
                entries.append({"text": action, "scope": slot_id, "kind": "action"})
    for branch in plan.get("branch_plans") or []:
        scope = f"{branch.get('structure_id')}/{branch.get('branch')}"
        for step in branch.get("steps") or []:
            action = str(step.get("action") or "").strip()
            if action:
                entries.append({"text": action, "scope": scope, "kind": "action"})
    for structure in artifact.structures:
        if structure.type != "decision":
            continue
        semantic_text = " ".join(
            part
            for part in [structure.purpose or "", *structure.branches]
            if str(part).strip()
        )
        if semantic_text:
            entries.append(
                {
                    "text": semantic_text,
                    "scope": f"decision:{structure.id}",
                    "kind": "decision_semantics",
                }
            )
    for entry in entries:
        entry["evidence"] = _coverage_evidence(entry["text"])
    return entries


def _coverage_entry_matches(source: Dict[str, Any], entry: Dict[str, Any]) -> bool:
    represented = entry.get("evidence")
    if not represented:
        return False
    if not set(source["operations"]).intersection(represented["operations"]):
        return False
    return bool(set(source["objects"]).intersection(represented["objects"]))


def _uncovered_coverage_operations(
    source: Dict[str, Any],
    entries: List[Dict[str, Any]],
) -> List[str]:
    uncovered: List[str] = []
    for operation in source["operations"]:
        source_objects = set(source["operation_objects"].get(operation) or source["objects"])
        if any(
            entry.get("evidence")
            and operation in entry["evidence"]["operations"]
            and source_objects.intersection(entry["evidence"]["objects"])
            for entry in entries
        ):
            continue
        coordinated_clause = bool(re.search(r"\b(?:and|as well as)\b", source["fragment"], re.IGNORECASE))
        if any(
            entry.get("kind") == "action"
            and entry.get("evidence")
            and (
                (
                    len(source["operations"]) > 1
                    and source_objects.intersection(entry["evidence"]["objects"])
                )
                or (
                    coordinated_clause
                    and len(source_objects.intersection(entry["evidence"]["objects"])) >= 2
                )
            )
            for entry in entries
        ):
            continue
        uncovered.append(operation)
    return uncovered


def _related_coverage_content(
    *,
    operations: List[str],
    objects: List[str],
    entries: List[Dict[str, Any]],
) -> List[str]:
    operation_set = set(operations)
    object_set = set(objects)
    related = [
        entry["text"]
        for entry in entries
        if entry.get("evidence")
        and (
            operation_set.intersection(entry["evidence"]["operations"])
            or object_set.intersection(entry["evidence"]["objects"])
        )
    ]
    return related[:4]


def _coverage_issue_priority(issue: Dict[str, Any]) -> tuple[int, int, int, int]:
    return (
        0 if len(issue["operations"]) == 1 else 1,
        0 if 1 <= len(issue["objects"]) <= 3 else 1,
        len(issue["objects"]),
        issue["source_index"],
    )


def _coverage_scope_hint(
    *,
    process_text: str,
    source: Dict[str, Any],
    uncovered_operations: List[str],
    artifact: TopologyArtifact,
    entries: List[Dict[str, Any]],
) -> str | None:
    if not artifact.structures:
        return "ROOT_START"
    if _TOPOLOGY_REQUIRED_CUES.search(source["sentence"]):
        return None

    scope_objects = {
        object_token
        for operation in uncovered_operations
        for object_token in source["operation_objects"].get(operation, source["objects"])
    }
    root_structures = [structure for structure in artifact.structures if structure.parent == "ROOT"]
    if len(root_structures) == 1 and _has_strong_universal_continuation(source["sentence"]):
        return f"AFTER_{root_structures[0].id}"

    branch_scopes = {
        f"{structure.id}/{branch}"
        for structure in artifact.structures
        for branch in structure.branches
        if set(_ownership_tokens(branch)).intersection(scope_objects)
    }
    if len(branch_scopes) == 1:
        return next(iter(branch_scopes))

    object_scopes = {
        str(entry["scope"])
        for entry in entries
        if entry.get("kind") == "action"
        and entry.get("evidence")
        and len(scope_objects.intersection(entry["evidence"]["objects"])) >= 2
    }
    if len(object_scopes) == 1:
        return next(iter(object_scopes))

    fragment_position = process_text.lower().find(source["fragment"].lower())
    first_control = re.search(r"\b(?:if|otherwise|whether|in case|depending on)\b", process_text, re.IGNORECASE)
    if fragment_position >= 0 and first_control is not None and fragment_position < first_control.start():
        return "ROOT_START"
    return None


def validate_semantic_coverage_against_evidence(
    process_text: str,
    *,
    topology_artifact: Dict[str, Any] | TopologyArtifact,
    semantic_plan: Dict[str, Any] | SemanticSketchPlan,
) -> Dict[str, Any]:
    """Reject definite source-activity omissions without rewriting semantic content."""
    artifact = _normalize_topology_artifact(topology_artifact)
    plan = _normalize_semantic_plan(semantic_plan).model_dump(mode="json")
    entries = _semantic_coverage_entries(artifact, plan)
    candidate_issues: List[Dict[str, Any]] = []

    for source_index, source in enumerate(_coverage_fragments(process_text)):
        if any(_coverage_entry_matches(source, entry) for entry in entries):
            continue
        uncovered_operations = _uncovered_coverage_operations(source, entries)
        if not uncovered_operations:
            continue
        scope_hint = _coverage_scope_hint(
            process_text=process_text,
            source=source,
            uncovered_operations=uncovered_operations,
            artifact=artifact,
            entries=entries,
        )
        if scope_hint is None:
            continue
        diagnostic_objects = sorted(
            {
                object_token
                for operation in uncovered_operations
                for object_token in source["operation_objects"].get(operation, source["objects"])
            }
        )
        issue = {
            "source_fragment": source["fragment"],
            "operations": uncovered_operations,
            "objects": diagnostic_objects,
            "qualification": "explicit executable operation with concrete business content",
            "checked_semantic_content": _related_coverage_content(
                operations=uncovered_operations,
                objects=diagnostic_objects,
                entries=entries,
            ),
            "scope_hint": scope_hint,
            "reason": "no equivalent Action or decision semantics found",
            "source_index": source_index,
        }
        duplicate_key = (scope_hint, tuple(uncovered_operations))
        if any(
            (existing["scope_hint"], tuple(existing["operations"])) == duplicate_key
            for existing in candidate_issues
        ):
            continue
        candidate_issues.append(issue)

    if candidate_issues:
        strongest_issue = min(candidate_issues, key=_coverage_issue_priority)
        strongest_issue.pop("source_index", None)
        raise SemanticCoverageEvidenceValidationError([strongest_issue])
    return plan


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


def _root_entry_slot_id(root_structure_id: str, root_structures: List[TopologyStructure]) -> str | None:
    for index, structure in enumerate(root_structures):
        if structure.id != root_structure_id:
            continue
        return "ROOT_START" if index == 0 else f"AFTER_{root_structures[index - 1].id}"
    return None


def _root_branch_containing_structure(
    structure: TopologyStructure,
    root_structure_id: str,
    by_id: Dict[str, TopologyStructure],
) -> str | None:
    current = structure
    visited: set[str] = set()
    while current.parent != "ROOT":
        if current.id in visited or current.parent not in by_id:
            return None
        visited.add(current.id)
        if current.parent == root_structure_id:
            return current.parent_branch
        current = by_id[current.parent]
    return None


def _shared_root_continuation_is_scope_safe(
    *,
    root_ancestor: TopologyStructure,
    decision: TopologyStructure,
    retry_side_branch: str,
    direct_branch: str,
    branch_plans: Dict[tuple[str, str], Dict[str, Any]],
    structures_by_id: Dict[str, TopologyStructure],
) -> bool:
    if root_ancestor.type != "decision":
        return False
    continuing_root_branches = {
        branch
        for branch in root_ancestor.branches
        if (branch_plans.get((root_ancestor.id, branch)) or {}).get("intent") == "continue"
    }
    if decision.id == root_ancestor.id:
        eligible_branches = {retry_side_branch, direct_branch}
    else:
        owner_branch = _root_branch_containing_structure(
            decision,
            root_ancestor.id,
            structures_by_id,
        )
        if owner_branch is None:
            return False
        eligible_branches = {owner_branch}
    return bool(continuing_root_branches) and continuing_root_branches.issubset(eligible_branches)


def _action_has_universal_continuation_evidence(action: str, sentences: List[str]) -> bool:
    return any(
        _has_strong_universal_continuation(sentence)
        and _action_matches_evidence(action, _ownership_tokens(sentence))
        for sentence in sentences
    )


def _source_conditionally_links_action(action: str, sentences: List[str]) -> bool:
    return any(
        re.search(r"\b(?:if|when|once|after|upon)\b", sentence, re.IGNORECASE)
        and _action_matches_evidence(action, _ownership_tokens(sentence))
        for sentence in sentences
    )


def _is_descendant_of(
    structure: TopologyStructure,
    ancestor_id: str,
    by_id: Dict[str, TopologyStructure],
) -> bool:
    current = structure
    visited: set[str] = set()
    while current.parent != "ROOT":
        if current.id in visited or current.parent not in by_id:
            return False
        visited.add(current.id)
        if current.parent == ancestor_id:
            return True
        current = by_id[current.parent]
    return False


def _shared_relocation_crosses_no_later_structure(
    *,
    decision: TopologyStructure,
    root_ancestor: TopologyStructure,
    structures: List[TopologyStructure],
    structures_by_id: Dict[str, TopologyStructure],
) -> bool:
    owner_branch = _root_branch_containing_structure(
        decision,
        root_ancestor.id,
        structures_by_id,
    )
    if owner_branch is None:
        return False
    decision_index = next(
        (index for index, structure in enumerate(structures) if structure.id == decision.id),
        None,
    )
    if decision_index is None:
        return False
    for later_structure in structures[decision_index + 1 :]:
        if _root_ancestor_id(later_structure, structures_by_id) != root_ancestor.id:
            continue
        if _root_branch_containing_structure(
            later_structure,
            root_ancestor.id,
            structures_by_id,
        ) != owner_branch:
            continue
        if not _is_descendant_of(later_structure, decision.id, structures_by_id):
            return False
    return True


def _constrained_shared_relocation_is_proven(
    *,
    action: str,
    direct_states: set[str],
    loop_success_states: set[str],
    sentences: List[str],
    scope_safe: bool,
    decision: TopologyStructure,
    root_ancestor: TopologyStructure,
    structures: List[TopologyStructure],
    structures_by_id: Dict[str, TopologyStructure],
) -> bool:
    return (
        scope_safe
        and bool(direct_states.intersection(loop_success_states))
        and _source_conditionally_links_action(action, sentences)
        and _shared_relocation_crosses_no_later_structure(
            decision=decision,
            root_ancestor=root_ancestor,
            structures=structures,
            structures_by_id=structures_by_id,
        )
    )


def _loop_outcome_states(*values: str) -> set[str]:
    states: set[str] = set()
    for value in values:
        for token in _tokenize(value):
            for stem, state in _LOOP_OUTCOME_STEMS.items():
                if token.startswith(stem):
                    states.add(state)
                    break
    return states


def _source_links_outcome_to_actions(
    process_text: str,
    *,
    outcome_states: set[str],
    actions: List[str],
) -> bool:
    if not outcome_states or not actions:
        return False
    for sentence in re.split(r"(?<=[.!?])\s+", process_text.strip()):
        if not outcome_states.intersection(_loop_outcome_states(sentence)):
            continue
        sentence_tokens = _ownership_tokens(sentence)
        if any(_action_matches_evidence(action, sentence_tokens) for action in actions):
            return True
    return False


def _has_explicit_retry_return_evidence(process_text: str, loop: TopologyStructure) -> bool:
    loop_tokens = _ownership_tokens(loop.purpose or "")
    if not loop_tokens:
        return False
    for sentence in re.split(r"(?<=[.!?])\s+", process_text.strip()):
        if not _EXPLICIT_RETRY_RETURN_PATTERN.search(sentence):
            continue
        if not re.search(
            r"\b(?:must\s+again|returns?\b.*\bagain|sent\s+back\b.*\b(?:beginning|first|review|supervisor))\b",
            sentence,
            re.IGNORECASE,
        ):
            continue
        if loop_tokens.intersection(_ownership_tokens(sentence)):
            return True
    return False


def _raise_shared_ownership_contradiction(reason: str) -> None:
    raise SemanticOwnershipEvidenceValidationError(
        "SemanticSketchPlan contradicts strong shared-continuation evidence: "
        f"{reason}. Preserve branch-local actions, place shared behavior once in the post-structure slot, "
        "and keep every path that must reach it continuing until that slot."
    )


def _raise_loop_continuation_contradiction(reason: str) -> None:
    raise SemanticOwnershipEvidenceValidationError(
        "SemanticSketchPlan contradicts loop-success-continuation evidence: "
        f"{reason}. Preserve the authoritative loop and unrelated semantic content; correct only the cited "
        "retry/success ownership or continuation."
    )


def _raise_unrepresentable_loop_continuation(reason: str) -> None:
    raise SemanticOwnershipEvidenceValidationError(
        "SemanticSketchPlan loop-success-continuation is unrepresentable under the current root-slot model: "
        f"{reason}. Preserve the branch-local action; do not relocate it to root/shared scope, invent a "
        "root_scope_* placeholder, or conflate retry_target with retry_success_continuation."
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
    branch_plans = _branch_plan_lookup(plan)
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", process_text.strip())
        if sentence.strip()
    ]

    if len(root_structures) == 1:
        root_structure = root_structures[0]
        post_slot_id = f"AFTER_{root_structure.id}"
        shared_actions = _root_action_texts(plan, post_slot_id)
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

    structures_by_id = {structure.id: structure for structure in artifact.structures}
    for loop in artifact.structures:
        if loop.type != "loop":
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
            _raise_loop_continuation_contradiction(
                f"loop={loop.id} requires exactly one retry branch with intent=loop_back and one successful "
                f"exit branch with intent=continue; retry_branches={[branch for branch, _ in retry_plans]}, "
                f"continue_branches={[branch for branch, _ in continuing_plans]}"
            )
        retry_branch, _retry_plan = retry_plans[0]
        loop_success_branch, loop_success_plan = continuing_plans[0]
        root_ancestor_id = _root_ancestor_id(loop, structures_by_id)
        if root_ancestor_id is None:
            continue
        root_ancestor = structures_by_id[root_ancestor_id]
        post_slot_id = f"AFTER_{root_ancestor_id}"
        shared_actions = _root_action_texts(plan, post_slot_id)
        has_explicit_retry_target = False

        if loop.parent != "ROOT" and loop.parent_branch:
            explicit_target = str(loop_success_plan.get("target_slot_id") or "").strip()
            if _has_explicit_retry_return_evidence(process_text, loop):
                entry_slot_id = _root_entry_slot_id(root_ancestor_id, root_structures)
                if entry_slot_id and explicit_target != entry_slot_id:
                    _raise_loop_continuation_contradiction(
                        f"loop={loop.id}, retry_branch={retry_branch}, success_branch={loop_success_branch}, "
                        f"expected_continuation={entry_slot_id}, retry_target={entry_slot_id}, "
                        f"allowed_target_slot_id={entry_slot_id}, current_target={explicit_target or post_slot_id}; "
                        "the source explicitly returns corrected work to earlier review; "
                        "retry_success_continuation remains separate"
                    )
                has_explicit_retry_target = bool(entry_slot_id and explicit_target == entry_slot_id)

        if loop.parent == "ROOT" or not loop.parent_branch:
            continue
        for decision, retry_side_branch in _decision_ancestor_scopes(loop, structures_by_id):
            if len(decision.branches) != 2:
                continue
            if not _purposes_share_retry_subject(decision.purpose, loop.purpose):
                continue
            if _root_ancestor_id(decision, structures_by_id) != root_ancestor_id:
                continue
            direct_branches = [branch for branch in decision.branches if branch != retry_side_branch]
            if len(direct_branches) != 1:
                continue
            direct_branch = direct_branches[0]
            direct_plan = branch_plans.get((decision.id, direct_branch))
            if direct_plan is None:
                continue
            # A structurally terminal sibling is a failure exit, not the ordinary
            # success path that a retry completion must rejoin.
            if direct_plan.get("intent") == "terminate":
                continue
            direct_actions = [
                str(step.get("action") or "").strip()
                for step in direct_plan.get("steps") or []
                if str(step.get("action") or "").strip()
            ]
            direct_states = _loop_outcome_states(direct_branch, *direct_actions)
            loop_success_states = _loop_outcome_states(loop_success_branch, loop.purpose or "")
            if not direct_states.intersection(loop_success_states) and not _source_links_outcome_to_actions(
                process_text,
                outcome_states=loop_success_states,
                actions=direct_actions,
            ):
                continue
            if direct_plan.get("intent") != "continue":
                _raise_loop_continuation_contradiction(
                    f"loop={loop.id}, success_branch={loop_success_branch}, ordinary_success="
                    f"{decision.id}/{direct_branch}, expected_continuation={post_slot_id}; ordinary success "
                    f"uses intent={direct_plan.get('intent')}"
                )
            # An explicit, validated re-review target returns execution to the
            # ordinary decision path; it is not a shared post-success slot.
            if has_explicit_retry_target:
                continue
            scope_safe = _shared_root_continuation_is_scope_safe(
                root_ancestor=root_ancestor,
                decision=decision,
                retry_side_branch=retry_side_branch,
                direct_branch=direct_branch,
                branch_plans=branch_plans,
                structures_by_id=structures_by_id,
            )
            candidate_shared_actions = [
                action
                for action in shared_actions
                if _source_links_outcome_to_actions(
                    process_text,
                    outcome_states=loop_success_states,
                    actions=[action],
                )
                and not _action_has_universal_continuation_evidence(action, sentences)
            ]
            if not scope_safe and (direct_actions or candidate_shared_actions):
                unsafe_actions = direct_actions or candidate_shared_actions
                _raise_unrepresentable_loop_continuation(
                    f"loop={loop.id}, success_branch={loop_success_branch}, local_owner="
                    f"{decision.id}/{direct_branch}, required_local_actions={unsafe_actions!r}; "
                    f"shared root slot {post_slot_id} is reached by unrelated non-terminated paths"
                )
            explicit_target = str(loop_success_plan.get("target_slot_id") or "").strip()
            if explicit_target and explicit_target != post_slot_id:
                _raise_loop_continuation_contradiction(
                    f"loop={loop.id}, success_branch={loop_success_branch}, ordinary_success="
                    f"{decision.id}/{direct_branch}, expected_continuation={post_slot_id}, "
                    f"current_target={explicit_target}"
                )
            evidenced_direct_actions = direct_actions
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
                constrained_relocation = (
                    len(evidenced_direct_actions) == 1
                    and _constrained_shared_relocation_is_proven(
                        action=evidenced_direct_actions[0],
                        direct_states=direct_states,
                        loop_success_states=loop_success_states,
                        sentences=sentences,
                        scope_safe=scope_safe,
                        decision=decision,
                        root_ancestor=root_ancestor,
                        structures=artifact.structures,
                        structures_by_id=structures_by_id,
                    )
                )
                constrained_instruction = ""
                if constrained_relocation:
                    exact_action = json.dumps(evidenced_direct_actions[0], ensure_ascii=False)
                    constrained_instruction = (
                        "; validator-approved constrained ownership relocation: "
                        f"exact_action={exact_action}; invalid_owner=branch_plans[structure_id={decision.id},"
                        f"branch={direct_branch}].steps; allowed_destination=root_actions[slot_id={post_slot_id}]"
                        ".actions; required_change=REMOVE exact_action from invalid_owner, then ADD exact_action "
                        "exactly once to allowed_destination; preserve=all_other_actions,intents,target_slot_ids,"
                        "topology_handles,branch_structure"
                    )
                _raise_loop_continuation_contradiction(
                    f"loop={loop.id}, success_branch={loop_success_branch}, "
                    f"expected_continuation={post_slot_id}, retry_success_continuation={post_slot_id}, "
                    f"allowed_shared_slot={post_slot_id}; "
                    f"retry success cannot reach action {evidenced_direct_actions!r} owned only by "
                    f"{decision.id}/{direct_branch}{constrained_instruction}"
                )
            _raise_loop_continuation_contradiction(
                f"loop={loop.id}, success_branch={loop_success_branch}, "
                f"expected_continuation={post_slot_id}, retry_success_continuation={post_slot_id}, "
                f"allowed_shared_slot={post_slot_id}; "
                f"shared action remains duplicated inside {decision.id}/{direct_branch}; keep it only once in "
                f"{post_slot_id}"
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
        artifact = None
        try:
            parsed_payload = _parse_semantic_sketch_plan_payload(raw_output)
            invalid_branch_plans = _log_invalid_semantic_branch_plans(
                raw_output=raw_output,
                parsed_payload=parsed_payload,
            )
            candidate_artifact = _revalidate_semantic_plan_against_topology(
                topology_artifact=normalized_topology_artifact,
                semantic_plan=parsed_payload,
            )
            candidate_artifact = validate_semantic_ownership_against_evidence(
                process_text,
                topology_artifact=normalized_topology_artifact,
                semantic_plan=candidate_artifact,
            )
            candidate_artifact = validate_semantic_coverage_against_evidence(
                process_text,
                topology_artifact=normalized_topology_artifact,
                semantic_plan=candidate_artifact,
            )
            artifact = candidate_artifact
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
    "SemanticCoverageEvidenceValidationError",
    "SemanticOwnershipEvidenceValidationError",
    "SemanticSketchPlanGenerationError",
    "build_semantic_sketch_experiment_prompt",
    "generate_semantic_sketch_plan",
    "parse_semantic_sketch_plan_json",
    "preserve_explicit_business_activities",
    "semantic_sketch_plan_response_format",
    "validate_semantic_coverage_against_evidence",
    "validate_semantic_ownership_against_evidence",
]
