from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.core.config import settings
from typing import Dict, Optional
import logging
from langchain_community.chat_message_histories import RedisChatMessageHistory
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all agents with common functionality."""
    
    def __init__(
        self,
        session_id: str,
        username: str,
        agent_name: str,
        model_name: str,
        temperature: float,
        redis_prefix: str = "base"
    ):
        try:
            logger.info(f"Initializing {agent_name} for session {session_id}")
            self.session_id = session_id
            self.username = username
            self.agent_name = agent_name
            
            # Initialize LLM
            self.llm = ChatOpenAI(
                model_name=model_name,
                temperature=temperature,
                api_key=settings.OPENAI_API_KEY,
                request_timeout=settings.OPENAI_TIMEOUT,
                max_retries=settings.OPENAI_MAX_RETRIES
            )
            
            # Setup Redis client
            redis_url = (
                f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
                f"?socket_timeout={settings.REDIS_SOCKET_TIMEOUT}"
                f"&socket_connect_timeout={settings.REDIS_CONNECT_TIMEOUT}"
            )
            
            # Initialize Redis client with retry logic
            self.message_history = self._init_redis(redis_url, redis_prefix)
            
            logger.info(f"{self.agent_name} initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize {agent_name}: {str(e)}", exc_info=True)
            raise
    
    @retry(
        stop=stop_after_attempt(settings.REDIS_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=settings.REDIS_RETRY_DELAY)
    )
    def _init_redis(self, redis_url: str, prefix: str) -> RedisChatMessageHistory:
        """Initialize Redis chat message history with retry logic."""
        return RedisChatMessageHistory(
            session_id=f"{prefix}_{self.session_id}",
            url=redis_url,
            key_prefix=f"{prefix}:",
            ttl=settings.REDIS_DATA_TTL
        )
    
    async def _invoke_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        variables: Dict,
        temperature: Optional[float] = None
    ) -> str:
        """Common method to invoke LLM with proper error handling."""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt)
            ])
            
            # Create a new LLM instance if temperature override is provided
            llm = self.llm
            if temperature is not None:
                llm = ChatOpenAI(
                    model_name=self.llm.model_name,
                    temperature=temperature,
                    api_key=settings.OPENAI_API_KEY,
                    request_timeout=settings.OPENAI_TIMEOUT,
                    max_retries=settings.OPENAI_MAX_RETRIES
                )
            
            chain = prompt | llm
            response = await chain.ainvoke(variables)
            return response.content
            
        except Exception as e:
            logger.error(f"Error invoking LLM: {str(e)}", exc_info=True)
            raise 