from uuid import UUID

from ninja import ModelSchema, Schema
from pydantic import Field

from metadata.models import Release


class ReleaseList(ModelSchema):
    class Meta:
        model = Release
        fields = ["id", "name", "description", "created_at", "release_notes"]


class ReleaseCreate(ModelSchema):
    class Meta:
        model = Release
        fields = ["project", "name", "description", "release_notes"]
        fields_optional = ["description", "release_notes"]


class ReleaseMerge(Schema):
    ground_truth_id: UUID
    incoming_id: UUID
    name: str
    description: str = ""
    release_notes: list[str] = []
