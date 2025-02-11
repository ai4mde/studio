from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import logging
from uuid import UUID

from app.core.auth import get_current_user
from app.models.user import User
from app.agents.diagram import DiagramAgent
from app.schemas.agents import (
    DiagramRequest,
    DiagramResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/diagram", tags=["diagram"])

@router.post("/generate", response_model=DiagramResponse)
async def generate_diagrams(
    *,
    request: DiagramRequest,
    current_user: User = Depends(get_current_user)
) -> DiagramResponse:
    """Generate UML diagrams from conversation."""
    try:
        agent = DiagramAgent(str(UUID()), current_user.username)
        result = await agent.generate_uml_diagrams(request.messages)
        return DiagramResponse(**result)
    except Exception as e:
        logger.error(f"Error generating diagrams: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate diagrams: {str(e)}"
        ) 