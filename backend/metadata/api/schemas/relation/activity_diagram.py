from ninja import ModelSchema

from metadata.api.schemas.classifier.class_diagram import AttributeRead
from metadata.models import ControlFlow
from metadata.models.types import RelationType


class ControlFlowRead(ModelSchema):
    attribute: AttributeRead | None
    
    class Meta:
        model = ControlFlow
        fields = [
            "guard",
            "weight",
            "is_else",
            "attribute",
            "operator",
            "aggregator",
            "comparison_value",
        ]


class ControlFlowCreate(ModelSchema):
    class Meta:
        model = ControlFlow
        fields = [
            "guard",
            "weight",
            "is_else",
            "attribute",
            "operator",
            "aggregator",
            "comparison_value",
        ]


class ControlFlowUpdate(ModelSchema):
    class Meta:
        model = ControlFlow
        fields = [
            "guard",
            "weight",
            "is_else",
            "attribute",
            "operator",
            "aggregator",
            "comparison_value",
        ]
        fields_optional = "__all__"


ACTIVITY_DIAGRAM_SCHEMAS = {
    RelationType.CONTROLFLOW: {
        "read": ControlFlowRead,
        "create": ControlFlowCreate,
        "update": ControlFlowUpdate,
    },
}
