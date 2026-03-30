from dataclasses import asdict, is_dataclass
from typing import Any, List
from uuid import uuid4

from ninja import Router
from pydantic import BaseModel

from prose.api.schemas.pipelines import PipelineSchema, PipelineRequirementsSchema, PipelineModelSchema, PipelineResultsSchema
from diagram.api.schemas import FullDiagram

from prose.models import Pipeline
from diagram.models import Diagram

from llm.chains.prose_chain import create_prose_chain_runner
from llm.handler import call_groq, call_openai


pipelines = Router()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    return value


def _build_chain_failure_output(
    *,
    code: str,
    message: str,
    details: dict[str, Any],
    failed_step: str | None,
    step_details: list[dict[str, Any]],
    outputs: dict[str, Any],
) -> dict[str, Any]:
    serialized_step_details = _to_jsonable(step_details)
    return {
        "error": {
            "code": code,
            "message": message,
            "details": _to_jsonable(details),
        },
        "failed_step": failed_step,
        "step_details": serialized_step_details,
        "chain_evidence": {
            "steps_completed": len(serialized_step_details),
            "outputs": _to_jsonable(outputs),
        },
    }


def _relation_multiplicity(relation: Any) -> dict[str, str]:
    if relation.multiplicity is None:
        return {"source": "1", "target": "*"}
    return {
        "source": relation.multiplicity.source,
        "target": relation.multiplicity.target,
    }


def _convert_validation_result_to_output(
    validation_result: Any, step_details: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    classifiers: list[dict[str, Any]] = []
    classifier_ids_by_name: dict[str, str] = {}

    for entity in validation_result.corrected_entities:
        classifier_id = uuid4().hex
        classifier_ids_by_name[entity.name] = classifier_id
        classifiers.append(
            {
                "id": classifier_id,
                "data": {
                    "name": entity.name,
                    "type": entity.type,
                    "attributes": [attribute.model_dump() for attribute in entity.attributes],
                },
            }
        )

    relations: list[dict[str, Any]] = []
    missing_endpoints: list[dict[str, str]] = []
    for relation in validation_result.corrected_relations:
        source_id = classifier_ids_by_name.get(relation.source)
        target_id = classifier_ids_by_name.get(relation.target)
        if source_id is None or target_id is None:
            missing_endpoints.append(
                {
                    "source": relation.source,
                    "target": relation.target,
                }
            )
            continue

        relations.append(
            {
                "id": uuid4().hex,
                "source": source_id,
                "target": target_id,
                "data": {
                    "type": relation.type,
                    "multiplicity": _relation_multiplicity(relation),
                    "derived": False,
                    "label": relation.label or " ",
                },
            }
        )

    return (
        {
            "classifiers": classifiers,
            "relations": relations,
            "chain_evidence": {
                "steps_completed": len(step_details),
                "issues_found": [issue.model_dump() for issue in validation_result.issues_found],
                "step_details": _to_jsonable(step_details),
            },
        },
        missing_endpoints,
    )


@pipelines.get('/', response=List[PipelineSchema])
def list_pipelines(request):
    return Pipeline.objects.all()


@pipelines.post('/', response=PipelineSchema)
def create_pipeline(request):
    return Pipeline.objects.create()


@pipelines.get('/{uuid:pipeline_id}/', response=PipelineSchema)
def get_pipeline(request, pipeline_id: str):
    return Pipeline.objects.get(id=pipeline_id)


@pipelines.post('/{uuid:pipeline_id}/requirements/', response=PipelineSchema)
def add_pipeline_requirements(request, pipeline_id: str, data: PipelineRequirementsSchema):
    pipeline = Pipeline.objects.get(id=pipeline_id)
    pipeline.requirements = data.requirements
    pipeline.step = 3
    pipeline.save()
    return pipeline


@pipelines.post('/{uuid:pipeline_id}/model/', response=PipelineSchema)
def set_pipeline_model(request, pipeline_id: str, data: PipelineModelSchema):
    pipeline = Pipeline.objects.get(id=pipeline_id)
    pipeline.type = data.type
    pipeline.url = data.url
    pipeline.step = 4
    pipeline.save()
    return pipeline


@pipelines.post('/{uuid:pipeline_id}/result/', response=PipelineSchema)
def set_pipeline_output(request, pipeline_id: str, data: PipelineResultsSchema):
    pipeline = Pipeline.objects.get(id=pipeline_id)
    pipeline.output = data.output
    pipeline.step = 5
    pipeline.save()
    return pipeline


@pipelines.post('/{uuid:pipeline_id}/run_model/', response=PipelineSchema)
def run_model(request, pipeline_id: str, model="llama-3.3-70b-versatile"):
    pipeline = Pipeline.objects.get(id=pipeline_id)

    def llm_caller(prompt: str) -> str:
        if model == "gpt-4o":
            return call_openai(model=model, prompt=prompt)
        return call_groq(model=model, prompt=prompt)

    chain_runner = create_prose_chain_runner(llm_caller=llm_caller)
    chain_result = chain_runner.run(initial_context={"requirements": pipeline.requirements})

    if not chain_result.success:
        error = chain_result.error
        pipeline.output = _build_chain_failure_output(
            code=error.code if error else "CHAIN_ERROR",
            message=error.message if error else "Prompt chain execution failed.",
            details=error.details if error else {},
            failed_step=chain_result.failed_step,
            step_details=chain_result.step_details,
            outputs=chain_result.outputs,
        )
    else:
        validation_result = chain_result.outputs.get("validation_result")
        if validation_result is None:
            pipeline.output = _build_chain_failure_output(
                code="MISSING_VALIDATION_RESULT",
                message="Chain completed without validation output.",
                details={},
                failed_step="validate_model",
                step_details=chain_result.step_details,
                outputs=chain_result.outputs,
            )
        else:
            converted_output, missing_endpoints = _convert_validation_result_to_output(
                validation_result, chain_result.step_details
            )
            if missing_endpoints:
                pipeline.output = _build_chain_failure_output(
                    code="RELATION_ENDPOINT_NOT_FOUND",
                    message="Corrected relation endpoint does not match any corrected entity.",
                    details={"missing_endpoints": missing_endpoints},
                    failed_step="output_conversion",
                    step_details=chain_result.step_details,
                    outputs=chain_result.outputs,
                )
            else:
                pipeline.output = converted_output

    pipeline.step = 5
    pipeline.save()
    return pipeline


@pipelines.post('/{uuid:pipeline_id}/add_to_diagram/{uuid:diagram_id}/', response=FullDiagram)
def add_to_diagram(request, pipeline_id: str, diagram_id: str, classifiers: List[dict], relations: List[dict]):
    diagram = Diagram.objects.get(id=diagram_id)

    # Keep an old-new id mapping for the classifiers being cloned
    id_map: dict[str, str] = {}

    for cls in classifiers:
        diagram.add_node_and_classifier(cls, id_map=id_map)
    for rel in relations:
        diagram.add_edge_and_relation(rel, id_map=id_map)

    diagram.auto_layout()
    return diagram


@pipelines.delete('/{uuid:pipeline_id}/')
def delete_pipeline(request, pipeline_id: str):
    pipeline = Pipeline.objects.get(id=pipeline_id)
    pipeline.delete()
    return {"status": "ok"}

__all__ = ["pipelines"]
