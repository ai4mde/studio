from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Optional
import logging
from uuid import UUID

from app.core.auth import get_current_user
from app.models.user import User
from app.agents.modification import ModificationAgent
from app.schemas.agents import (
    ModificationRequest,
    ModificationAnalysisResponse,
    ModificationApplyRequest,
    ModificationApplyResponse,
    ModificationHistory,
    ModificationHistoryEntry
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/modification", tags=["modification"])

@router.post("/analyze", response_model=ModificationAnalysisResponse)
async def analyze_changes(
    *,
    request: ModificationRequest,
    current_user: User = Depends(get_current_user)
) -> ModificationAnalysisResponse:
    """Analyze requested changes to document and diagrams."""
    try:
        agent = ModificationAgent(str(UUID()), current_user.username)
        result = await agent.analyze_change_request(
            request=request.request,
            current_content=request.current_content
        )
        return ModificationAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"Error analyzing changes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze changes: {str(e)}"
        )

@router.post("/apply", response_model=ModificationApplyResponse)
async def apply_changes(
    *,
    request: ModificationApplyRequest,
    current_user: User = Depends(get_current_user)
) -> ModificationApplyResponse:
    """Apply suggested changes to document and diagrams."""
    try:
        agent = ModificationAgent(str(UUID()), current_user.username)
        result = await agent.apply_changes(
            suggestions=request.suggestions,
            current_content=request.current_content
        )
        return ModificationApplyResponse(**result)
    except Exception as e:
        logger.error(f"Error applying changes: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply changes: {str(e)}"
        )

@router.get("/history", response_model=ModificationHistory)
async def get_modification_history(
    current_user: User = Depends(get_current_user),
    document_id: Optional[str] = Query(None, description="Filter by document ID")
) -> ModificationHistory:
    """Get modification history, optionally filtered by document."""
    try:
        agent = ModificationAgent(str(UUID()), current_user.username)
        history = await agent.get_modification_history(document_id)
        return ModificationHistory(modifications=history)
    except Exception as e:
        logger.error(f"Error getting modification history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get modification history: {str(e)}"
        )

@router.get("/{modification_id}", response_model=ModificationHistoryEntry)
async def get_modification(
    modification_id: str,
    current_user: User = Depends(get_current_user)
) -> ModificationHistoryEntry:
    """Get details of a specific modification."""
    try:
        agent = ModificationAgent(str(UUID()), current_user.username)
        modification = await agent.get_modification(modification_id)
        return ModificationHistoryEntry(**modification)
    except Exception as e:
        logger.error(f"Error getting modification: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get modification: {str(e)}"
        ) 