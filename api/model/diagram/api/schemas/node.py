from uuid import UUID

from ninja import ModelSchema

from diagram.models import Node
from metadata.api.schemas.classifier import ClassifierRead


class NodeRead(ModelSchema):
    classifier: ClassifierRead, # type: ignore[valid-type]
    system_name: str
    system_id: UUID

    class Meta:
        model = Node
        fields = [
            "id",
            "parent",
            "x_position",
            "y_position",
            "height",
            "width",
            "color",
            "font",
        ]

    @staticmethod
    def resolve_system_name(obj):
        return obj.classifier.system.name

    @staticmethod
    def resolve_system_id(obj):
        return obj.classifier.system.id
