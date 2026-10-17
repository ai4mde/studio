from ninja import ModelSchema

from metadata.models import (
    Actor,
    SystemBoundary,
    Usecase,
)
from metadata.models.types import ClassifierType


class SystemBoundaryRead(ModelSchema):
    class Meta:
        model = SystemBoundary
        fields = ["name", "system"]


class SystemBoundaryCreate(ModelSchema):
    class Meta:
        model = SystemBoundary
        fields = ["name", "system"]


class SystemBoundaryUpdate(ModelSchema):
    class Meta:
        model = SystemBoundary
        fields = ["name", "system"]
        fields_optional = "__all__"


class ActorRead(ModelSchema):
    class Meta:
        model = Actor
        fields = ["name", "boundary"]


class ActorCreate(ModelSchema):
    class Meta:
        model = Actor
        fields = ["name", "boundary"]


class ActorUpdate(ModelSchema):
    class Meta:
        model = Actor
        fields = ["name", "boundary"]
        fields_optional = "__all__"


class UsecaseRead(ModelSchema):
    class Meta:
        model = Usecase
        fields = ["name", "boundary"]


class UsecaseCreate(ModelSchema):
    class Meta:
        model = Usecase
        fields = ["name", "boundary"]


class UsecaseUpdate(ModelSchema):
    class Meta:
        model = Usecase
        fields = ["name", "boundary"]
        fields_optional = "__all__"


USECASE_DIAGRAM_SCHEMAS = {
    ClassifierType.SYSTEM_BOUNDARY: {
        "read": SystemBoundaryRead,
        "create": SystemBoundaryCreate,
        "update": SystemBoundaryUpdate,
    },
    ClassifierType.ACTOR: {
        "read": ActorRead,
        "create": ActorCreate,
        "update": ActorUpdate,
    },
    ClassifierType.USECASE: {
        "read": UsecaseRead,
        "create": UsecaseCreate,
        "update": UsecaseUpdate,
    },
}