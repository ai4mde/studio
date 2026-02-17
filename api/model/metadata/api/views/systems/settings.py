from ninja import Router, Schema
from django.http import HttpRequest
from typing import Dict, Any

from metadata.models import System

settings = Router()


class ClassifierColor(Schema):
    background_hex: str
    text_hex: str


class SystemSettingsResponse(Schema):
    classifier_colors: Dict[str, ClassifierColor]


class UpdateSystemSettingsPayload(Schema):
    classifier_colors: Dict[str, ClassifierColor]


@settings.get("/", response=SystemSettingsResponse)
def get_system_settings(request: HttpRequest):
    """Get the system settings including classifier colors."""
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)
    
    if not system:
        return 404, "System not found"
    
    colors = system.get_default_colors()
    return {"classifier_colors": colors}


@settings.put("/", response=SystemSettingsResponse)
def update_system_settings(request: HttpRequest, payload: UpdateSystemSettingsPayload):
    """Update the system settings including classifier colors."""
    if not request.resolver_match:
        return 500, "Resolver match not found"

    system_id = request.resolver_match.kwargs.get("system_id")
    system = System.objects.get(id=system_id)
    
    if not system:
        return 404, "System not found"
    
    # Update settings with new classifier colors
    if system.settings is None:
        system.settings = {}
    
    colors_dict = {}
    for color_type, color in payload.classifier_colors.items():
        colors_dict[color_type] = {
            'background_hex': color.get('background_hex') if isinstance(color, dict) else color.background_hex,
            'text_hex': color.get('text_hex') if isinstance(color, dict) else color.text_hex,
        }
    
    system.settings['classifier_colors'] = colors_dict
    system.save()
    system.refresh_from_db()
    
    return {"classifier_colors": system.get_default_colors()}


__all__ = [
    "settings",
]
