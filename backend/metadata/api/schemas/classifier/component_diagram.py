from ninja import ModelSchema

from metadata.models import (
    Component,
    Container,
    SystemClassifier,
)
from metadata.models.types import ClassifierType


class SystemClassifierRead(ModelSchema):
    class Meta:
        model = SystemClassifier
        fields = ["name"]


class SystemClassifierCreate(ModelSchema):
    class Meta:
        model = SystemClassifier
        fields = ["name"]


class SystemClassifierUpdate(ModelSchema):
    class Meta:
        model = SystemClassifier
        fields = ["name"]
        fields_optional = "__all__"


class ContainerRead(ModelSchema):
    class Meta:
        model = Container
        fields = ["name"]


class ContainerCreate(ModelSchema):
    class Meta:
        model = Container
        fields = ["name"]


class ContainerUpdate(ModelSchema):
    class Meta:
        model = Container
        fields = ["name"]
        fields_optional = "__all__"


class ComponentRead(ModelSchema):
    class Meta:
        model = Component
        fields = ["name"]


class ComponentCreate(ModelSchema):
    class Meta:
        model = Component
        fields = ["name"]


class ComponentUpdate(ModelSchema):
    class Meta:
        model = Component
        fields = ["name"]
        fields_optional = "__all__"


COMPONENT_DIAGRAM_SCHEMAS = {
    ClassifierType.SYSTEM: {
        "read": SystemClassifierRead,
        "create": SystemClassifierCreate,
        "update": SystemClassifierUpdate,
    },
    ClassifierType.CONTAINER: {
        "read": ContainerRead,
        "create": ContainerCreate,
        "update": ContainerUpdate,
    },
    ClassifierType.COMPONENT: {
        "read": ComponentRead,
        "create": ComponentCreate,
        "update": ComponentUpdate,
    },
}