from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from .core import AutomaticItem, Counts, EvalGraph, evaluation_item_id


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


def evaluate_actions(
    case_id: str,
    candidate_id: str,
    reference: EvalGraph,
    generated: EvalGraph,
    similarity: SimilarityProvider,
    threshold: float,
) -> ActionResult:
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Action threshold must be between 0 and 1")
    ref = sorted((node for node in reference.nodes if node.type == "action"), key=lambda n: n.id)
    gen = sorted((node for node in generated.nodes if node.type == "action"), key=lambda n: n.id)
    scores = similarity.matrix([node.label or "" for node in ref], [node.label or "" for node in gen])
    if len(scores) != len(ref) or any(len(row) != len(gen) for row in scores):
        raise ValueError("Similarity provider returned an invalid matrix")
    eligible = [[score if score >= threshold else 0.0 for score in row] for row in scores]
    matches = tuple(
        ActionMatch(case_id, candidate_id, ref[i].id, gen[j].id, scores[i][j])
        for i, j in _maximum_assignment(eligible)
        if scores[i][j] >= threshold
    )
    matched_ref = {match.reference_id for match in matches}
    matched_gen = {match.generated_id for match in matches}
    items: list[AutomaticItem] = []
    ref_by_id, gen_by_id = reference.by_id, generated.by_id
    for match in matches:
        items.append(AutomaticItem(
            case_id, candidate_id, "Action",
            evaluation_item_id(case_id, candidate_id, "action", "match", match.reference_id, match.generated_id), "TP",
            {"reference_id": match.reference_id, "generated_id": match.generated_id, "similarity": match.similarity},
            {"reference_label": ref_by_id[match.reference_id].label, "generated_label": gen_by_id[match.generated_id].label},
            "One-to-one semantic similarity met the configured threshold.",
        ))
    for node in ref:
        if node.id not in matched_ref:
            items.append(AutomaticItem(case_id, candidate_id, "Action",
                evaluation_item_id(case_id, candidate_id, "action", "missing", node.id), "FN",
                {"reference_id": node.id}, {"reference_label": node.label}, "No eligible generated action was assigned."))
    for node in gen:
        if node.id not in matched_gen:
            items.append(AutomaticItem(case_id, candidate_id, "Action",
                evaluation_item_id(case_id, candidate_id, "action", "extra", node.id), "FP",
                {"generated_id": node.id}, {"generated_label": node.label}, "Generated action was not assigned to a reference action."))
    return ActionResult(
        case_id, candidate_id, matches,
        Counts(len(matches), len(gen) - len(matches), len(ref) - len(matches)), tuple(items),
    )
