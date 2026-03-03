from ninja import Router, Schema
from django.http import HttpRequest
from typing import Dict

from metadata.models import Project

settings = Router()


class ClassifierColor(Schema):
    background_hex: str
    text_hex: str


class ProjectSettingsResponse(Schema):
    classifier_colors: Dict[str, ClassifierColor]


class UpdateProjectSettingsPayload(Schema):
    classifier_colors: Dict[str, ClassifierColor]


@settings.get("/", response=ProjectSettingsResponse)
def get_project_settings(request: HttpRequest):
    """Get the project settings including classifier colors."""
    if not request.resolver_match:
        return 500, "Resolver match not found"

    project_id = request.resolver_match.kwargs.get("project_id")
    project = Project.objects.get(id=project_id)
    
    if not project:
        return 404, "Project not found"
    
    colors = project.get_default_colors()
    return {"classifier_colors": colors}


@settings.put("/", response=ProjectSettingsResponse)
def update_project_settings(request: HttpRequest, payload: UpdateProjectSettingsPayload):
    """Update the project settings including classifier colors."""
    if not request.resolver_match:
        return 500, "Resolver match not found"

    project_id = request.resolver_match.kwargs.get("project_id")
    project = Project.objects.get(id=project_id)
    
    if not project:
        return 404, "Project not found"
    
    # Update settings with new classifier colors
    if project.settings is None:
        project.settings = {}
    
    colors_dict = {}
    for color_type, color in payload.classifier_colors.items():
        colors_dict[color_type] = {
            'background_hex': color.get('background_hex') if isinstance(color, dict) else color.background_hex,
            'text_hex': color.get('text_hex') if isinstance(color, dict) else color.text_hex,
        }
    
    project.settings['classifier_colors'] = colors_dict
    project.save()
    project.refresh_from_db()
    
    return {"classifier_colors": project.get_default_colors()}


__all__ = [
    "settings",
]
