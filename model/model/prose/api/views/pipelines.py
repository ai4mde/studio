from typing import List
from ninja import Router
from prose.api.schemas.pipelines import PipelineSchema, PipelineRequirementsSchema, PipelineModelSchema, PipelineResultsSchema

from prose.models import Pipeline

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

@pipelines.delete('/{uuid:pipeline_id}/')
def delete_pipeline(request, pipeline_id: str):
    pipeline = Pipeline.objects.get(id=pipeline_id)
    pipeline.delete()
    return {"status": "ok"}

__all__ = ["pipelines"]
