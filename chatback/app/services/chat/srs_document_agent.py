from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from app.core.config import settings
from typing import Dict
import logging
import os
import time

logger = logging.getLogger(__name__)

class SRSDocumentAgent:
    def __init__(self, session_id: str, username: str):
        try:
            logger.info(f"Initializing SRSDocumentAgent for session {session_id}")
            self.session_id = session_id
            self.username = username
            
            # Get agent name from settings
            self.agent_name = settings.AGENT_JONES_NAME
            
            # Initialize LLM for technical writing
            self.llm = ChatOpenAI(
                model_name=settings.AGENT_JONES_MODEL,
                temperature=settings.AGENT_JONES_TEMPERATURE,
                api_key=settings.OPENAI_API_KEY,
                request_timeout=settings.OPENAI_TIMEOUT,
                max_retries=settings.OPENAI_MAX_RETRIES
            )
            
            # Setup Redis memory
            redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
            self.message_history = RedisChatMessageHistory(
                session_id=f"document_{session_id}",
                url=redis_url
            )
            
            # Create user-specific SRS documents directory
            self.srsdocs_dir = settings.get_user_srs_path(username)
            if not os.path.exists(self.srsdocs_dir):
                logger.info(f"Creating SRS documents directory: {self.srsdocs_dir}")
            os.makedirs(self.srsdocs_dir, exist_ok=True)
            
            # Load SRS template
            self.srs_template_path = os.path.join(settings.TEMPLATES_PATH, "srsdoc_template.md")
            
            # Check if template exists
            if not os.path.exists(self.srs_template_path):
                logger.error(f"SRS template file not found at: {self.srs_template_path}")
                raise FileNotFoundError(
                    f"Required SRS template file not found. "
                    f"Please ensure it exists at {self.srs_template_path}"
                )
            
            # Check if template is readable
            if not os.access(self.srs_template_path, os.R_OK):
                logger.error(f"SRS template file is not readable: {self.srs_template_path}")
                raise PermissionError(
                    f"Cannot read SRS template file. "
                    f"Please check file permissions at {self.srs_template_path}"
                )
            
            with open(self.srs_template_path, 'r') as f:
                try:
                    self.srs_template = f.read()
                except UnicodeDecodeError as e:
                    logger.error(f"Failed to decode SRS template file: {str(e)}")
                    raise ValueError(
                        f"SRS template file has invalid encoding. "
                        f"Please ensure it is UTF-8 encoded."
                    )
            
            # Validate template content
            if not self.srs_template.strip():
                logger.error("SRS template file is empty")
                raise ValueError("SRS template file is empty")
            
            logger.info(f"{self.agent_name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_name}: {str(e)}", exc_info=True)
            if isinstance(e, (FileNotFoundError, PermissionError, ValueError)):
                raise
            raise RuntimeError(f"Failed to initialize SRS document agent: {str(e)}") from e

    async def generate_srs_document(self, chat_name: str, messages: list, uml_diagrams: str) -> Dict:
        """Generate a Software Requirements Specification document."""
        try:
            logger.info(f"Generating SRS document for session {self.session_id}")
            
            # Sanitize chat name (replace spaces with hyphens)
            safe_chat_name = chat_name.replace(' ', '-')
            
            # Generate filename with timestamp
            timestamp = str(int(time.time()))
            filename = f"{safe_chat_name}_{timestamp}.md"
            filepath = os.path.join(self.srsdocs_dir, filename)
            
            # Check write permissions for output directory
            if not os.access(self.srsdocs_dir, os.W_OK):
                logger.error(f"Cannot write to SRS directory: {self.srsdocs_dir}")
                raise PermissionError(
                    f"Cannot write to SRS directory. "
                    f"Please check permissions at {self.srsdocs_dir}"
                )
            
            # Create prompt for SRS generation
            # TODO: Need to do some tweaking here!!!
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
            chain = prompt | self.llm
            response = await chain.ainvoke({
                "conversation": "\n".join([f"{msg.type}: {msg.content}" for msg in messages])
            })
            
            # Replace template placeholders with generated content
            document_content = self.srs_template.format(
                chat_name=safe_chat_name,
                project_name=chat_name,
                introduction=response.content,
                uml_models=uml_diagrams  # Add the UML diagrams from Agent Jackson
            )
            
            # Save document to file
            with open(filepath, 'w') as f:
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