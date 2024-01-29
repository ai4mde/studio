from typing import Literal
from pydantic import BaseModel


class UsecaseRelation(BaseModel):
    type: Literal["interaction", "exclusion", "inclusion"] = "interaction"


__all__ = ["UsecaseRelation"]
