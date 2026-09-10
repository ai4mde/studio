from uuid import UUID

from ninja import ModelSchema

from metadata.models import System

class SystemRead(ModelSchema):
    diagrams: list[UUID] = []

    class Meta:
        model = System
        fields = ["id", "name", "description", "project"]
    
    @staticmethod
    def resolve_diagrams(obj):
        return list(obj.diagrams)