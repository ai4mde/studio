from .action import ActionClassifier
from .control import ControlClassifier
from .object import ObjectClassifier
from .swimlane import SwimLaneClassifier
 
from typing import Union
 
ActivityClassifier = Union[SwimLaneClassifier, ActionClassifier, ControlClassifier, ObjectClassifier]
 
__all__ = ["ActivityClassifier"]