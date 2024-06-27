from typing import List, Optional

from metadata.api.schemas import CreateInterface, ReadInterface, UpdateInterface
from metadata.models import System, Interface
from django.http import HttpRequest

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
    )


@interfaces.put("/{uuid:id}/", response=ReadInterface)
def update_interface(request, id, payload: UpdateInterface):
    print(payload)
    return None

@interfaces.delete("/{uuid:interface_id}", response=bool)
def delete_interface(request, interface_id):
    try:
        Interface.objects.filter(id=interface_id).delete()
    except Interface.DoesNotExist:
        return False
    return True



__all__ = ["interfaces"]
