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
    id: Optional[UUID] = None
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
        cls_data = obj.cls.data

        # Add the actor node names to the swimlanes
        if obj.cls.data.get('type') == 'swimlanegroup':
            cls_data['swimlanes'] = [
                {
                    **swimlane,
                    'actorNodeName': (
                        Node.objects.get(id=swimlane['actorNode']).cls.data['name']
                        if Node.objects.filter(id=swimlane['actorNode']).exists()
                        else 'Unknown actor'
                    )
                } for swimlane in obj.cls.data.get('swimlanes', [])
            ]

        return cls_data

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
