from typing import List
from uuid import UUID

from ninja import ModelSchema, Schema

from metadata.models import System


class FlatDiagram(Schema):
    id: UUID
    name: str
    description: str = None


class SystemDiagrams(Schema):
    classes: List[FlatDiagram]
    activity: List[FlatDiagram]
    usecase: List[FlatDiagram]
    component: List[FlatDiagram]


class ReadSystem(ModelSchema):
    diagrams_by_type: SystemDiagrams = None

    class Meta:
        model = System
        fields = ["id", "name", "description"]


class CreateSystem(ModelSchema):
    project: str

    class Meta:
        model = System
        fields = ["name", "description"]


class UpdateSystem(ModelSchema):
    class Meta:
        model = System
        fields = ["name", "description"]
