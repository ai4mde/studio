from uuid import UUID

from ninja import ModelSchema

from diagram.api.schemas.diagram import DiagramRead
from metadata.models import System

class SystemRead(ModelSchema):
    diagrams: list[DiagramRead]

    class Meta:
        model = System
        fields = ["id", "name", "description", "project"]
    
    @staticmethod
    def resolve_diagrams(obj):
        return obj.diagrams.all()


class SystemCreate(ModelSchema):
    project_id: UUID

    class Meta:
        model = System
        fields = ["name", "description"]
        fields_optional = ["description"]


class SystemUpdate(ModelSchema):
    class Meta:
        model = System
        fields = ["name", "description"]
        fields_optional = "_all__"
