from typing import List, Optional, Any, Dict

from django.shortcuts import get_object_or_404

from metadata.api.schemas import ReadRelease, ImportRelease, ExportRelease, ExportProject, CreateRelease
from metadata.api.views.utils.releases import serialize_interfaces, serialize_diagrams, load_interfaces, load_diagrams
from metadata.models import Release, Project
from ninja import Router, Schema
import json

releases = Router()


@releases.get("/project/{uuid:project_id}/", response=List[ReadRelease])
def list_releases(request, project_id):
    project = Project.objects.get(id=project_id)
    if not project:
        return 404, "Project not found"
    return Release.objects.filter(project=project).order_by('created_at')


@releases.get("/{uuid:release_id}", response=ReadRelease)
def read_release(request, release_id):
    release = Release.objects.get(id=release_id)
    if not release:
        return 404, "Release not found"
    return release


@releases.post("/", response=ReadRelease)
def create_release(request, payload: CreateRelease):
    project = get_object_or_404(Project, id=payload.project)
    project_schema = ExportProject.model_validate(project)

    return Release.objects.create(
        name=payload.name,
        project=project,
        project_data=project_schema.model_dump(mode="json"),
        release_notes=payload.release_notes,
    )


@releases.post("/{uuid:release_id}/load/")
def load_release(request, release_id):
    release = get_object_or_404(Release, id=release_id)
    
    if not release.project_data:
        return 404, "Release does not contain project data"

    try:
        Project.import_from_json(release.project_data)
    except Exception as e:
        return 422, f"Failed to import project data: {e}"
    return 200, "Release loaded successfully"


@releases.post("/import/{uuid:project_id}")
def import_release(request, project_id: str, payload: ImportRelease):
    if not payload.name:
        return 422

    if payload.project != project_id:
        return 422, "Project ID in payload does not match URL"

    Release.objects.create(
        name=payload.name,
        project_id=project_id,
        project_data=payload.project_data.dict(),
        release_notes=payload.release_notes or [],
    )

    return 200, "Release imported successfully"

@releases.get("/{uuid:release_id}/export/", response=ExportRelease)
def export_release(request, release_id):
    release = get_object_or_404(Release, id=release_id)
    if not release.project_data:
        return 404, "Release does not contain project data"
    
    return release

@releases.delete("/{uuid:release_id}/")
def delete_release(request, release_id):
    try:
        release = Release.objects.get(id=release_id)
        release.delete()
    except Exception as e:
        return 422, f"Failed to delete release: {e}"
    return 200, "Release deleted successfully"
    

__all__ = ["releases"]
