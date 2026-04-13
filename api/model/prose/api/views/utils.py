from __future__ import annotations

"""Baseline single-call prose parser preserved for thesis comparison evidence.

The active runtime path is the M05 3-step prompt chain with structured parsing (M04).
Do not delete this module; it is retained for baseline-vs-mechanism evaluation.
"""

from uuid import uuid4

from llm.parsers.base import ParseResult
from llm.parsers.json_parser import JsonOutputParser
from llm.parsers.schemas.prose_output import ProseGenerationOutput, ProseRelation


def _build_classifier_payload(parsed: ProseGenerationOutput) -> tuple[list[dict], dict[str, str]]:
    classifiers: list[dict] = []
    classifier_ids_by_name: dict[str, str] = {}

    for cls in parsed.classifiers:
        classifier_id = uuid4().hex
        classifier_ids_by_name[cls.name] = classifier_id

        classifiers.append(
            {
                "id": classifier_id,
                "data": {
                    "name": cls.name,
                    "type": "class",
                    "attributes": [attr.model_dump() for attr in cls.attributes],
                },
            }
        )

    return classifiers, classifier_ids_by_name


def _relation_multiplicity(relation: ProseRelation) -> dict[str, str]:
    if relation.multiplicity is None:
        return {"source": "1", "target": "*"}
    return {
        "source": relation.multiplicity.source,
        "target": relation.multiplicity.target,
    }


def _build_relation_payload(
    relations: list[ProseRelation], classifier_ids_by_name: dict[str, str]
) -> ParseResult[list[dict]]:
    relation_payloads: list[dict] = []

    for relation in relations:
        source_id = classifier_ids_by_name.get(relation.source)
        target_id = classifier_ids_by_name.get(relation.target)

        if source_id is None or target_id is None:
            return ParseResult.fail(
                code="RELATION_ENDPOINT_NOT_FOUND",
                message="Relation endpoint name does not match any classifier.",
                raw_response="",
                details={
                    "source": relation.source,
                    "target": relation.target,
                },
            )

        relation_payloads.append(
            {
                "id": uuid4().hex,
                "source": source_id,
                "target": target_id,
                "data": {
                    "type": relation.type,
                    "multiplicity": _relation_multiplicity(relation),
                    "derived": False,
                    "label": " ",
                },
            }
        )

    return ParseResult.ok(data=relation_payloads, raw_response="")


def parse_llm_response(response: str) -> ParseResult[dict]:
    parser = JsonOutputParser(schema=ProseGenerationOutput)
    parsed_result = parser.parse(response)

    if not parsed_result.success or parsed_result.data is None:
        return parsed_result

    classifiers, classifier_ids_by_name = _build_classifier_payload(parsed_result.data)
    relation_result = _build_relation_payload(parsed_result.data.relations, classifier_ids_by_name)

    if not relation_result.success or relation_result.data is None:
        return ParseResult.fail(
            code=relation_result.error.code,
            message=relation_result.error.message,
            raw_response=response,
            details=relation_result.error.details,
        )

    output = {
        "classifiers": classifiers,
        "relations": relation_result.data,
    }
    return ParseResult.ok(data=output, raw_response=response)
