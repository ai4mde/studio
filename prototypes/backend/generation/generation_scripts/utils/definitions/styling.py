from enum import Enum
from uuid import uuid4

class StyleType(Enum):
    BASIC = 1
    MODERN = 2
    ABSTRACT = 3

class LayoutType(Enum):
    SIDEBAR = 1
    TOPNAV = 2
    DASHBOARD = 3
    SPLIT = 4
    WIZARD = 5
    MINIMAL = 6

class Styling():
    '''Definition of a Styling object.'''
    def __init__(
            self,
            id: str = uuid4(),
            style_type: StyleType = StyleType.BASIC,
            layout_type: LayoutType = LayoutType.SIDEBAR,
            radius: int = 5,
            text_color: str = "#000000",
            accent_color: str = "#777777",
            background_color: str = "#FFFFFF",
    ):
        self.id = id
        self.style_type = style_type
        self.layout_type = layout_type
        self.radius = radius
        self.text_color = text_color
        self.accent_color = accent_color
        self.background_color = background_color