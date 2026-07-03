from ninja import Router
from django.http import HttpRequest
from typing import List

from metadata.models import System

from diagram.schemas.diagram import FullDiagram
from diagram.models.diagram import Diagram

system = Router()

@system.get("/{uuid:system_id}/", response=List[FullDiagram])
def get_diagrams(request: HttpRequest, system_id: str):
    system = System.objects.get(id=system_id)
    if system == None:
        return 405, "Failed to resolve system."
    return Diagram.objects.filter(system=system)
