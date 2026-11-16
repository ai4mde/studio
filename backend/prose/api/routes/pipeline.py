from typing import List

from django.shortcuts import get_object_or_404
from ninja import Router

from diagram.api.schemas.diagram import DiagramRead
from diagram.models import Diagram
from diagram.services.diagrams.auto_layout import auto_layout_diagram

from prose.api.schemas.pipeline import (
    PipelineModelSchema,
    PipelineRequirementsSchema,
    PipelineResultsSchema,
    PipelineSchema,
)
from prose.models import Pipeline
from prose.services.model_creation import (
    add_to_diagram as add_to_diagram_service,
)
from prose.services.pipeline import run_pipeline

router = Router()


@router.get('/', response=List[PipelineSchema])
def list_pipelines(request):
    return Pipeline.objects.all()


@router.post('/', response=PipelineSchema)
def create_pipeline(request):
    return Pipeline.objects.create()


@router.get('/{uuid:pipeline_id}/', response=PipelineSchema)
def get_pipeline(request, pipeline_id: str):
    return Pipeline.objects.get(id=pipeline_id)


@router.post('/{uuid:pipeline_id}/requirements/', response=PipelineSchema)
def add_pipeline_requirements(request, pipeline_id: str, data: PipelineRequirementsSchema):
    pipeline = Pipeline.objects.get(id=pipeline_id)
    pipeline.requirements = data.requirements
    pipeline.step = 3
    pipeline.save()
    return pipeline


@router.post('/{uuid:pipeline_id}/model/', response=PipelineSchema)
def set_pipeline_model(request, pipeline_id: str, data: PipelineModelSchema):
    pipeline = Pipeline.objects.get(id=pipeline_id)
    pipeline.type = data.type
    pipeline.url = data.url
    pipeline.step = 4
    pipeline.save()
    return pipeline


@router.post('/{uuid:pipeline_id}/result/', response=PipelineSchema)
def set_pipeline_output(request, pipeline_id: str, data: PipelineResultsSchema):
    pipeline = Pipeline.objects.get(id=pipeline_id)
    pipeline.output = data.output
    pipeline.step = 5
    pipeline.save()
    return pipeline


@router.post(
    "/{uuid:pipeline_id}/run_model/",
    response={200: PipelineSchema, 503: dict},
)
def run_model(
    request,
    pipeline_id: str,
    model: str = "llama-3.3-70b-versatile",
):
    pipeline = Pipeline.objects.get(id=pipeline_id)

    result = run_pipeline(pipeline, model)

    if result is None:
        return 503, {"message": "LLM returned no response."}

    return result



@router.post(
    "/{uuid:pipeline_id}/add_to_diagram/{uuid:diagram_id}/",
    response=DiagramRead,
)
def add_to_diagram(
    request,
    pipeline_id: str,
    diagram_id: str,
    classifiers: List[dict],
    relations: List[dict],
):
    get_object_or_404(Pipeline, pk=pipeline_id)
    diagram = get_object_or_404(Diagram, pk=diagram_id)

    add_to_diagram_service(
        diagram=diagram,
        classifiers=classifiers,
        relations=relations,
    )
    
    auto_layout_diagram(diagram)
    
    return diagram


@router.delete('/{uuid:pipeline_id}/')
def delete_pipeline(request, pipeline_id: str):
    pipeline = Pipeline.objects.get(id=pipeline_id)
    pipeline.delete()
    return {"status": "ok"}
