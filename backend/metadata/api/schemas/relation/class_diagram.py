from ninja import ModelSchema, Schema

from metadata.models import (
    Association,
    Composition,
    Dependency,
)
from metadata.models.types import RelationType


class MultiplicitySchema(Schema):
    source_lower: int = 1
    source_upper: int | None = 1
    target_lower: int = 1
    target_upper: int | None = 1


class MultiplicityUpdateSchema(Schema):
    source_lower: int | None = None
    source_upper: int | None = None
    target_lower: int | None = None
    target_upper: int | None = None


class EndpointLabelSchema(Schema):
    source: str = ""
    target: str = ""


class EndpointLabelUpdateSchema(Schema):
    source: str | None = None
    target: str | None = None


class AssociationRead(ModelSchema):
    multiplicity: MultiplicitySchema
    labels: EndpointLabelSchema

    class Meta:
        model = Association
        fields = ["derived", "label"]


class AssociationCreate(ModelSchema):
    multiplicity: MultiplicitySchema = MultiplicitySchema()
    labels: EndpointLabelSchema = EndpointLabelSchema()

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
    multiplicity: MultiplicitySchema = MultiplicitySchema()
    labels: EndpointLabelSchema = EndpointLabelSchema()

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