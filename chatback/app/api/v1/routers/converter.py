from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import logging
from uuid import UUID

from app.core.auth import get_current_user
from app.models.user import User
from app.agents.converter import UMLConverterAgent
from app.schemas.agents import (
    ConverterRequest,
    ConverterResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/converter", tags=["converter"])

@router.post("/uml-to-json", response_model=ConverterResponse)
async def convert_uml_to_json(
    *,
    request: ConverterRequest,
    current_user: User = Depends(get_current_user)
) -> ConverterResponse:
    """Convert PlantUML to JSON format."""
    try:
        agent = UMLConverterAgent(str(UUID()), current_user.username)
        result = await agent.convert_uml_to_json(
            plantuml_code=request.plantuml_code,
            diagram_type=request.diagram_type
        )
        return ConverterResponse(**result)
    except Exception as e:
        logger.error(f"Error converting UML: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to convert UML: {str(e)}"
        ) 