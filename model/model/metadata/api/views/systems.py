from ninja import Router
from typing import List
from metadata.models import System
from metadata.api.schemas import system as schema

systems = Router()

@systems.get('/', response=List[schema.ReadSystem])
def list_systems(request, project):
    qs = System.objects.all()
    return qs

__all__ = [
    'systems'
]