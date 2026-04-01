from typing import List, Optional

from ninja import ModelSchema, Schema
from metadata.models import Project, System
from metadata.api.schemas.system import ExportSystem, ImportSystem


class ReadProject(ModelSchema):
    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class CreateProject(ModelSchema):
    class Meta:
        model = Project
        fields = ["name", "description"]


class UpdateProject(ModelSchema):
    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class DeleteProject(ModelSchema):
    class Meta:
        model = Project
        fields = ["id"]


class ExportProject(ModelSchema):
    systems: List[ExportSystem] = []
    
    class Meta:
        model = Project
        fields = "__all__"

    @staticmethod
    def resolve_systems(obj):
        return System.objects.filter(project=obj)


class ImportProject(Schema):
    id: str
    name: str
    description: Optional[str] = None
    systems: List[ImportSystem]


__all__ = [
    "ReadProject",
    "CreateProject",
    "UpdateProject",
    "DeleteProject",
    "ExportProject",
    "ImportProject",
]
