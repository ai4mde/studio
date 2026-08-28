from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .core import CONTROL_NODE_TYPES, AutomaticItem, Counts, EvalGraph, evaluation_item_id, normalize_label, reachable


ACTION_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
ACTION_MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
ACTION_SIMILARITY_THRESHOLD = 0.44


class SimilarityProvider(Protocol):
    def matrix(self, reference: Sequence[str], generated: Sequence[str]) -> list[list[float]]: ...


class SentenceTransformerSimilarity:
    """Lazy, explicitly configured semantic similarity provider."""

    def __init__(self, model_name: str, revision: str, cache_folder: str) -> None:
        if not model_name or not revision or not cache_folder:
            raise ValueError("Action model name, revision, and cache folder are required")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError("sentence-transformers is required for a real V2 run") from exc
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError("torch is required for a deterministic V2 Action run") from exc
        torch.manual_seed(0)
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        self.model = SentenceTransformer(
            model_name,
            revision=revision,
            device="cpu",
            cache_folder=cache_folder,
            local_files_only=True,
        )

    def matrix(self, reference: Sequence[str], generated: Sequence[str]) -> list[list[float]]:
        if not reference or not generated:
            return [[] for _ in reference]
        embeddings = self.model.encode(
            list(reference) + list(generated),
            batch_size=32,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        split = len(reference)
        return (embeddings[:split] @ embeddings[split:].T).tolist()


@dataclass(frozen=True, slots=True)
class ActionMatch:
    case_id: str
    candidate_id: str
    reference_id: str
    generated_id: str
    similarity: float
    occurrence_ambiguous: bool = False
    contested: bool = False
    review_pending: bool = False
    uncertainty_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ActionResult:
    case_id: str
    candidate_id: str
    matches: tuple[ActionMatch, ...]
    counts: Counts
    items: tuple[AutomaticItem, ...]

    @property
    def reference_to_generated(self) -> dict[str, str]:
        return {match.reference_id: match.generated_id for match in self.matches}

    @property
    def generated_to_reference(self) -> dict[str, str]:
        return {match.generated_id: match.reference_id for match in self.matches}

    @property
    def occurrence_ambiguous_reference_ids(self) -> frozenset[str]:
        return frozenset(match.reference_id for match in self.matches if match.occurrence_ambiguous)

    @property
    def contested_reference_ids(self) -> frozenset[str]:
        return frozenset(match.reference_id for match in self.matches if match.contested)

    @property
    def review_pending_reference_ids(self) -> frozenset[str]:
        return frozenset(match.reference_id for match in self.matches if match.review_pending)


def _maximum_assignment(weights: list[list[float]]) -> list[tuple[int, int]]:
    """Maximum-weight square assignment using the O(n^3) Hungarian algorithm."""
    rows = len(weights)
    cols = len(weights[0]) if rows else 0
    size = max(rows, cols)
    if not size:
        return []
    cost = [[0.0] * size for _ in range(size)]
    for i in range(rows):
        for j in range(cols):
            cost[i][j] = -weights[i][j]
    u, v = [0.0] * (size + 1), [0.0] * (size + 1)
    p, way = [0] * (size + 1), [0] * (size + 1)
    for i in range(1, size + 1):
        p[0] = i
        j0 = 0
        minimum = [float("inf")] * (size + 1)
        used = [False] * (size + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], float("inf"), 0
            for j in range(1, size + 1):
                if used[j]:
                    continue
                current = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if current < minimum[j]:
                    minimum[j], way[j] = current, j0
                if minimum[j] < delta:
                    delta, j1 = minimum[j], j
            for j in range(size + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    return sorted((p[j] - 1, j - 1) for j in range(1, size + 1) if p[j] and p[j] <= rows and j <= cols)


def _lexicographic_assignment(scores: list[list[float]], threshold: float) -> list[tuple[int, int]]:
    """Maximize eligible cardinality, then similarity, without a methodological weight."""
    rows = len(scores)
    cols = len(scores[0]) if rows else 0
    # One additional eligible pair must dominate every possible difference in
    # total cosine similarity. This is an exact encoding of the two objectives.
    cardinality_unit = max(rows, cols) + 1
    objective = [
        [cardinality_unit + score if score >= threshold else 0.0 for score in row]
        for row in scores
    ]
    return [(i, j) for i, j in _maximum_assignment(objective) if scores[i][j] >= threshold]


def _occurrence_order(graph: EvalGraph, node_ids: Sequence[str]) -> tuple[str, ...] | None:
    ids = set(node_ids)
    if len(ids) < 2:
        return tuple(node_ids)
    before = {(left, right) for left in ids for right in ids - {left} if right in reachable(graph, left)}
    if any((left, right) not in before and (right, left) not in before for left in ids for right in ids if left < right):
        return None
    return tuple(sorted(ids, key=lambda node: (sum((other, node) in before for other in ids), node)))


def _local_context(graph: EvalGraph, node_id: str) -> dict[str, Any]:
    def describe(ids: Sequence[str]) -> list[dict[str, str | None]]:
        return [
            {"id": item, "type": graph.by_id[item].type, "label": graph.by_id[item].label}
            for item in ids
        ]
    return {"incoming": describe(graph.incoming[node_id]), "outgoing": describe(graph.outgoing[node_id])}


def _source_excerpt(source_text: str | None, labels: Sequence[str | None]) -> str:
    if not source_text:
        return ""
    concepts = {token for label in labels if label for token in label.split() if len(token) > 2}
    passages = [part.strip() for part in source_text.replace("\n", " ").split(".") if part.strip()]
    if not passages:
        return source_text[:500]
    return max(passages, key=lambda part: (len(concepts & set(part.casefold().split())), -len(part)))[:500]


def _source_scope_evidence(
    source_text: str | None, label: str | None, *, reference_side: bool
) -> dict[str, Any] | None:
    if not source_text or not label:
        return None
    label_tokens = {token for token in label.split() if len(token) > 2}
    normalized_source = normalize_label(source_text) or ""
    source_tokens = set(normalized_source.split())
    passages = [normalize_label(part) or "" for part in source_text.replace("\n", " ").split(".")]
    passages = [part for part in passages if part]
    local_source = max(
        passages, key=lambda part: (len(label_tokens & set(part.split())), -len(part)), default=normalized_source
    )
    categories = {"in_scope_executable_action"}
    cues: set[str] = set()
    cue_groups = {
        "trigger_event": {"when", "whenever", "upon", "once", "triggered"},
        "precondition": {"before", "requires", "required", "provided", "prerequisite"},
        "postcondition": {"after", "afterwards", "finally", "completion", "completed"},
        "out_of_scope_interaction": {"external", "outside", "third party"},
    }
    for category, category_cues in cue_groups.items():
        matched = {cue for cue in category_cues if cue in local_source}
        if matched:
            categories.add(category)
            cues.update(matched)
    overlap = sorted(label_tokens & source_tokens)
    if reference_side and label_tokens and not overlap:
        categories.add("reference_only_modelling_addition")
        cues.add("no_source_label_token_overlap")
    if len(categories) < 2:
        return None
    return {
        "possible_scope_categories": sorted(categories),
        "scope_cues": sorted(cues),
        "label_source_token_overlap": overlap,
        "source_text_excerpt": _source_excerpt(source_text, (label,)),
    }


def evaluate_actions(
    case_id: str,
    candidate_id: str,
    reference: EvalGraph,
    generated: EvalGraph,
    similarity: SimilarityProvider,
    threshold: float,
    *,
    source_text: str | None = None,
    reference_review_evidence: Sequence[Mapping[str, Any]] = (),
) -> ActionResult:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Action threshold must be between 0 and 1")
    ref = sorted((node for node in reference.nodes if node.type == "action"), key=lambda n: n.id)
    gen = sorted((node for node in generated.nodes if node.type == "action"), key=lambda n: n.id)
    scores = similarity.matrix([node.label or "" for node in ref], [node.label or "" for node in gen])
    if len(scores) != len(ref) or any(len(row) != len(gen) for row in scores):
        raise ValueError("Similarity provider returned an invalid matrix")
    pairs = _lexicographic_assignment(scores, threshold)

    # Exact duplicate reference labels have identical semantic rows. Resolve only
    # those occurrences by graph order when both sides form a total precedence order.
    occurrence_ambiguous: set[tuple[int, int]] = set()
    by_label: dict[str, list[int]] = {}
    for index, node in enumerate(ref):
        by_label.setdefault(node.label or "", []).append(index)
    for indices in by_label.values():
        if len(indices) < 2:
            continue
        selected = [(i, j) for i, j in pairs if i in indices]
        if len(selected) < 2:
            continue
        ref_order = _occurrence_order(reference, [ref[i].id for i, _ in selected])
        gen_order = _occurrence_order(generated, [gen[j].id for _, j in selected])
        if ref_order is None or gen_order is None:
            occurrence_ambiguous.update(selected)
            continue
        ref_index = {node.id: i for i, node in enumerate(ref)}
        gen_index = {node.id: j for j, node in enumerate(gen)}
        pairs = [(i, j) for i, j in pairs if i not in indices]
        pairs.extend((ref_index[left], gen_index[right]) for left, right in zip(ref_order, gen_order))

    matched_ref_indices = {i for i, _ in pairs}
    matched_gen_indices = {j for _, j in pairs}
    pair_reasons: dict[tuple[int, int], set[str]] = {pair: set() for pair in pairs}
    for i, j in pairs:
        eligible_row = [column for column, score in enumerate(scores[i]) if score >= threshold]
        eligible_col = [row for row in range(len(ref)) if scores[row][j] >= threshold]
        if scores[i][j] != max(scores[i][column] for column in eligible_row) or scores[i][j] != max(scores[row][j] for row in eligible_col):
            pair_reasons[(i, j)].add("non_reciprocal_best")
        if len(eligible_row) > 1 or len(eligible_col) > 1:
            pair_reasons[(i, j)].add("competing_eligible_action")
        if (i, j) in occurrence_ambiguous:
            pair_reasons[(i, j)].add("unresolved_duplicate_occurrence")

    unmatched_ref = set(range(len(ref))) - matched_ref_indices
    unmatched_gen = set(range(len(gen))) - matched_gen_indices
    ref_review: dict[int, set[str]] = {i: set() for i in range(len(ref))}
    gen_review: dict[int, set[str]] = {j: set() for j in range(len(gen))}
    ref_review_evidence: dict[int, dict[str, Any]] = {i: {} for i in range(len(ref))}
    gen_review_evidence: dict[int, dict[str, Any]] = {j: {} for j in range(len(gen))}
    for j in unmatched_gen:
        related = [(i, matched_j) for i, matched_j in pairs if scores[i][j] >= threshold]
        if related:
            gen_review[j].add("possible_split_action")
            for pair in related:
                pair_reasons[pair].add("possible_split_action")
    for i in unmatched_ref:
        related = [(matched_i, j) for matched_i, j in pairs if scores[i][j] >= threshold]
        if related:
            ref_review[i].add("possible_combined_action")
            for pair in related:
                pair_reasons[pair].add("possible_combined_action")

    ignored_tokens = {
        token
        for evidence in reference_review_evidence
        for value in evidence.values()
        if isinstance(value, str)
        for token in value.split()
        if len(token) > 2
    }
    for j in unmatched_gen:
        if ignored_tokens & set((gen[j].label or "").split()):
            gen_review[j].add("possible_cross_notation_evidence")

    labelled_controls = sorted(
        (node for node in generated.nodes if node.type in CONTROL_NODE_TYPES and node.label),
        key=lambda node: node.id,
    )
    if unmatched_ref and labelled_controls:
        unmatched_ref_order = sorted(unmatched_ref)
        control_scores = similarity.matrix(
            [ref[index].label or "" for index in unmatched_ref_order],
            [node.label or "" for node in labelled_controls],
        )
        if len(control_scores) != len(unmatched_ref_order) or any(
            len(row) != len(labelled_controls) for row in control_scores
        ):
            raise ValueError("Similarity provider returned an invalid task/control matrix")
        for row_index, ref_index in enumerate(unmatched_ref_order):
            candidates = [
                {"node_id": node.id, "node_type": node.type, "label": node.label,
                 "similarity": control_scores[row_index][column]}
                for column, node in enumerate(labelled_controls)
                if control_scores[row_index][column] >= threshold
            ]
            if candidates:
                ref_review[ref_index].add("task_vs_control_node")
                ref_review_evidence[ref_index]["labelled_control_candidates"] = candidates

    for index in unmatched_ref:
        scope = _source_scope_evidence(source_text, ref[index].label, reference_side=True)
        if scope:
            ref_review[index].add("source_scope_ambiguity")
            ref_review_evidence[index]["source_scope_evidence"] = scope
    for index in unmatched_gen:
        scope = _source_scope_evidence(source_text, gen[index].label, reference_side=False)
        if scope:
            gen_review[index].add("source_scope_ambiguity")
            gen_review_evidence[index]["source_scope_evidence"] = scope

    matches = tuple(
        ActionMatch(
            case_id, candidate_id, ref[i].id, gen[j].id, scores[i][j],
            "unresolved_duplicate_occurrence" in pair_reasons[(i, j)],
            bool(pair_reasons[(i, j)]), bool(pair_reasons[(i, j)]),
            tuple(sorted(pair_reasons[(i, j)])),
        )
        for i, j in sorted(pairs)
    )
    matched_ref = {match.reference_id for match in matches}
    matched_gen = {match.generated_id for match in matches}
    items: list[AutomaticItem] = []
    ref_by_id, gen_by_id = reference.by_id, generated.by_id
    for match in matches:
        items.append(AutomaticItem(
            case_id, candidate_id, "Action",
            evaluation_item_id(case_id, candidate_id, "action", "match", match.reference_id, match.generated_id), "TP",
            {"reference_id": match.reference_id, "generated_id": match.generated_id, "similarity": match.similarity,
             "review_triggers": list(match.uncertainty_reasons), "occurrence_ambiguous": match.occurrence_ambiguous,
             "contested": match.contested, "review_pending": match.review_pending},
            {"reference_label": ref_by_id[match.reference_id].label, "generated_label": gen_by_id[match.generated_id].label,
             "reference_context": _local_context(reference, match.reference_id),
             "generated_context": _local_context(generated, match.generated_id),
             "source_text_excerpt": _source_excerpt(source_text, (ref_by_id[match.reference_id].label, gen_by_id[match.generated_id].label))},
            "One-to-one semantic similarity met the configured threshold.",
        ))
    for node in ref:
        if node.id not in matched_ref:
            items.append(AutomaticItem(case_id, candidate_id, "Action",
                evaluation_item_id(case_id, candidate_id, "action", "missing", node.id), "FN",
                {"reference_id": node.id, "review_triggers": sorted(ref_review[ref.index(node)])},
                {"reference_label": node.label, "reference_context": _local_context(reference, node.id),
                 "source_text_excerpt": _source_excerpt(source_text, (node.label,)),
                 **ref_review_evidence[ref.index(node)]},
                "No eligible generated action was assigned."))
    for node in gen:
        if node.id not in matched_gen:
            items.append(AutomaticItem(case_id, candidate_id, "Action",
                evaluation_item_id(case_id, candidate_id, "action", "extra", node.id), "FP",
                {"generated_id": node.id, "review_triggers": sorted(gen_review[gen.index(node)])},
                {"generated_label": node.label, "generated_context": _local_context(generated, node.id),
                 "source_text_excerpt": _source_excerpt(source_text, (node.label,)),
                 "cross_notation_reference_evidence": list(reference_review_evidence),
                 **gen_review_evidence[gen.index(node)]},
                "Generated action was not assigned to a reference action."))
    return ActionResult(
        case_id, candidate_id, matches,
        Counts(len(matches), len(gen) - len(matches), len(ref) - len(matches)), tuple(items),
    )
