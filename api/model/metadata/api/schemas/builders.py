# Shared utilities for dynamically building typed API schemas.

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

        literal_type = Literal[data_type]  # type: ignore[valid-type]

        fields = {
            "type": (literal_type, ...),
            "data": (schemas["read"], ...),
        }

        model = create_model(
            f"{data_type.name.title()}{name}Read",
            __base__=base_model,
            **fields,
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

        literal_type = Literal[data_type]  # type: ignore[valid-type]

        fields = {
            "type": (literal_type, ...),
            "data": (schemas["create"], ...),
        }

        model = create_model(
            f"{data_type.name.title()}{name}Create",
            __base__=base_model,
            **fields,
        )

        models.append(model)

    union = reduce(or_, models)

    return create_model(
        f"{name}Create",
        __base__=RootModel,
        root=(
            Annotated[
                union,  # type: ignore[valid-type]
                Field(discriminator="type"),
            ],
            ...,
        ),
    )