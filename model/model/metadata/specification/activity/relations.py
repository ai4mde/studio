from pydantic import BaseModel
from pydantic.types import Literal


class ActivityRelation(BaseModel):
    is_directed: bool = True
    guard: str = ""
    weight: str = ""
    type: Literal["activity"] = "activity"
    diagram: Literal["activity"] = "activity"
