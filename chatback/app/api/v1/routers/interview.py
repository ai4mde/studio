from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import logging
from uuid import UUID

from app.core.auth import get_current_user
from app.models.user import User
from app.agents.interview import InterviewAgent
from app.schemas.agents import (
    InterviewResponse,
    InterviewSession,
    InterviewSessionList,
    DeleteResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/interview", tags=["interview"])

@router.post("/start", response_model=InterviewResponse)
async def start_interview(
    *,
    current_user: User = Depends(get_current_user)
) -> InterviewResponse:
    """Start a new interview session."""
    try:
        agent = InterviewAgent(str(UUID()), current_user.username)
        response = await agent.process_message("Hello")
        return InterviewResponse(message=response, session_id=agent.session_id)
    except Exception as e:
        logger.error(f"Error starting interview: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {str(e)}"
        )

@router.post("/{session_id}/message", response_model=InterviewResponse)
async def process_interview_message(
    *,
    session_id: str,
    message: str,
    current_user: User = Depends(get_current_user)
) -> InterviewResponse:
    """Process a message in an existing interview session."""
    try:
        agent = InterviewAgent(session_id, current_user.username)
        response = await agent.process_message(message)
        return InterviewResponse(message=response)
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )

@router.get("/sessions", response_model=InterviewSessionList)
async def list_interview_sessions(
    current_user: User = Depends(get_current_user)
) -> InterviewSessionList:
    """List all interview sessions for the current user."""
    try:
        agent = InterviewAgent(str(UUID()), current_user.username)
        sessions = await agent.list_sessions()
        return InterviewSessionList(sessions=sessions)
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sessions: {str(e)}"
        )

@router.get("/{session_id}", response_model=InterviewSession)
async def get_interview_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> InterviewSession:
    """Get details of a specific interview session."""
    try:
        agent = InterviewAgent(session_id, current_user.username)
        session_data = await agent.get_session_data()
        return InterviewSession(**session_data)
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )

@router.delete("/{session_id}", response_model=DeleteResponse)
async def delete_interview_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
) -> DeleteResponse:
    """Delete a specific interview session."""
    try:
        agent = InterviewAgent(session_id, current_user.username)
        await agent.delete_session()
        return DeleteResponse(message="Session deleted successfully", id=session_id)
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        ) 