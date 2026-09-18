from uuid import UUID

from ninja import ModelSchema

from diagram.models import Diagram


class DiagramRead(ModelSchema):
    project: UUID
    system_id: UUID
    system_name: str

    
    class Meta:
        model = Diagram
        fields = ["id", "name", "description", "type"]

    @staticmethod
    def resolve_project(obj) -> UUID:
        return obj.system.project.id

    @staticmethod
    def resolve_system_name(obj) -> str:
        return obj.system.name


class DiagramCreate(ModelSchema):
    system_id: UUID

    class Meta:
        model = Diagram
        fields = ["name", "description", "type"]
        fields_optional = ["description"]


class DiagramUpdate(ModelSchema):
    class Meta:
        model = Diagram
        fields = ["name", "description"]
        fields_optional = "_all__"
