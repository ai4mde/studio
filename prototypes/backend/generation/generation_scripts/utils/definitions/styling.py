from enum import Enum
from uuid import uuid4

class StyleType(Enum):
    BASIC = 1
    MODERN = 2
    ABSTRACT = 3
    ELEGANT = 4
    BRUTALIST = 5
    GLASSMORPHISM = 6
    DARK = 7

class LayoutType(Enum):
    SIDEBAR_LEFT = 1
    SIDEBAR_RIGHT = 2
    TOP_NAV = 3
    TOP_NAV_SIDEBAR = 4

class Styling():
    '''Definition of a Styling object.'''
    def __init__(
            self,
            id: str = uuid4(),
            style_type: StyleType = StyleType.BASIC,
            layout_type: LayoutType = LayoutType.SIDEBAR_LEFT,
            radius: int = 5,
            text_color: str = "#000000", # TODO: might need some backend validation
            accent_color: str = "#777777", # TODO: might need some backend validation
            background_color: str = "#FFFFFF", # TODO: might need some backend validation
    ):
        self.id = id
        self.style_type = style_type
        self.layout_type = layout_type
        self.radius = radius
        self.text_color = text_color
        self.accent_color = accent_color
        self.background_color = background_color