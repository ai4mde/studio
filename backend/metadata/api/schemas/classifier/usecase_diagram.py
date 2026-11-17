from uuid import UUID

from ninja import Field, ModelSchema

from metadata.models import (
    Actor,
    SystemBoundary,
    Usecase,
)
from metadata.models.types import ClassifierType


# Django Ninja infers int for foreign keys to models whose primary key is
# a OneToOneField referencing a UUID. Explicitly annotate these as UUID.

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
    boundary: UUID | None = Field(None, alias="boundary_id")

    class Meta:
        model = Actor
        fields = ["name", "boundary"]


class ActorCreate(ModelSchema):
    boundary: UUID | None = Field(None, alias="boundary_id")

    class Meta:
        model = Actor
        fields = ["name", "boundary"]


class ActorUpdate(ModelSchema):
    boundary: UUID | None = Field(None, alias="boundary_id")

    class Meta:
        model = Actor
        fields = ["name", "boundary"]
        fields_optional = "__all__"


class UsecaseRead(ModelSchema):
    boundary: UUID | None = Field(None, alias="boundary_id")

    class Meta:
        model = Usecase
        fields = ["name", "boundary"]


class UsecaseCreate(ModelSchema):
    boundary: UUID | None = Field(None, alias="boundary_id")

    class Meta:
        model = Usecase
        fields = ["name", "boundary"]


class UsecaseUpdate(ModelSchema):
    boundary: UUID | None = Field(None, alias="boundary_id")

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