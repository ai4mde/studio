from typing import Union

from .action import ActionClassifier
from .control import ControlClassifier
from .event import EventClassifier
from .object import ObjectClassifier
from .swimlane import SwimLaneClassifier

ActivityClassifier = Union[SwimLaneClassifier, ActionClassifier, ControlClassifier, ObjectClassifier, EventClassifier]
 
__all__ = ["ActivityClassifier"]