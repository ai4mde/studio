from ninja import ModelSchema

from metadata.models import (
    ClassClassifier,
    Enum,
    InterfaceClassifier,
    Signal,
)
from metadata.models.types import ClassifierType

class ClassClassifierRead(ModelSchema):
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


class EnumRead(ModelSchema):
    class Meta:
        model = Enum
        fields = ["name"]


class EnumCreate(ModelSchema):
    class Meta:
        model = Enum
        fields = ["name"]


class EnumUpdate(ModelSchema):
    class Meta:
        model = Enum
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