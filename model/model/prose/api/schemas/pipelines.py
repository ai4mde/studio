from ninja import ModelSchema, Schema
from prose.models import Pipeline

class PipelineSchema(ModelSchema):
    class Meta:
        model = Pipeline
        fields = '__all__'

class PipelineRequirementsSchema(Schema):
    requirements: str

class PipelineModelSchema(Schema):
    type: str
    url: str

class PipelineResultsSchema(Schema):
    output: dict

__all__ = [
    "PipelineSchema",
    "PipelineRequirementsSchema",
    "PipelineModelSchema",
    "PipelineResultsSchema",
]
