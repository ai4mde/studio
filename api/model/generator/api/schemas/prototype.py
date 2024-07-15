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
            "container_id", 
            "container_url", 
            "container_port"
        ]


class CreatePrototype(ModelSchema):
    class Meta:
        model = Prototype
        fields = [
            "name", 
            "description", 
            "system", 
            "running", 
            "container_id", 
            "container_url", 
            "container_port"
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
            "container_id", 
            "container_url", 
            "container_port"
        ]


__all__ = ["ReadPrototype", "CreatePrototype", "UpdatePrototype"]
