from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

class ChatSessionBase(BaseModel):
    title: str

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionUpdate(ChatSessionBase):
    pass

class ChatSession(ChatSessionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatMessageBase(BaseModel):
    content: str

class ChatMessageCreate(ChatMessageBase):
    message_uuid: str

class ChatMessage(ChatMessageBase):
    id: int
    session_id: int
    role: str
    message_uuid: str
    created_at: Optional[datetime] = None
    content: str
    progress: Optional[float] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: str}
    )

class ChatResponse(BaseModel):
    message: str
    session_id: int
    message_uuid: str
    progress: float | None = None

class MessageResponse(BaseModel):
    message_uuid: str
    user_id: int
    content: str
    timestamp: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={UUID: str}
    )
  