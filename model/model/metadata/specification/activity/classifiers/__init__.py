from pydantic import BaseModel
from .action import ActionClassifier
from .control import ControlClassifier
from .object import ObjectClassifier

from pydantic.types import Union, Annotated
from pydantic.fields import Field, Literal

class ActivityClassifier(BaseModel):
    diagram: Literal["activity"] = "activity"
    data: Annotated[
        Union[ActionClassifier, ControlClassifier, ObjectClassifier,],
        Field(
            discriminator="role",
        ),
    ]

__all__ = ["ActivityClassifier"]
