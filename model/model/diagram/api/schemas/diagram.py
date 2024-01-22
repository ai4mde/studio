from enum import Enum

from ninja import ModelSchema, Schema

from diagram.models import Diagram


class DiagramType(str, Enum):
    classes = "classes"
    usecase = "usecase"
    activity = "activity"
    component = "component"


class ReadDiagram(ModelSchema):
    class Meta:
        model = Diagram
        fields = ["id", "name", "description"]


class CreateDiagram(Schema):
    system: str
    type: DiagramType = "classes"
    name: str = "Diagram"


class UpdateDiagram(ModelSchema):
    class Meta:
        model = Diagram
        fields = ["id", "name", "description"]


__all__ = [
    "ReadDiagram",
    "CreateDiagram",
    "UpdateDiagram",
]
