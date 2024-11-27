from ninja import ModelSchema
from metadata.models import Release


class ReadRelease(ModelSchema):
    class Meta:
        model = Release
        fields = ["id", "name", "created_at", "project", "system", "diagrams", "metadata", "interfaces", "release_notes" ]


class UpdateRelease(ModelSchema):
    class Meta:
        model = Release
        fields = ["id", "name", "created_at", "project", "system", "diagrams", "metadata", "interfaces", "release_notes" ]


__all__ = ["ReadRelease", "UpdateRelease"]
