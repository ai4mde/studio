from uuid import UUID

from ninja import ModelSchema

from diagram.new_api.schemas.diagram import DiagramRead
from metadata.models import System

class SystemRead(ModelSchema):
    diagrams: list[DiagramRead]

    class Meta:
        model = System
        fields = ["id", "name", "description", "project"]
    
    @staticmethod
    def resolve_diagrams(obj):
        return list(obj.diagrams)


class SystemCreate(ModelSchema):
    project_id: UUID

    class Meta:
        model = System
        fields = ["name", "description"]


class SystemUpdate(ModelSchema):
    class Meta:
        model = System
        fields = ["name", "description"]
        fields_optional = "_all__"
