
import csv
from io import StringIO
from uuid import uuid4

from metadata.models.types import DataType


TYPE_MAPPING = {
    "str": DataType.STRING,
    "string": DataType.STRING,
    "int": DataType.INT,
    "bool": DataType.BOOL,
    "datetime": DataType.DATETIME,
    "enum": DataType.ENUM,
}


def parse_multiplicity(value: str) -> tuple[int, int | None]:
    value = value.strip()

    if value == "*":
        return 0, None

    if ".." in value:
        lower, upper = value.split("..", 1)
        lower = int(lower)
        upper = None if upper == "*" else int(upper)
    else:
        lower = upper = int(value)

    if lower < 0 or (upper is not None and upper < lower):
        raise ValueError(f"Invalid multiplicity: {value}")

    return lower, upper


def parse_classifiers(csv_table: str) -> list[dict]:
    classifiers = []
    names = set()

    reader = csv.DictReader(StringIO(csv_table.strip()))

    for row in reader:
        name = row["class_name"].strip().strip('"')

        if not name or name in names:
            raise ValueError(f"Invalid or duplicate class name: {name}")

        names.add(name)
        attributes = []

        for attribute in row["attributes"].strip().strip("[]").split(","):
            if not attribute.strip():
                continue

            raw_type, attribute_name = attribute.strip().split(":", 1)
            raw_type = raw_type.strip().lower()
            attribute_name = attribute_name.strip()

            attribute_type = TYPE_MAPPING.get(raw_type)

            if attribute_type is None:
                raise ValueError(f"Unsupported attribute type: {raw_type}")

            if not attribute_name:
                raise ValueError("Attribute name cannot be empty.")

            attributes.append({
                "name": attribute_name,
                "type": attribute_type,
                "derived": False,
                "description": None,
                "body": None,
            })

        classifiers.append({
            "id": str(uuid4()),
            "type": "class",
            "name": name,
            "attributes": attributes,
        })

    return classifiers


def parse_relations(csv_table: str, classifiers: list[dict]) -> list[dict]:
    relations = []

    classifier_ids = {
        classifier["name"]: classifier["id"]
        for classifier in classifiers
    }

    reader = csv.DictReader(StringIO(csv_table.strip()))

    for row in reader:
        source_name = row["source_class_name"].strip()
        target_name = row["target_class_name"].strip()

        if source_name not in classifier_ids or target_name not in classifier_ids:
            raise ValueError(
                f"Unknown relation endpoint: {source_name} -> {target_name}"
            )

        source_lower, source_upper = parse_multiplicity(
            row["source_multiplicity"]
        )
        target_lower, target_upper = parse_multiplicity(
            row["target_multiplicity"]
        )

        relations.append({
            "id": str(uuid4()),
            "type": "association",
            "source": classifier_ids[source_name],
            "target": classifier_ids[target_name],
            "derived": False,
            "label": "",
            "multiplicity": {
                "source_lower": source_lower,
                "source_upper": source_upper,
                "target_lower": target_lower,
                "target_upper": target_upper,
            },
        })

    return relations


def parse_llm_response(response: str) -> dict:
    tables = []
    current = None

    for line in response.splitlines():
        if line.strip() == "START":
            current = []
        elif line.strip() == "END" and current is not None:
            tables.append("\n".join(current))
            current = None
        elif current is not None:
            current.append(line)

    if len(tables) != 2:
        raise ValueError(
            f"Expected 2 CSV tables, found {len(tables)}."
        )

    classifiers = parse_classifiers(tables[0])
    relations = parse_relations(tables[1], classifiers)

    return {
        "classifiers": classifiers,
        "relations": relations,
    }
