from pydantic import BaseModel
from pydantic.types import Literal


class UsecaseRelation(BaseModel):
    diagram: Literal["usecase"] = "usecase"
    type: Literal["interaction", "exclusion", "inclusion"] = "interaction"

__all__ = [
    "UsecaseRelation"
]
