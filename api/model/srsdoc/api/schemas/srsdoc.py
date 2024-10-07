from ninja import ModelSchema
from srsdoc.models import SRSDocument


class ReadSRSDocument(ModelSchema):
    class Meta:
        model = SRSDocument
        fields = ["id", "title", "version", "description", "path"]


class CreateSRSDocument(ModelSchema):
    class Meta:
        model = SRSDocument
        fields = ["title", "version", "description", "path"]


class UpdateSRSDocument(ModelSchema):
    class Meta:
        model = SRSDocument
        fields = ["id", "title", "version", "description", "path"]


class DeleteSRSDocument(ModelSchema):
    class Meta:
        model = SRSDocument
        fields = ["id"]


__all__ = ["ReadSRSDocument", "CreateSRSDocument", "UpdateSRSDocument", "DeleteSRSDocument"]
