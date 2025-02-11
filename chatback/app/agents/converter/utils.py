import logging
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

def validate_diagram_type(diagram_type: str, supported_diagrams: List[str]) -> None:
    """Validate if the diagram type is supported."""
    normalized_type = diagram_type.lower()
    if normalized_type == "classes":
        normalized_type = "class"
        
    if normalized_type not in supported_diagrams:
        logger.error(f"Unsupported diagram type: {diagram_type}")
        raise ValueError(
            f"Unsupported diagram type: {diagram_type}. "
            f"Supported types are: {', '.join(supported_diagrams)}"
        )

def extract_diagrams(content: str) -> List[Dict[str, str]]:
    """Extract individual UML diagrams from content."""
    try:
        diagrams = []
        current_type = None
        current_content = []
        
        for line in content.split('\n'):
            if '### Class Diagram' in line:
                if current_type and current_content:
                    diagrams.append({
                        'type': current_type,
                        'content': '\n'.join(current_content)
                    })
                current_type = 'class'
                current_content = []
            elif '### Activity Diagram' in line:
                if current_type and current_content:
                    diagrams.append({
                        'type': current_type,
                        'content': '\n'.join(current_content)
                    })
                current_type = 'activity'
                current_content = []
            elif '### Use Case Diagram' in line:
                if current_type and current_content:
                    diagrams.append({
                        'type': current_type,
                        'content': '\n'.join(current_content)
                    })
                current_type = 'usecase'
                current_content = []
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
        
    except Exception as e:
        logger.error(f"Error extracting diagrams: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to extract diagrams: {str(e)}") from e

def validate_json_structure(json_data: Dict, diagram_type: str) -> None:
    """Validate the JSON structure for a specific diagram type."""
    try:
        if diagram_type == "class":
            required_keys = ["classes", "relationships"]
            class_keys = ["name", "attributes", "methods"]
            relationship_keys = ["source", "target", "type"]
        elif diagram_type == "activity":
            required_keys = ["activities", "transitions"]
            activity_keys = ["id", "name", "type"]
            transition_keys = ["source", "target"]
        elif diagram_type == "usecase":
            required_keys = ["actors", "useCases", "relationships"]
            actor_keys = ["id", "name"]
            usecase_keys = ["id", "name"]
            relationship_keys = ["source", "target", "type"]
        else:
            raise ValueError(f"Unknown diagram type: {diagram_type}")
            
        # Check for required top-level keys
        missing_keys = [key for key in required_keys if key not in json_data]
        if missing_keys:
            raise ValueError(f"Missing required keys in JSON: {', '.join(missing_keys)}")
            
        # Validate structure based on diagram type
        if diagram_type == "class":
            for cls in json_data["classes"]:
                missing = [key for key in class_keys if key not in cls]
                if missing:
                    raise ValueError(f"Class missing required keys: {', '.join(missing)}")
                    
            for rel in json_data["relationships"]:
                missing = [key for key in relationship_keys if key not in rel]
                if missing:
                    raise ValueError(f"Relationship missing required keys: {', '.join(missing)}")
                    
        elif diagram_type == "activity":
            for act in json_data["activities"]:
                missing = [key for key in activity_keys if key not in act]
                if missing:
                    raise ValueError(f"Activity missing required keys: {', '.join(missing)}")
                    
            for trans in json_data["transitions"]:
                missing = [key for key in transition_keys if key not in trans]
                if missing:
                    raise ValueError(f"Transition missing required keys: {', '.join(missing)}")
                    
        elif diagram_type == "usecase":
            for actor in json_data["actors"]:
                missing = [key for key in actor_keys if key not in actor]
                if missing:
                    raise ValueError(f"Actor missing required keys: {', '.join(missing)}")
                    
            for uc in json_data["useCases"]:
                missing = [key for key in usecase_keys if key not in uc]
                if missing:
                    raise ValueError(f"Use case missing required keys: {', '.join(missing)}")
                    
            for rel in json_data["relationships"]:
                missing = [key for key in relationship_keys if key not in rel]
                if missing:
                    raise ValueError(f"Relationship missing required keys: {', '.join(missing)}")
                    
    except Exception as e:
        logger.error(f"Error validating JSON structure: {str(e)}", exc_info=True)
        if isinstance(e, ValueError):
            raise
        raise RuntimeError(f"Failed to validate JSON structure: {str(e)}") from e

def parse_json_response(response_content: str) -> Dict:
    """Parse and validate JSON response from LLM."""
    try:
        # Remove markdown code block if present
        content = response_content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
            
        content = content.strip()
        
        try:
            json_data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON generated: {str(e)}")
            logger.error(f"Raw content: {content}")
            raise ValueError("Failed to generate valid JSON structure")
            
        return json_data
        
    except Exception as e:
        logger.error(f"Error parsing JSON response: {str(e)}", exc_info=True)
        if isinstance(e, ValueError):
            raise
        raise RuntimeError(f"Failed to parse JSON response: {str(e)}") from e 