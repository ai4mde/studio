from typing import Dict, List
import logging
import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage

from app.core.config import settings
from app.agents.base import BaseAgent
from .utils import load_srs_template, ensure_srs_directory, sanitize_filename

logger = logging.getLogger(__name__)

class SRSDocumentAgent(BaseAgent):
    """Agent responsible for generating Software Requirements Specification documents."""
    
    def __init__(self, session_id: str, username: str):
        super().__init__(
            session_id=session_id,
            username=username,
            agent_name=settings.AGENT_JONES_NAME,
            model_name=settings.AGENT_JONES_MODEL,
            temperature=settings.AGENT_JONES_TEMPERATURE,
            redis_prefix="document"
        )
        
        try:
            # Load SRS template
            self.srs_template = load_srs_template()
            
            # Ensure SRS directory exists
            self.srsdocs_dir = ensure_srs_directory(username)
            
            logger.info(f"{self.agent_name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_name}: {str(e)}", exc_info=True)
            if isinstance(e, (FileNotFoundError, PermissionError, ValueError)):
                raise
            raise RuntimeError(f"Failed to initialize SRS document agent: {str(e)}") from e

    async def generate_srs_document(self, chat_name: str, messages: List[BaseMessage], uml_diagrams: str) -> Dict:
        """Generate a Software Requirements Specification document."""
        try:
            logger.info(f"Generating SRS document for session {self.session_id}")
            
            # Sanitize chat name and generate filename
            safe_chat_name = sanitize_filename(chat_name)
            timestamp = str(int(time.time()))
            filename = f"{safe_chat_name}_{timestamp}.md"
            filepath = os.path.join(self.srsdocs_dir, filename)
            
            # Create prompt for SRS generation
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, a precise and methodical technical writer 
                specializing in Software Requirements Specifications. Your directive is to analyze 
                the provided interview conversation and create a detailed SRS document following 
                the IEEE 830 standard format.
                
                Important guidelines:
                1. Extract and organize requirements with mathematical precision
                2. Use clear, unambiguous language that leaves no room for interpretation
                3. Make each requirement specific, measurable, and testable
                4. Include both functional and non-functional requirements
                5. Maintain professional technical writing style
                6. Use proper requirement traceability format
                
                Format the output as a proper markdown document."""),
                ("human", "Please create an SRS document based on the following interview conversation: {conversation}")
            ])
            
            # Create and execute chain
            response = await self._invoke_llm(
                system_prompt=prompt.messages[0].content,
                user_prompt=prompt.messages[-1].content,
                variables={
                    "conversation": "\n".join([f"{msg.type}: {msg.content}" for msg in messages])
                }
            )
            
            # Replace template placeholders with generated content
            document_content = self.srs_template.format(
                chat_name=safe_chat_name,
                project_name=chat_name,
                introduction=response,
                uml_models=uml_diagrams
            )
            
            # Save document to file
            with open(filepath, 'w', encoding='utf-8') as f:
                try:
                    f.write(document_content)
                except IOError as e:
                    logger.error(f"Failed to write SRS document: {str(e)}")
                    raise IOError(f"Failed to save SRS document: {str(e)}")
            
            logger.info(f"SRS document saved to {filepath}")
            
            return {
                "message": f"The requirements have been documented with perfect precision. - {self.agent_name}",
                "file_path": filepath
            }
            
        except Exception as e:
            logger.error(f"Error generating SRS document: {str(e)}", exc_info=True)
            if isinstance(e, (FileNotFoundError, PermissionError, ValueError, IOError)):
                raise
            raise RuntimeError(f"Failed to generate SRS document: {str(e)}") from e