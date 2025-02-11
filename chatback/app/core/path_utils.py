import os
import re
from typing import Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def sanitize_path_component(component: str) -> str:
    """
    Sanitize a path component (username, filename, etc).
    
    Args:
        component: String to sanitize
        
    Returns:
        Sanitized string safe for filesystem use
    """
    # Remove any non-alphanumeric chars except dash and underscore
    sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '_', component.lower())
    # Remove consecutive underscores/dashes
    sanitized = re.sub(r'[_\-]{2,}', '_', sanitized)
    # Remove leading/trailing underscores/dashes
    return sanitized.strip('_-')

def validate_path(path: str, base_path: str) -> Optional[str]:
    """
    Validate a path is safe and within allowed base path.
    
    Args:
        path: Path to validate
        base_path: Base path that should contain the path
        
    Returns:
        Validated absolute path or None if invalid
    """
    try:
        # Convert to absolute path
        abs_path = os.path.abspath(path)
        abs_base = os.path.abspath(base_path)
        
        # Check if path is within base path
        if not abs_path.startswith(abs_base):
            logger.error(f"Path {path} is outside base path {base_path}")
            return None
            
        return abs_path
        
    except Exception as e:
        logger.error(f"Path validation error: {str(e)}")
        return None

def ensure_path(path: str) -> bool:
    """
    Ensure a path exists, creating it if necessary.
    
    Args:
        path: Path to ensure exists
        
    Returns:
        True if path exists/created, False on error
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create path {path}: {str(e)}")
        return False 