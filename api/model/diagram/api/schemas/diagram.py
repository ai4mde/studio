from enum import Enum
from typing import List, Optional

from ninja import ModelSchema, Schema

from diagram.models import Diagram, Node
from .node import CreateNode, NodeSchema
from .edge import CreateEdge, EdgeSchema


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


class UpdateDiagram(Schema):
    name: Optional[str] = None
    description: Optional[str] = None


class RelatedNode(ModelSchema):
    name: str
    type: str

    class Meta:
        model = Node
        fields = ["id"]
    
    @staticmethod
    def resolve_name(obj):
        return obj.cls.data["name"]

    @staticmethod
    def resolve_type(obj):
        return obj.cls.data["type"]

class RelatedDiagram(ModelSchema):
    nodes: List[RelatedNode]

    class Meta:
        model = Diagram
        fields = ["id", "name", "type"]
    
    @staticmethod
    def resolve_nodes(obj):
        return obj.nodes.all()


class FullDiagram(ReadDiagram):
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]
    related_diagrams: List[RelatedDiagram]

    @staticmethod
    def resolve_nodes(obj):
        return obj.nodes.prefetch_related("cls").all()

    @staticmethod
    def resolve_edges(obj):
        return obj.edges.prefetch_related("rel").all()

    @staticmethod
    def resolve_related_diagrams(obj):
        return Diagram.objects.filter(system=obj.system.id).exclude(id=obj.id)


class ImportDiagram(CreateDiagram):
    nodes: List[CreateNode]
    edges: List[CreateEdge]


__all__ = [
    "ReadDiagram",
    "ImportDiagram",
    "CreateDiagram",
    "UpdateDiagram",
    "FullDiagram",
]
