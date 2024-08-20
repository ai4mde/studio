from enum import Enum
from uuid import uuid4

class StyleType(Enum):
    BASIC = 1
    MODERN = 2
    ABSTRACT = 3

class Styling():
    '''Definition of a Styling object.'''
    def __init__(
            self,
            id: str = uuid4(),
            style_type: StyleType = StyleType.BASIC,
            radius: int = 5,
            text_color: str = "#000000", # TODO: might need some backend validation
            accent_color: str = "#777777", # TODO: might need some backend validation
            background_color: str = "#FFFFFF", # TODO: might need some backend validation
    ):
        self.id = id
        self.style_type = style_type
        self.radius = radius
        self.text_color = text_color
        self.accent_color = accent_color
        self.background_color = background_color