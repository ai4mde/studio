from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from typing import Dict, List, Optional
import logging
from langchain_redis import RedisChatMessageHistory
import json

logger = logging.getLogger(__name__)

class UMLConverterAgent:
    """Agent responsible for converting UML diagrams to JSON format."""
    
    SUPPORTED_DIAGRAMS = ['class', 'activity', 'usecase']
    
    def __init__(self, session_id: str):
        try:
            logger.info(f"Initializing UMLConverterAgent for session {session_id}")
            self.session_id = session_id
            
            # Get agent name from settings
            self.agent_name = settings.AGENT_BROWN_NAME
            
            # Initialize LLM for UML parsing
            self.llm = ChatOpenAI(
                model_name=settings.AGENT_BROWN_MODEL,
                temperature=settings.AGENT_BROWN_TEMPERATURE,
                api_key=settings.OPENAI_API_KEY,
                request_timeout=settings.OPENAI_TIMEOUT,
                max_retries=settings.OPENAI_MAX_RETRIES
            )
            
            # Setup Redis memory
            redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
            self.message_history = RedisChatMessageHistory(
                session_id=f"uml_converter_{session_id}",
                url=redis_url
            )
            
            logger.info(f"{self.agent_name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_name}: {str(e)}", exc_info=True)
            raise

    async def convert_uml_to_json(self, plantuml_code: str, diagram_type: str) -> Dict:
        """Convert PlantUML diagram code to JSON format."""
        try:
            if diagram_type.lower() not in self.SUPPORTED_DIAGRAMS:
                raise ValueError(f"Unsupported diagram type: {diagram_type}. "
                               f"Supported types are: {', '.join(self.SUPPORTED_DIAGRAMS)}")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, the UML conversion specialist.
                Your task is to parse PlantUML code and convert it to a structured JSON format.
                Focus only on extracting the essential elements and relationships.
                
                For Class Diagrams:
                - Classes, attributes, methods
                - Relationships (inheritance, association, etc.)
                
                For Activity Diagrams:
                - Activities, decisions, forks
                - Transitions and conditions
                
                For Use Case Diagrams:
                - Actors, use cases
                - Relationships (include, extend, etc.)
                
                Provide the output as valid JSON only."""),
                ("human", f"Convert this {diagram_type} diagram to JSON:\n\n{plantuml_code}")
            ])
            
            chain = prompt | self.llm
            response = await chain.ainvoke({})
            
            # Validate JSON structure
            try:
                json_data = json.loads(response.content)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON generated: {str(e)}")
                raise ValueError("Failed to generate valid JSON structure")
            
            return {
                "diagram_type": diagram_type,
                "json_data": json_data,
                "message": f"UML conversion completed successfully. - {self.agent_name}"
            }
            
        except Exception as e:
            logger.error(f"Error converting UML to JSON: {str(e)}", exc_info=True)
            raise

    def validate_diagram_type(self, diagram_type: str) -> bool:
        """Validate if the diagram type is supported."""
        return diagram_type.lower() in self.SUPPORTED_DIAGRAMS

    async def extract_diagrams(self, content: str) -> List[Dict[str, str]]:
        """Extract individual UML diagrams from content."""
        diagrams = []
        current_type = None
        current_content = []
        
        for line in content.split('\n'):
            if '### Class Diagram' in line:
                current_type = 'class'
            elif '### Activity Diagram' in line:
                current_type = 'activity'
            elif '### Use Case Diagram' in line:
                current_type = 'usecase'
            elif current_type and '@startuml' in line:
                current_content = [line]
            elif current_type and '@enduml' in line:
                current_content.append(line)
                diagrams.append({
                    'type': current_type,
                    'content': '\n'.join(current_content)
                })
                current_type = None
            elif current_type and current_content:
                current_content.append(line)
        
        return diagrams 