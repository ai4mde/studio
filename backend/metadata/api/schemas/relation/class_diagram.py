from ninja import ModelSchema

from metadata.models import (
    Association,
    Composition,
    Dependency,
    Multiplicity,
    EndpointLabel,
)
from metadata.models.types import RelationType


class MultiplicitySchema(ModelSchema):
    class Meta:
        model = Multiplicity
        fields = [
            "source_lower",
            "source_upper",
            "target_lower",
            "target_upper",
        ]


class MultiplicityUpdateSchema(ModelSchema):
    class Meta:
        model = Multiplicity
        fields = [
            "source_lower",
            "source_upper",
            "target_lower",
            "target_upper",
        ]
        fields_optional = "__all__"


class EndpointLabelSchema(ModelSchema):
    class Meta:
        model = EndpointLabel
        fields = ["source", "target"]


class EndpointLabelUpdateSchema(ModelSchema):
    class Meta:
        model = EndpointLabel
        fields = ["source", "target"]
        fields_optional = "__all__"


class AssociationRead(ModelSchema):
    multiplicity: MultiplicitySchema
    labels: EndpointLabelSchema

    class Meta:
        model = Association
        fields = ["derived", "label"]


class AssociationCreate(ModelSchema):
    multiplicity: MultiplicitySchema
    labels: EndpointLabelSchema | None = None

    class Meta:
        model = Association
        fields = ["derived", "label"]
        fields_optional = ["derived", "label"]


class AssociationUpdate(ModelSchema):
    multiplicity: MultiplicityUpdateSchema | None = None
    labels: EndpointLabelUpdateSchema | None = None

    class Meta:
        model = Association
        fields = ["derived", "label"]
        fields_optional = "__all__"


class CompositionRead(ModelSchema):
    multiplicity: MultiplicitySchema
    labels: EndpointLabelSchema

    class Meta:
        model = Composition
        fields = ["label"]


class CompositionCreate(ModelSchema):
    multiplicity: MultiplicitySchema
    labels: EndpointLabelSchema | None = None

    class Meta:
        model = Composition
        fields = ["label"]
        fields_optional = ["label"]


class CompositionUpdate(ModelSchema):
    multiplicity: MultiplicityUpdateSchema | None = None
    labels: EndpointLabelUpdateSchema | None = None

    class Meta:
        model = Composition
        fields = ["label"]
        fields_optional = "__all__"

class DependencyRead(ModelSchema):
    class Meta:
        model = Dependency
        fields = ["label"]


class DependencyCreate(ModelSchema):
    class Meta:
        model = Dependency
        fields = ["label"]


class DependencyUpdate(ModelSchema):
    class Meta:
        model = Dependency
        fields = ["label"]
        fields_optional = "__all__"


CLASS_DIAGRAM_SCHEMAS = {
    RelationType.ASSOCIATION: {
        "read": AssociationRead,
        "create": AssociationCreate,
        "update": AssociationUpdate,
    },
    RelationType.COMPOSITION: {
        "read": CompositionRead,
        "create": CompositionCreate,
        "update": CompositionUpdate,
    },
    RelationType.DEPENDENCY: {
        "read": DependencyRead,
        "create": DependencyCreate,
        "update": DependencyUpdate,
    },
}