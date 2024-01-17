from ninja import Router
from typing import List
from metadata.models import System
from metadata.api.schemas import ReadSystem, CreateSystem, UpdateSystem

systems = Router()

@systems.get('/', response=List[ReadSystem])
def list_systems(request, project):
    qs = System.objects.all()
    return qs

@systems.get('/{uuid:id}', response=ReadSystem)
def read_system(request, project, id):
    return System.objects.get(id=id)

@systems.post('/', response=ReadSystem)
def create_system(request, payload: CreateSystem):
    print(payload)
    pass

@systems.put('/{uuid:id}', response=ReadSystem)
def update_system(request, payload: UpdateSystem):
    print(payload)
    pass

@systems.delete('/{uuid:id}')
def delete_system(request, id):
    print(id)
    pass

__all__ = [
    'systems'
]