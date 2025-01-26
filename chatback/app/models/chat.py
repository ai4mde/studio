from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.db.base_class import Base
import uuid

class ChatRole(str, enum.Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"

class ConversationState(str, enum.Enum):
    INTERVIEW = "INTERVIEW"
    DOCUMENT = "DOCUMENT"
    COMPLETED = "COMPLETED"

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=False)

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    state = relationship("ChatState", back_populates="session", uselist=False, cascade="all, delete-orphan")
    user = relationship("User", back_populates="chat_sessions")
    group = relationship("Group", back_populates="chat_sessions")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    message_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    role = Column(SQLEnum(ChatRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    message_metadata = Column(JSONB, nullable=True)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_uuid": str(self.message_uuid),
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at
        }

class ChatState(Base):
    __tablename__ = "chat_state"

    session_id = Column(Integer, ForeignKey("chat_sessions.id"), primary_key=True)
    current_section = Column(Integer, nullable=False)
    current_question_index = Column(Integer, nullable=False)
    state = Column(SQLEnum(ConversationState), nullable=False)
    progress = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="state")