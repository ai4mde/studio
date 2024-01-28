from enum import Enum

from ninja import ModelSchema, Schema

from diagram.models import Diagram


class DiagramType(str, Enum):
    classes = "classes"
    usecase = "usecase"
    activity = "activity"
    component = "component"


class ReadDiagram(ModelSchema):
    project: str

    class Meta:
        model = Diagram
        fields = ["id", "name", "description", "type", "system"]

    @staticmethod
    def resolve_project(obj):
        return str(obj.system.project.id)

class CreateDiagram(Schema):
    system: str
    type: DiagramType = DiagramType.classes
    name: str = "Diagram"


class UpdateDiagram(ModelSchema):
    class Meta:
        model = Diagram
        fields = ["id", "name", "description"]

class FullDiagram(ReadDiagram):
    nodes: list = []
    edges: list = []

    @staticmethod
    def resolve_nodes(obj):
        return obj.nodes.all()

    @staticmethod
    def resolve_edges(obj):
        return obj.edges.all()


__all__ = [
    "ReadDiagram",
    "CreateDiagram",
    "UpdateDiagram",
    "FullDiagram",
]
