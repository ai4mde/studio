from typing import Optional
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from .base import CRUDBase
import logging

logger = logging.getLogger(__name__)

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def authenticate(self, db, *, username: str, password: str) -> Optional[User]:
        """Authenticate user by username and password"""
        try:
            logger.info(f"Attempting authentication for username: {username}")
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"No user found with username: {username}")
                return None

            logger.info(f"Found user: {user.username}, verifying password")
            if not verify_password(password, user.hashed_password):
                logger.warning("Password verification failed")
                return None

            logger.info("Authentication successful")
            return user
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None

    async def get_by_username(self, db, *, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create new user"""
        try:
            db_obj = User(
                email=obj_in.email,
                username=obj_in.username,
                hashed_password=get_password_hash(obj_in.password),
                is_active=True,
                group_id=obj_in.group_id if hasattr(obj_in, 'group_id') else None
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

crud_user = CRUDUser(User) 