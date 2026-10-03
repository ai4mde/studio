from typing import Any

from ninja import ModelSchema

from metadata.models import Classifier
from metadata.models.types import ClassifierType

from metadata.api.schemas.builders import (
    EMPTY_TYPED_SCHEMAS,
    build_create_model,
    build_read_union,
)
from .activity_diagram import ACTIVITY_DIAGRAM_SCHEMAS
from .class_diagram import CLASS_DIAGRAM_SCHEMAS
from .component_diagram import COMPONENT_DIAGRAM_SCHEMAS
from .usecase_diagram import USECASE_DIAGRAM_SCHEMAS


CLASSIFIER_SCHEMAS = {
    **ACTIVITY_DIAGRAM_SCHEMAS,
    **CLASS_DIAGRAM_SCHEMAS,
    **COMPONENT_DIAGRAM_SCHEMAS,
    **USECASE_DIAGRAM_SCHEMAS,
}


def get_classifier_schemas(classifier_type: ClassifierType):
    return CLASSIFIER_SCHEMAS.get(
        classifier_type,
        EMPTY_TYPED_SCHEMAS,
    )


class ClassifierReadBase(ModelSchema):
    class Meta:
        model = Classifier
        fields = ["id", "system"]


class ClassifierCreateBase(ModelSchema):
    class Meta:
        model = Classifier
        fields = ["system"]


# Create the read and create models for all classifier types using the builder functions
ClassifierRead = build_read_union(
    type_enum=ClassifierType,
    base_model=ClassifierReadBase,
    get_schemas=get_classifier_schemas,
    name="Classifier",
)


ClassifierCreate = build_create_model(
    type_enum=ClassifierType,
    base_model=ClassifierCreateBase,
    get_schemas=get_classifier_schemas,
    name="Classifier",
)


# We will retrieve the type of the classifier from the database
# During the update, since the type is not provided in the body
class ClassifierUpdate(ModelSchema):
    data: dict[str, Any] | None = None

    class Meta:
        model = Classifier

        # If in the future we want to allow updating a field
        # Replace with fields = ["future_field"]
        # This is added since an empty fields list is not allowed in pydantic
        exclude = ["id", "system", "type"]
        fields_optional = "__all__"