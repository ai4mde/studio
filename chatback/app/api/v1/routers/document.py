from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import logging
from uuid import UUID

from app.core.auth import get_current_user
from app.models.user import User
from app.agents.document import SRSDocumentAgent
from app.schemas.agents import (
    Document,
    DocumentList,
    DocumentRequest,
    DocumentResponse,
    DeleteResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/document", tags=["document"])

@router.post("/generate", response_model=DocumentResponse)
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

@router.get("/list", response_model=DocumentList)
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

@router.get("/{document_id}", response_model=Document)
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

@router.delete("/{document_id}", response_model=DeleteResponse)
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