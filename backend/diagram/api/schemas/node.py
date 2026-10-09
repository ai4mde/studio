from ninja import ModelSchema

from diagram.models import Node

from metadata.api.schemas.classifier import (
    ClassifierCreate,
    ClassifierRead,
    ClassifierUpdate,
)


class NodeRead(ModelSchema):
    classifier: ClassifierRead  # type: ignore[valid-type]

    class Meta:
        model = Node
        fields = [
            "id",
            "diagram",
            "classifier",
            "parent",
            "x_position",
            "y_position",
            "height",
            "width",
            "color",
            "font",
        ]


class NodeCreate(ModelSchema):
    classifier: ClassifierCreate # type: ignore[valid-type]

    class Meta:
        model = Node
        fields = [
            "parent",
            "x_position",
            "y_position",
            "height",
            "width",
            "color",
            "font",
        ]
        fields_optional = [
            "parent",
            "x_position",
            "y_position",
            "height",
            "width",
            "color",
            "font",
        ]


class NodeUpdate(ModelSchema):
    classifier: ClassifierUpdate | None = None

    class Meta:
        model = Node
        fields = [
            "parent",
            "x_position",
            "y_position",
            "height",
            "width",
            "color",
            "font",
        ]
        fields_optional = "__all__"