from typing import Enum
from sqlalchemy import Column
from sqlalchemy.types import Enum as SQLAlchemyEnum

class ChatRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"

# Make sure your SQLAlchemy model uses this enum
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    role = Column(SQLAlchemyEnum(ChatRole, name="chatrole")) 