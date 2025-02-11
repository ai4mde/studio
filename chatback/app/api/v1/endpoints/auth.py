from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserStatus
from app.schemas.token import Token
from datetime import timedelta
from typing import Any
import logging
from app.crud import crud_user
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=UserSchema)
def register(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
    user = db.query(User).filter(User.username == user_in.username).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this username already exists.",
        )
    
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=security.get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    Uses username for login.
    """
    try:
        # Get user with group preloaded
        stmt = (
            select(User)
            .options(selectinload(User.group))
            .where(User.username == form_data.username)
        )
        
        async with AsyncSessionLocal() as session:
            # Execute query and get result
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user or not security.verify_password(form_data.password, user.hashed_password):
                logger.warning(f"Login failed for username: {form_data.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                )
            elif not user.is_active:
                logger.warning(f"Inactive user attempted login: {form_data.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Inactive user",
                )

            logger.info(f"Successful login for user: {user.username}")
            
            # Create and return token with additional info
            token = Token(
                access_token=security.create_access_token(
                    data={"sub": user.username}
                ),
                token_type="bearer",
                id=str(user.id),
                username=user.username,
                group_name=user.group.name if user.group else None
            )
            logger.info(f"Generated token for user: {user.username}")
            return token

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

@router.get("/status", response_model=UserStatus)
async def get_user_status(
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get current user status.
    
    Requires authentication via Bearer token.
    
    Returns:
        UserStatus: Current user information including id, username, and email
    
    Raises:
        HTTPException: 401 if not authenticated or token is invalid
    """
    return UserStatus(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        token=None
    )

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("Authorization")
    return {"message": "Successfully logged out"} 