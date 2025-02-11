from .srs_document_agent import SRSDocumentAgent
from .diagram_agent import DiagramAgent
from typing import Dict
import logging
import os

logger = logging.getLogger(__name__)

class DocumentCoordinationError(Exception):
    """Base exception for document coordination errors."""
    pass

class DocumentCoordinator:
    def __init__(self, session_id: str, username: str):
        try:
            logger.info(f"Initializing DocumentCoordinator for session {session_id}")
            self.session_id = session_id
            self.username = username
            
            # Initialize agents with proper error handling
            try:
                self.srs_agent = SRSDocumentAgent(session_id, username)
                logger.info("SRS Document Agent initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize SRS Document Agent: {str(e)}")
                raise DocumentCoordinationError("Failed to initialize SRS agent") from e
            
            try:
                self.diagram_agent = DiagramAgent(session_id, username)
                logger.info("Diagram Agent initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Diagram Agent: {str(e)}")
                raise DocumentCoordinationError("Failed to initialize diagram agent") from e
            
            logger.info("Document Coordinator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Document Coordinator: {str(e)}")
            raise

    async def generate_complete_document(self, chat_name: str, messages: list) -> Dict:
        """Coordinate the generation of the complete SRS document with diagrams."""
        try:
            logger.info("Initiating document generation protocol")
            
            if not messages:
                logger.error("No messages provided for document generation")
                raise ValueError("Cannot generate document without conversation history")
            
            if not chat_name:
                logger.error("No chat name provided")
                raise ValueError("Chat name is required for document generation")
            
            # First, Agent Jackson creates the visualizations
            logger.info(f"Agent Jackson analyzing system structure")
            try:
                diagrams_result = await self.diagram_agent.generate_uml_diagrams(messages)
            except Exception as e:
                logger.error(f"Failed to generate UML diagrams: {str(e)}")
                raise DocumentCoordinationError("UML diagram generation failed") from e
            
            if not diagrams_result or "uml_diagrams" not in diagrams_result:
                logger.error("Invalid diagram generation result")
                raise DocumentCoordinationError("UML diagrams were not properly generated")
            
            # Then Agent Jones documents the specifications
            logger.info(f"Agent Jones documenting specifications")
            try:
                document_result = await self.srs_agent.generate_srs_document(
                    chat_name=chat_name,
                    messages=messages,
                    uml_diagrams=diagrams_result["uml_diagrams"]
                )
            except Exception as e:
                logger.error(f"Failed to generate SRS document: {str(e)}")
                raise DocumentCoordinationError("SRS document generation failed") from e
            
            if not document_result or "file_path" not in document_result:
                logger.error("Invalid SRS document generation result")
                raise DocumentCoordinationError("SRS document was not properly generated")
            
            # Validate the generated file exists
            if not os.path.exists(document_result["file_path"]):
                logger.error(f"Generated file not found: {document_result['file_path']}")
                raise DocumentCoordinationError("Generated document file is missing")
            
            return {
                "message": (
                    "System documentation protocol completed.\n"
                    f"{diagrams_result['message']}\n"
                    f"{document_result['message']}"
                ),
                "file_path": document_result["file_path"]
            }
            
        except Exception as e:
            logger.error(f"Error in document coordination: {str(e)}")
            if isinstance(e, (ValueError, DocumentCoordinationError)):
                raise
            raise DocumentCoordinationError(f"Document generation failed: {str(e)}") from e