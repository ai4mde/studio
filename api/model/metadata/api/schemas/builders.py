# This module contains shared schema-building utilties for typed data models.
# It does not define API schemas directly.
# If you want to define API schemas for a specific typed data model, you should do that in the corresponding file in the api/schemas directory.

from functools import reduce
from operator import or_
from typing import Annotated, Literal

from ninja import Schema
from pydantic import Field, RootModel, create_model


class EmptyTypedData(Schema):
    pass


EMPTY_TYPED_SCHEMAS = {
    "read": EmptyTypedData,
    "create": EmptyTypedData,
    "update": EmptyTypedData,
}


def build_read_union(
    *,
    type_enum,
    base_model,
    get_schemas,
    name: str,
):
    models = []

    for data_type in type_enum:
        schemas = get_schemas(data_type)

        model = create_model(
            f"{data_type.name.title()}{name}Read",
            __base__=base_model,
            type=(Literal[data_type], ...),
            data=(schemas["read"], ...),
        )

        models.append(model)

    return Annotated[
        reduce(or_, models),
        Field(discriminator="type"),
    ]


def build_create_model(
    *,
    type_enum,
    base_model,
    get_schemas,
    name: str,
):
    models = []

    for data_type in type_enum:
        schemas = get_schemas(data_type)

        model = create_model(
            f"{data_type.name.title()}{name}Create",
            __base__=base_model,
            type=(Literal[data_type], ...),
            data=(schemas["create"], ...),
        )

        models.append(model)

    union = reduce(or_, models)

    class TypedCreate(RootModel):
        root: Annotated[
            union,  # type: ignore[valid-type]
            Field(discriminator="type"),
        ]

    TypedCreate.__name__ = f"{name}Create"

    return TypedCreate
