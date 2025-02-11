from typing import Dict, Optional
import logging
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.agents.base import BaseAgent
from .utils import (
    validate_content,
    analyze_change_impact,
    validate_modifications,
    track_modification_history
)

logger = logging.getLogger(__name__)

class ModificationAgent(BaseAgent):
    """Agent responsible for handling document and diagram modifications."""
    
    def __init__(self, session_id: str, username: str):
        super().__init__(
            session_id=session_id,
            username=username,
            agent_name=settings.AGENT_WHITE_NAME,
            model_name=settings.AGENT_WHITE_MODEL,
            temperature=settings.AGENT_WHITE_TEMPERATURE,
            redis_prefix="modification"
        )
        
        logger.info(f"{self.agent_name} initialized successfully")

    async def analyze_change_request(self, request: str, current_content: Dict) -> Dict:
        """Analyze user's change request and determine required modifications."""
        try:
            logger.info(f"Analyzing change request for session {self.session_id}")
            
            # Validate current content
            validate_content(current_content)
            
            # Create prompt for change analysis
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, the modification specialist.
                Analyze the user's change request and determine:
                1. What needs to be modified (SRS sections, UML diagrams, or both)
                2. The specific changes required
                3. Impact analysis of the changes
                4. Dependencies between document and diagrams
                
                Format your response as a JSON object with this structure:
                {{
                    "srs_modifications": [
                        {{
                            "section": "section name or path",
                            "changes": "detailed description of changes needed",
                            "reason": "justification for the change"
                        }}
                    ],
                    "diagram_modifications": [
                        {{
                            "type": "class|activity|usecase",
                            "changes": "detailed description of changes needed",
                            "reason": "justification for the change"
                        }}
                    ]
                }}"""),
                ("human", f"""Current content: {json.dumps(current_content)}
                
                Change request: {request}
                
                Analyze the changes needed.""")
            ])
            
            # Generate change analysis
            response = await self._invoke_llm(
                system_prompt=prompt.messages[0].content,
                user_prompt=prompt.messages[-1].content,
                variables={}
            )
            
            # Parse and validate suggestions
            try:
                suggestions = json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response: {str(e)}")
                raise ValueError("Failed to parse change suggestions")
                
            # Validate modification structure
            validate_modifications(suggestions)
            
            # Analyze impact
            impact = analyze_change_impact(suggestions, current_content)
            
            # Track modification history
            history = track_modification_history(suggestions, self.session_id)
            
            return {
                "suggestions": suggestions,
                "impact_analysis": impact,
                "history": history,
                "message": f"Change analysis completed. - {self.agent_name}"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing change request: {str(e)}", exc_info=True)
            if isinstance(e, ValueError):
                raise
            raise RuntimeError(f"Failed to analyze change request: {str(e)}") from e

    async def apply_changes(self, suggestions: Dict, current_content: Dict) -> Dict:
        """Apply approved changes to documents and diagrams."""
        try:
            logger.info(f"Applying changes for session {self.session_id}")
            
            # Validate inputs
            if not suggestions:
                raise ValueError("No modification suggestions provided")
            validate_content(current_content)
            validate_modifications(suggestions)
            
            # Create prompt for SRS modifications
            srs_prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, applying changes to the SRS document.
                Modify the document according to the suggested changes.
                Maintain document structure and formatting.
                Return the complete updated document."""),
                ("human", f"""Current SRS: {current_content['srs']}
                
                Suggested changes: {json.dumps(suggestions['srs_modifications'])}
                
                Apply these changes and return the updated document.""")
            ])
            
            # Create prompt for diagram modifications
            diagram_prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, applying changes to UML diagrams.
                Modify the PlantUML code according to the suggested changes.
                Maintain diagram consistency and relationships.
                Return the updated PlantUML code for each modified diagram."""),
                ("human", f"""Current diagrams: {json.dumps(current_content['diagrams'])}
                
                Suggested changes: {json.dumps(suggestions['diagram_modifications'])}
                
                Apply these changes and return the updated diagrams.""")
            ])
            
            # Apply SRS changes
            updated_srs = await self._invoke_llm(
                system_prompt=srs_prompt.messages[0].content,
                user_prompt=srs_prompt.messages[-1].content,
                variables={}
            )
            
            # Apply diagram changes
            updated_diagrams_response = await self._invoke_llm(
                system_prompt=diagram_prompt.messages[0].content,
                user_prompt=diagram_prompt.messages[-1].content,
                variables={}
            )
            
            try:
                updated_diagrams = json.loads(updated_diagrams_response)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid diagram modification result: {str(e)}")
                raise ValueError("Failed to generate valid diagram modifications")
            
            # Track modification history
            history = track_modification_history(suggestions, self.session_id)
            
            return {
                "updated_content": {
                    "srs": updated_srs,
                    "diagrams": updated_diagrams
                },
                "history": history,
                "message": f"Changes have been applied successfully. - {self.agent_name}"
            }
            
        except Exception as e:
            logger.error(f"Error applying changes: {str(e)}", exc_info=True)
            if isinstance(e, ValueError):
                raise
            raise RuntimeError(f"Failed to apply changes: {str(e)}") from e 