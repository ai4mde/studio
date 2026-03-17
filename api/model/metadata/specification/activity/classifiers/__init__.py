from typing import Union

from .action import ActionClassifier
from .control import ControlClassifier
from .object import ObjectClassifier
from .swimlane import SwimLaneClassifier
from .event import EventClassifier
 
ActivityClassifier = Union[SwimLaneClassifier, ActionClassifier, ControlClassifier, ObjectClassifier, EventClassifier]
 
__all__ = ["ActivityClassifier"]