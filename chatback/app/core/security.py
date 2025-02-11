from datetime import datetime, timedelta
from typing import Optional, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__rounds=4,  # Number of iterations
    argon2__memory_cost=65536,  # Memory usage in kibibytes
    argon2__parallelism=2  # Number of parallel threads
)

def create_access_token(data: dict[str, Any]) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    if "sub" in to_encode and isinstance(to_encode["sub"], str) and to_encode["sub"].isdigit():
        # Convert user ID to username for sub claim
        from app.models.user import User
        from app.db.session import SessionLocal
        with SessionLocal() as db:
            user = db.query(User).filter(User.id == int(to_encode["sub"])).first()
            if user:
                to_encode["sub"] = user.username
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password) 