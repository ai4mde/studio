from uuid import UUID

from ninja import ModelSchema

from generator.models import Prototype


class PrototypeRead(ModelSchema):
    class Meta:
        model = Prototype
        fields = [
            "id",
            "name",
            "description",
            "system",
            "database_hash",
        ]


class PrototypeCreate(ModelSchema):
    system_id: UUID
    interface_ids: list[UUID]
    use_authentication: bool
    database_prototype_name: str | None = None

    class Meta:
        model = Prototype
        fields = [
            "name",
            "description",
        ]


class PrototypeUpdate(ModelSchema):
    class Meta:
        model = Prototype
        fields = [
            "name",
            "description",
        ]
