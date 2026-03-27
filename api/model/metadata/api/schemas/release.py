from typing import List, Optional

from ninja import ModelSchema, Schema
from metadata.models import Release
from metadata.api.schemas import ImportProject


class ReadRelease(ModelSchema):
    class Meta:
        model = Release
        fields = ["id", "name", "created_at", "release_notes"]


class ImportRelease(Schema):
    project: str
    name: str
    project_data: ImportProject
    release_notes: Optional[List[str]] = None


class CreateRelease(Schema):
    project: str
    name: str
    release_notes: List[str] = []


class ExportRelease(ModelSchema):
    class Meta:
        model = Release
        fields = ["project", "project_data", "release_notes"]


__all__ = ["ReadRelease", "ImportRelease", "CreateRelease", "ExportRelease"]
