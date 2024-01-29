from enum import Enum
from typing import List

from ninja import ModelSchema, Schema

from diagram.models import Diagram
from .node import NodeSchema
from .edge import EdgeSchema


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
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]

    @staticmethod
    def resolve_nodes(obj):
        return obj.nodes.prefetch_related("cls").all()

    @staticmethod
    def resolve_edges(obj):
        return obj.edges.prefetch_related("rel").all()


__all__ = [
    "ReadDiagram",
    "CreateDiagram",
    "UpdateDiagram",
    "FullDiagram",
]
