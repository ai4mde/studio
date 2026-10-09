from ninja import ModelSchema

from metadata.models import (
    Association,
    Composition,
    Dependency,
)
from metadata.models.types import RelationType


class AssociationRead(ModelSchema):
    class Meta:
        model = Association
        fields = [
            "derived",
            "label",
            "multiplicity",
            "labels",
        ]


class AssociationCreate(ModelSchema):
    class Meta:
        model = Association
        fields = [
            "derived",
            "label",
            "multiplicity",
            "labels",
        ]


class AssociationUpdate(ModelSchema):
    class Meta:
        model = Association
        fields = [
            "derived",
            "label",
            "multiplicity",
            "labels",
        ]
        fields_optional = "__all__"


class CompositionRead(ModelSchema):
    class Meta:
        model = Composition
        fields = [
            "label",
            "multiplicity",
            "labels",
        ]


class CompositionCreate(ModelSchema):
    class Meta:
        model = Composition
        fields = [
            "label",
            "multiplicity",
            "labels",
        ]


class CompositionUpdate(ModelSchema):
    class Meta:
        model = Composition
        fields = [
            "label",
            "multiplicity",
            "labels",
        ]
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