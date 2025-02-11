import logging
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

def validate_content(current_content: Dict) -> None:
    """Validate the content structure for modification."""
    try:
        if not current_content:
            logger.error("No current content provided for analysis")
            raise ValueError("Current content is required for analysis")
            
        # Validate current content structure
        required_keys = ["srs", "diagrams"]
        missing_keys = [key for key in required_keys if key not in current_content]
        if missing_keys:
            logger.error(f"Missing required content keys: {missing_keys}")
            raise ValueError(f"Current content missing required sections: {', '.join(missing_keys)}")
            
        # Validate SRS content
        if not current_content["srs"] or not current_content["srs"].strip():
            logger.error("Empty SRS content provided")
            raise ValueError("SRS content cannot be empty")
            
        # Validate diagrams content
        if not current_content["diagrams"] or not isinstance(current_content["diagrams"], dict):
            logger.error("Invalid diagrams content provided")
            raise ValueError("Diagrams content must be a non-empty dictionary")
            
    except Exception as e:
        logger.error(f"Error validating content: {str(e)}", exc_info=True)
        if isinstance(e, ValueError):
            raise
        raise RuntimeError(f"Failed to validate content: {str(e)}") from e

def analyze_change_impact(suggestions: Dict, current_content: Dict) -> Dict:
    """Analyze the impact of suggested changes."""
    try:
        if not suggestions:
            raise ValueError("No modification suggestions provided")
            
        # Initialize impact analysis
        impact = {
            "srs_changes": [],
            "diagram_changes": [],
            "dependencies": [],
            "risk_level": "low"
        }
        
        # Analyze SRS changes
        if "srs_modifications" in suggestions:
            srs_changes = suggestions["srs_modifications"]
            impact["srs_changes"] = [
                change["section"] for change in srs_changes
                if isinstance(change, dict) and "section" in change
            ]
            
        # Analyze diagram changes
        if "diagram_modifications" in suggestions:
            diagram_changes = suggestions["diagram_modifications"]
            impact["diagram_changes"] = [
                change["type"] for change in diagram_changes
                if isinstance(change, dict) and "type" in change
            ]
            
        # Identify dependencies
        if impact["srs_changes"] and impact["diagram_changes"]:
            impact["dependencies"].append(
                "Changes affect both documentation and diagrams - synchronization required"
            )
            
        # Calculate risk level
        total_changes = len(impact["srs_changes"]) + len(impact["diagram_changes"])
        if total_changes > 10:
            impact["risk_level"] = "high"
        elif total_changes > 5:
            impact["risk_level"] = "medium"
            
        return impact
        
    except Exception as e:
        logger.error(f"Error analyzing change impact: {str(e)}", exc_info=True)
        if isinstance(e, ValueError):
            raise
        raise RuntimeError(f"Failed to analyze change impact: {str(e)}") from e

def validate_modifications(modifications: Dict) -> None:
    """Validate the structure of modification suggestions."""
    try:
        if not modifications:
            raise ValueError("No modifications provided")
            
        required_keys = ["srs_modifications", "diagram_modifications"]
        missing_keys = [key for key in required_keys if key not in modifications]
        if missing_keys:
            raise ValueError(f"Missing required modification sections: {', '.join(missing_keys)}")
            
        # Validate SRS modifications
        if "srs_modifications" in modifications:
            srs_mods = modifications["srs_modifications"]
            if not isinstance(srs_mods, list):
                raise ValueError("SRS modifications must be a list")
                
            for mod in srs_mods:
                if not isinstance(mod, dict):
                    raise ValueError("Each SRS modification must be a dictionary")
                if "section" not in mod or "changes" not in mod:
                    raise ValueError("SRS modification missing required keys: section, changes")
                    
        # Validate diagram modifications
        if "diagram_modifications" in modifications:
            diagram_mods = modifications["diagram_modifications"]
            if not isinstance(diagram_mods, list):
                raise ValueError("Diagram modifications must be a list")
                
            for mod in diagram_mods:
                if not isinstance(mod, dict):
                    raise ValueError("Each diagram modification must be a dictionary")
                if "type" not in mod or "changes" not in mod:
                    raise ValueError("Diagram modification missing required keys: type, changes")
                    
    except Exception as e:
        logger.error(f"Error validating modifications: {str(e)}", exc_info=True)
        if isinstance(e, ValueError):
            raise
        raise RuntimeError(f"Failed to validate modifications: {str(e)}") from e

def track_modification_history(modifications: Dict, session_id: str) -> Dict:
    """Track modification history with timestamps."""
    from datetime import datetime
    
    try:
        timestamp = datetime.utcnow().isoformat()
        
        history_entry = {
            "timestamp": timestamp,
            "session_id": session_id,
            "modifications": {
                "srs_count": len(modifications.get("srs_modifications", [])),
                "diagram_count": len(modifications.get("diagram_modifications", [])),
                "sections_modified": [
                    mod["section"] 
                    for mod in modifications.get("srs_modifications", [])
                    if isinstance(mod, dict) and "section" in mod
                ],
                "diagrams_modified": [
                    mod["type"] 
                    for mod in modifications.get("diagram_modifications", [])
                    if isinstance(mod, dict) and "type" in mod
                ]
            }
        }
        
        return history_entry
        
    except Exception as e:
        logger.error(f"Error tracking modification history: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to track modification history: {str(e)}") from e 