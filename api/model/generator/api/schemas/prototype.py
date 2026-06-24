from ninja import ModelSchema
from ninja import Schema
from generator.models import Prototype
from typing import Any, Dict, Optional


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


class CreatePrototype(Schema):
    name: str
    description: Optional[str] = ""
    system: Optional[str] = None
    system_id: Optional[str] = None
    database_hash: Optional[str] = ""
    metadata: Dict[str, Any]


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
