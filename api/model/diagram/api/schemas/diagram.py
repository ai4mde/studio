from uuid import UUID

from ninja import ModelSchema

from diagram.models import Diagram
from diagram.api.schemas.node import NodeRead


class DiagramRead(ModelSchema):
    class Meta:
        model = Diagram
        fields = ["id", "name", "description", "type", "system"]


class RelatedDiagramRead(ModelSchema):
    nodes: list[UUID]

    class Meta:
        model = Diagram
        fields = ["id", "name", "type"]


class DiagramReadFull(DiagramRead):
    nodes: list[NodeRead]
    edges: list[UUID]
    related_diagrams: list[RelatedDiagramRead]

    @staticmethod
    def resolve_related_diagrams(obj):
        return Diagram.objects.filter(
            system_id=obj.system_id,
        ).exclude(id=obj.id)


class DiagramCreate(ModelSchema):
    system_id: UUID

    class Meta:
        model = Diagram
        fields = ["name", "description", "type"]
        fields_optional = ["name", "description"]


class DiagramUpdate(ModelSchema):
    class Meta:
        model = Diagram
        fields = ["name", "description"]
        fields_optional = "_all__"
