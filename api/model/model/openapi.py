from uuid import UUID

from ninja import NinjaAPI
from ninja.orm import register_field

register_field("OneToOneField", UUID)

def resolve(schema, definitions):
    while "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[-1]
        schema = definitions[name]
    return schema


def make_example(schema, definitions):
    schema = resolve(schema, definitions)

    for key in ("example", "default", "const"):
        if key in schema:
            return schema[key]

    if "enum" in schema:
        return schema["enum"][0]

    if "anyOf" in schema:
        option = next(
            (
                s for s in schema["anyOf"]
                if s.get("type") != "null"
            ),
            schema["anyOf"][0],
        )
        return make_example(option, definitions)

    if "oneOf" in schema:
        return make_example(schema["oneOf"][0], definitions)

    if "properties" in schema:
        return {
            field: make_example(field_schema, definitions)
            for field, field_schema in schema["properties"].items()
        }

    if schema.get("type") == "array":
        return []

    if schema.get("format") == "uuid":
        return "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    return {
        "string": "string",
        "integer": 0,
        "number": 0.0,
        "boolean": False,
    }.get(schema.get("type"), {})


class StudioAPI(NinjaAPI):
    def get_openapi_schema(self, **kwargs):
        openapi = super().get_openapi_schema(**kwargs)
        definitions = openapi["components"]["schemas"]

        for path in openapi["paths"].values():
            for operation in path.values():
                if not isinstance(operation, dict):
                    continue

                media = (
                    operation.get("requestBody", {})
                    .get("content", {})
                    .get("application/json")
                )

                if not media or "examples" in media:
                    continue

                request_schema = media.get("schema", {})
                root = resolve(request_schema, definitions)

                # Find the discriminated union, including nested fields.
                variants = None
                field_name = None

                if "discriminator" in root and "oneOf" in root:
                    variants = root
                else:
                    for field, property_schema in root.get(
                        "properties", {}
                    ).items():
                        candidate = resolve(property_schema, definitions)

                        if (
                            "discriminator" in candidate
                            and "oneOf" in candidate
                        ):
                            variants = candidate
                            field_name = field
                            break

                if variants is None:
                    continue

                examples = {}

                for data_type, ref in variants[
                    "discriminator"
                ]["mapping"].items():
                    variant_example = make_example(
                        {"$ref": ref},
                        definitions,
                    )

                    if field_name is None:
                        value = variant_example
                    else:
                        value = make_example(
                            request_schema,
                            definitions,
                        )
                        value[field_name] = variant_example

                    examples[data_type] = {
                        "summary": data_type,
                        "value": value,
                    }

                media["examples"] = examples

        return openapi