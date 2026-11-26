from ninja import ModelSchema

from metadata.models import (
    ClassClassifier,
    Enum,
    EnumLiteral,
    InterfaceClassifier,
    Signal,
)
from metadata.models.types import ClassifierType


from uuid import UUID

from ninja import ModelSchema

from metadata.models import Attribute, Operation


class EnumLiteralRead(ModelSchema):
    class Meta:
        model = EnumLiteral
        fields = ["id", "value", "order"]


class EnumLiteralCreate(ModelSchema):
    class Meta:
        model = EnumLiteral
        fields = ["value", "order"]


class EnumLiteralUpdate(ModelSchema):
    class Meta:
        model = EnumLiteral
        fields = ["value", "order"]
        fields_optional = "__all__"


class EnumRead(ModelSchema):
    literals: list[EnumLiteralRead]

    class Meta:
        model = Enum
        fields = ["name"]


class EnumCreate(ModelSchema):
    literals: list[EnumLiteralCreate]

    class Meta:
        model = Enum
        fields = ["name"]


class EnumUpdate(ModelSchema):
    class Meta:
        model = Enum
        fields = ["name"]
        fields_optional = "__all__"


class AttributeRead(ModelSchema):
    enum: EnumRead | None

    class Meta:
        model = Attribute
        fields = [
            "id",
            "name",
            "type",
            "derived",
            "enum",
            "description",
            "body",
        ]


class AttributeCreate(ModelSchema):
    enum_id: UUID | None = None

    class Meta:
        model = Attribute
        fields = [
            "name",
            "type",
            "derived",
            "description",
            "body",
        ]


class AttributeUpdate(ModelSchema):
    enum_id: UUID | None = None

    class Meta:
        model = Attribute
        fields = [
            "name",
            "type",
            "derived",
            "description",
            "body",
        ]
        fields_optional = "__all__"


class OperationRead(ModelSchema):
    class Meta:
        model = Operation
        fields = [
            "id",
            "name",
            "type",
            "description",
            "body",
        ]


class OperationCreate(ModelSchema):
    class Meta:
        model = Operation
        fields = [
            "name",
            "type",
            "description",
            "body",
        ]


class OperationUpdate(ModelSchema):
    class Meta:
        model = Operation
        fields = [
            "name",
            "type",
            "description",
            "body",
        ]
        fields_optional = "__all__"
    

class ClassClassifierRead(ModelSchema):
    attributes: list[AttributeRead]
    operations: list[OperationRead]

    class Meta:
        model = ClassClassifier
        fields = ["name"]


class ClassClassifierCreate(ModelSchema):
    class Meta:
        model = ClassClassifier
        fields = ["name"]


class ClassClassifierUpdate(ModelSchema):
    class Meta:
        model = ClassClassifier
        fields = ["name"]
        fields_optional = "__all__"


class InterfaceClassifierRead(ModelSchema):
    class Meta:
        model = InterfaceClassifier
        fields = ["name"]


class InterfaceClassifierCreate(ModelSchema):
    class Meta:
        model = InterfaceClassifier
        fields = ["name"]


class InterfaceClassifierUpdate(ModelSchema):
    class Meta:
        model = InterfaceClassifier
        fields = ["name"]
        fields_optional = "__all__"


class SignalRead(ModelSchema):
    class Meta:
        model = Signal
        fields = ["name"]


class SignalCreate(ModelSchema):
    class Meta:
        model = Signal
        fields = ["name"]


class SignalUpdate(ModelSchema):
    class Meta:
        model = Signal
        fields = ["name"]
        fields_optional = "__all__"


CLASS_DIAGRAM_SCHEMAS = {
    ClassifierType.CLASS: {
        "read": ClassClassifierRead,
        "create": ClassClassifierCreate,
        "update": ClassClassifierUpdate,
    },
    ClassifierType.ENUM: {
        "read": EnumRead,
        "create": EnumCreate,
        "update": EnumUpdate,
    },
    ClassifierType.INTERFACE: {
        "read": InterfaceClassifierRead,
        "create": InterfaceClassifierCreate,
        "update": InterfaceClassifierUpdate,
    },
    ClassifierType.SIGNAL: {
        "read": SignalRead,
        "create": SignalCreate,
        "update": SignalUpdate,
    },
}