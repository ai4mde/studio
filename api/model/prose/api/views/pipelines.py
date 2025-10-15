from typing import List
from ninja import Router
from prose.api.schemas.pipelines import PipelineSchema, PipelineRequirementsSchema, PipelineModelSchema, PipelineResultsSchema
from diagram.api.schemas import FullDiagram

from prose.models import Pipeline
from diagram.models import Diagram

from llm.handler import llm_handler
from .utils import parse_llm_response


pipelines = Router()


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
    response = llm_handler("PROSE_GENERATE_METADATA", model, input_data={"requirements": pipeline.requirements})
    if not response:
        return 503
    print(response)
    pipeline.output = parse_llm_response(response)
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
