from pydantic import BaseModel
from typing import Optional, List

class PositionHandlers(BaseModel):
    x: int
    y: int

class RelationBase(BaseModel):
    position_handlers: Optional[List[PositionHandlers]] = []
