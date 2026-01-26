from typing import List, Optional, Any, Dict

from metadata.api.schemas import ReadRelease, UpdateRelease
from metadata.api.views.utils.releases import serialize_interfaces, serialize_diagrams, load_interfaces, load_diagrams
from metadata.models import Release, System
from ninja import Router, Schema
import json

releases = Router()

class ImportReleaseBody(Schema):
    diagrams: List[Dict[str, Any]]
    interfaces: List[Dict[str, Any]]
    useAuthentication: Optional[bool] = None
    release_notes: Optional[List[str]] = None


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
def create_release(request, system_id: str, name: str, release_notes: Optional[str] = None):
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
        release_notes=json.loads(release_notes or ""),
        interfaces=serialized_interfaces,
    )


@releases.post("/{uuid:release_id}/load/")
def load_release(request, release_id, system_id: str | None = None):
    release = Release.objects.filter(id=release_id).first()
    if not release:
        return 404, "Release not found"
    
    target_system = (
        System.objects.filter(id=system_id).first()
        if system_id
        else release.system
    )
    if not target_system:
        return 404, "System not found"
    
    if not load_diagrams(system=target_system, release=release):
        return 422
    
    if not load_interfaces(system=target_system, release=release):
        return 422
    
    return 200
    
    
@releases.post("/import", response=ReadRelease)
def import_release(request, system_id: str, name: str, payload: ImportReleaseBody):
    system = System.objects.filter(id=system_id).first()
    if not system:
        return 404, "System not found"
    if not name:
        return 422, "Name is required"
    
    release = Release.objects.create(
        name=name,
        project=system.project,
        system=system,
        diagrams=payload.diagrams,
        metadata={},
        release_notes=payload.release_notes or [],
        interfaces=payload.interfaces,
    )
    return release



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
