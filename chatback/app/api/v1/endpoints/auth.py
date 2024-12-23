from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, Token, UserStatus
from datetime import timedelta
from typing import Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Registration endpoint disabled
# Use create_user script to create users:
# `docker exec -it studio-chatback-1 python scripts/create_user.py`
#
#@router.post("/register", response_model=UserSchema)
#def register(
#    *,
#    db: Session = Depends(deps.get_db),
#    user_in: UserCreate,
#) -> Any:
#    user = db.query(User).filter(User.email == user_in.email).first()
#    if user:
#        raise HTTPException(
#            status_code=400,
#            detail="A user with this email already exists.",
#        )
#    user = db.query(User).filter(User.username == user_in.username).first()
#    if user:
#        raise HTTPException(
#            status_code=400,
#            detail="A user with this username already exists.",
#        )
#    
#    user = User(
#        email=user_in.email,
#        username=user_in.username,
#        hashed_password=security.get_password_hash(user_in.password),
#    )
#    db.add(user)
#    db.commit()
#    db.refresh(user)
#    return user


@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """Authenticate user and return token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = {"access_token": access_token, "token_type": "bearer"}
    return response

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