from typing import List, Optional
from generator.api.schemas import ReadPrototype, CreatePrototype, UpdatePrototype
from generator.models import Prototype
from metadata.models import System
from ninja import Router
import json
import requests

prototypes = Router()


@prototypes.get("/", response=List[ReadPrototype])
def list_prototypes(request, system: Optional[str] = None):
    qs = None
    if system:
        qs = Prototype.objects.filter(system=system)
    else:
        qs = Prototype.objects.all()
    return qs


@prototypes.get("/{str:database_hash}", response=List[ReadPrototype])
def list_prototypes_hash(request, database_hash):
    return Prototype.objects.filter(database_hash=database_hash)


@prototypes.get("/{uuid:id}/", response=ReadPrototype)
def read_prototype(request, id):
    return Prototype.objects.get(id=id)


@prototypes.post("/", response=ReadPrototype)
def create_prototype(request, prototype: CreatePrototype, database_prototype_name: Optional[str]):
    GENERATION_URL = "http://studio-prototypes:8010/generate" # TODO: put this in env
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
        metadata={} # TODO: maybe we do not want to push all metadata to the DB?
    )
    return new_prototype


@prototypes.delete("/{uuid:prototype_id}", response=bool)
def delete_prototype(request, prototype_id):
    DELETION_URL = "http://studio-prototypes:8010/remove" # TODO: put this in env
    prototype = Prototype.objects.filter(id=prototype_id).first()
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


@prototypes.delete("/system/{uuid:system_id}", response=bool)
def delete_system_prototypes(request, system_id):
    DELETION_URL = "http://studio-prototypes:8010/remove" # TODO: put this in env

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


@prototypes.get("/status/{str:prototype_name}")
def get_prototype_status(request, prototype_name):
    STATUS_URL = f"http://studio-prototypes:8010/status/{prototype_name}" # TODO: put this in env
    response = requests.get(STATUS_URL)
    return response.json()


@prototypes.post("/stop/{str:prototype_name}", response=bool)
def stop_prototype(request, prototype_name):
    STOP_URL = f"http://studio-prototypes:8010/stop/{prototype_name}" # TODO: put this in env
    try:
        response = requests.post(STOP_URL)
    except:
        return False
    
    if response.status_code == 200:
        return True
    return False


@prototypes.post("/run/{str:prototype_name}", response=bool)
def run_prototype(request, prototype_name):
    RUN_URL = f"http://studio-prototypes:8010/run/{prototype_name}" # TODO: put this in env
    try:
        response = requests.post(RUN_URL)
    except:
        return False
    
    if response.status_code in [200, 307]:
        return True
    return False

__all__ = ["prototypes"]
