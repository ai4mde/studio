from .action import ActionClassifier
from .control import ControlClassifier
from .object import ObjectClassifier

from typing import Union

ActivityClassifier = Union[ActionClassifier, ControlClassifier, ObjectClassifier]

__all__ = ["ActivityClassifier"]
