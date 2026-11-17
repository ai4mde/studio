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
    class Meta:
        model = Prototype
        fields = [
            "name", 
            "description", 
            "system", 
            "database_hash",
            "metadata",
        ]


class PrototypeUpdate(ModelSchema):
    class Meta:
        model = Prototype
        fields = [
            "name", 
            "description", 
            "system", 
            "database_hash"
        ]
