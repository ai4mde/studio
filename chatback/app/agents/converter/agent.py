from typing import Dict, List, Optional
import logging
import json
import uuid
import httpx
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.agents.base import BaseAgent
from .utils import (
    validate_diagram_type,
    extract_diagrams,
    validate_json_structure,
    parse_json_response
)

logger = logging.getLogger(__name__)

class UMLConverterAgent(BaseAgent):
    """Agent responsible for converting UML diagrams to JSON format and interacting with ACC API."""
    
    SUPPORTED_DIAGRAMS = ['class', 'activity', 'usecase']
    USECASE_EDGE_TYPES = ['interaction', 'extension', 'inclusion']
    ACTIVITY_EDGE_TYPES = ['controlflow']
    
    def __init__(self, session_id: str, username: str):
        super().__init__(
            session_id=session_id,
            username=username,
            agent_name=settings.AGENT_BROWN_NAME,
            model_name=settings.AGENT_BROWN_MODEL,
            temperature=settings.AGENT_BROWN_TEMPERATURE,
            redis_prefix="converter"
        )
        
        self.studio_api_url = settings.STUDIO_API_URL
        self.access_token = None
        
        logger.info(f"{self.agent_name} initialized successfully")

    async def authenticate(self, username: str, password: str) -> None:
        """Authenticate with the ACC API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.studio_api_url}/auth/token",
                    data={
                        "username": username,
                        "password": password
                    }
                )
                response.raise_for_status()
                self.access_token = response.json()["access_token"]
                logger.info("Successfully authenticated with ACC API")
                
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}", exc_info=True)
            raise RuntimeError("Failed to authenticate with ACC API") from e

    async def convert_uml_to_json(self, plantuml_code: str, diagram_type: str) -> Dict:
        """Convert PlantUML diagram code to JSON format."""
        try:
            # Validate diagram type
            validate_diagram_type(diagram_type, self.SUPPORTED_DIAGRAMS)
            normalized_type = diagram_type.lower()
            if normalized_type == "classes":
                normalized_type = "class"
            
            # Create prompt for UML conversion
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, the UML conversion specialist.
                Your task is to parse PlantUML code and convert it to a structured JSON format.
                Focus only on extracting the essential elements and relationships.
                
                For Class Diagrams:
                - Extract classes with their attributes and methods
                - Include relationships between classes
                - Output format should be:
                {{
                    "classes": [
                        {{
                            "name": "ClassName",
                            "attributes": [
                                {{
                                    "name": "attributeName",
                                    "type": "attributeType",
                                    "visibility": "public|private|protected"
                                }}
                            ],
                            "methods": [
                                {{
                                    "name": "methodName",
                                    "returnType": "returnType",
                                    "parameters": [
                                        {{
                                            "name": "paramName",
                                            "type": "paramType"
                                        }}
                                    ],
                                    "visibility": "public|private|protected"
                                }}
                            ]
                        }}
                    ],
                    "relationships": [
                        {{
                            "source": "SourceClass",
                            "target": "TargetClass",
                            "type": "inheritance|association|aggregation|composition",
                            "label": "optional relationship label"
                        }}
                    ]
                }}
                
                For Activity Diagrams:
                - Extract activities, decisions, and transitions
                - Include guard conditions and descriptions
                - Output format should be:
                {{
                    "activities": [
                        {{
                            "id": "unique_id",
                            "name": "ActivityName",
                            "type": "action|initial|final|decision|merge|fork|join",
                            "description": "optional description"
                        }}
                    ],
                    "transitions": [
                        {{
                            "source": "source_activity_id",
                            "target": "target_activity_id",
                            "guard": "optional guard condition",
                            "description": "optional description"
                        }}
                    ]
                }}
                
                For Use Case Diagrams:
                - Extract actors, use cases, and relationships
                - Include descriptions and relationship types
                - Output format should be:
                {{
                    "actors": [
                        {{
                            "id": "unique_id",
                            "name": "ActorName",
                            "description": "optional description"
                        }}
                    ],
                    "useCases": [
                        {{
                            "id": "unique_id",
                            "name": "UseCaseName",
                            "description": "optional description"
                        }}
                    ],
                    "relationships": [
                        {{
                            "source": "source_id",
                            "target": "target_id",
                            "type": "include|extend|association",
                            "description": "optional description"
                        }}
                    ]
                }}
                
                IMPORTANT:
                1. Return ONLY the JSON object, no additional text
                2. Ensure all JSON is properly formatted and valid
                3. Use the exact structure shown above for each diagram type
                4. Generate unique IDs for elements that require them
                5. Include all relationships and connections from the PlantUML"""),
                ("human", f"Convert this {normalized_type} diagram to JSON:\n\n{plantuml_code}")
            ])
            
            # Generate JSON conversion
            response = await self._invoke_llm(
                system_prompt=prompt.messages[0].content,
                user_prompt=prompt.messages[-1].content,
                variables={}
            )
            
            # Parse and validate JSON response
            json_data = parse_json_response(response)
            validate_json_structure(json_data, normalized_type)
            
            return {
                "diagram_type": diagram_type,
                "json_data": json_data,
                "message": f"UML conversion completed successfully. - {self.agent_name}"
            }
            
        except Exception as e:
            logger.error(f"Error converting UML to JSON: {str(e)}", exc_info=True)
            if isinstance(e, ValueError):
                raise
            raise RuntimeError(f"Failed to convert UML to JSON: {str(e)}") from e

    async def create_diagram(self, system_id: str, plantuml_code: str, diagram_type: str) -> Dict:
        """Create a new diagram in ACC API."""
        try:
            if not self.access_token:
                raise ValueError("Not authenticated. Call authenticate() first.")
                
            # Create diagram using basic endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.studio_api_url}/diagram/",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    },
                    json={
                        "system": system_id,
                        "type": diagram_type,
                        "name": f"test_{diagram_type}_{uuid.uuid4().hex[:8]}"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Create diagram failed with status {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    logger.error(f"Request body: {response.request.content}")
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Failed to create diagram: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to create diagram: {str(e)}") from e

    async def create_diagram_flow(
        self,
        username: str,
        password: str,
        system_name: str,
        system_description: str,
        plantuml_code: str,
        diagram_type: str
    ) -> Dict:
        """Convenience method to create a diagram with all necessary steps."""
        try:
            # Step 1: Authenticate
            await self.authenticate(username, password)
            logger.info("Authentication successful")

            # Step 2: Get or create project using session ID
            project_name = f"uml_project_{self.session_id}"
            projects = await self.get_projects()
            project = next((p for p in projects if p["name"] == project_name), None)
            
            if project:
                project_id = project["id"]
                logger.info(f"Using existing project with ID: {project_id}")
            else:
                project_id = await self.create_project(
                    name=project_name,
                    description=f"UML project for session {self.session_id}"
                )
                logger.info(f"Created new project with ID: {project_id}")

            # Step 3: Get or create system
            systems = await self.get_systems(project_id)
            system = next((s for s in systems if s["name"] == system_name), None)
            
            if system:
                system_id = system["id"]
                logger.info(f"Using existing system with ID: {system_id}")
            else:
                system_id = await self.create_system(
                    project_id=project_id,
                    name=system_name,
                    description=system_description
                )
                logger.info(f"Created new system with ID: {system_id}")

            # Step 4: Create diagram
            diagram = await self.create_diagram(
                system_id=system_id,
                plantuml_code=plantuml_code,
                diagram_type=diagram_type
            )
            logger.info(f"{diagram_type} diagram created successfully")

            return {
                "project_id": project_id,
                "system_id": system_id,
                "diagram": diagram,
                "message": f"{diagram_type} diagram creation flow completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to complete diagram creation flow: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to complete diagram creation flow: {str(e)}") from e 