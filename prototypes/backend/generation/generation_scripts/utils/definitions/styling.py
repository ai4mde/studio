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
            radius: int = 8,
            text_color: str = "#111827",
            accent_color: str = "#2563eb",
            background_color: str = "#ffffff",
            font_family: str = "inter",
            page_max_width: str = "xl",
            button_style: str = "solid",
            card_hover: str = "lift",
            image_ratio: str = "4:3",
            divider: str = "none",
    ):
        self.id = id
        self.style_type = style_type
        self.radius = radius
        self.text_color = text_color
        self.accent_color = accent_color
        self.background_color = background_color
        self.font_family = font_family
        self.page_max_width = page_max_width
        self.button_style = button_style
        self.card_hover = card_hover
        self.image_ratio = image_ratio
        self.divider = divider