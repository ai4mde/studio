from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class GroupUpdate(GroupBase):
    pass

class GroupInDBBase(GroupBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class Group(GroupInDBBase):
    pass

class GroupWithUsers(GroupInDBBase):
    users: List["UserBase"]

class UserInGroup(BaseModel):
    id: int
    email: str
    username: str

    model_config = ConfigDict(from_attributes=True)

# Avoid circular imports
from app.schemas.user import UserBase
GroupWithUsers.model_rebuild() 