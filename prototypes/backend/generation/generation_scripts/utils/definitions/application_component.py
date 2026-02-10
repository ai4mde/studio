from utils.sanitization import app_name_sanitization
from typing import List
from utils.definitions.page import Page
from utils.definitions.styling import Styling
from utils.definitions.settings import Settings

class ApplicationComponent():
    '''Definition of an Application Component. One application component
    maps to an input interface, and to an output Django app.'''
    def __init__(
        self,
        id: str,
        project: str,
        name: str,
        categories: List[str],
        pages: List[Page],
        styling: Styling,
        settings: Settings,
        authentication_present: bool = True,
    ):
        self.id = id
        self.project = project
        self.name = app_name_sanitization(name)
        self.categories = categories
        self.pages = pages
        self.styling = styling
        self.settings = settings
        self.authentication_present = authentication_present # TODO: maybe put this in a global settings object

    def __str__(self):
        return self.name