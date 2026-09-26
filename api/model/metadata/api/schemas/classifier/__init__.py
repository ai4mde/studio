from functools import reduce
from operator import or_
from typing import Annotated, Any, Literal

from ninja import ModelSchema, Schema
from pydantic import create_model, Field, RootModel

from metadata.models import Classifier
from metadata.models.types import ClassifierType

from .registry import get_classifier_schemas


class ClassifierReadBase(ModelSchema):
    class Meta:
        model = Classifier
        fields = ["id", "system"]


class ClassifierCreateBase(ModelSchema):
    class Meta:
        model = Classifier
        fields = ["system"]


CLASSIFIER_CREATE_MODELS = []
for classifier_type in ClassifierType:
    schemas = get_classifier_schemas(classifier_type)

    model = create_model(
        f"{classifier_type.name.title()}ClassifierCreate",
        __base__=ClassifierCreateBase,
        type=(Literal[classifier_type], ...),
        data=(schemas["create"], ...),
    )

    CLASSIFIER_CREATE_MODELS.append(model)


CLASSIFIER_READ_MODELS = []
for classifier_type in ClassifierType:
    schemas = get_classifier_schemas(classifier_type)

    model = create_model(
        f"{classifier_type.name.title()}ClassifierRead",
        __base__=ClassifierReadBase,
        type=(Literal[classifier_type], ...),
        data=(schemas["read"], ...),
    )

    CLASSIFIER_READ_MODELS.append(model)


ClassifierRead = Annotated[
    reduce(or_, CLASSIFIER_READ_MODELS),
    Field(discriminator="type"),
]

CLASSIFIER_CREATE_UNION = reduce(or_, CLASSIFIER_CREATE_MODELS)

class ClassifierCreate(RootModel):
    root: Annotated[ 
        CLASSIFIER_CREATE_UNION,    # type: ignore[valid-type]
        Field(discriminator="type"),
    ]

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

