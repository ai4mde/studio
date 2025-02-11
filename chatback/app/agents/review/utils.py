import logging
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

def validate_review_content(document_content: str, uml_diagrams: str) -> None:
    """Validate the content to be reviewed."""
    try:
        if not document_content or not document_content.strip():
            logger.error("Empty document content provided for review")
            raise ValueError("Document content cannot be empty")
            
        if not uml_diagrams or not uml_diagrams.strip():
            logger.error("Empty UML diagrams provided for review")
            raise ValueError("UML diagrams cannot be empty")
            
        # Check for required SRS sections
        required_sections = [
            "# Introduction",
            "## Purpose",
            "## Scope",
            "# Requirements",
            "## Functional Requirements",
            "## Non-Functional Requirements"
        ]
        
        missing_sections = [
            section for section in required_sections 
            if section.lower() not in document_content.lower()
        ]
        
        if missing_sections:
            logger.error(f"Missing required SRS sections: {missing_sections}")
            raise ValueError(f"Document missing required sections: {', '.join(missing_sections)}")
            
        # Check for UML diagram sections
        required_diagrams = ["@startuml", "@enduml"]
        missing_diagrams = [
            marker for marker in required_diagrams 
            if marker not in uml_diagrams
        ]
        
        if missing_diagrams:
            logger.error(f"Invalid UML diagram format: missing {missing_diagrams}")
            raise ValueError("UML diagrams have invalid format")
            
    except Exception as e:
        logger.error(f"Error validating review content: {str(e)}", exc_info=True)
        if isinstance(e, ValueError):
            raise
        raise RuntimeError(f"Failed to validate review content: {str(e)}") from e

def format_review_report(review_content: str) -> Dict[str, str]:
    """Format the review report with consistent structure."""
    try:
        if not review_content or not review_content.strip():
            logger.error("Empty review content provided")
            raise ValueError("Review content cannot be empty")
            
        # Ensure the review has a clear structure
        sections = [
            "# Document Review Report",
            "## Requirements Analysis",
            "## Technical Accuracy",
            "## Completeness Check",
            "## Consistency Verification",
            "## Recommendations"
        ]
        
        # Check if all sections are present
        missing_sections = [
            section for section in sections 
            if section.lower() not in review_content.lower()
        ]
        
        if missing_sections:
            logger.error(f"Review missing required sections: {missing_sections}")
            raise ValueError(f"Review report missing sections: {', '.join(missing_sections)}")
            
        return {
            "review_report": review_content,
            "sections_reviewed": len(sections) - len(missing_sections),
            "is_complete": len(missing_sections) == 0
        }
        
    except Exception as e:
        logger.error(f"Error formatting review report: {str(e)}", exc_info=True)
        if isinstance(e, ValueError):
            raise
        raise RuntimeError(f"Failed to format review report: {str(e)}") from e

def analyze_review_metrics(review_report: Dict[str, str]) -> Dict[str, any]:
    """Analyze the review report and extract key metrics."""
    try:
        if not review_report or "review_report" not in review_report:
            logger.error("Invalid review report provided for analysis")
            raise ValueError("Invalid review report format")
            
        content = review_report["review_report"]
        
        # Count issues by severity
        critical_issues = content.lower().count("critical:")
        major_issues = content.lower().count("major:")
        minor_issues = content.lower().count("minor:")
        
        # Calculate overall quality score (example metric)
        total_issues = critical_issues * 3 + major_issues * 2 + minor_issues
        max_acceptable_issues = 10  # Example threshold
        quality_score = max(0, 100 - (total_issues / max_acceptable_issues * 100))
        
        return {
            "metrics": {
                "critical_issues": critical_issues,
                "major_issues": major_issues,
                "minor_issues": minor_issues,
                "quality_score": round(quality_score, 2)
            },
            "needs_revision": quality_score < 80  # Example threshold
        }
        
    except Exception as e:
        logger.error(f"Error analyzing review metrics: {str(e)}", exc_info=True)
        if isinstance(e, ValueError):
            raise
        raise RuntimeError(f"Failed to analyze review metrics: {str(e)}") from e 