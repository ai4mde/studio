from typing import List, Optional
from generator.api.schemas import ReadPrototype, CreatePrototype, UpdatePrototype
from generator.models import Prototype
from metadata.models import System
from ninja import Router
import subprocess
import json

prototypes = Router()


@prototypes.get("/", response=List[ReadPrototype])
def list_prototypes(request, system: Optional[str] = None):
    qs = None
    if system:
        qs = Prototype.objects.filter(system=system)
    else:
        qs = Prototype.objects.all()
    return qs


@prototypes.get("/{uuid:id}/", response=ReadPrototype)
def read_prototype(request, id):
    return Prototype.objects.get(id=id)


@prototypes.post("/", response=ReadPrototype)
def create_prototype(request, prototype: CreatePrototype):
    GENERATOR_PATH="/usr/src/model/generator/generation/generator.sh"
    port=0
    new_prototype = Prototype.objects.create(
        name=prototype.name,
        description=prototype.description,
        system=System.objects.get(pk=prototype.system),
        running=True,
        port=port,
        metadata={} # TODO: maybe we do not want to push all metadata to the DB?
    )
    subprocess.run([GENERATOR_PATH, prototype.name, json.dumps(prototype.metadata)], check=True)

    return new_prototype

@prototypes.delete("/{uuid:prototype_id}", response=bool)
def delete_prototype(request, prototype_id):
    REMOVER_PATH="/usr/src/model/generator/generation/remover.sh"
    try:
        prot = Prototype.objects.filter(id=prototype_id).first()
        subprocess.run([REMOVER_PATH, prot.name], check=True)
        prot.delete()
    except Prototype.DoesNotExist:
        return False
    return True

@prototypes.delete("/system/{uuid:system_id}", response=bool)
def delete_system_prototypes(request, system_id):
    REMOVER_PATH="/usr/src/model/generator/generation/remover.sh"
    try:
        prots = Prototype.objects.filter(system=System.objects.get(pk=system_id))
        for prot in prots:
            subprocess.run([REMOVER_PATH, prot.name], check=True)
        prots.delete()
    except:
        return False
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


__all__ = ["prototypes"]
