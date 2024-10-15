from typing import List

from metadata.api.schemas import ReadRelease, UpdateRelease
from metadata.models import Release, System, Interface
from diagram.models import Diagram
from ninja import Router

releases = Router()


@releases.get("/system/{uuid:system_id}/", response=List[ReadRelease])
def list_releases(request, system_id):
    system = System.objects.get(id=system_id)
    if not system:
        return 404, "System not found"
    return Release.objects.filter(system=system).order_by('created_at')


@releases.get("/{uuid:release_id}", response=ReadRelease)
def read_release(request, release_id):
    release = Release.objects.get(id=release_id)
    if not release:
        return 404, "Release not found"
    return release


@releases.post("/", response=ReadRelease)
def create_release(request, system_id: str, name: str):
    system = System.objects.get(id=system_id)
    if not name:
        return 422
    if not system:
        return 404, "System not found"
    
    interfaces = Interface.objects.filter(system=system)
    serialized_interfaces = []
    for interface in interfaces:
        obj = {
            "id": str(interface.id),
            "name": str(interface.name),
            "description": str(interface.description),
            "system": str(system_id),
            "actor": str(interface.actor.id),
            "data": interface.data
        }
        serialized_interfaces.append(obj)
    
    diagrams = Diagram.objects.filter(system=system)
    serialized_diagrams = []
    for diagram in diagrams:
        obj = {
            "id": str(diagram.id),
            "project": str(system.project.id),
            "name": str(diagram.name),
            "description": str(diagram.description),
            "type": str(diagram.type),
            "system": str(system_id),
            "nodes": [], # TODO
            "edges": [], # TODO
        }
        serialized_diagrams.append(obj)
    
    return Release.objects.create(
        name=name,
        project=system.project,
        system=system,
        diagrams=serialized_diagrams, # TODO
        metadata={}, # TODO
        interfaces=serialized_interfaces,
    )
    


@releases.put("/{uuid:release_id}/", response=ReadRelease)
def update_release(request, release_id, payload: UpdateRelease):
    print(release_id)
    print(payload)
    return None


@releases.delete("/{uuid:release_id}")
def delete_release(request, release_id):
    try:
        release = Release.objects.get(id=release_id)
        release.delete()
    except Exception as e:
        raise Exception("Failed to delete release, error: " + e)
    return True
    

__all__ = ["releases"]
