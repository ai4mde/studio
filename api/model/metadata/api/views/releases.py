from typing import List

from metadata.api.schemas import ReadRelease, UpdateRelease
from metadata.api.views.utils.releases import serialize_interfaces, serialize_diagrams
from metadata.models import Release, System
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
    
    serialized_interfaces = serialize_interfaces(system=system)
    serialized_diagrams = serialize_diagrams(system=system)
    
    return Release.objects.create(
        name=name,
        project=system.project,
        system=system,
        diagrams=serialized_diagrams,
        metadata={},
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
