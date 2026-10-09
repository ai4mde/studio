from uuid import UUID

from ninja import ModelSchema

from diagram.models import Diagram
from diagram.api.schemas.node import NodeRead
from diagram.api.schemas.edge import EdgeRead


class DiagramRead(ModelSchema):
    class Meta:
        model = Diagram
        fields = ["id", "name", "description", "type", "system"]


class RelatedDiagramRead(ModelSchema):
    nodes: list[EdgeRead]

    class Meta:
        model = Diagram
        fields = ["id", "name", "type"]


class DiagramReadFull(DiagramRead):
    nodes: list[NodeRead]
    edges: list[EdgeRead]


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
