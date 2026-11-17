
import json
import os
from uuid import UUID

import requests

from generator.api.schemas.prototype import PrototypeCreate
from generator.models import Prototype
from metadata.models import System


PROTOTYPE_API_PROTO = os.environ.get("PROTOTYPE_API_PROTO", "http://")
PROTOTYPE_API_HOST = os.environ.get("PROTOTYPE_API_HOST", "studio-prototypes")
PROTOTYPE_API_PORT = os.environ.get("PROTOTYPE_API_PORT", 8010)
PROTOTYPE_API_URL = (
    f"{PROTOTYPE_API_PROTO}{PROTOTYPE_API_HOST}:{PROTOTYPE_API_PORT}"
)


def create_prototype(
    prototype: PrototypeCreate,
    database_prototype_name: str | None = None,
) -> Prototype:
    new_prototype = Prototype.objects.create(
        name=prototype.name,
        description=prototype.description,
        system=System.objects.get(pk=prototype.system),
        database_hash=prototype.database_hash,
        metadata=prototype.metadata,
    )

    data = {
        "id": str(new_prototype.id),
        "name": prototype.name,
        "system": str(prototype.system),
        "metadata": json.dumps(prototype.metadata),
    }

    if database_prototype_name:
        data["database_prototype_name"] = database_prototype_name

    response = requests.post(
        f"{PROTOTYPE_API_URL}/generate",
        json=data,
    )

    if response.status_code != 200:
        raise Exception("Failed to generate prototype " + prototype.name)

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
