from ninja import ModelSchema

from metadata.models import (
    Action,
    Event,
    Final,
    Initial,
    Object,
    Swimlane,
)
from metadata.models.types import ClassifierType


class SwimlaneRead(ModelSchema):
    class Meta:
        model = Swimlane
        fields = ["parent", "actor", "component"]


class SwimlaneCreate(ModelSchema):
    class Meta:
        model = Swimlane
        fields = ["parent", "actor", "component"]


class SwimlaneUpdate(ModelSchema):
    class Meta:
        model = Swimlane
        fields = ["parent", "actor", "component"]
        fields_optional = "__all__"


class ActionRead(ModelSchema):
    class Meta:
        model = Action
        fields = ["name", "is_automatic", "custom_code", "swimlane"]


class ActionCreate(ModelSchema):
    class Meta:
        model = Action
        fields = ["name", "is_automatic", "custom_code", "swimlane"]


class ActionUpdate(ModelSchema):
    class Meta:
        model = Action
        fields = ["name", "is_automatic", "custom_code", "swimlane"]
        fields_optional = "__all__"


class ObjectRead(ModelSchema):
    class Meta:
        model = Object
        fields = ["name", "uml_class", "state"]


class ObjectCreate(ModelSchema):
    class Meta:
        model = Object
        fields = ["name", "uml_class", "state"]


class ObjectUpdate(ModelSchema):
    class Meta:
        model = Object
        fields = ["name", "uml_class", "state"]
        fields_optional = "__all__"


class EventRead(ModelSchema):
    class Meta:
        model = Event
        fields = ["name", "signal"]


class EventCreate(ModelSchema):
    class Meta:
        model = Event
        fields = ["name", "signal"]


class EventUpdate(ModelSchema):
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