from typing import Dict, List
import logging
import time
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage
import os
import json

from app.core.config import settings
from app.agents.base import BaseAgent
from .utils import load_srs_template, ensure_srs_directory, sanitize_filename
from langchain.memory import RedisChatMessageHistory

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
        
        # Setup Redis client
        redis_url = (
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
            f"?socket_timeout={settings.REDIS_TIMEOUT}"
            f"&socket_connect_timeout={settings.REDIS_TIMEOUT}"
        )
        
        # Initialize Redis client
        self.message_history = RedisChatMessageHistory(
            session_id=f"document_{session_id}",
            url=redis_url,
            key_prefix="document:",
            ttl=settings.REDIS_DATA_TTL
        )
        
        # Get Redis client from message history
        self.redis_client = self.message_history.redis_client
        
        # Get user's group info from Redis
        user_info = self._get_user_info()
        self.group_name = user_info.get('group_name', 'default')

    def _get_user_info(self) -> dict:
        """Get user info including group from Redis."""
        try:
            user_info_key = f"user_info:{self.username}"
            user_info = self.redis_client.get(user_info_key)
            if user_info:
                return json.loads(user_info)
            logger.warning(f"No user info found for user {self.username}")
            return {'group_name': 'default'}
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {'group_name': 'default'}

    async def generate_srs_document(self, chat_name: str, messages: List[BaseMessage], uml_diagrams: str) -> Dict:
        """Generate a Software Requirements Specification document."""
        try:
            # Create prompt for SRS content generation
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, a precise technical writer specializing in Software Requirements Specifications.
                Based on the provided interview conversation, generate a detailed SRS document following IEEE 830 standard.
                
                Extract from the conversation:
                1. Project title and description
                2. Project scope and objectives
                3. Functional requirements
                4. Non-functional requirements
                5. System interfaces and constraints
                6. User characteristics and assumptions
                
                Format your response as a structured document with these sections filled with the extracted information.
                Be specific and detailed, using actual information from the conversation."""),
                ("human", "Generate SRS content based on this interview: {conversation}")
            ])

            # Generate SRS content
            srs_content = await self._invoke_llm(
                system_prompt=prompt.messages[0].content,
                user_prompt=prompt.messages[-1].content,
                variables={
                    "conversation": "\n".join([f"{msg.type}: {msg.content}" for msg in messages])
                }
            )

            # Extract project title and description from the content
            # This should be improved with better parsing
            title = chat_name
            description = "Software Requirements Specification based on stakeholder interview"
            
            # Load template
            template = load_srs_template()
            
            # Prepare document variables
            current_date = datetime.now().strftime("%Y-%m-%d")
            doc_vars = {
                "chat_name": chat_name,
                "title": title,
                "description": description,
                "date": current_date,
                "project_name": title,
                "version": "1.0",
                "agent_name": self.agent_name,
                "organization": self.group_name,
                "date_updated": current_date,
                "content": srs_content,
                "uml_models": uml_diagrams,
                "interview_log": "\n".join([f"{msg.type}: {msg.content}" for msg in messages])
            }

            # Generate document content
            document_content = template.format(**doc_vars)

            # Save document in group directory
            timestamp = int(time.time())
            filename = f"srs_{sanitize_filename(chat_name)}_{timestamp}.md"
            
            # Create group-specific path
            filepath = os.path.join(
                settings.CHATBOT_DATA_PATH,
                self.group_name,
                chat_name,
                "srsdocs",
                filename
            )
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(document_content)

            logger.info(f"SRS document saved to {filepath}")

            return {
                "message": f"The requirements have been documented with perfect precision. - {self.agent_name}",
                "file_path": filepath
            }

        except Exception as e:
            logger.error(f"Error generating SRS document: {str(e)}", exc_info=True)
            raise 

def load_srs_template() -> str:
    """Load the SRS document template."""
    try:
        # Ensure templates directory exists
        os.makedirs(settings.TEMPLATES_PATH, exist_ok=True)
        
        template_path = os.path.join(settings.TEMPLATES_PATH, "srsdoc_template.md")
        
        # If template doesn't exist, copy from app data
        if not os.path.exists(template_path):
            source_template = os.path.join(
                os.path.dirname(__file__), 
                "..", "..", "data", 
                "templates", 
                "srsdoc_template.md"
            )
            if os.path.exists(source_template):
                import shutil
                shutil.copy2(source_template, template_path)
            else:
                raise FileNotFoundError(f"Template not found at {source_template}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    except Exception as e:
        logger.error(f"Error loading SRS template: {str(e)}")
        raise 