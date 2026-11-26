from uuid import UUID

from ninja import Field, ModelSchema

from metadata.models import (
    Action,
    Event,
    Final,
    Initial,
    Object,
    Swimlane,
)
from metadata.models.types import ClassifierType
from metadata.api.schemas.classifier.usecase_diagram import ActorRead


# Django Ninja infers int for foreign keys to models whose primary key is
# a OneToOneField referencing a UUID. Explicitly annotate these as UUID.

class SwimlaneRead(ModelSchema):
    parent: UUID | None = Field(None, alias="parent_id")
    actor: ActorRead | None

    class Meta:
        model = Swimlane
        fields = ["parent", "actor", "component"]


class SwimlaneCreate(ModelSchema):
    parent: UUID | None = Field(None, alias="parent_id")
    actor: UUID | None = Field(None, alias="actor_id")

    class Meta:
        model = Swimlane
        fields = ["parent", "actor", "component"]


class SwimlaneUpdate(ModelSchema):
    parent: UUID | None = Field(None, alias="parent_id")
    actor: UUID | None = Field(None, alias="actor_id")

    class Meta:
        model = Swimlane
        fields = ["parent", "actor", "component"]
        fields_optional = "__all__"


class ActionRead(ModelSchema):
    swimlane: SwimlaneRead | None

    class Meta:
        model = Action
        fields = ["name", "is_automatic", "custom_code", "swimlane"]


class ActionCreate(ModelSchema):
    swimlane: UUID | None = Field(None, alias="swimlane_id")

    class Meta:
        model = Action
        fields = ["name", "is_automatic", "custom_code", "swimlane"]


class ActionUpdate(ModelSchema):
    swimlane: UUID | None = Field(None, alias="swimlane_id")  

    class Meta:
        model = Action
        fields = ["name", "is_automatic", "custom_code", "swimlane"]
        fields_optional = "__all__"


class ObjectRead(ModelSchema):
    uml_class: UUID | None = Field(None, alias="uml_class_id")


    class Meta:
        model = Object
        fields = ["name", "uml_class", "state"]


class ObjectCreate(ModelSchema):
    uml_class: UUID | None = Field(None, alias="uml_class_id")


    class Meta:
        model = Object
        fields = ["name", "uml_class", "state"]


class ObjectUpdate(ModelSchema):
    uml_class: UUID | None = Field(None, alias="uml_class_id")

    class Meta:
        model = Object
        fields = ["name", "uml_class", "state"]
        fields_optional = "__all__"


class EventRead(ModelSchema):
    signal: UUID | None = Field(None, alias="signal_id")

    class Meta:
        model = Event
        fields = ["name", "signal"]


class EventCreate(ModelSchema):
    signal: UUID | None = Field(None, alias="signal_id")

    class Meta:
        model = Event
        fields = ["name", "signal"]


class EventUpdate(ModelSchema):
    signal: UUID | None = Field(None, alias="signal_id")


    class Meta:
        model = Event
        fields = ["name", "signal"]
        fields_optional = "__all__"


class FinalRead(ModelSchema):
    class Meta:
        model = Final
        fields = ["activity_scope"]


class FinalCreate(ModelSchema):
    class Meta:
        model = Final
        fields = ["activity_scope"]


class FinalUpdate(ModelSchema):
    class Meta:
        model = Final
        fields = ["activity_scope"]
        fields_optional = "__all__"


class InitialRead(ModelSchema):
    class Meta:
        model = Initial
        fields = ["scheduled", "schedule"]


class InitialCreate(ModelSchema):
    class Meta:
        model = Initial
        fields = ["scheduled", "schedule"]


class InitialUpdate(ModelSchema):
    class Meta:
        model = Initial
        fields = ["scheduled", "schedule"]
        fields_optional = "__all__"


ACTIVITY_DIAGRAM_SCHEMAS = {
    ClassifierType.SWIMLANE: {
        "read": SwimlaneRead,
        "create": SwimlaneCreate,
        "update": SwimlaneUpdate,
    },
    ClassifierType.ACTION: {
        "read": ActionRead,
        "create": ActionCreate,
        "update": ActionUpdate,
    },
    ClassifierType.OBJECT: {
        "read": ObjectRead,
        "create": ObjectCreate,
        "update": ObjectUpdate,
    },
    ClassifierType.EVENT: {
        "read": EventRead,
        "create": EventCreate,
        "update": EventUpdate,
    },
    ClassifierType.FINAL: {
        "read": FinalRead,
        "create": FinalCreate,
        "update": FinalUpdate,
    },
    ClassifierType.INITIAL: {
        "read": InitialRead,
        "create": InitialCreate,
        "update": InitialUpdate,
    },   
}