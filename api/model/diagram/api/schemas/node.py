from typing import List, Optional
from uuid import UUID

from ninja import ModelSchema, Schema
from diagram.models import Node, Classifier as ClassifierModel
from metadata.specification import Classifier


class NodePosition(Schema):
    x: int = 0
    y: int = 0


class NodeData(Schema):
    position: NodePosition
    background_color_hex: Optional[str] = None


class CreateNode(Schema):
    id: Optional[UUID] = None
    cls: Classifier
    background_color_hex: Optional[str] = None


class NodeSchema(ModelSchema):
    cls: Classifier
    cls_ptr: UUID
    data: NodeData
    system_name: str
    system_id: UUID

    class Meta:
        model = Node
        fields = ["id", "data"]

    @staticmethod
    def resolve_cls(obj):
        return obj.cls.data

    @staticmethod
    def resolve_cls_ptr(obj):
        return obj.cls.id
    
    @staticmethod
    def resolve_system_name(obj):
        return obj.cls.system.name
    
    @staticmethod
    def resolve_system_id(obj):
        return getattr(obj.cls, "system_id", None)


class PatchNode(Schema):
    cls: Optional[dict] = None
    data: Optional[NodeData] = None


class ListNodes(Schema):
    nodes: List[NodeSchema] = []


class DiagramUsageItem(Schema):
    diagram_id: str
    diagram_name: str
    system_id: str
    system_name: str


class ClassifierUsageResponse(Schema):
    classifier_id: str
    classifier_name: str
    usages: List[DiagramUsageItem]


class RelationUsageResponse(Schema):
    relation_id: str
    usages: List[DiagramUsageItem]


class ExportClassifier(ModelSchema):
    class Meta:
        model = ClassifierModel
        fields = "__all__"


class ImportClassifier(Schema):
    id: str
    system: str
    data: dict


class ExportNode(ModelSchema):
    cls_data: ExportClassifier

    class Meta:
        model = Node
        fields = "__all__"

    @staticmethod
    def resolve_cls_data(obj):
        return obj.cls


class ImportNode(Schema):
    id: str
    cls_data: ImportClassifier
    diagram: str
    cls: str
    data: NodeData


__all__ = [
    "CreateNode",
    "PatchNode",
    "NodeSchema",
    "ListNodes",
    "DiagramUsageItem",
    "ClassifierUsageResponse",
    "RelationUsageResponse",
    "ExportNode",
    "ImportNode",
]
