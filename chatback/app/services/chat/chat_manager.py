from typing import List, Dict, Any, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from app.core.config import settings
from app.services.vector_store import QdrantManager
from app.services.chat.interview_agent import InterviewAgent
from app.services.chat.document_coordinator import DocumentCoordinator
from enum import Enum
import logging
import traceback
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ConversationState(Enum):
    INTERVIEW = "interview"
    DOCUMENT = "document"
    COMPLETED = "completed"

class ChatError(Exception):
    """Base class for chat-related errors"""
    pass

class ChatManagerError(ChatError):
    """Errors in the chat manager"""
    pass

class LangChainChatManager:
    def __init__(self, session_id: str, username: str):
        try:
            logger.info(f"Initializing LangChainChatManager for session {session_id}")
            if not session_id:
                raise ChatManagerError("Session ID cannot be empty")
                
            self.session_id = session_id
            self.username = username
            
            # The Architect - oversees the system
            self.manager_name = "The Architect"  
            
            # Initialize agents
            try:
                self.interview_agent = InterviewAgent(session_id, username)  # Agent Smith
                logger.info("Agent Smith initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Agent Smith: {str(e)}")
                raise ChatManagerError("Failed to initialize interview agent") from e
                
            try:
                self.document_coordinator = DocumentCoordinator(session_id, username)  # Coordinates Jones & Jackson
                logger.info("Documentation team initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Documentation team: {str(e)}")
                raise ChatManagerError("Failed to initialize documentation team") from e
            
            self.state = ConversationState.INTERVIEW
            self.user_responses = {}
            
            logger.info(f"{self.manager_name} initialized successfully")
            
        except ChatManagerError as e:
            logger.error(f"Chat manager initialization error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing {self.manager_name}: {str(e)}\n{traceback.format_exc()}")
            raise ChatManagerError(f"Failed to initialize chat manager: {str(e)}") from e

    async def _reset_system(self) -> str:
        """Reset the system state and clear message histories."""
        try:
            logger.info(f"{self.manager_name} initiating system reset for session {self.session_id}")
            
            # Clear message histories
            try:
                self.interview_agent.message_history.clear()
                self.document_coordinator.srs_agent.message_history.clear()
                self.document_coordinator.diagram_agent.message_history.clear()
            except Exception as e:
                logger.error(f"Error clearing message histories: {str(e)}")
                raise ChatManagerError("Failed to clear message histories") from e
            
            # Reset state
            self.state = ConversationState.INTERVIEW
            
            # Initialize new interview
            try:
                initial_response = await self.interview_agent.process_message("hello")
                return f"{self.manager_name}: System reset complete. Initiating new interview protocol...\n\n{initial_response}"
            except Exception as e:
                logger.error(f"Error starting new interview: {str(e)}")
                raise ChatManagerError("Failed to start new interview") from e
                
        except Exception as e:
            logger.error(f"Error in system reset: {str(e)}")
            raise

    async def process_message(self, content: str) -> str:
        """Process incoming messages and manage conversation flow."""
        try:
            logger.info(f"{self.manager_name} processing message for session {self.session_id} in state {self.state}")
            
            if not content:
                raise ChatManagerError("Message content cannot be empty")
            
            # Handle system reset
            if content.lower() == 'restart':
                return await self._reset_system()
            
            # Handle completed state
            if self.state == ConversationState.COMPLETED:
                return f"{self.manager_name}: The system specifications are complete. Type 'restart' to begin a new session."
            
            # Handle interview state
            if self.state == ConversationState.INTERVIEW:
                try:
                    response = await self.interview_agent.process_message(content)
                    
                    if "Goodbye!" in response:
                        return await self._handle_documentation_transition(response)
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"Error in interview process: {str(e)}")
                    raise ChatManagerError("Error during interview process") from e
            
            return f"{self.manager_name}: Error in the system. Type 'restart' to reinitialize the process."

        except ChatManagerError as e:
            logger.error(f"Chat processing error: {str(e)}")
            return f"{self.manager_name}: An error has occurred: {str(e)}. Type 'restart' to reinitialize the process."
        except Exception as e:
            logger.error(f"Unexpected error in message processing: {str(e)}\n{traceback.format_exc()}")
            return f"{self.manager_name}: A system error has occurred. Type 'restart' to reinitialize the process."

    async def _handle_documentation_transition(self, interview_response: str) -> str:
        """Handle transition from interview to documentation phase."""
        try:
            logger.info(f"{self.manager_name} transitioning to documentation phase")
            self.state = ConversationState.DOCUMENT
            
            transition_message = (
                f"\n\n{self.manager_name}: Subject interview protocol completed. "
                f"Analysis indicates sufficient data acquired.\n\n"
                f"Initiating documentation sequence...\n"
                f"[System]: Dispatching Agent Jackson for structural analysis...\n"
                f"[System]: Agent Jackson engaged - Constructing system visualization matrices...\n"
                f"[System]: Dispatching Agent Jones for specification compilation...\n"
                f"[System]: Agent Jones engaged - Documenting system parameters...\n"
                f"Please maintain connection while the agents process the data..."
            )
            
            messages = self.interview_agent.message_history.messages
            result = await self.document_coordinator.generate_complete_document(
                chat_name=self.session_id,
                messages=messages
            )
            
            completion_message = (
                f"{interview_response}\n"
                f"{transition_message}\n\n"
                f"[System]: Documentation sequence completed.\n"
                f"{result['message']}\n"
                f"{self.manager_name}: The specifications have been archived at: {result['file_path']}\n"
                f"Your cooperation in this process has been... optimal."
            )
            
            self.state = ConversationState.COMPLETED
            return completion_message
            
        except Exception as e:
            logger.error(f"Error in documentation transition: {str(e)}")
            self.state = ConversationState.INTERVIEW  # Revert on error
            return (
                f"{self.manager_name}: An anomaly has been detected in the documentation process. "
                "The system will need to be... recalibrated. Type 'restart' to reinitialize."
            )

    def get_conversation_state(self) -> Dict:
        """Return current conversation state information"""
        return {
            "manager": self.manager_name,
            "state": self.state.value,
            "current_agent": (
                self.interview_agent.agent_name if self.state == ConversationState.INTERVIEW 
                else "Documentation Team" if self.state == ConversationState.DOCUMENT 
                else None
            ),
            "user_responses": self.user_responses if hasattr(self, 'user_responses') else {}
        }
