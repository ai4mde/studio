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
            "running", 
            "port",
        ]


class CreatePrototype(ModelSchema):
    class Meta:
        model = Prototype
        fields = [
            "name", 
            "description", 
            "system", 
            "running", 
            "port",
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
            "running", 
            "port",
        ]


__all__ = ["ReadPrototype", "CreatePrototype", "UpdatePrototype"]
