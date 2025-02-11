from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ChatMemoryManager(BaseChatMessageHistory):
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history = RedisChatMessageHistory(
            session_id=session_id,
            url=settings.REDIS_URL,
            ttl=settings.REDIS_DATA_TTL
        )

    @property
    def messages(self) -> list[BaseMessage]:
        """Sync method to get messages"""
        return self.history.messages

    async def aget_messages(self) -> list[BaseMessage]:
        """Async method to get messages"""
        return self.messages

    def add_message(self, role: str, content: str) -> None:
        """Sync method to add a message"""
        try:
            if role == "user":
                self.history.add_user_message(content)
            elif role == "assistant":
                self.history.add_ai_message(content)
        except Exception as e:
            logger.error(f"Error adding message to history: {str(e)}")
            raise

    async def aadd_message(self, role: str, content: str) -> None:
        """Async method to add a message"""
        self.add_message(role, content)

    def add_messages(self, messages: list[BaseMessage]) -> None:
        """Add multiple messages to the store"""
        for message in messages:
            if message.type == "human":
                self.history.add_user_message(message.content)
            elif message.type == "ai":
                self.history.add_ai_message(message.content)

    async def aadd_messages(self, messages: list[BaseMessage]) -> None:
        """Add multiple messages to the store async"""
        self.add_messages(messages)

    def clear(self) -> None:
        """Clear message history"""
        try:
            self.history.clear()
        except Exception as e:
            logger.error(f"Error clearing chat history: {str(e)}")
            raise

    async def aclear(self) -> None:
        """Clear message history async"""
        self.clear()
