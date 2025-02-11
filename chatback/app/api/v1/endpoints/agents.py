from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Optional
import logging
from uuid import UUID

from app.core.auth import get_current_user
from app.models.user import User
from app.agents.interview import InterviewAgent
from app.agents.document import SRSDocumentAgent
from app.agents.review import ReviewAgent
from app.agents.converter import UMLConverterAgent
from app.agents.modification import ModificationAgent
from app.agents.diagram import DiagramAgent
from app.schemas.agents import (
    InterviewResponse,
    InterviewSession,
    InterviewSessionList,
    Document,
    DocumentList,
    DiagramRequest,
    DiagramResponse,
    DocumentRequest,
    DocumentResponse,
    ReviewRequest,
    ReviewResponse,
    ReviewHistory,
    ReviewHistoryEntry,
    ConverterRequest,
    ConverterResponse,
    ModificationRequest,
    ModificationHistory,
    ModificationHistoryEntry,
    ModificationAnalysisResponse,
    ModificationApplyRequest,
    ModificationApplyResponse,
    DeleteResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/interview/start", response_model=InterviewResponse)
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

@router.post("/interview/{session_id}/message", response_model=InterviewResponse)
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

@router.post("/diagram/generate", response_model=DiagramResponse)
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

@router.post("/document/generate", response_model=DocumentResponse)
async def generate_document(
    *,
    request: DocumentRequest,
    current_user: User = Depends(get_current_user)
) -> DocumentResponse:
    """Generate SRS document from conversation and diagrams."""
    try:
        agent = SRSDocumentAgent(str(UUID()), current_user.username)
        result = await agent.generate_srs_document(
            chat_name=request.chat_name,
            messages=request.messages,
            uml_diagrams=request.uml_diagrams
        )
        return DocumentResponse(**result)
    except Exception as e:
        logger.error(f"Error generating document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate document: {str(e)}"
        )

@router.post("/review/document", response_model=ReviewResponse)
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

@router.post("/converter/uml-to-json", response_model=ConverterResponse)
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

@router.post("/modification/analyze", response_model=ModificationAnalysisResponse)
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

@router.post("/modification/apply", response_model=ModificationApplyResponse)
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

@router.get("/interview/sessions", response_model=InterviewSessionList)
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

@router.get("/interview/{session_id}", response_model=InterviewSession)
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

@router.delete("/interview/{session_id}", response_model=DeleteResponse)
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

@router.get("/document/list", response_model=DocumentList)
async def list_documents(
    current_user: User = Depends(get_current_user)
) -> DocumentList:
    """List all generated documents for the current user."""
    try:
        agent = SRSDocumentAgent(str(UUID()), current_user.username)
        documents = await agent.list_documents()
        return DocumentList(documents=documents)
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )

@router.get("/document/{document_id}", response_model=Document)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
) -> Document:
    """Get a specific document's content."""
    try:
        agent = SRSDocumentAgent(str(UUID()), current_user.username)
        document = await agent.get_document(document_id)
        return Document(**document)
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )

@router.delete("/document/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
) -> DeleteResponse:
    """Delete a specific document."""
    try:
        agent = SRSDocumentAgent(str(UUID()), current_user.username)
        await agent.delete_document(document_id)
        return DeleteResponse(message="Document deleted successfully", id=document_id)
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )

@router.get("/review/history", response_model=ReviewHistory)
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

@router.get("/review/{review_id}", response_model=ReviewHistoryEntry)
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

@router.get("/modification/history", response_model=ModificationHistory)
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

@router.get("/modification/{modification_id}", response_model=ModificationHistoryEntry)
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