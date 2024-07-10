from ninja import ModelSchema
from metadata.models import Interface


class ReadInterface(ModelSchema):
    class Meta:
        model = Interface
        fields = ["id", "name", "description", "system", "data"]


class CreateInterface(ModelSchema):
    class Meta:
        model = Interface
        fields = ["name", "description", "system", "data"]


class UpdateInterface(ModelSchema):
    class Meta:
        model = Interface
        fields = ["id", "name", "description", "system", "data"]


class DeleteInterface(ModelSchema):
    class Meta:
        model = Interface
        fields = ["id"]


__all__ = ["ReadInterface", "CreateInterface", "UpdateInterface", "DeleteInterface"]
