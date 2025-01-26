from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from typing import Dict, List, Optional
import logging
from langchain_redis import RedisChatMessageHistory
import json
import httpx
import uuid

logger = logging.getLogger(__name__)

class UMLConverterAgent:
    """Agent responsible for converting UML diagrams to JSON format and interacting with ACC API."""
    
    SUPPORTED_DIAGRAMS = ['classes', 'activity', 'usecase']
    ACC_API_BASE_URL = "https://acc-api.ai4mde.org/api/v1"
    
    def __init__(self, session_id: str):
        try:
            logger.info(f"Initializing UMLConverterAgent for session {session_id}")
            self.session_id = session_id
            self.agent_name = settings.AGENT_BROWN_NAME
            self.access_token = None
            
            # Initialize LLM for UML parsing
            self.llm = ChatOpenAI(
                model_name=settings.AGENT_BROWN_MODEL,
                temperature=settings.AGENT_BROWN_TEMPERATURE,
                api_key=settings.OPENAI_API_KEY,
                request_timeout=settings.OPENAI_TIMEOUT,
                max_retries=settings.OPENAI_MAX_RETRIES
            )
            
            # Setup Redis memory (optional)
            try:
                redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
                self.message_history = RedisChatMessageHistory(
                    session_id=f"uml_converter_{session_id}",
                    url=redis_url
                )
            except Exception as redis_error:
                logger.warning(f"Redis initialization failed, continuing without message history: {str(redis_error)}")
                self.message_history = None
            
            logger.info(f"{self.agent_name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_name}: {str(e)}", exc_info=True)
            raise

    async def authenticate(self, username: str, password: str) -> str:
        """Authenticate with ACC API and get access token."""
        try:
            async with httpx.AsyncClient() as client:
                # Use JSON format for authentication
                json_data = {
                    "username": username,
                    "password": password
                }
                
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/auth/token",
                    json=json_data,
                    headers={"accept": "*/*", "Content-Type": "application/json"}
                )
                
                # Print response for debugging
                if response.status_code != 200:
                    logger.error(f"Auth failed with status {response.status_code}")
                    logger.error(f"Response: {response.text}")
                
                response.raise_for_status()
                data = response.json()
                self.access_token = data["token"]
                return self.access_token
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}", exc_info=True)
            raise

    async def create_project(self, name: str, description: str) -> str:
        """Create a new project in ACC API."""
        try:
            if not self.access_token:
                raise ValueError("Not authenticated. Call authenticate() first.")
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/metadata/projects/",  # Add metadata to path
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    },
                    json={"name": name, "description": description}
                )
                
                # Print response for debugging
                if response.status_code != 200:
                    logger.error(f"Create project failed with status {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    logger.error(f"Request body: {response.request.content}")
                
                response.raise_for_status()
                return response.json()["id"]
        except Exception as e:
            logger.error(f"Failed to create project: {str(e)}", exc_info=True)
            raise

    async def create_system(self, project_id: str, name: str, description: str) -> str:
        """Create a new system in ACC API."""
        try:
            if not self.access_token:
                raise ValueError("Not authenticated. Call authenticate() first.")
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/metadata/systems/",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    },
                    json={
                        "project": project_id,
                        "name": name,
                        "description": description
                    }
                )
                
                # Print response for debugging
                if response.status_code != 200:
                    logger.error(f"Create system failed with status {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    logger.error(f"Request body: {response.request.content}")
                
                response.raise_for_status()
                return response.json()["id"]
        except Exception as e:
            logger.error(f"Failed to create system: {str(e)}", exc_info=True)
            raise

    async def create_diagram(self, system_id: str, plantuml_code: str, diagram_type: str) -> Dict:
        """Create a new diagram in ACC API."""
        try:
            if not self.access_token:
                raise ValueError("Not authenticated. Call authenticate() first.")
                
            # Create diagram using basic endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/diagram/",  # Added trailing slash
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
            raise

    async def convert_uml_to_json(self, plantuml_code: str, diagram_type: str) -> Dict:
        """Convert PlantUML diagram code to JSON format."""
        try:
            # Normalize diagram type
            normalized_type = diagram_type.lower()
            if normalized_type == "classes":
                normalized_type = "class"
            
            if normalized_type not in ['class', 'activity', 'usecase']:
                raise ValueError(f"Unsupported diagram type: {diagram_type}. "
                               f"Supported types are: {', '.join(self.SUPPORTED_DIAGRAMS)}")
            
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
            
            chain = prompt | self.llm
            response = await chain.ainvoke({})
            
            # Extract content from response
            content = response.content.strip()
            
            # Try to parse the JSON, removing any potential markdown code block markers
            try:
                # Remove markdown code block if present
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                    
                content = content.strip()
                json_data = json.loads(content)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON generated: {str(e)}")
                logger.error(f"Raw content: {content}")
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

    async def get_projects(self) -> List[Dict]:
        """Get all projects from ACC API."""
        try:
            if not self.access_token:
                raise ValueError("Not authenticated. Call authenticate() first.")
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/projects",  # Remove trailing slash
                    headers={
                        "accept": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    }
                )
                
                # Print response for debugging
                if response.status_code != 200:
                    logger.error(f"Get projects failed with status {response.status_code}")
                    logger.error(f"Response: {response.text}")
                
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get projects: {str(e)}", exc_info=True)
            raise

    async def get_systems(self, project_id: str) -> List[Dict]:
        """Get all systems for a project from ACC API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/systems/",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params={"project_id": project_id}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get systems: {str(e)}", exc_info=True)
            raise

    async def create_class_diagram_flow(
        self,
        username: str,
        password: str,
        system_name: str,
        system_description: str,
        plantuml_code: str
    ) -> Dict:
        """Convenience method to create a class diagram with all necessary steps."""
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

            # Step 4: Create class diagram
            diagram = await self.create_diagram(
                system_id=system_id,
                plantuml_code=plantuml_code,
                diagram_type="class"
            )
            logger.info("Class diagram created successfully")

            return {
                "project_id": project_id,
                "system_id": system_id,
                "diagram": diagram,
                "message": "Class diagram creation flow completed successfully"
            }
        except Exception as e:
            logger.error(f"Failed to complete class diagram creation flow: {str(e)}", exc_info=True)
            raise 

    async def add_class_attribute(
        self,
        diagram_id: str,
        class_name: str,
        attribute_name: str,
        attribute_type: str,
        visibility: str = "public"
    ) -> Dict:
        """Add an attribute to a class in a diagram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/classes/{class_name}/attributes",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json={
                        "name": attribute_name,
                        "type": attribute_type,
                        "visibility": visibility
                    }
                )
                response.raise_for_status()
                logger.info(f"Added attribute {attribute_name} to class {class_name}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to add class attribute: {str(e)}", exc_info=True)
            raise

    async def get_class_attributes(
        self,
        diagram_id: str,
        class_name: str
    ) -> List[Dict]:
        """Get all attributes of a class in a diagram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/classes/{class_name}/attributes",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get class attributes: {str(e)}", exc_info=True)
            raise

    async def update_class_attribute(
        self,
        diagram_id: str,
        class_name: str,
        attribute_id: str,
        attribute_name: str = None,
        attribute_type: str = None,
        visibility: str = None
    ) -> Dict:
        """Update an attribute of a class in a diagram."""
        try:
            update_data = {}
            if attribute_name is not None:
                update_data["name"] = attribute_name
            if attribute_type is not None:
                update_data["type"] = attribute_type
            if visibility is not None:
                update_data["visibility"] = visibility

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/classes/{class_name}/attributes/{attribute_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=update_data
                )
                response.raise_for_status()
                logger.info(f"Updated attribute {attribute_id} in class {class_name}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to update class attribute: {str(e)}", exc_info=True)
            raise

    async def delete_class_attribute(
        self,
        diagram_id: str,
        class_name: str,
        attribute_id: str
    ) -> None:
        """Delete an attribute from a class in a diagram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/classes/{class_name}/attributes/{attribute_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                logger.info(f"Deleted attribute {attribute_id} from class {class_name}")
        except Exception as e:
            logger.error(f"Failed to delete class attribute: {str(e)}", exc_info=True)
            raise 

    async def add_edge(
        self,
        diagram_id: str,
        source_class: str,
        target_class: str,
        edge_type: str,
        label: Optional[str] = None
    ) -> Dict:
        """Add an edge (relationship) between classes in a diagram."""
        try:
            edge_data = {
                "source": source_class,
                "target": target_class,
                "type": edge_type
            }
            if label:
                edge_data["label"] = label

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/edges",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=edge_data
                )
                response.raise_for_status()
                logger.info(f"Added {edge_type} edge from {source_class} to {target_class}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to add edge: {str(e)}", exc_info=True)
            raise

    async def get_edges(
        self,
        diagram_id: str,
        source_class: Optional[str] = None,
        target_class: Optional[str] = None
    ) -> List[Dict]:
        """Get edges (relationships) in a diagram with optional source/target filtering."""
        try:
            params = {}
            if source_class:
                params["source"] = source_class
            if target_class:
                params["target"] = target_class

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/edges",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get edges: {str(e)}", exc_info=True)
            raise

    async def update_edge(
        self,
        diagram_id: str,
        edge_id: str,
        source_class: Optional[str] = None,
        target_class: Optional[str] = None,
        edge_type: Optional[str] = None,
        label: Optional[str] = None
    ) -> Dict:
        """Update an edge (relationship) in a diagram."""
        try:
            update_data = {}
            if source_class is not None:
                update_data["source"] = source_class
            if target_class is not None:
                update_data["target"] = target_class
            if edge_type is not None:
                update_data["type"] = edge_type
            if label is not None:
                update_data["label"] = label

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/edges/{edge_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=update_data
                )
                response.raise_for_status()
                logger.info(f"Updated edge {edge_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to update edge: {str(e)}", exc_info=True)
            raise

    async def delete_edge(
        self,
        diagram_id: str,
        edge_id: str
    ) -> None:
        """Delete an edge (relationship) from a diagram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/edges/{edge_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                logger.info(f"Deleted edge {edge_id}")
        except Exception as e:
            logger.error(f"Failed to delete edge: {str(e)}", exc_info=True)
            raise 

    async def add_actor(
        self,
        diagram_id: str,
        name: str,
        description: Optional[str] = None
    ) -> Dict:
        """Add an actor to a use-case diagram."""
        try:
            node_id = str(uuid.uuid4())
            actor_data = {
                "data": {
                    "id": node_id,
                    "cls": {
                        "namespace": "",
                        "name": name,
                        "type": "actor",
                        "role": "actor",
                        "description": description or f"Actor representing {name}",
                        "localPrecondition": "",
                        "localPostcondition": "",
                        "body": "",
                        "operation": {
                            "name": name,
                            "description": description or "",
                            "type": "str",
                            "body": ""
                        },
                        "publish": [],
                        "subscribe": [],
                        "classes": [],
                        "application_models": [],
                        "page": ""
                    }
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/diagram/{diagram_id}/node/",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    },
                    json=actor_data
                )
                response.raise_for_status()
                logger.info(f"Added actor {name} to diagram")
                # Return response with data structure
                return {"data": {"id": node_id}}
        except Exception as e:
            logger.error(f"Failed to add actor: {str(e)}", exc_info=True)
            raise

    async def get_actors(
        self,
        diagram_id: str
    ) -> List[Dict]:
        """Get all actors in a use-case diagram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/actors",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get actors: {str(e)}", exc_info=True)
            raise

    async def update_actor(
        self,
        diagram_id: str,
        actor_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """Update an actor in a use-case diagram."""
        try:
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if description is not None:
                update_data["description"] = description

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/actors/{actor_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=update_data
                )
                response.raise_for_status()
                logger.info(f"Updated actor {actor_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to update actor: {str(e)}", exc_info=True)
            raise

    async def delete_actor(
        self,
        diagram_id: str,
        actor_id: str
    ) -> None:
        """Delete an actor from a use-case diagram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/actors/{actor_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                logger.info(f"Deleted actor {actor_id}")
        except Exception as e:
            logger.error(f"Failed to delete actor: {str(e)}", exc_info=True)
            raise

    async def add_use_case(
        self,
        diagram_id: str,
        name: str,
        description: Optional[str] = None
    ) -> Dict:
        """Add a use case to a use-case diagram."""
        try:
            node_id = str(uuid.uuid4())
            use_case_data = {
                "data": {
                    "id": node_id,
                    "cls": {
                        "namespace": "",
                        "name": name,
                        "type": "usecase",
                        "role": "usecase",
                        "description": description or f"Use case for {name}",
                        "localPrecondition": "",
                        "localPostcondition": "",
                        "body": "",
                        "operation": {
                            "name": name,
                            "description": description or "",
                            "type": "str",
                            "body": ""
                        },
                        "publish": [],
                        "subscribe": [],
                        "classes": [],
                        "application_models": [],
                        "page": ""
                    }
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/diagram/{diagram_id}/node/",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    },
                    json=use_case_data
                )
                response.raise_for_status()
                logger.info(f"Added use case {name} to diagram")
                # Return response with data structure
                return {"data": {"id": node_id}}
        except Exception as e:
            logger.error(f"Failed to add use case: {str(e)}", exc_info=True)
            raise

    async def get_use_cases(
        self,
        diagram_id: str
    ) -> List[Dict]:
        """Get all use cases in a use-case diagram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/usecases",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get use cases: {str(e)}", exc_info=True)
            raise

    async def update_use_case(
        self,
        diagram_id: str,
        use_case_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """Update a use case in a use-case diagram."""
        try:
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if description is not None:
                update_data["description"] = description

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/usecases/{use_case_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=update_data
                )
                response.raise_for_status()
                logger.info(f"Updated use case {use_case_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to update use case: {str(e)}", exc_info=True)
            raise

    async def delete_use_case(
        self,
        diagram_id: str,
        use_case_id: str
    ) -> None:
        """Delete a use case from a use-case diagram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/usecases/{use_case_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                logger.info(f"Deleted use case {use_case_id}")
        except Exception as e:
            logger.error(f"Failed to delete use case: {str(e)}", exc_info=True)
            raise

    async def create_use_case_diagram_flow(
        self,
        username: str,
        password: str,
        system_name: str,
        system_description: str,
        plantuml_code: str
    ) -> Dict:
        """Convenience method to create a use-case diagram with all necessary steps."""
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

            # Step 4: Create use-case diagram
            diagram = await self.create_diagram(
                system_id=system_id,
                plantuml_code=plantuml_code,
                diagram_type="usecase"
            )
            logger.info("Use-case diagram created successfully")

            return {
                "project_id": project_id,
                "system_id": system_id,
                "diagram": diagram,
                "message": "Use-case diagram creation flow completed successfully"
            }
        except Exception as e:
            logger.error(f"Failed to complete use-case diagram creation flow: {str(e)}", exc_info=True)
            raise 

    async def add_use_case_relationship(
        self,
        diagram_id: str,
        source_use_case: str,
        target_use_case: str,
        relationship_type: str,  # 'include' or 'extend'
        description: Optional[str] = None
    ) -> Dict:
        """Add a relationship between use cases (include/extend)."""
        try:
            if relationship_type not in ['include', 'extend']:
                raise ValueError("Relationship type must be either 'include' or 'extend'")

            # Convert string IDs to UUID objects
            source_uuid = str(uuid.UUID(source_use_case))
            target_uuid = str(uuid.UUID(target_use_case))
            
            edge_data = {
                "data": {
                    "source": source_uuid,
                    "target": target_uuid,
                    "rel": relationship_type
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/diagram/{diagram_id}/edge/",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    },
                    json=edge_data
                )
                response.raise_for_status()
                logger.info(f"Added {relationship_type} relationship from {source_use_case} to {target_use_case}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to add use case relationship: {str(e)}", exc_info=True)
            raise

    async def get_use_case_relationships(
        self,
        diagram_id: str,
        source_use_case: Optional[str] = None,
        target_use_case: Optional[str] = None,
        relationship_type: Optional[str] = None
    ) -> List[Dict]:
        """Get relationships between use cases with optional filtering."""
        try:
            params = {}
            if source_use_case:
                params["source_use_case"] = source_use_case
            if target_use_case:
                params["target_use_case"] = target_use_case
            if relationship_type:
                if relationship_type not in ['include', 'extend']:
                    raise ValueError("Relationship type must be either 'include' or 'extend'")
                params["type"] = relationship_type

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/usecase-relationships",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get use case relationships: {str(e)}", exc_info=True)
            raise

    async def add_actor_association(
        self,
        diagram_id: str,
        actor_id: str,
        use_case_id: str,
        description: Optional[str] = None
    ) -> Dict:
        """Add an association between an actor and a use case."""
        try:
            # Convert string IDs to UUID objects
            source_uuid = str(uuid.UUID(actor_id))
            target_uuid = str(uuid.UUID(use_case_id))
            
            edge_data = {
                "data": {
                    "source": source_uuid,
                    "target": target_uuid,
                    "rel": "association"
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/diagram/{diagram_id}/edge/",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    },
                    json=edge_data
                )
                response.raise_for_status()
                logger.info(f"Added association between actor {actor_id} and use case {use_case_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to add actor association: {str(e)}", exc_info=True)
            raise

    async def get_actor_associations(
        self,
        diagram_id: str,
        actor_id: Optional[str] = None,
        use_case_id: Optional[str] = None
    ) -> List[Dict]:
        """Get associations between actors and use cases with optional filtering."""
        try:
            params = {}
            if actor_id:
                params["actor_id"] = actor_id
            if use_case_id:
                params["use_case_id"] = use_case_id

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/actor-associations",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get actor associations: {str(e)}", exc_info=True)
            raise

    async def delete_use_case_relationship(
        self,
        diagram_id: str,
        relationship_id: str
    ) -> None:
        """Delete a relationship between use cases."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/usecase-relationships/{relationship_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                logger.info(f"Deleted use case relationship {relationship_id}")
        except Exception as e:
            logger.error(f"Failed to delete use case relationship: {str(e)}", exc_info=True)
            raise

    async def delete_actor_association(
        self,
        diagram_id: str,
        association_id: str
    ) -> None:
        """Delete an association between an actor and a use case."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/actor-associations/{association_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                logger.info(f"Deleted actor association {association_id}")
        except Exception as e:
            logger.error(f"Failed to delete actor association: {str(e)}", exc_info=True)
            raise

    async def add_activity(
        self,
        diagram_id: str,
        name: str,
        activity_type: str,  # 'action', 'initial', 'final', 'decision', 'merge', 'fork', 'join'
        description: Optional[str] = None
    ) -> Dict:
        """Add an activity node to an activity diagram."""
        try:
            activity_data = {
                "name": name,
                "type": activity_type
            }
            if description:
                activity_data["description"] = description

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/activities",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=activity_data
                )
                response.raise_for_status()
                logger.info(f"Added {activity_type} activity {name} to diagram")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to add activity: {str(e)}", exc_info=True)
            raise

    async def get_activities(
        self,
        diagram_id: str,
        activity_type: Optional[str] = None
    ) -> List[Dict]:
        """Get all activities in an activity diagram with optional type filtering."""
        try:
            params = {}
            if activity_type:
                params["type"] = activity_type

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/activities",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get activities: {str(e)}", exc_info=True)
            raise

    async def update_activity(
        self,
        diagram_id: str,
        activity_id: str,
        name: Optional[str] = None,
        activity_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """Update an activity in an activity diagram."""
        try:
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if activity_type is not None:
                update_data["type"] = activity_type
            if description is not None:
                update_data["description"] = description

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/activities/{activity_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=update_data
                )
                response.raise_for_status()
                logger.info(f"Updated activity {activity_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to update activity: {str(e)}", exc_info=True)
            raise

    async def delete_activity(
        self,
        diagram_id: str,
        activity_id: str
    ) -> None:
        """Delete an activity from an activity diagram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/activities/{activity_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                logger.info(f"Deleted activity {activity_id}")
        except Exception as e:
            logger.error(f"Failed to delete activity: {str(e)}", exc_info=True)
            raise

    async def add_transition(
        self,
        diagram_id: str,
        source_activity_id: str,
        target_activity_id: str,
        guard_condition: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """Add a transition between activities in an activity diagram."""
        try:
            transition_data = {
                "source_activity_id": source_activity_id,
                "target_activity_id": target_activity_id
            }
            if guard_condition:
                transition_data["guard_condition"] = guard_condition
            if description:
                transition_data["description"] = description

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/transitions",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=transition_data
                )
                response.raise_for_status()
                logger.info(f"Added transition from {source_activity_id} to {target_activity_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to add transition: {str(e)}", exc_info=True)
            raise

    async def get_transitions(
        self,
        diagram_id: str,
        source_activity_id: Optional[str] = None,
        target_activity_id: Optional[str] = None
    ) -> List[Dict]:
        """Get transitions in an activity diagram with optional filtering."""
        try:
            params = {}
            if source_activity_id:
                params["source_activity_id"] = source_activity_id
            if target_activity_id:
                params["target_activity_id"] = target_activity_id

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/transitions",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get transitions: {str(e)}", exc_info=True)
            raise

    async def update_transition(
        self,
        diagram_id: str,
        transition_id: str,
        guard_condition: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """Update a transition in an activity diagram."""
        try:
            update_data = {}
            if guard_condition is not None:
                update_data["guard_condition"] = guard_condition
            if description is not None:
                update_data["description"] = description

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/transitions/{transition_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=update_data
                )
                response.raise_for_status()
                logger.info(f"Updated transition {transition_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to update transition: {str(e)}", exc_info=True)
            raise

    async def delete_transition(
        self,
        diagram_id: str,
        transition_id: str
    ) -> None:
        """Delete a transition from an activity diagram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/transitions/{transition_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                logger.info(f"Deleted transition {transition_id}")
        except Exception as e:
            logger.error(f"Failed to delete transition: {str(e)}", exc_info=True)
            raise

    async def create_activity_diagram_flow(
        self,
        username: str,
        password: str,
        system_name: str,
        system_description: str,
        plantuml_code: str
    ) -> Dict:
        """Convenience method to create an activity diagram with all necessary steps."""
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

            # Step 4: Create activity diagram
            diagram = await self.create_diagram(
                system_id=system_id,
                plantuml_code=plantuml_code,
                diagram_type="activity"
            )
            logger.info("Activity diagram created successfully")

            return {
                "project_id": project_id,
                "system_id": system_id,
                "diagram": diagram,
                "message": "Activity diagram creation flow completed successfully"
            }
        except Exception as e:
            logger.error(f"Failed to complete activity diagram creation flow: {str(e)}", exc_info=True)
            raise 

    async def add_class(
        self,
        diagram_id: str,
        name: str,
        description: Optional[str] = None
    ) -> Dict:
        """Add a class to a class diagram."""
        try:
            class_data = {
                "name": name
            }
            if description:
                class_data["description"] = description

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/classes",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=class_data
                )
                response.raise_for_status()
                logger.info(f"Added class {name} to diagram")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to add class: {str(e)}", exc_info=True)
            raise

    async def get_classes(
        self,
        diagram_id: str
    ) -> List[Dict]:
        """Get all classes in a class diagram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/classes",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get classes: {str(e)}", exc_info=True)
            raise

    async def update_class(
        self,
        diagram_id: str,
        class_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """Update a class in a class diagram."""
        try:
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if description is not None:
                update_data["description"] = description

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/classes/{class_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=update_data
                )
                response.raise_for_status()
                logger.info(f"Updated class {class_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to update class: {str(e)}", exc_info=True)
            raise

    async def delete_class(
        self,
        diagram_id: str,
        class_id: str
    ) -> None:
        """Delete a class from a class diagram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/classes/{class_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                logger.info(f"Deleted class {class_id}")
        except Exception as e:
            logger.error(f"Failed to delete class: {str(e)}", exc_info=True)
            raise

    async def add_method(
        self,
        diagram_id: str,
        class_id: str,
        name: str,
        return_type: str,
        visibility: str = "public",
        parameters: Optional[List[Dict[str, str]]] = None
    ) -> Dict:
        """Add a method to a class."""
        try:
            method_data = {
                "name": name,
                "return_type": return_type,
                "visibility": visibility
            }
            if parameters:
                method_data["parameters"] = parameters

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/classes/{class_id}/methods",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=method_data
                )
                response.raise_for_status()
                logger.info(f"Added method {name} to class {class_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to add method: {str(e)}", exc_info=True)
            raise

    async def get_methods(
        self,
        diagram_id: str,
        class_id: str
    ) -> List[Dict]:
        """Get all methods of a class."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/classes/{class_id}/methods",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get methods: {str(e)}", exc_info=True)
            raise

    async def update_method(
        self,
        diagram_id: str,
        class_id: str,
        method_id: str,
        name: Optional[str] = None,
        return_type: Optional[str] = None,
        visibility: Optional[str] = None,
        parameters: Optional[List[Dict[str, str]]] = None
    ) -> Dict:
        """Update a method in a class."""
        try:
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if return_type is not None:
                update_data["return_type"] = return_type
            if visibility is not None:
                update_data["visibility"] = visibility
            if parameters is not None:
                update_data["parameters"] = parameters

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/classes/{class_id}/methods/{method_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    json=update_data
                )
                response.raise_for_status()
                logger.info(f"Updated method {method_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to update method: {str(e)}", exc_info=True)
            raise

    async def delete_method(
        self,
        diagram_id: str,
        class_id: str,
        method_id: str
    ) -> None:
        """Delete a method from a class."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.ACC_API_BASE_URL}/diagrams/{diagram_id}/classes/{class_id}/methods/{method_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                response.raise_for_status()
                logger.info(f"Deleted method {method_id}")
        except Exception as e:
            logger.error(f"Failed to delete method: {str(e)}", exc_info=True)
            raise 

    async def add_node(
        self,
        diagram_id: str,
        name: str,
        node_type: str,
        description: Optional[str] = None,
        properties: Optional[Dict] = None
    ) -> Dict:
        """Add a node to a diagram."""
        try:
            if not self.access_token:
                raise ValueError("Not authenticated. Call authenticate() first.")
                
            # Create the request body with the required data structure
            request_data = {
                "id": str(uuid.uuid4()),  # Generate a unique ID for the node
                "cls": {
                    "namespace": "",
                    "name": name,
                    "type": node_type,
                    "role": node_type,
                    "localPrecondition": "",
                    "localPostcondition": "",
                    "body": "",
                    "operation": {
                        "name": name,
                        "description": description or "",
                        "type": "str",
                        "body": ""
                    },
                    "publish": [],
                    "subscribe": [],
                    "classes": {
                        "input": [],
                        "output": []
                    },
                    "application_models": [],
                    "page": ""
                }
            }

            # Add any additional properties if provided
            if properties:
                if "attributes" in properties:
                    request_data["cls"]["attributes"] = properties["attributes"]
                if "methods" in properties:
                    request_data["cls"]["methods"] = properties["methods"]

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ACC_API_BASE_URL}/diagram/{diagram_id}/node/",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    },
                    json=request_data
                )
                
                if response.status_code != 200:
                    logger.error(f"Add node failed with status {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    logger.error(f"Request body: {response.request.content}")
                
                response.raise_for_status()
                logger.info(f"Added node {name} of type {node_type} to diagram {diagram_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to add node: {str(e)}", exc_info=True)
            raise

    async def get_nodes(
        self,
        diagram_id: str,
        node_type: Optional[str] = None
    ) -> List[Dict]:
        """Get all nodes in a diagram with optional type filtering."""
        try:
            if not self.access_token:
                raise ValueError("Not authenticated. Call authenticate() first.")
                
            params = {}
            if node_type:
                params["type"] = node_type

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ACC_API_BASE_URL}/diagram/{diagram_id}/nodes",
                    headers={
                        "accept": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    },
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"Get nodes failed with status {response.status_code}")
                    logger.error(f"Response: {response.text}")
                
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get nodes: {str(e)}", exc_info=True)
            raise

    async def update_node(
        self,
        diagram_id: str,
        node_id: str,
        name: Optional[str] = None,
        node_type: Optional[str] = None,
        description: Optional[str] = None,
        properties: Optional[Dict] = None
    ) -> Dict:
        """Update a node in a diagram."""
        try:
            if not self.access_token:
                raise ValueError("Not authenticated. Call authenticate() first.")
                
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if node_type is not None:
                update_data["type"] = node_type
            if description is not None:
                update_data["description"] = description
            if properties is not None:
                update_data["properties"] = properties

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.ACC_API_BASE_URL}/diagram/{diagram_id}/nodes/{node_id}",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    },
                    json=update_data
                )
                
                if response.status_code != 200:
                    logger.error(f"Update node failed with status {response.status_code}")
                    logger.error(f"Response: {response.text}")
                    logger.error(f"Request body: {response.request.content}")
                
                response.raise_for_status()
                logger.info(f"Updated node {node_id} in diagram {diagram_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to update node: {str(e)}", exc_info=True)
            raise

    async def delete_node(
        self,
        diagram_id: str,
        node_id: str
    ) -> None:
        """Delete a node from a diagram."""
        try:
            if not self.access_token:
                raise ValueError("Not authenticated. Call authenticate() first.")
                
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.ACC_API_BASE_URL}/diagram/{diagram_id}/nodes/{node_id}",
                    headers={
                        "accept": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Delete node failed with status {response.status_code}")
                    logger.error(f"Response: {response.text}")
                
                response.raise_for_status()
                logger.info(f"Deleted node {node_id} from diagram {diagram_id}")
        except Exception as e:
            logger.error(f"Failed to delete node: {str(e)}", exc_info=True)
            raise 