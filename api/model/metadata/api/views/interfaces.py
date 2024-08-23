from typing import List, Optional

from metadata.api.schemas import CreateInterface, ReadInterface, UpdateInterface
from metadata.models import System, Interface, Classifier
from django.http import HttpRequest
from metadata.api.views.defaulting import create_default_interface

from ninja import Router

interfaces = Router()


@interfaces.get("/", response=List[ReadInterface])
def list_interfaces(request, system: Optional[str] = None):
    qs = None
    if system:
        qs = Interface.objects.filter(system=system)
    else:
        qs = Interface.objects.all()
    return qs


@interfaces.get("/{uuid:id}/", response=ReadInterface)
def read_interface(request, id):
    return Interface.objects.get(id=id)


@interfaces.post("/", response=ReadInterface)
def create_interface(request, interface: CreateInterface):
    return Interface.objects.create(
        name=interface.name,
        description=interface.description,
        system=System.objects.get(pk=interface.system),
        actor=Classifier.objects.get(pk=interface.actor),
        data=interface.data
    )


@interfaces.post("/default", response=List[ReadInterface])
def create_default_interfaces(request, system_id: str):
    system = System.objects.get(pk=system_id)
    if not system:
        return []
    
    actors = system.classifiers.filter(data__type='actor')

    out = []
    for actor in actors:
        interface = create_default_interface(system, actor)
        out.append(interface)
    
    return out


@interfaces.put("/{uuid:id}/", response=bool)
def update_interface(request, id, interface: UpdateInterface):
    try: 
        Interface.objects.filter(id=id).update(name=interface.name,
                                               description=interface.description,
                                               system=interface.system, 
                                               data=interface.data)
    except Interface.DoesNotExist:
        return False
    return True


@interfaces.delete("/{uuid:interface_id}", response=bool)
def delete_interface(request, interface_id):
    try:
        Interface.objects.filter(id=interface_id).delete()
    except Interface.DoesNotExist:
        return False
    return True



__all__ = ["interfaces"]
