from typing import List, Optional
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
    # TODO: Don't do this resolver magic, but return a NodeSchema here and use native depth = 1
    source_ptr: Optional[UUID] = None
    target_ptr: Optional[UUID] = None

    class Meta:
        model = Edge
        fields = ["id", "data"]

    @staticmethod
    def resolve_rel(obj):
        return obj.rel.data

    @staticmethod
    def resolve_rel_ptr(obj):
        return obj.rel.id

    @staticmethod
    def resolve_source_ptr(obj):
        return obj.source.id

    @staticmethod
    def resolve_target_ptr(obj):
        return obj.target.id


class ListEdges(Schema):
    nodes: List[EdgeSchema] = []


__all__ = [
    "CreateEdge",
    "EdgeSchema",
    "ListEdges",
]
