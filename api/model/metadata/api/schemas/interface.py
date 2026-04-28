
from ninja import ModelSchema, Schema

from metadata.models import Interface


class ReadInterface(ModelSchema):
    class Meta:
        model = Interface
        fields = ["id", "name", "description", "system", "actor", "data"]


class CreateInterface(ModelSchema):
    class Meta:
        model = Interface
        fields = ["name", "description", "system", "actor", "data"]


class UpdateInterface(ModelSchema):
    class Meta:
        model = Interface
        fields = ["id", "name", "description", "system", "actor", "data"]


class DeleteInterface(ModelSchema):
    class Meta:
        model = Interface
        fields = ["id"]


class ExportInterface(ModelSchema):
    class Meta:
        model = Interface
        fields = "__all__"


class ImportInterface(Schema):
    id: str
    name: str
    description: str
    actor: str
    system: str
    data: dict


__all__ = [
    "ReadInterface",
    "CreateInterface",
    "UpdateInterface",
    "DeleteInterface",
    "ExportInterface",
]
