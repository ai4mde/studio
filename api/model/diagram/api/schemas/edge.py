from uuid import UUID

from ninja import ModelSchema

from metadata.api.schemas.relation import (
    RelationCreate,
    RelationRead,
    RelationUpdate,
)
from diagram.models import Edge


class EdgeRead(ModelSchema):
    relation: RelationRead  # type: ignore[valid-type]
    source: UUID
    target: UUID

    class Meta:
        model = Edge
        fields = [
            "id",
            "diagram",
            "relation",
            "width",
            "color",
            "font",
            "rounded",
        ]

    @staticmethod
    def resolve_source(obj):
        return obj.source.id

    @staticmethod
    def resolve_target(obj):
        return obj.target.id

class EdgeCreate(ModelSchema):
    relation: RelationCreate    # type: ignore[valid-type]
    source_id: UUID
    target_id: UUID

    class Meta:
        model = Edge
        fields = [
            "diagram",
            "width",
            "color",
            "font",
            "rounded",
        ]
        fields_optional = [
            "width",
            "color",
            "font",
            "rounded",
        ]    


class EdgeUpdate(ModelSchema):
    relation: RelationUpdate | None = None

    class Meta:
        model = Edge
        fields = [
            "width",
            "color",
            "font",
            "rounded",
        ]
        fields_optional = "__all__"