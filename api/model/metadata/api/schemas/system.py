from typing import List, Optional
from uuid import UUID

from ninja import ModelSchema, Schema

from metadata.models import System


class FlatDiagram(Schema):
    id: UUID
    name: str
    description: Optional[str] = None


class SystemDiagrams(Schema):
    classes: List[FlatDiagram]
    activity: List[FlatDiagram]
    usecase: List[FlatDiagram]
    component: List[FlatDiagram]


class ReadSystem(ModelSchema):
    diagrams_by_type: Optional[SystemDiagrams] = None

    class Meta:
        model = System
        fields = ["id", "name", "description", "project"]

    @staticmethod
    def resolve_diagrams_by_type(obj):
        return {
            "classes": obj.diagrams.filter(type="classes"),
            "activity": obj.diagrams.filter(type="activity"),
            "usecase": obj.diagrams.filter(type="usecase"),
            "component": obj.diagrams.filter(type="component"),
        }


class CreateSystem(ModelSchema):
    project: str

    class Meta:
        model = System
        fields = ["name", "description"]


class UpdateSystem(ModelSchema):
    class Meta:
        model = System
        fields = ["name", "description"]
