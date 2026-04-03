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
    CARDS = 7
    TABS = 8
    DRAWER = 9
    CUSTOM = 10

class DisplayMode(Enum):
    TABLE = 1
    CARDS = 2
    LIST = 3

class Styling():
    '''Definition of a Styling object.'''
    def __init__(
            self,
            id: str = uuid4(),
            style_type: StyleType = StyleType.BASIC,
            layout_type: LayoutType = LayoutType.SIDEBAR,
            display_mode: DisplayMode = DisplayMode.TABLE,
            radius: int = 5,
            text_color: str = "#000000",
            accent_color: str = "#777777",
            background_color: str = "#FFFFFF",
            font_url: str = "",
            custom_css: str = "",
            custom_html: str = "",
            custom_page_jinja2: str = "",
            custom_django_templates: dict = None,
    ):
        self.id = id
        self.style_type = style_type
        self.layout_type = layout_type
        self.display_mode = display_mode
        self.radius = radius
        self.text_color = text_color
        self.accent_color = accent_color
        self.background_color = background_color
        self.font_url = font_url
        self.custom_css = custom_css
        self.custom_html = custom_html
        self.custom_page_jinja2 = custom_page_jinja2
        self.custom_django_templates = custom_django_templates or {}