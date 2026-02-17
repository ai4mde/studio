"""Utility functions for the metadata app."""

from typing import Dict, Any, Optional


DEFAULT_CLASSIFIER_COLORS = {
    'c4container': {
        'background_hex': '#438DD5',
        'text_hex': '#FFFFFF'
    },
    'c4component': {
        'background_hex': '#85BBF0',
        'text_hex': '#FFFFFF'
    }
}

DEFAULT_FALLBACK_COLORS = {
    'background_hex': '#FFFFFF',
    'text_hex': '#000000'
}


def get_default_colors(settings: Dict[str, Any] | None) -> Dict[str, Any]:
    """
    Get default classifier colors from system settings.
    
    Args:
        settings: The system settings dictionary (can be None or empty)
        
    Returns:
        Dictionary with classifier color definitions
    """
    if not settings:
        return DEFAULT_CLASSIFIER_COLORS
    
    return settings.get('classifier_colors', DEFAULT_CLASSIFIER_COLORS)


def get_classifier_colors(settings: Dict[str, Any] | None, classifier_type: str) -> Dict[str, str]:
    """
    Get colors for a specific classifier type.
    
    Uses black background and white text as fallback for unknown types.
    
    Args:
        settings: The system settings dictionary (can be None or empty)
        classifier_type: The classifier type to get colors for
        
    Returns:
        Dictionary with 'background_hex' and 'text_hex' keys
    """
    colors = get_default_colors(settings)
    return colors.get(classifier_type, DEFAULT_FALLBACK_COLORS)


def get_classifier_background_color(settings: Dict[str, Any] | None, classifier_type: str) -> str:
    """
    Get the background color hex for a specific classifier type.
    
    Args:
        settings: The system settings dictionary (can be None or empty)
        classifier_type: The classifier type to get the color for
        
    Returns:
        Hex color string (defaults to black for unknown types)
    """
    colors = get_classifier_colors(settings, classifier_type)
    return colors.get('background_hex', DEFAULT_FALLBACK_COLORS['background_hex'])


def get_classifier_text_color(settings: Dict[str, Any] | None, classifier_type: str) -> str:
    """
    Get the text color hex for a specific classifier type.
    
    Args:
        settings: The system settings dictionary (can be None or empty)
        classifier_type: The classifier type to get the color for
        
    Returns:
        Hex color string (defaults to white for unknown types)
    """
    colors = get_classifier_colors(settings, classifier_type)
    return colors.get('text_hex', DEFAULT_FALLBACK_COLORS['text_hex'])


__all__ = [
    'get_default_colors',
    'get_classifier_colors',
    'get_classifier_background_color',
    'get_classifier_text_color',
    'DEFAULT_CLASSIFIER_COLORS',
    'DEFAULT_FALLBACK_COLORS',
]
