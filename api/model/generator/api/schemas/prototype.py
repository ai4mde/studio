from ninja import ModelSchema
from generator.models import Prototype


class ReadPrototype(ModelSchema):
    class Meta:
        model = Prototype
        fields = [
            "id",
            "name", 
            "description", 
            "system", 
            "database_hash",
        ]


class CreatePrototype(ModelSchema):
    class Meta:
        model = Prototype
        fields = [
            "name", 
            "description", 
            "system", 
            "database_hash",
            "metadata",
        ]


class UpdatePrototype(ModelSchema):
    class Meta:
        model = Prototype
        fields = [
            "id",
            "name", 
            "description", 
            "system", 
            "database_hash"
        ]


__all__ = ["ReadPrototype", "CreatePrototype", "UpdatePrototype"]
