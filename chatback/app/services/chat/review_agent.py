from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from typing import Dict
import logging
from langchain_community.chat_message_histories import RedisChatMessageHistory
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class ReviewAgent:
    def __init__(self, session_id: str, username: str):
        try:
            logger.info(f"Initializing ReviewAgent for session {session_id}")
            self.session_id = session_id
            self.username = username
            
            # Get agent name from settings
            self.agent_name = settings.AGENT_THOMPSON_NAME
            
            # Initialize LLM for document review
            self.llm = ChatOpenAI(
                model_name=settings.AGENT_THOMPSON_MODEL,
                temperature=settings.AGENT_THOMPSON_TEMPERATURE,
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
            retry = Retry(ExponentialBackoff(), settings.REDIS_RETRY_ATTEMPTS)
            
            # Initialize Redis client
            self.message_history = RedisChatMessageHistory(
                session_id=f"review_{session_id}",
                url=redis_url,
                key_prefix="review:",
                ttl=settings.REDIS_DATA_TTL
            )
            
            logger.info(f"{self.agent_name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.agent_name}: {str(e)}", exc_info=True)
            raise

    async def review_document(self, document_content: str, uml_diagrams: str) -> Dict[str, str]:
        """Review the SRS document and UML diagrams for quality and completeness."""
        try:
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

                If any issues are found, provide specific feedback for correction.
                If the document meets standards, provide approval.
                
                Format your response as a formal review report."""),
                ("human", "Review this SRS document and UML diagrams:\n\nSRS Document:\n{document}\n\nUML Diagrams:\n{diagrams}")
            ])
            
            chain = prompt | self.llm
            response = await chain.ainvoke({
                "document": document_content,
                "diagrams": uml_diagrams
            })
            
            return {
                "review_report": response.content,
                "message": f"Quality assurance review completed. - {self.agent_name}"
            }
            
        except Exception as e:
            logger.error(f"Error during document review: {str(e)}", exc_info=True)
            raise 