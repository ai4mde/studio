from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Optional
import logging
from uuid import UUID

from app.core.auth import get_current_user
from app.models.user import User
from app.agents.review import ReviewAgent
from app.schemas.agents import (
    ReviewRequest,
    ReviewResponse,
    ReviewHistory,
    ReviewHistoryEntry
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/review", tags=["review"])

@router.post("/document", response_model=ReviewResponse)
async def review_document(
    *,
    request: ReviewRequest,
    current_user: User = Depends(get_current_user)
) -> ReviewResponse:
    """Review SRS document and UML diagrams."""
    try:
        agent = ReviewAgent(str(UUID()), current_user.username)
        result = await agent.review_document(
            document_content=request.document_content,
            uml_diagrams=request.uml_diagrams
        )
        return ReviewResponse(**result)
    except Exception as e:
        logger.error(f"Error reviewing document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review document: {str(e)}"
        )

@router.get("/history", response_model=ReviewHistory)
async def get_review_history(
    current_user: User = Depends(get_current_user),
    document_id: Optional[str] = Query(None, description="Filter by document ID")
) -> ReviewHistory:
    """Get review history, optionally filtered by document."""
    try:
        agent = ReviewAgent(str(UUID()), current_user.username)
        history = await agent.get_review_history(document_id)
        return ReviewHistory(reviews=history)
    except Exception as e:
        logger.error(f"Error getting review history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review history: {str(e)}"
        )

@router.get("/{review_id}", response_model=ReviewHistoryEntry)
async def get_review(
    review_id: str,
    current_user: User = Depends(get_current_user)
) -> ReviewHistoryEntry:
    """Get a specific review's details."""
    try:
        agent = ReviewAgent(str(UUID()), current_user.username)
        review = await agent.get_review(review_id)
        return ReviewHistoryEntry(**review)
    except Exception as e:
        logger.error(f"Error getting review: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review: {str(e)}"
        ) 