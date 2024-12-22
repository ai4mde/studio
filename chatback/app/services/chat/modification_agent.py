from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from typing import Dict, List, Optional
import logging
from langchain_community.chat_message_histories import RedisChatMessageHistory
import json
import os
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ModificationError(Exception):
    """Base exception for modification-related errors."""
    pass

class ModificationAgent:
    """Agent responsible for handling document and diagram modifications."""
    
    def __init__(self, session_id: str, username: str):
        try:
            logger.info(f"Initializing ModificationAgent for session {session_id}")
            self.session_id = session_id
            self.username = username
            
            # Get agent name from settings
            self.agent_name = settings.AGENT_WHITE_NAME
            
            # Initialize LLM for handling modifications
            self.llm = ChatOpenAI(
                model_name=settings.AGENT_WHITE_MODEL,
                temperature=settings.AGENT_WHITE_TEMPERATURE,
                api_key=settings.OPENAI_API_KEY,
                request_timeout=settings.OPENAI_TIMEOUT,
                max_retries=settings.OPENAI_MAX_RETRIES
            )
            
            # Setup Redis client
            redis_url = (
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
                f"?socket_timeout={settings.REDIS_TIMEOUT}"
                f"&socket_connect_timeout={settings.REDIS_TIMEOUT}"
            )
            
            # Initialize Redis client
            self.message_history = RedisChatMessageHistory(
                session_id=f"modification_{session_id}",
                url=redis_url,
                key_prefix="modification:",
                ttl=settings.REDIS_DATA_TTL
            )
            
            logger.info(f"{self.agent_name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_name}: {str(e)}", exc_info=True)
            if isinstance(e, (ValueError, IOError)):
                raise
            raise ModificationError(f"Failed to initialize modification agent: {str(e)}") from e

    async def analyze_change_request(self, request: str, current_content: Dict) -> Dict:
        """Analyze user's change request and determine required modifications."""
        try:
            if not request:
                logger.error("Empty change request provided")
                raise ValueError("Change request cannot be empty")
            
            if not current_content:
                logger.error("No current content provided for analysis")
                raise ValueError("Current content is required for analysis")
            
            # Validate current content structure
            required_keys = ["srs", "diagrams"]
            missing_keys = [key for key in required_keys if key not in current_content]
            if missing_keys:
                logger.error(f"Missing required content keys: {missing_keys}")
                raise ValueError(f"Current content missing required sections: {', '.join(missing_keys)}")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, the modification specialist.
                Analyze the user's change request and determine:
                1. What needs to be modified (SRS sections, UML diagrams, or both)
                2. The specific changes required
                3. Impact analysis of the changes
                4. Dependencies between document and diagrams
                
                Provide a structured analysis of the required changes."""),
                ("human", f"""Current content: {json.dumps(current_content)}
                
                Change request: {request}
                
                Analyze the changes needed.""")
            ])
            
            chain = prompt | self.llm
            response = await chain.ainvoke({})
            
            if not response.content:
                logger.error("Empty analysis response received")
                raise ModificationError("Failed to generate modification analysis")
            
            return {
                "analysis": response.content,
                "message": f"Change request analyzed. - {self.agent_name}"
            }
        except Exception as e:
            logger.error(f"Error analyzing change request: {str(e)}", exc_info=True)
            if isinstance(e, (ValueError, ModificationError)):
                raise
            raise ModificationError(f"Failed to analyze change request: {str(e)}") from e

    async def apply_changes(self, suggestions: Dict, current_content: Dict) -> Dict:
        """Apply approved changes to documents and diagrams."""
        try:
            if not suggestions:
                raise ValueError("No modification suggestions provided")
            
            if not current_content:
                raise ValueError("No current content provided")
            
            # Validate content structure
            for key in ["srs", "diagrams"]:
                if key not in current_content:
                    raise ValueError(f"Missing required content section: {key}")
            
            # Apply changes to SRS document
            updated_srs = await self._modify_srs(suggestions, current_content["srs"])
            
            # Apply changes to UML diagrams
            updated_diagrams = await self._modify_diagrams(suggestions, current_content["diagrams"])
            
            if not updated_srs or not updated_diagrams:
                raise ModificationError("Failed to apply all modifications")
            
            return {
                "updated_content": {
                    "srs": updated_srs,
                    "diagrams": updated_diagrams
                },
                "message": f"Changes have been applied successfully. - {self.agent_name}"
            }
            
        except Exception as e:
            logger.error(f"Error applying changes: {str(e)}", exc_info=True)
            if isinstance(e, (ValueError, ModificationError)):
                raise
            raise ModificationError(f"Failed to apply changes: {str(e)}") from e

    async def _modify_srs(self, suggestions: Dict, current_srs: str) -> str:
        """Apply modifications to SRS document."""
        try:
            if not suggestions or not current_srs:
                raise ValueError("Missing required modification data")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, applying changes to the SRS document.
                Modify the document according to the suggested changes.
                Maintain document structure and formatting.
                Return the complete updated document."""),
                ("human", f"""Current SRS: {current_srs}
                
                Suggested changes: {json.dumps(suggestions)}
                
                Apply these changes and return the updated document.""")
            ])
            
            chain = prompt | self.llm
            response = await chain.ainvoke({})
            
            if not response.content:
                raise ModificationError("Failed to generate modified SRS content")
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error modifying SRS: {str(e)}", exc_info=True)
            if isinstance(e, (ValueError, ModificationError)):
                raise
            raise ModificationError(f"Failed to modify SRS: {str(e)}") from e

    async def _modify_diagrams(self, suggestions: Dict, current_diagrams: Dict) -> Dict:
        """Apply modifications to UML diagrams."""
        try:
            if not suggestions or not current_diagrams:
                raise ValueError("Missing required diagram modification data")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, applying changes to UML diagrams.
                Modify the PlantUML code according to the suggested changes.
                Maintain diagram consistency and relationships.
                Return the updated PlantUML code for each modified diagram."""),
                ("human", f"""Current diagrams: {json.dumps(current_diagrams)}
                
                Suggested changes: {json.dumps(suggestions)}
                
                Apply these changes and return the updated diagrams.""")
            ])
            
            chain = prompt | self.llm
            response = await chain.ainvoke({})
            
            try:
                modified_diagrams = json.loads(response.content)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid diagram modification result: {str(e)}")
                raise ModificationError("Failed to generate valid diagram modifications")
            
            # Validate diagram structure
            required_diagrams = ["class", "sequence", "usecase"]
            missing_diagrams = [d for d in required_diagrams if d not in modified_diagrams]
            if missing_diagrams:
                raise ModificationError(f"Missing required diagrams: {', '.join(missing_diagrams)}")
            
            return modified_diagrams
            
        except Exception as e:
            logger.error(f"Error modifying diagrams: {str(e)}", exc_info=True)
            if isinstance(e, (ValueError, ModificationError, json.JSONDecodeError)):
                raise
            raise ModificationError(f"Failed to modify diagrams: {str(e)}") from e
