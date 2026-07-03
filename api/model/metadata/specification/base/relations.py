from typing import List, Optional

from pydantic import BaseModel


class PositionHandlers(BaseModel):
    x: int
    y: int

class RelationBase(BaseModel):
    position_handlers: Optional[List[PositionHandlers]] = []
