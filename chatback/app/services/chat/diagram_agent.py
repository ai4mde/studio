from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from typing import Dict
import logging
from langchain_community.chat_message_histories import RedisChatMessageHistory
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class DiagramAgent:
    def __init__(self, session_id: str, username: str):
        try:
            logger.info(f"Initializing DiagramAgent for session {session_id}")
            self.session_id = session_id
            self.username = username
            
            # Get agent name from settings
            self.agent_name = settings.AGENT_JACKSON_NAME
            
            # Initialize LLM for UML generation
            self.llm = ChatOpenAI(
                model_name=settings.AGENT_JACKSON_MODEL,
                temperature=settings.AGENT_JACKSON_TEMPERATURE,
                api_key=settings.OPENAI_API_KEY,
                request_timeout=settings.OPENAI_TIMEOUT,
                max_retries=settings.OPENAI_MAX_RETRIES
            )
            
            # Setup Redis client first
            redis_url = (
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
                f"?socket_timeout={settings.REDIS_SOCKET_TIMEOUT}"
                f"&socket_connect_timeout={settings.REDIS_CONNECT_TIMEOUT}"
            )
            
            # Initialize Redis client
            @retry(
                stop=stop_after_attempt(settings.REDIS_RETRY_ATTEMPTS),
                wait=wait_exponential(multiplier=settings.REDIS_RETRY_DELAY)
            )
            def init_redis():
                return RedisChatMessageHistory(
                    session_id=f"diagram_{session_id}",
                    url=redis_url,
                    key_prefix="diagram:",
                    ttl=settings.REDIS_DATA_TTL
                )
            
            self.message_history = init_redis()
            
            logger.info(f"{self.agent_name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_name}: {str(e)}", exc_info=True)
            raise

    async def generate_uml_diagrams(self, messages: list) -> Dict[str, str]:
        """Generate PlantUML code for various UML diagrams."""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, visualization specialist for the Matrix.
                Your purpose is to create perfect system visualizations through UML diagrams.
                Based on the provided requirements discussion, generate PlantUML code for:
                1. Class Diagram showing the main entities and their relationships
                2. Use Case Diagram showing system actors and main use cases
                3. Sequence Diagram for the most important workflow
                
                Format each diagram with clear headers and PlantUML code blocks."""),
                ("human", "Generate UML diagrams based on this conversation: {conversation}")
            ])
            
            chain = prompt | self.llm
            
            # Process messages
            conversation = []
            for msg in messages:
                if hasattr(msg, 'type') and hasattr(msg, 'content'):
                    conversation.append(f"{msg.type}: {msg.content}")
                elif isinstance(msg, dict):
                    conversation.append(f"{msg.get('role', 'unknown')}: {msg.get('content', '')}")
            
            if not conversation:
                logger.error("No messages provided for UML generation")
                raise ValueError("Cannot generate UML diagrams without conversation history")
            
            # Invoke chain with processed conversation
            response = await chain.ainvoke({
                "conversation": "\n".join(conversation)
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
            
            return {
                "uml_diagrams": uml_content,
                "message": f"The system structure has been visualized. - {self.agent_name}"
            }
            
        except Exception as e:
            logger.error(f"Error generating UML diagrams: {str(e)}", exc_info=True)
            if isinstance(e, (ValueError, IOError)):
                raise
            raise RuntimeError(f"Failed to generate UML diagrams: {str(e)}") from e

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