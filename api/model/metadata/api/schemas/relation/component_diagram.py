from ninja import ModelSchema

from metadata.models import InterfaceRelation
from metadata.models.types import RelationType


class InterfaceRelationRead(ModelSchema):
    class Meta:
        model = InterfaceRelation
        fields = [
            "required",
            "provided",
        ]


class InterfaceRelationCreate(ModelSchema):
    class Meta:
        model = InterfaceRelation
        fields = [
            "required",
            "provided",
        ]


class InterfaceRelationUpdate(ModelSchema):
    class Meta:
        model = InterfaceRelation
        fields = [
            "required",
            "provided",
        ]
        fields_optional = "__all__"


COMPONENT_DIAGRAM_SCHEMAS = {
    RelationType.INTERFACE: {
        "read": InterfaceRelationRead,
        "create": InterfaceRelationCreate,
        "update": InterfaceRelationUpdate,
    },
}