from copy import deepcopy
import hashlib
import json
import os
from uuid import UUID

import requests

from generator.api.schemas.prototype import PrototypeCreate
from generator.models import Prototype
from generator.services.metadata import build_generator_metadata
from metadata.models import Interface, System


PROTOTYPE_API_PROTO = os.environ.get("PROTOTYPE_API_PROTO", "http://")
PROTOTYPE_API_HOST = os.environ.get("PROTOTYPE_API_HOST", "studio-prototypes")
PROTOTYPE_API_PORT = os.environ.get("PROTOTYPE_API_PORT", 8010)
PROTOTYPE_API_URL = (
    f"{PROTOTYPE_API_PROTO}{PROTOTYPE_API_HOST}:{PROTOTYPE_API_PORT}"
)


def calculate_database_hash(
    system: System,
    metadata: dict,
) -> str:
    classes = {}
    relations = {}

    for diagram in metadata["diagrams"]:
        if diagram["type"] != "class":
            continue

        for node in diagram["nodes"]:
            classifier = node["classifier"]

            if classifier["type"] == "class":
                classes[classifier["id"]] = deepcopy(classifier)

        for edge in diagram["edges"]:
            relation = edge["relation"]
            relations[relation["id"]] = relation

    # Make nested collections deterministic as well.
    for classifier in classes.values():
        classifier["data"]["attributes"].sort(
            key=lambda item: item["id"]
        )
        classifier["data"]["operations"].sort(
            key=lambda item: item["id"]
        )

    interface_names = list(
        Interface.objects.filter(system=system)
        .order_by("name")
        .values_list("name", flat=True)
    )

    hash_data = {
        "system": str(system.id),
        "classes": [classes[key] for key in sorted(classes)],
        "relations": [relations[key] for key in sorted(relations)],
        "interfaces": interface_names,
    }

    serialized = json.dumps(
        hash_data,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def create_prototype(
    prototype: PrototypeCreate,
) -> Prototype:
    system = System.objects.get(pk=prototype.system_id)

    metadata = build_generator_metadata(
        system=system,
        interface_ids=prototype.interface_ids,
        use_authentication=prototype.use_authentication,
    ).model_dump(mode="json")

    database_hash = calculate_database_hash(
        system=system,
        metadata=metadata,
    )

    new_prototype = Prototype.objects.create(
        name=prototype.name,
        description=prototype.description,
        system=system,
        database_hash=database_hash,
        metadata=metadata,
    )

    data = {
        "id": str(new_prototype.id),
        "name": prototype.name,
        "system": str(system.id),
        "metadata": json.dumps(metadata),
    }

    if prototype.database_prototype_name:
        data["database_prototype_name"] = (
            prototype.database_prototype_name
        )

    response = requests.post(
        f"{PROTOTYPE_API_URL}/generate",
        json=data,
    )

    if response.status_code != 200:
        # TODO Generator should implement a validation phase to check the data
        # Handle the messages it sends back here
        raise Exception(
            "Failed to generate prototype " + prototype.name
        )

    return new_prototype


def delete_prototype(prototype_id: UUID) -> bool:
    prototype = Prototype.objects.filter(id=prototype_id).first()

    if not prototype:
        return False

    data = {
        "id": str(prototype.id),
        "name": prototype.name,
        "system": str(prototype.system.id),
    }

    response = requests.delete(
        f"{PROTOTYPE_API_URL}/remove",
        json=data,
    )

    if response.status_code != 200:
        raise Exception("Failed to delete prototype " + prototype.name)

    prototype.delete()
    return True


def delete_system_prototypes(system_id: UUID) -> bool:
    prototypes = Prototype.objects.filter(system_id=system_id)

    if not prototypes.exists():
        return False

    for prototype in prototypes:
        delete_prototype(prototype.id)

    return True


def stop_prototypes() -> bool:
    try:
        response = requests.post(
            f"{PROTOTYPE_API_URL}/stop_prototypes"
        )
    except requests.RequestException:
        return False

    return response.status_code == 200


def run_prototype(prototype_id: UUID) -> bool:
    prototype = Prototype.objects.get(id=prototype_id)

    data = {
        "id": str(prototype.id),
        "name": prototype.name,
        "system": str(prototype.system.id),
    }

    try:
        response = requests.post(
            f"{PROTOTYPE_API_URL}/run",
            json=data,
        )
    except requests.RequestException:
        return False

    return response.status_code in (200, 307)


def get_active_prototype() -> dict:
    response = requests.get(
        f"{PROTOTYPE_API_URL}/active_prototype"
    )
    return response.json()
