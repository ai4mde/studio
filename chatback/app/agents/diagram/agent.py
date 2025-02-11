from typing import Dict, List
import logging
from app.core.config import settings
from app.agents.base import BaseAgent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

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
        
        # Initialize summarization LLM
        self.summary_llm = ChatOpenAI(
            model_name=settings.AGENT_SUMMARY_MODEL,
            temperature=0.0,
            api_key=settings.OPENAI_API_KEY,
            request_timeout=settings.OPENAI_TIMEOUT,
            max_retries=settings.OPENAI_MAX_RETRIES
        )

    def _chunk_conversation(self, messages: List, chunk_size: int = 10) -> List[List]:
        """Split conversation into smaller chunks for processing."""
        return [messages[i:i + chunk_size] for i in range(0, len(messages), chunk_size)]

    async def _summarize_chunk(self, messages: List) -> str:
        """Summarize a single chunk of conversation."""
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
            
            user_prompt = "Summarize this conversation chunk for UML diagram generation: {conversation}"
            
            return await self._invoke_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                variables={"conversation": "\n".join(conversation)},
                temperature=0.0
            )
            
        except Exception as e:
            logger.error(f"Error summarizing chunk: {str(e)}", exc_info=True)
            # If summarization fails, return original messages joined
            return "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" 
                if isinstance(msg, dict) 
                else f"{msg.type}: {msg.content}"
                for msg in messages
            ])

    async def _summarize_conversation(self, messages: List) -> str:
        """Summarize long conversations to reduce token count."""
        try:
            if not messages:
                return ""
            
            # Split conversation into manageable chunks
            chunks = self._chunk_conversation(messages)
            logger.info(f"Split conversation into {len(chunks)} chunks")
            
            # Summarize each chunk
            chunk_summaries = []
            for chunk in chunks:
                summary = await self._summarize_chunk(chunk)
                if summary:
                    chunk_summaries.append(summary)
            
            # If we have multiple summaries, combine them
            if len(chunk_summaries) > 1:
                system_prompt = """Combine these conversation summaries into a single coherent summary.
                Focus on the most important information for UML diagram generation:
                - System components and their relationships
                - Main use cases and actors
                - Key workflows and sequences
                - Important constraints and business rules"""
                
                user_prompt = "Combine these summaries into one: {summaries}"
                
                return await self._invoke_llm(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    variables={"summaries": "\n\n---\n\n".join(chunk_summaries)},
                    temperature=0.0
                )
            elif chunk_summaries:
                return chunk_summaries[0]
            else:
                return ""
            
        except Exception as e:
            logger.error(f"Error summarizing conversation: {str(e)}", exc_info=True)
            # If summarization completely fails, return a truncated version of the original
            all_text = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}" 
                if isinstance(msg, dict) 
                else f"{msg.type}: {msg.content}"
                for msg in messages
            ])
            # Take first ~10000 characters as emergency fallback
            return all_text[:10000] + "... (truncated)"

    async def generate_uml_diagrams(self, messages: list) -> Dict[str, str]:
        """Generate PlantUML code for various UML diagrams."""
        try:
            # First summarize the conversation if it's long
            conversation_summary = await self._summarize_conversation(messages)
            
            system_prompt = f"""You are {self.agent_name}, visualization specialist for the Matrix.
            Your purpose is to create perfect system visualizations through UML diagrams.
            Based on the provided requirements discussion, generate PlantUML code for:
            1. Class Diagram showing the main entities and their relationships
            2. Use Case Diagram showing system actors and main use cases
            3. Sequence Diagram for the most important workflow
            
            Format each diagram with clear headers and PlantUML code blocks."""
            
            user_prompt = "Generate UML diagrams based on this conversation summary: {conversation}"
            
            uml_content = await self._invoke_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                variables={"conversation": conversation_summary}
            )
            
            # Validate UML content
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