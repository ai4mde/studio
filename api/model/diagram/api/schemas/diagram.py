from uuid import UUID
from enum import Enum
from typing import List, Optional

from ninja import ModelSchema, Schema

from diagram.models import Diagram
from .node import CreateNode, NodeSchema
from .edge import CreateEdge, EdgeSchema


class DiagramType(str, Enum):
    classes = "classes"
    usecase = "usecase"
    activity = "activity"
    component = "component"


class ReadDiagram(ModelSchema):
    project: str
    system_id: UUID
    system_name: str

    class Meta:
        model = Diagram
        fields = ["id", "name", "description", "type", "system"]

    @staticmethod
    def resolve_project(obj):
        return str(obj.system.project.id)
    
    @staticmethod
    def resolve_system_id(obj):
        return str(obj.system_id)
    
    @staticmethod
    def resolve_system_name(obj):
        return str(obj.system.name)


class CreateDiagram(Schema):
    system: str
    type: DiagramType = DiagramType.classes
    name: str = "Diagram"


class UpdateDiagram(Schema):
    name: Optional[str] = None
    description: Optional[str] = None


class FullDiagram(ReadDiagram):
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]

    @staticmethod
    def resolve_nodes(obj):
        return obj.nodes.prefetch_related("cls").all()

    @staticmethod
    def resolve_edges(obj):
        return obj.edges.prefetch_related("rel").all()


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
