from typing import List, Optional, Dict
from generator.api.schemas import ReadPrototype, CreatePrototype, UpdatePrototype
from generator.models import Prototype
from metadata.models import System
from ninja import Router
import json
import requests
import os

prototypes = Router()

PROTOTYPE_API_PROTO = os.environ.get('PROTOTYPE_API_PROTO', "http://")
PROTOTYPE_API_HOST = os.environ.get('PROTOTYPE_API_HOST', "studio-prototypes")
PROTOTYPE_API_PORT = os.environ.get('PROTOTYPE_API_PORT', 8010)
PROTOTYPE_API_URL = f"{PROTOTYPE_API_PROTO}{PROTOTYPE_API_HOST}:{PROTOTYPE_API_PORT}"


@prototypes.get("/", response=List[ReadPrototype])
def list_prototypes(request, system: Optional[str] = None):
    qs = None
    if system:
        qs = Prototype.objects.filter(system=system)
    else:
        qs = Prototype.objects.all()
    return qs


@prototypes.get("/{uuid:id}/meta/", response=Dict)
def read_prototype_meta(request, id):
    prototype = Prototype.objects.get(id=id)
    if not prototype:
        return 404, "Prototype not found"
    return prototype.metadata


@prototypes.get("/{str:database_hash}", response=List[ReadPrototype])
def list_prototypes_hash(request, database_hash):
    return Prototype.objects.filter(database_hash=database_hash)


@prototypes.get("/{uuid:id}/", response=ReadPrototype)
def read_prototype(request, id):
    return Prototype.objects.get(id=id)


@prototypes.post("/", response=ReadPrototype)
def create_prototype(request, prototype: CreatePrototype, database_prototype_name: Optional[str]):
    GENERATION_URL = f"{PROTOTYPE_API_URL}/generate"
    data = {
        'prototype_name': prototype.name,
        'metadata': json.dumps(prototype.metadata)
    }
    if database_prototype_name and database_prototype_name != "":
        data['database_prototype_name'] = database_prototype_name
    response = requests.post(GENERATION_URL, json=data)

    if response.status_code != 200:
        raise Exception("Failed to generate prototype " + prototype.name)

    new_prototype = Prototype.objects.create(
        name=prototype.name,
        description=prototype.description,
        system=System.objects.get(pk=prototype.system),
        database_hash=prototype.database_hash,
        metadata=prototype.metadata # TODO: maybe we do not want to push all metadata to the DB?
    )
    return new_prototype


@prototypes.delete("/{uuid:id}/", response=bool)
def delete_prototype(request, id):
    DELETION_URL = f"{PROTOTYPE_API_URL}/remove"
    prototype = Prototype.objects.filter(id=id).first()
    if not prototype:
        return False

    data = {
        'prototype_name': prototype.name,
    }

    response = requests.delete(DELETION_URL, json=data)
    if response.status_code != 200:
        raise Exception("Failed to delete prototype " + prototype.name)
    prototype.delete()
    return True


@prototypes.delete("/system/{uuid:system_id}/", response=bool)
def delete_system_prototypes(request, system_id):
    DELETION_URL = f"{PROTOTYPE_API_URL}/remove"

    prototypes = Prototype.objects.filter(system=System.objects.get(pk=system_id))
    if not prototypes:
        return False
    
    for prototype in prototypes:
        data = {
            'prototype_name': prototype.name,
        }
        response = requests.delete(DELETION_URL, json=data)
        if response.status_code != 200:
            raise Exception("Failed to delete prototype " + prototype.name)
        prototype.delete()
    return True


@prototypes.put("/{uuid:id}/", response=bool)
def update_prototype(request, id, prototype: UpdatePrototype):
    try: 
        Prototype.objects.filter(id=id).update(name=prototype.name,
                                               description=prototype.description,
                                               system=prototype.system,
                                               running=prototype.running)
    except Prototype.DoesNotExist:
        return False
    return True


@prototypes.post("/stop_prototypes/", response=bool)
def stop_prototypes(request):
    STOP_URL = f"{PROTOTYPE_API_URL}/stop_prototypes"
    try:
        response = requests.post(STOP_URL)
    except:
        return False
    
    if response.status_code == 200:
        return True
    return False


@prototypes.post("/run/{str:prototype_name}", response=bool)
def run_prototype(request, prototype_name):
    RUN_URL = f"{PROTOTYPE_API_URL}/run/{prototype_name}"
    try:
        response = requests.post(RUN_URL)
    except:
        return False
    
    if response.status_code in [200, 307]:
        return True
    return False


@prototypes.get("/active_prototype/")
def get_active_prototype(request):
    STATUS_URL = f"{PROTOTYPE_API_URL}/active_prototype"
    response = requests.get(STATUS_URL)
    return response.json()


__all__ = ["prototypes"]
