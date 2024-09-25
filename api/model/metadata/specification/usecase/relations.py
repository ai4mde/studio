from typing import Literal
from pydantic import BaseModel


class UsecaseRelation(BaseModel):
    type: Literal["interaction", "extension", "inclusion"] = "interaction"


__all__ = ["UsecaseRelation"]
