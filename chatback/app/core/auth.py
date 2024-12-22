from typing import Optional
from fastapi import Depends, HTTPException, Security
from app.models.user import User
from jose import JWTError, jwt
from app.core.config import settings
from app.api.deps import oauth2_scheme

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await User.get_by_username(username)
    if user is None:
        raise credentials_exception
    return user 