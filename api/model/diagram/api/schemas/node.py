from typing import List, Optional
from uuid import UUID

from ninja import ModelSchema, Schema
from diagram.models import Node
from metadata.specification import Classifier


class NodePosition(Schema):
    x: int = 0
    y: int = 0


class NodeData(Schema):
    position: NodePosition


class CreateNode(Schema):
    cls: Classifier


class NodeSchema(ModelSchema):
    cls: Classifier
    cls_ptr: UUID
    data: NodeData

    class Meta:
        model = Node
        fields = ["id", "data"]

    @staticmethod
    def resolve_cls(obj):
        return obj.cls.data

    @staticmethod
    def resolve_cls_ptr(obj):
        return obj.cls.id


class PatchNode(Schema):
    cls: Optional[dict] = None
    data: Optional[NodeData] = None


class ListNodes(Schema):
    nodes: List[NodeSchema] = []


__all__ = [
    "CreateNode",
    "PatchNode",
    "NodeSchema",
    "ListNodes",
]
