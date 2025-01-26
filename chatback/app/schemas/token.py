from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    id: Optional[str] = None
    username: str
    group_name: Optional[str] = None 