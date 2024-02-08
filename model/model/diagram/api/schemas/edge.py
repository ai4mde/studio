from typing import List
from uuid import UUID

from ninja import ModelSchema, Schema
from diagram.models import Edge
from metadata.specification import Relation


class EdgeData(Schema):
    pass


class CreateEdge(Schema):
    source: UUID
    target: UUID
    rel: Relation


class EdgeSchema(ModelSchema):
    rel: Relation
    rel_ptr: UUID
    data: EdgeData

    class Meta:
        model = Edge
        fields = ["id", "data"]

    @staticmethod
    def resolve_rel(obj):
        return obj.rel.data

    @staticmethod
    def resolve_rel_ptr(obj):
        return obj.rel.id


class ListEdges(Schema):
    nodes: List[EdgeSchema] = []


__all__ = [
    "CreateEdge",
    "EdgeSchema",
    "ListEdges",
]
