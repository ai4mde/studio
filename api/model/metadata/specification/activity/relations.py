from pydantic import BaseModel
from typing import Literal


class ActivityRelation(BaseModel):
    is_directed: bool = True
    guard: str = ""
    weight: str = ""
    type: Literal["activity"] = "activity"
