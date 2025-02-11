from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from typing import Dict, List
import logging
from langchain_community.chat_message_histories import RedisChatMessageHistory
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
from app.agents.base import BaseAgent
import os
from datetime import datetime
import json
from redis.exceptions import TimeoutError, ConnectionError

logger = logging.getLogger(__name__)

class DiagramAgent(BaseAgent):
    """Agent responsible for generating UML diagrams from conversations."""
    
    def __init__(self, session_id: str, username: str):
        super().__init__(
            session_id=session_id,
            username=username,
            agent_name=settings.AGENT_JACKSON_NAME,
            model_name=settings.AGENT_JACKSON_MODEL,
            temperature=settings.AGENT_JACKSON_TEMPERATURE,
            redis_prefix="diagram"
        )
        
        # Setup Redis client
        redis_url = (
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
            f"?socket_timeout={settings.REDIS_TIMEOUT}"
            f"&socket_connect_timeout={settings.REDIS_TIMEOUT}"
        )
        
        # Initialize Redis client
        self.message_history = RedisChatMessageHistory(
            session_id=f"diagram_{session_id}",
            url=redis_url,
            key_prefix="diagram:",
            ttl=settings.REDIS_DATA_TTL
        )
        
        # Get Redis client from message history
        self.redis_client = self.message_history.redis_client
        
        # Get user's group info from Redis
        user_info = self._get_user_info()
        self.group_name = user_info.get('group_name', 'default')
        
        # Initialize summarization LLM with increased timeouts
        self.summary_llm = ChatOpenAI(
            model_name=settings.AGENT_SUMMARY_MODEL,
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY,
            request_timeout=120.0,
            max_retries=5,
            http_client=httpx.Client(
                timeout=httpx.Timeout(
                    connect=30.0,
                    read=120.0,
                    write=60.0,
                    pool=10.0
                ),
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10,
                    keepalive_expiry=30.0
                )
            )
        )

    def _chunk_conversation(self, messages: List, chunk_size: int = 10) -> List[List]:
        """Split conversation into smaller chunks for processing."""
        return [messages[i:i + chunk_size] for i in range(0, len(messages), chunk_size)]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.ReadTimeout, httpx.TimeoutException))
    )
    async def _summarize_chunk(self, messages: List) -> str:
        """Summarize a single chunk of conversation with retry logic."""
        try:
            if not messages:
                return ""
                
            # Process messages into conversation text
            conversation = []
            for msg in messages:
                if hasattr(msg, 'type') and hasattr(msg, 'content'):
                    conversation.append(f"{msg.type}: {msg.content}")
                elif isinstance(msg, dict):
                    conversation.append(f"{msg.get('role', 'unknown')}: {msg.get('content', '')}")
            
            system_prompt = """Summarize the key requirements and design decisions from this conversation chunk.
            Focus on information relevant for generating UML diagrams:
            - System components and their relationships
            - Main use cases and actors
            - Key workflows and sequences
            - Important constraints and business rules
            
            Keep the summary concise but include all essential details for system design."""
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "Summarize this conversation chunk: {conversation}")
            ])
            
            chain = prompt | self.summary_llm
            response = await chain.ainvoke({"conversation": "\n".join(conversation)})
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error summarizing chunk: {str(e)}", exc_info=True)
            raise

    async def _summarize_conversation(self, messages: List) -> str:
        """Summarize the entire conversation in chunks with improved error handling."""
        try:
            # Split conversation into smaller chunks
            chunks = self._chunk_conversation(messages)
            chunk_summaries = []
            
            # Process each chunk with retries
            for chunk in chunks:
                try:
                    summary = await self._summarize_chunk(chunk)
                    if summary:
                        chunk_summaries.append(summary)
                except Exception as e:
                    logger.error(f"Error processing chunk: {str(e)}", exc_info=True)
                    # Continue with other chunks even if one fails
                    continue
            
            if not chunk_summaries:
                raise ValueError("Failed to generate any summaries from the conversation")
            
            # Combine chunk summaries
            prompt = ChatPromptTemplate.from_messages([
                ("system", "Combine these conversation summaries into a coherent overview of the system requirements."),
                ("human", "Combine these summaries:\n{summaries}")
            ])
            
            chain = prompt | self.summary_llm
            response = await chain.ainvoke({
                "summaries": "\n\n---\n\n".join(chunk_summaries)
            })
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error summarizing conversation: {str(e)}", exc_info=True)
            # Return a basic summary if the detailed process fails
            return "\n".join(chunk_summaries) if chunk_summaries else "Failed to generate summary"

    async def generate_uml_diagrams(self, messages: list) -> Dict[str, str]:
        """Generate PlantUML code for various UML diagrams and save them."""
        try:
            # First summarize the conversation if it's long
            conversation_summary = await self._summarize_conversation(messages)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, visualization specialist for the Matrix.
                Your purpose is to create perfect system visualizations through UML diagrams.
                Based on the provided requirements discussion, generate PlantUML code for:
                1. Class Diagram showing the main entities and their relationships
                2. Use Case Diagram showing system actors and main use cases
                3. Sequence Diagram for the most important workflow
                
                Format each diagram with clear headers and PlantUML code blocks."""),
                ("human", "Generate UML diagrams based on this conversation summary: {conversation}")
            ])
            
            chain = prompt | self.llm
            
            # Invoke chain with processed conversation
            response = await chain.ainvoke({
                "conversation": conversation_summary
            })
            
            # Validate UML content
            uml_content = response.content
            if not uml_content or not uml_content.strip():
                logger.error("Generated UML content is empty")
                raise ValueError("Failed to generate UML diagrams: empty response")
            
            # Validate required diagram sections
            required_sections = ["Class Diagram", "Use Case Diagram", "Sequence Diagram"]
            missing_sections = []
            for section in required_sections:
                if section not in uml_content:
                    missing_sections.append(section)
            
            if missing_sections:
                logger.error(f"Missing required UML sections: {', '.join(missing_sections)}")
                raise ValueError(
                    f"Incomplete UML generation. Missing sections: {', '.join(missing_sections)}"
                )
            
            # Validate PlantUML syntax
            if not all(marker in uml_content for marker in ["@startuml", "@enduml"]):
                logger.error("Invalid PlantUML syntax: missing @startuml/@enduml markers")
                raise ValueError(
                    "Generated UML diagrams have invalid syntax. "
                    "Missing required PlantUML markers."
                )
            
            # Get timestamp and chat name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            chat_name = await self._get_chat_name()
            
            # Create diagrams directory structure
            diagrams_dir = os.path.join(
                settings.CHATBOT_DATA_PATH,
                self.group_name,
                chat_name,
                "diagrams"
            )
            os.makedirs(diagrams_dir, exist_ok=True)
            
            # Split and save individual diagrams
            diagram_files = {}
            current_type = None
            current_content = []
            
            for line in uml_content.split('\n'):
                if '### Class Diagram' in line:
                    if current_type and current_content:
                        # Save previous diagram if exists
                        filepath = self._save_diagram(
                            diagrams_dir, current_type, 
                            '\n'.join(current_content), 
                            timestamp
                        )
                        diagram_files[current_type] = filepath
                    current_type = 'class'
                    current_content = []
                elif '### Use Case Diagram' in line:
                    if current_type and current_content:
                        filepath = self._save_diagram(
                            diagrams_dir, current_type, 
                            '\n'.join(current_content), 
                            timestamp
                        )
                        diagram_files[current_type] = filepath
                    current_type = 'use_case'
                    current_content = []
                elif '### Activity Diagram' in line:
                    if current_type and current_content:
                        filepath = self._save_diagram(
                            diagrams_dir, current_type, 
                            '\n'.join(current_content), 
                            timestamp
                        )
                        diagram_files[current_type] = filepath
                    current_type = 'activity'
                    current_content = []
                elif current_type:
                    current_content.append(line)
            
            # Save the last diagram
            if current_type and current_content:
                filepath = self._save_diagram(
                    diagrams_dir, current_type, 
                    '\n'.join(current_content), 
                    timestamp
                )
                diagram_files[current_type] = filepath
            
            logger.info(f"UML diagrams saved in {diagrams_dir}")
            
            return {
                "uml_diagrams": uml_content,
                "diagram_files": diagram_files,
                "message": f"The system structure has been visualized. - {self.agent_name}"
            }
            
        except Exception as e:
            logger.error(f"Error generating UML diagrams: {str(e)}", exc_info=True)
            if isinstance(e, (ValueError, IOError)):
                raise
            raise RuntimeError(f"Failed to generate UML diagrams: {str(e)}") from e

    def _save_diagram(self, diagrams_dir: str, diagram_type: str, content: str, timestamp: str) -> str:
        """Save individual diagram to file."""
        try:
            filename = f"{diagram_type}_{timestamp}.puml"
            filepath = os.path.join(diagrams_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved {diagram_type} diagram to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving {diagram_type} diagram: {str(e)}")
            raise

    def _validate_plantuml_section(self, content: str, section_name: str) -> bool:
        """Validate a specific PlantUML diagram section."""
        try:
            section_start = content.find(f"### {section_name}")
            if section_start == -1:
                return False
            
            section_content = content[section_start:]
            next_section = content.find("###", section_start + 3)
            if next_section != -1:
                section_content = section_content[:next_section]
            
            # Check for required PlantUML elements
            has_start = "@startuml" in section_content
            has_end = "@enduml" in section_content
            has_content = len(section_content.strip()) > 20  # Arbitrary minimum length
            
            return has_start and has_end and has_content
            
        except Exception as e:
            logger.error(f"Error validating {section_name}: {str(e)}")
            return False

    async def _get_chat_name(self) -> str:
        """Get a sanitized chat name for the file."""
        try:
            # Try to get chat name from Redis
            chat_name_key = f"chat_name:{self.session_id}"
            chat_name = self.redis_client.get(chat_name_key)
            
            if chat_name:
                chat_name = chat_name.decode('utf-8')
            else:
                # Fallback to session-based name
                chat_name = f"chat_session_{self.session_id}"
            
            # Sanitize filename
            chat_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in chat_name)
            return chat_name
            
        except Exception as e:
            logger.error(f"Error getting chat name: {str(e)}", exc_info=True)
            # Fallback to session ID if anything fails
            return f"chat_session_{self.session_id}"

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