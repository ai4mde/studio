from typing import Dict, Optional
import logging
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.agents.base import BaseAgent
from .utils import validate_review_content, format_review_report, analyze_review_metrics

logger = logging.getLogger(__name__)

class ReviewAgent(BaseAgent):
    """Agent responsible for reviewing SRS documents and UML diagrams."""
    
    def __init__(self, session_id: str, username: str):
        super().__init__(
            session_id=session_id,
            username=username,
            agent_name=settings.AGENT_THOMPSON_NAME,
            model_name=settings.AGENT_THOMPSON_MODEL,
            temperature=settings.AGENT_THOMPSON_TEMPERATURE,
            redis_prefix="review"
        )
        
        logger.info(f"{self.agent_name} initialized successfully")

    async def review_document(self, document_content: str, uml_diagrams: str) -> Dict[str, str]:
        """Review the SRS document and UML diagrams for quality and completeness."""
        try:
            logger.info(f"Starting document review for session {self.session_id}")
            
            # Validate input content
            validate_review_content(document_content, uml_diagrams)
            
            # Create prompt for document review
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""You are {self.agent_name}, the senior quality assurance specialist.
                Your purpose is to maintain the highest standards of documentation quality.
                Review the provided SRS document and UML diagrams for:

                1. Completeness of requirements
                2. Clarity and precision of language
                3. Consistency between requirements
                4. Proper requirement traceability
                5. UML diagram accuracy and completeness
                6. Alignment between diagrams and specifications
                7. Technical accuracy and feasibility
                8. Compliance with IEEE 830 standards

                Format your response as a formal review report with these sections:
                # Document Review Report
                ## Requirements Analysis
                ## Technical Accuracy
                ## Completeness Check
                ## Consistency Verification
                ## Recommendations

                For each issue found, prefix with severity:
                - CRITICAL: for show-stopping issues
                - MAJOR: for significant problems
                - MINOR: for style and clarity issues"""),
                ("human", "Review this SRS document and UML diagrams:\n\nSRS Document:\n{document}\n\nUML Diagrams:\n{diagrams}")
            ])
            
            # Generate review report
            response = await self._invoke_llm(
                system_prompt=prompt.messages[0].content,
                user_prompt=prompt.messages[-1].content,
                variables={
                    "document": document_content,
                    "diagrams": uml_diagrams
                }
            )
            
            # Format and analyze review report
            formatted_report = format_review_report(response)
            metrics = analyze_review_metrics(formatted_report)
            
            # Combine results
            result = {
                "review_report": formatted_report["review_report"],
                "message": f"Quality assurance review completed. - {self.agent_name}",
                **metrics
            }
            
            # Log review completion with metrics
            logger.info(
                f"Review completed for session {self.session_id}. "
                f"Quality score: {metrics['metrics']['quality_score']}%, "
                f"Issues found: {sum(metrics['metrics'].values()) - metrics['metrics']['quality_score']}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error during document review: {str(e)}", exc_info=True)
            if isinstance(e, ValueError):
                raise
            raise RuntimeError(f"Failed to complete document review: {str(e)}") from e 