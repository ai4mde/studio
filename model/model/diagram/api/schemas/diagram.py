from diagram.models import Diagram
from ninja import ModelSchema, Schema


class ReadDiagram(ModelSchema):
    class Meta:
        model = Diagram
        fields = ["id", "name", "description"]


class CreateDiagram(Schema):
    system: str
    type: str = "classes"


class UpdateDiagram(ModelSchema):
    class Meta:
        model = Diagram
        fields = ["id", "name", "description"]


__all__ = [
    "ReadDiagram",
    "CreateDiagram",
    "UpdateDiagram",
]
