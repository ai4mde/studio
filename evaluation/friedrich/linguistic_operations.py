from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .eval_graph import normalize_label


SPACY_MODEL = "en_core_web_sm"
SPACY_MODEL_VERSION = "3.8.0"
WORDNET_ARCHIVE_SHA256 = "cbda5ea6eef7f36a97a43d4a75f85e07fccbb4f23657d27b4ccbc93e2646ab59"


@dataclass(frozen=True, slots=True)
class OperationRepresentation:
    original_normalized_label: str
    original_root: str
    root_pos: str
    root_lemma: str
    derivation_source: str
    canonical_operation: str
    operation_resolved: bool
    derivation_candidates: tuple[str, ...]
    object_phrase: str | None
    canonical_label: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LinguisticOperationExtractor:
    def __init__(self, wordnet_data_dir: str | Path) -> None:
        import nltk
        import spacy
        from nltk.corpus import wordnet

        data_dir = str(Path(wordnet_data_dir))
        if data_dir not in nltk.data.path:
            nltk.data.path.insert(0, data_dir)
        wordnet.ensure_loaded()
        self._wordnet = wordnet
        self._nlp = spacy.load(SPACY_MODEL)

    def _has_verb_sense(self, lemma: str) -> bool:
        return bool(self._wordnet.synsets(lemma, pos=self._wordnet.VERB))

    def _derivational_verbs(self, noun_lemma: str) -> tuple[str, ...]:
        verbs = {
            related.name().replace("_", " ")
            for lemma in self._wordnet.lemmas(noun_lemma, pos=self._wordnet.NOUN)
            for related in lemma.derivationally_related_forms()
            if related.synset().pos() == self._wordnet.VERB
        }
        return tuple(sorted(verbs))

    @staticmethod
    def _is_finite_verb(token: Any) -> bool:
        return token.pos_ == "VERB" and "VerbForm=Fin" in token.morph

    def _select_operation_token(
        self, doc: Any
    ) -> tuple[Any, str, str | None, str | None]:
        root = next(token for token in doc if token.head == token)
        if self._is_finite_verb(root):
            return root, "spacy_dependency_root", None, None

        # Actor/acronym-led labels may be parsed as an infinitive headed by the
        # actor (for example, a short identifier that is also an English verb).
        # Reparse the remaining phrase with an explicit generic subject.
        if len(doc) > 1 and (
            doc[0].pos_ == "PROPN"
            or (root.i == 0 and root.pos_ == "VERB" and "VerbForm=Inf" in root.morph)
        ):
            tail_text = " ".join(token.text for token in doc[1:])
            tail = self._nlp(f"They {tail_text}.")
            tail_root = next(token for token in tail if token.head == token)
            if (
                tail_root.pos_ == "VERB"
                and tail_root.i > 0
                and tail_root.lemma_.casefold() != tail_root.text.casefold()
            ):
                original_index = tail_root.i
                if original_index < len(doc):
                    return (
                        doc[original_index],
                        "spacy_actor_predicate_fallback",
                        tail_root.lemma_.casefold(),
                        tail_root.pos_,
                    )

        if root.pos_ == "VERB" and root.i == 0:
            return root, "spacy_dependency_root", None, None

        # Short imperative labels are parsed more reliably with an explicit subject.
        surrogate = self._nlp(f"They {doc.text}.")
        surrogate_root = next(token for token in surrogate if token.head == token)
        if (
            surrogate_root.pos_ == "VERB"
            and surrogate_root.i > 0
            and self._has_verb_sense(surrogate_root.lemma_.casefold())
        ):
            original_index = surrogate_root.i - 1
            if 0 <= original_index < len(doc):
                return (
                    doc[original_index],
                    "spacy_imperative_surrogate",
                    surrogate_root.lemma_.casefold(),
                    surrogate_root.pos_,
                )

        # Prefer a defensible derivation of the parsed nominal root over a verb
        # mentioned in its complement (for example, "registration of request").
        if root.pos_ in {"NOUN", "PROPN"} and self._derivational_verbs(
            root.lemma_.casefold()
        ):
            return root, "spacy_nominal_root", None, None

        # Acronym-led fragments can confuse the parser; choose the first token that
        # spaCy lemmatizes to a WordNet verb instead of guessing from suffixes.
        for token in doc:
            lemma = token.lemma_.casefold()
            if token.is_alpha and self._has_verb_sense(lemma):
                return token, "wordnet_verb_fallback", lemma, "VERB"
        return root, "spacy_nominal_root", None, None

    @staticmethod
    def _subtree_text(token: Any) -> str | None:
        text = " ".join(item.text for item in token.subtree if not item.is_punct)
        return normalize_label(text)

    def _object_phrase(self, doc: Any, operation_token: Any) -> str | None:
        object_deps = {"dobj", "obj", "attr", "oprd"}
        objects = [
            self._subtree_text(child)
            for child in operation_token.children
            if child.dep_ in object_deps
        ]
        objects = [item for item in objects if item]
        for child in operation_token.children:
            if child.dep_ == "prep" and child.lower_ in {"of", "about", "for", "to", "at"}:
                objects.extend(
                    item
                    for grandchild in child.children
                    if grandchild.dep_ == "pobj"
                    if (item := self._subtree_text(grandchild))
                )
        if objects:
            return normalize_label(" ".join(objects))

        # Parser fallback for imperative fragments: preserve text following the
        # operation token, excluding leading function words.
        trailing = [
            token.text
            for token in doc[operation_token.i + 1 :]
            if not token.is_punct and token.pos_ not in {"ADP", "DET", "AUX", "PART"}
        ]
        return normalize_label(" ".join(trailing)) if trailing else None

    def extract(self, label: str) -> OperationRepresentation:
        normalized = normalize_label(label)
        if normalized is None:
            raise ValueError("Action label must not normalize to an empty value")
        doc = self._nlp(normalized)
        operation_token, selection_source, lemma_override, pos_override = (
            self._select_operation_token(doc)
        )
        lemma = lemma_override or operation_token.lemma_.casefold()
        operation_pos = pos_override or operation_token.pos_
        candidates: tuple[str, ...] = ()

        if operation_pos == "VERB":
            canonical = lemma
            resolved = True
            source = f"{selection_source}:verb_lemma"
        else:
            candidates = self._derivational_verbs(lemma)
            if len(candidates) == 1:
                canonical = candidates[0]
                resolved = True
                source = "wordnet_unique_derivational_verb"
            else:
                canonical = lemma
                resolved = False
                source = (
                    "wordnet_ambiguous_derivation"
                    if candidates
                    else "wordnet_no_derivational_verb"
                )

        object_phrase = self._object_phrase(doc, operation_token)
        canonical_label = normalize_label(
            " ".join(part for part in (canonical, object_phrase) if part)
        )
        if canonical_label is None:
            canonical_label = normalized
        return OperationRepresentation(
            original_normalized_label=normalized,
            original_root=operation_token.text.casefold(),
            root_pos=operation_pos,
            root_lemma=lemma,
            derivation_source=source,
            canonical_operation=canonical,
            operation_resolved=resolved,
            derivation_candidates=candidates,
            object_phrase=object_phrase,
            canonical_label=canonical_label,
        )
