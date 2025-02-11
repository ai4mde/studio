from pydantic import BaseModel, EmailStr, StringConstraints, field_validator
from typing import Annotated, Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str
    group_id: int | None = None

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserUpdate(UserBase):
    password: str | None = None
    group_id: int | None = None

class User(UserBase):
    id: int
    is_active: bool
    group_id: int | None = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenData(BaseModel):
    username: Optional[str] = None

class UserStatus(BaseModel):
    id: int
    username: str
    email: str
    token: Optional[str] = None