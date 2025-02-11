import os
from typing import Dict
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def load_srs_template() -> str:
    """Load and validate the SRS document template."""
    try:
        template_path = os.path.join(settings.TEMPLATES_PATH, "srsdoc_template.md")
        
        # Check if template exists
        if not os.path.exists(template_path):
            logger.error(f"SRS template file not found at: {template_path}")
            raise FileNotFoundError(
                f"Required SRS template file not found. "
                f"Please ensure it exists at {template_path}"
            )
        
        # Check if template is readable
        if not os.access(template_path, os.R_OK):
            logger.error(f"SRS template file is not readable: {template_path}")
            raise PermissionError(
                f"Cannot read SRS template file. "
                f"Please check file permissions at {template_path}"
            )
        
        with open(template_path, 'r', encoding='utf-8') as f:
            try:
                template_content = f.read()
            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode SRS template file: {str(e)}")
                raise ValueError(
                    f"SRS template file has invalid encoding. "
                    f"Please ensure it is UTF-8 encoded."
                )
        
        # Validate template content
        if not template_content.strip():
            logger.error("SRS template file is empty")
            raise ValueError("SRS template file is empty")
            
        return template_content
        
    except Exception as e:
        logger.error(f"Failed to load SRS template: {str(e)}", exc_info=True)
        if isinstance(e, (FileNotFoundError, PermissionError, ValueError)):
            raise
        raise RuntimeError(f"Failed to load SRS template: {str(e)}") from e

def ensure_srs_directory(username: str) -> str:
    """Ensure the SRS documents directory exists for the user."""
    try:
        srsdocs_dir = settings.get_user_srs_path(username)
        if not os.path.exists(srsdocs_dir):
            logger.info(f"Creating SRS documents directory: {srsdocs_dir}")
            os.makedirs(srsdocs_dir, exist_ok=True)
            
        # Verify write permissions
        if not os.access(srsdocs_dir, os.W_OK):
            logger.error(f"Cannot write to SRS directory: {srsdocs_dir}")
            raise PermissionError(
                f"Cannot write to SRS directory. "
                f"Please check permissions at {srsdocs_dir}"
            )
            
        return srsdocs_dir
        
    except Exception as e:
        logger.error(f"Failed to ensure SRS directory: {str(e)}", exc_info=True)
        if isinstance(e, (FileNotFoundError, PermissionError)):
            raise
        raise RuntimeError(f"Failed to ensure SRS directory: {str(e)}") from e

def sanitize_filename(name: str) -> str:
    """Sanitize a filename by replacing invalid characters."""
    # Replace spaces with hyphens and remove other invalid characters
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in name) 