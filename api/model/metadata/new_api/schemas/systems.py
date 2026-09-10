from uuid import UUID

from ninja import ModelSchema

from metadata.models import System

class SystemRead(ModelSchema):
    diagrams: list[UUID] = [] # TODO import the diagram schema here and use it

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
