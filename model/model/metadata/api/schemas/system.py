from typing import List

from metadata.models import System
from ninja import ModelSchema, Schema


class FlatDiagram(Schema):
    id: str
    name: str
    description: str = None


class SystemDiagrams(Schema):
    classes: List[FlatDiagram]
    activity: List[FlatDiagram]
    usecase: List[FlatDiagram]
    component: List[FlatDiagram]


class ReadSystem(ModelSchema):
    diagrams: SystemDiagrams = None

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
