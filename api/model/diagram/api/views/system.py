from typing import List

from django.http import HttpRequest
from metadata.models import System
from ninja import Router

from diagram.api.schemas.diagram import FullDiagram
from diagram.models import Diagram

system = Router()

@system.get("/{uuid:system_id}/", response=List[FullDiagram])
def get_diagrams(request: HttpRequest, system_id: str):
    system = System.objects.get(id=system_id)
    if system == None:
        return 405, "Failed to resolve system."
    return Diagram.objects.filter(system=system)

__all__= ["system"]