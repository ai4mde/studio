from uuid import UUID
from enum import Enum
from typing import List, Optional

from ninja import ModelSchema, Schema

from diagram.models import Diagram, Node
from .node import CreateNode, NodeSchema, ExportNode, ImportNode
from .edge import CreateEdge, EdgeSchema, ExportEdge, ImportEdge


class DiagramType(str, Enum):
    classes = "classes"
    usecase = "usecase"
    activity = "activity"
    component = "component"


class ReadDiagram(ModelSchema):
    project: str
    system_id: UUID
    system_name: str
    system: UUID # TODO Remove later

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

    # TODO Remove later
    @staticmethod
    def resolve_system(obj):
        return str(obj.system.id)


class CreateDiagram(Schema):
    system: str
    type: DiagramType = DiagramType.classes
    name: str = "Diagram"


class UpdateDiagram(Schema):
    name: Optional[str] = None
    description: Optional[str] = None


class RelatedClassAttribute(Schema):
    name: str
    type: str

class RelatedNode(ModelSchema):
    name: str
    type: str
    actorNode: Optional[str]
    classAttributes: Optional[List[RelatedClassAttribute]] = None


    class Meta:
        model = Node
        fields = ["id", "cls"]
    
    @staticmethod
    def resolve_name(obj):
        return obj.cls.data.get('name') or ""

    @staticmethod
    def resolve_type(obj):
        return obj.cls.data["type"]

    @staticmethod
    def resolve_actorNode(obj):
        return obj.cls.data.get('actorNode')
    
    @staticmethod
    def resolve_classAttributes(obj):
        if obj.cls.data.get('type') == 'class':
            return [
                RelatedClassAttribute(name=attribute['name'], type=attribute['type'])
                for attribute in obj.cls.data.get('attributes', [])
            ]
        return None


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
    related_diagrams: List[RelatedDiagram] = []

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


class ExportDiagram(ModelSchema):
    nodes: List[ExportNode] = []
    edges: List[ExportEdge] = []

    class Meta:
        model = Diagram
        fields = "__all__"

    @staticmethod
    def resolve_nodes(obj):
        return obj.nodes.all()

    @staticmethod
    def resolve_edges(obj):
        return obj.edges.all()


class ImportDiagram(Schema):
    id: str
    type: DiagramType
    name: str
    description: Optional[str] = None
    system: str
    nodes: list[ImportNode]
    edges: list[ImportEdge]


__all__ = [
    "ReadDiagram",
    "ImportDiagram",
    "CreateDiagram",
    "UpdateDiagram",
    "FullDiagram",
    "ExportDiagram",
    "ImportDiagram",
]
