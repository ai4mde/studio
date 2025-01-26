from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    group_id = Column(Integer, ForeignKey("groups.id"))

    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user")
    group = relationship("Group", back_populates="users")

    def to_token_payload(self) -> dict:
        """Return user data for token payload"""
        return {
            "sub": str(self.id),
            "email": self.email,
            "username": self.username,
            "group_name": self.group.name if self.group else None
        }
  