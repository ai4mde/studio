from typing import Any

from ninja import ModelSchema

from metadata.models import Relation
from metadata.models.types import RelationType

from ..builders import (
    EMPTY_TYPED_SCHEMAS,
    build_create_model,
    build_read_union,
)
from .activity_diagram import ACTIVITY_DIAGRAM_SCHEMAS
from .class_diagram import CLASS_DIAGRAM_SCHEMAS
from .component_diagram import COMPONENT_DIAGRAM_SCHEMAS
from .usecase_diagram import USECASE_DIAGRAM_SCHEMAS


RELATION_SCHEMAS = {
    **ACTIVITY_DIAGRAM_SCHEMAS,
    **CLASS_DIAGRAM_SCHEMAS,
    **COMPONENT_DIAGRAM_SCHEMAS,
    **USECASE_DIAGRAM_SCHEMAS,
}


def get_relation_schemas(relation_type: RelationType):
    return RELATION_SCHEMAS.get(
        relation_type,
        EMPTY_TYPED_SCHEMAS,
    )


class RelationReadBase(ModelSchema):
    class Meta:
        model = Relation
        fields = [
            "id",
            "system",
            "source",
            "target",
        ]


class RelationCreateBase(ModelSchema):
    class Meta:
        model = Relation
        fields = [
            "system",
            "source",
            "target",
        ]


RelationRead = build_read_union(
    type_enum=RelationType,
    base_model=RelationReadBase,
    get_schemas=get_relation_schemas,
    name="Relation",
)


RelationCreate = build_create_model(
    type_enum=RelationType,
    base_model=RelationCreateBase,
    get_schemas=get_relation_schemas,
    name="Relation",
)


# We will retrieve the type of the relation from the database
# During the update, since the type is not provided in the body
class RelationUpdate(ModelSchema):
    data: dict[str, Any] | None = None

    class Meta:
        model = Relation

        # If in the future we want to allow updating a field
        # Replace with fields = ["future_field"]
        # This is added since an empty fields list is not allowed in pydantic
        exclude = [
            "id",
            "system",
            "source",
            "target",
            "type",
        ]
        fields_optional = "__all__"
